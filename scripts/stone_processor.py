"""Processa CSV extrato Stone e cruza com Trinks — segmentado por dia/semana/mês/ano.

Retorna estrutura:
{
  "periodo_ini": ..., "periodo_fim": ..., "total_lancamentos": ...,
  "nao_conciliado": {  # prioridade máxima
    "total_valor_risco": ...,
    "orfaos_stone": [...],       # dinheiro caiu, sem match Trinks
    "orfaos_trinks": [...],       # registrado, não caiu
    "a_receber_d30": ...,         # cartões em D+30
    "vendas_sem_transacao_stone": [...],  # cartão vendido, ainda não creditou
  },
  "por_periodo": {
    "hoje":   {pix:{...}, cartao:{...}, resumo:{...}},
    "semana": {...},
    "mes":    {...},
    "ano":    {...}
  },
  "taxa_pix_pct": 0.637,
  "fluxo_caixa": {"entradas":..., "saidas":..., "varredura":...},
  "recebiveis_cartao": [...]
}
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# BRT (UTC-3, sem horário de verão desde 2019). Todo o processador opera em BRT
# — datas do CSV Stone vêm sem timezone e são tratadas como local BRT.
BRT = timezone(timedelta(hours=-3))


def _hoje_brt() -> date:
    """Data de hoje em Brasília, independente do TZ do sistema (container = UTC)."""
    return datetime.now(BRT).date()


def _agora_brt_naive() -> datetime:
    """Datetime naive representando 'agora' em BRT — pra comparar com CSV naive."""
    return datetime.now(BRT).replace(tzinfo=None)

CARTAO_MEIOS = {"Mastercard", "Visa", "Elo Débito", "Maestro/Redeshop",
                "Visa Electron", "American Express", "Elo Crédito", "Hipercard"}

# Modalidade Stone: débito cai em D+1 · crédito 1x cai em D+30
DEBITO_MEIOS = {"Elo Débito", "Maestro/Redeshop", "Visa Electron"}
# Taxas Stone oficiais SIIBELLO (StoneCode 162989011) — MDR sobre venda · antecipação sobre valor a receber
TAXA_MDR = {"debito": 0.0146, "credito1x": 0.0208}
TAXA_ANTECIPACAO_MENSAL = 0.0166  # Automática 1,66% a.m. (Pontual seria 2,26%)


def _pv(s):
    s = str(s or "").replace("R$", "").replace(".", "").replace(",", ".").strip()
    try: return float(s)
    except: return 0.0


def _parse_dt(s):
    if not s: return None
    for fmt in ["%d/%m/%Y %H:%M", "%d/%m/%Y"]:
        try: return datetime.strptime(s[:16] if len(s) > 10 else s[:10], fmt).date()
        except: pass
    return None


def _r(v): return round(float(v or 0), 2)


def _matchear_pix(stone_pix_list, trinks_pix_list):
    """Match em 2 passes:
       1) 1:1 exato por (data, valor ±0.5)
       2) Composto: 1 Trinks = soma de N Stones do MESMO DIA (ex: pagou em 2 PIX)
    Retorna (matches, orfaos_stone, orfaos_trinks)."""
    matches = []
    usados_trinks = set()
    usados_stone = set()

    # --- PASS 1: match 1:1 exato ---
    for si, s in enumerate(stone_pix_list):
        ds = s["data"]; vs = s["valor"]
        best_i, best_diff = None, 1e9
        for i, t in enumerate(trinks_pix_list):
            if i in usados_trinks: continue
            if t["data"] != ds: continue
            diff = abs(t["valor"] - vs)
            if diff < best_diff and diff <= 0.5:
                best_diff, best_i = diff, i
        if best_i is not None:
            usados_trinks.add(best_i)
            usados_stone.add(si)
            matches.append({
                "data": ds.isoformat(), "valor": vs,
                "cliente_trinks": trinks_pix_list[best_i]["cliente"],
                "origem_stone": s["origem"], "tipo": "1:1",
            })

    # --- PASS 2: match composto (múltiplos Stones = 1 Trinks) ---
    # Para cada Trinks órfão, procurar subset de Stones órfãos do mesmo dia que somem o valor
    from itertools import combinations
    for ti, t in enumerate(trinks_pix_list):
        if ti in usados_trinks: continue
        stones_dia = [(si, stone_pix_list[si]) for si in range(len(stone_pix_list))
                      if si not in usados_stone and stone_pix_list[si]["data"] == t["data"]]
        if len(stones_dia) < 2: continue  # composição precisa 2+
        # tenta combinações de 2 a 4 elementos (evita explosão combinatória)
        achou = None
        for tam in range(2, min(5, len(stones_dia) + 1)):
            for combo in combinations(stones_dia, tam):
                soma = sum(x[1]["valor"] for x in combo)
                if abs(soma - t["valor"]) <= 0.5:
                    achou = combo
                    break
            if achou: break
        if achou:
            usados_trinks.add(ti)
            for si, _ in achou:
                usados_stone.add(si)
            origens = " + ".join(f"{x[1]['origem']} R$ {x[1]['valor']:.0f}" for x in achou)
            matches.append({
                "data": t["data"].isoformat(),
                "valor": sum(x[1]["valor"] for x in achou),
                "cliente_trinks": t["cliente"],
                "origem_stone": f"[COMPOSTO {len(achou)}×] {origens}",
                "tipo": f"composto_{len(achou)}",
            })

    # --- ÓRFÃOS finais ---
    orfaos_stone = [
        {"data": stone_pix_list[si]["data"].isoformat() if stone_pix_list[si]["data"] else None,
         "valor": stone_pix_list[si]["valor"], "origem": stone_pix_list[si]["origem"],
         "tarifa": stone_pix_list[si]["tarifa"]}
        for si in range(len(stone_pix_list)) if si not in usados_stone
    ]
    orfaos_trinks = [
        {"data": trinks_pix_list[i]["data"].isoformat(),
         "valor": trinks_pix_list[i]["valor"],
         "cliente": trinks_pix_list[i]["cliente"]}
        for i in range(len(trinks_pix_list)) if i not in usados_trinks
    ]
    return matches, orfaos_stone, orfaos_trinks


def _agregar_periodo(pix_stone, pix_trinks, cartao_stone_recebiveis, cartao_trinks_vendas, dinheiro_trinks=None):
    """Calcula agregados de um recorte já filtrado por período."""
    matches, orf_s, orf_t = _matchear_pix(pix_stone, pix_trinks)
    pix_bruto = sum(x["valor"] for x in pix_stone)
    pix_tarifa = sum(x["tarifa"] for x in pix_stone)
    pix_trinks_tot = sum(x["valor"] for x in pix_trinks)
    cart_recebido = sum(x["valor"] for x in cartao_stone_recebiveis)
    cart_vendido = sum(x["valor"] for x in cartao_trinks_vendas)
    a_receber = max(0, cart_vendido * 0.965 - cart_recebido)
    din = dinheiro_trinks or []
    din_total = sum(x["valor"] for x in din)

    return {
        "pix": {
            "stone_bruto": _r(pix_bruto),
            "stone_liquido": _r(pix_bruto - pix_tarifa),
            "stone_tarifa": _r(pix_tarifa),
            "stone_n": len(pix_stone),
            "trinks_valor": _r(pix_trinks_tot),
            "trinks_n": len(pix_trinks),
            "matches_n": len(matches),
            "orfaos_stone": orf_s,
            "orfaos_trinks": orf_t,
            "diff": _r(pix_bruto - pix_trinks_tot),
        },
        "cartao": {
            "stone_recebido": _r(cart_recebido),
            "stone_n": len(cartao_stone_recebiveis),
            "trinks_vendido": _r(cart_vendido),
            "trinks_n": len(cartao_trinks_vendas),
            "a_receber_d30": _r(a_receber),
        },
        "dinheiro": {
            "total": _r(din_total),
            "n": len(din),
            "transacoes": [{"data": x["data"].isoformat() if x.get("data") else None,
                            "valor": _r(x["valor"]),
                            "cliente": x.get("cliente", "")} for x in din],
        },
        "resumo": {
            "recebido_total": _r(pix_bruto - pix_tarifa + cart_recebido + din_total),
            "a_receber": _r(a_receber),
        },
    }


def processar_stone_csv(csv_path: Path, transacoes_trinks: list, hoje: date | None = None) -> dict | None:
    if not csv_path.exists():
        return None
    hoje = hoje or _hoje_brt()  # BRT · container roda UTC, date.today() daria dia +1 entre 21-00h BRT

    # ==== 1. LER CSV STONE ====
    recs = []
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            with open(csv_path, encoding=enc, newline="") as f:
                for row in csv.DictReader(f): recs.append(row)
            break
        except Exception:
            continue
    if not recs:
        return None

    # Categorizar Stone
    pix_stone_all = []
    cartao_stone_all = []
    transf_stone = []
    debitos_transacao = []
    pix_enviados = []
    resgates_aplicacao = []

    for r in recs:
        tipo = r.get("Tipo", "")
        mov = r.get("Movimentação", "")
        origem = r.get("Origem", "")
        data = _parse_dt(r.get("Data"))
        valor = _pv(r.get("Valor"))
        tarifa = _pv(r.get("Tarifa"))

        if mov == "Crédito" and (tipo == "Pix" or (tipo == "Transação" and origem and origem != "Desconhecido")):
            pix_stone_all.append({"data": data, "valor": valor, "tarifa": tarifa, "origem": origem or ""})
        elif (mov == "Crédito" and tipo == "Transação"
              and origem in ("", "Desconhecido")
              and "STONE" in (r.get("Origem Instituição") or "").upper()):
            # RESGATE da aplicação: dinheiro voltando da reserva para a conta.
            # Não é entrada nova (não é venda) — é caixa que já estava contabilizado
            # saindo da reserva, normalmente para uma sangria via PIX logo em seguida.
            # Sem esta categoria o resgate ficava invisível e o saldo da reserva só
            # crescia: em 04/09 saíram R$ 28.965,12 para a conta XP e o painel seguiu
            # mostrando o valor como se ainda estivesse aplicado.
            resgates_aplicacao.append({"data": data, "valor": valor})
        elif mov == "Crédito" and tipo == "Recebível de Cartão":
            cartao_stone_all.append({"data": data, "valor": valor})
        elif mov == "Crédito" and tipo == "Transferência entre contas Stone":
            transf_stone.append({"data": data, "valor": valor})
        elif mov == "Débito" and tipo == "Transação":
            debitos_transacao.append({"data": data, "valor": abs(valor)})
        elif mov == "Débito" and tipo == "Pix":
            pix_enviados.append({"data": data, "valor": abs(valor)})

    datas_stone = sorted({r["data"] for r in pix_stone_all + cartao_stone_all if r["data"]})
    ini = datas_stone[0] if datas_stone else None
    fim = datas_stone[-1] if datas_stone else None

    # ==== 2. NORMALIZAR TRINKS (separa débito D+1 de crédito D+30) ====
    pix_trinks_all = []
    cartao_trinks_all = []
    debito_trinks_all = []
    credito_trinks_all = []
    dinheiro_trinks_all = []
    for t in transacoes_trinks:
        if not t.get("data") or not t.get("meio"): continue
        if t["meio"] == "PIX":
            pix_trinks_all.append({"data": t["data"], "valor": t["valor"], "cliente": t.get("cliente", "")})
        elif t["meio"] in CARTAO_MEIOS:
            item = {"data": t["data"], "valor": t["valor"], "cliente": t.get("cliente", ""), "meio": t["meio"], "parcelas": t.get("parcelas", 1)}
            cartao_trinks_all.append(item)
            if t["meio"] in DEBITO_MEIOS:
                debito_trinks_all.append(item)
            else:
                credito_trinks_all.append(item)
        elif t["meio"] == "Dinheiro":
            if t["valor"] > 0:
                dinheiro_trinks_all.append({"data": t["data"], "valor": t["valor"], "cliente": t.get("cliente", "")})

    # ==== 3. FUNÇÃO FILTRO POR PERÍODO ====
    def filtrar(items, ini_p, fim_p):
        return [x for x in items if x.get("data") and ini_p <= x["data"] <= fim_p]

    seg = hoje - timedelta(days=hoje.weekday())    # segunda da semana atual
    dom = seg + timedelta(days=6)
    ini_mes = date(hoje.year, hoje.month, 1)
    from calendar import monthrange
    fim_mes = date(hoje.year, hoje.month, monthrange(hoje.year, hoje.month)[1])
    ini_ano = date(hoje.year, 1, 1)
    fim_ano = date(hoje.year, 12, 31)

    periodos = {
        "hoje":   (hoje, hoje),
        "semana": (seg, dom),
        "mes":    (ini_mes, fim_mes),
        "ano":    (ini_ano, fim_ano),
    }

    por_periodo = {}
    for nome, (a, b) in periodos.items():
        por_periodo[nome] = _agregar_periodo(
            filtrar(pix_stone_all, a, b),
            filtrar(pix_trinks_all, a, b),
            filtrar(cartao_stone_all, a, b),
            filtrar(cartao_trinks_all, a, b),
            filtrar(dinheiro_trinks_all, a, b),
        )
        por_periodo[nome]["periodo_ini"] = a.isoformat()
        por_periodo[nome]["periodo_fim"] = b.isoformat()

    # ==== 4. NÃO CONCILIADO CONSOLIDADO (todo o extrato) ====
    matches_all, orf_s_all, orf_t_all = _matchear_pix(pix_stone_all, pix_trinks_all)

    # Cartões: vendas Trinks sem crédito Stone (D+30 pendente)
    cartao_trinks_periodo = filtrar(cartao_trinks_all, ini or hoje, fim or hoje)
    cart_stone_periodo = filtrar(cartao_stone_all, ini or hoje, fim or hoje)
    total_vendido_cart = sum(x["valor"] for x in cartao_trinks_periodo)
    total_recebido_cart = sum(x["valor"] for x in cart_stone_periodo)
    a_receber_total = max(0, total_vendido_cart * 0.965 - total_recebido_cart)

    # === RECONCILIAÇÕES MANUAIS: filtra órfãos Trinks confirmados fora do Stone ===
    # (ex: PIX que foi feito direto pra conta XP, não passou pelo Stone).
    # Lista vem de data/config.json > reconciliacoes_manuais.itens.
    import json as _json, os as _os
    reconc_manuais = []
    try:
        cfg_path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "data", "config.json")
        _cfg = _json.loads(open(cfg_path, encoding="utf-8").read())
        reconc_manuais = (_cfg.get("reconciliacoes_manuais") or {}).get("itens") or []
    except Exception:
        reconc_manuais = []

    def _bate_reconc(orf, reconc):
        try:
            if orf.get("data") != reconc.get("data"): return False
            if abs(float(orf.get("valor", 0)) - float(reconc.get("valor", 0))) > 0.01: return False
            token = (reconc.get("cliente_contem") or "").lower().strip()
            if token and token not in (orf.get("cliente") or "").lower(): return False
            return True
        except Exception:
            return False

    orf_t_reconciliados = []
    orf_t_pendentes = []
    for orf in orf_t_all:
        marcado = next((r for r in reconc_manuais if _bate_reconc(orf, r)), None)
        if marcado:
            orf_t_reconciliados.append({**orf, "motivo": marcado.get("motivo", ""), "confirmado_em": marcado.get("confirmado_em")})
        else:
            orf_t_pendentes.append(orf)

    valor_orf_stone = sum(o["valor"] for o in orf_s_all)
    valor_orf_trinks = sum(o["valor"] for o in orf_t_pendentes)  # só pendentes contam como risco
    total_risco = valor_orf_stone + valor_orf_trinks + a_receber_total

    nao_conciliado = {
        "total_valor_risco": _r(total_risco),
        "orfaos_stone_n": len(orf_s_all),
        "orfaos_stone_v": _r(valor_orf_stone),
        "orfaos_stone": orf_s_all[:50],
        "orfaos_trinks_n": len(orf_t_pendentes),
        "orfaos_trinks_v": _r(valor_orf_trinks),
        "orfaos_trinks": orf_t_pendentes[:50],
        "orfaos_trinks_reconciliados_n": len(orf_t_reconciliados),
        "orfaos_trinks_reconciliados_v": _r(sum(o["valor"] for o in orf_t_reconciliados)),
        "orfaos_trinks_reconciliados": orf_t_reconciliados[:50],
        "a_receber_d30": _r(a_receber_total),
        "matches_consolidados": len(matches_all),
    }

    # ==== 5. FLUXO CAIXA + META ====
    tot_pix_bruto = sum(x["valor"] for x in pix_stone_all)
    tot_pix_tarifa = sum(x["tarifa"] for x in pix_stone_all)
    tot_cart_liq = sum(x["valor"] for x in cartao_stone_all)
    tot_saidas = sum(x["valor"] for x in debitos_transacao)
    tot_retornos = sum(x["valor"] for x in transf_stone)
    fluxo = {
        "entradas_pix_liq": _r(tot_pix_bruto - tot_pix_tarifa),
        "entradas_cartao_liq": _r(tot_cart_liq),
        "transf_stone": _r(tot_retornos),
        "saidas_transacao": _r(tot_saidas),
        "pix_enviados_v": _r(sum(x["valor"] for x in pix_enviados)),
        "pix_enviados_n": len(pix_enviados),
    }

    # ==== 6. APLICAÇÃO RESERVA STONE ====
    # Padrão: cada crédito → débito "Transação" imediato = VARREDURA para a aplicação.
    # As varreduras se acumulam, MENOS os resgates (crédito "Transação" vindo da
    # própria Stone), que são dinheiro voltando da reserva para a conta — em geral
    # às vésperas de uma sangria via PIX para o banco principal.
    from collections import defaultdict
    aportes_dia = defaultdict(float)
    transfer_recebidas_dia = defaultdict(float)
    resgates_dia = defaultdict(float)
    for x in debitos_transacao:
        if x["data"]: aportes_dia[x["data"]] += x["valor"]
    for x in transf_stone:
        if x["data"]: transfer_recebidas_dia[x["data"]] += x["valor"]
    for x in resgates_aplicacao:
        if x["data"]: resgates_dia[x["data"]] += x["valor"]

    tot_resgates = sum(x["valor"] for x in resgates_aplicacao)
    saldo_reserva = tot_saidas - tot_resgates

    dias_ord = sorted(set(list(aportes_dia.keys()) + list(transfer_recebidas_dia.keys())
                          + list(resgates_dia.keys())))
    historico = []
    saldo_acum = 0
    for d in dias_ord:
        s = aportes_dia.get(d, 0)
        r = transfer_recebidas_dia.get(d, 0)
        g = resgates_dia.get(d, 0)
        saldo_acum += s - g
        historico.append({
            "data": d.isoformat(),
            "aporte": _r(s),
            "resgate": _r(g),
            "transf_recebida": _r(r),
            "saldo_aplicado_acum": _r(saldo_acum),
        })

    # Rendimento estimado: CDI ~14,5% a.a. ≈ 1,13% a.m., apropriado dia a dia sobre o
    # saldo efetivamente aplicado naquele dia. A versão anterior ponderava só os aportes
    # pelo tempo, o que ignorava resgates e passou a superestimar assim que houve um.
    #
    # Duas janelas, porque um resgate separa dois dinheiros diferentes:
    #  · período  = tudo desde o início do extrato (inclui juros de dinheiro já sacado)
    #  · atual    = só depois do último resgate, que é o que ainda está rendendo
    # Sem essa separação, o "saldo + rendimento" somaria a um saldo de R$ 7 mil os juros
    # de um saldo de R$ 29 mil que já foi para a XP.
    CDI_DIA_PCT = 1.13 / 30
    ultimo_resgate_d = max((d for d, v in resgates_dia.items() if v > 0), default=None)

    saldo_dia_acum = 0.0
    soma_saldo_dias_atual = 0.0
    rendimento_periodo_r = 0.0
    rendimento_atual_r = 0.0
    if dias_ord:
        d = dias_ord[0]
        while d <= hoje:
            saldo_dia_acum += aportes_dia.get(d, 0) - resgates_dia.get(d, 0)
            rendimento_periodo_r += saldo_dia_acum * CDI_DIA_PCT / 100
            if ultimo_resgate_d is None or d > ultimo_resgate_d:
                soma_saldo_dias_atual += saldo_dia_acum
                rendimento_atual_r += saldo_dia_acum * CDI_DIA_PCT / 100
            d += timedelta(days=1)

    # "dias médios" = quantos dias o saldo ATUAL equivale a ter ficado aplicado
    dias_medio_aporte = soma_saldo_dias_atual / saldo_reserva if saldo_reserva > 0 else 0
    rendimento_estimado_r = rendimento_atual_r
    rendimento_estimado_pct = (rendimento_atual_r / saldo_reserva * 100) if saldo_reserva > 0 else 0

    aplicacao_reserva = {
        "saldo_aplicado": _r(saldo_reserva),
        "total_aportes_periodo": _r(tot_saidas),
        "total_resgates_periodo": _r(tot_resgates),
        "resgates_n": len(resgates_aplicacao),
        "ultimo_resgate": max((x["data"] for x in resgates_aplicacao if x["data"]), default=None),
        "transf_recebidas_periodo": _r(tot_retornos),
        "dias_medio_aporte": round(dias_medio_aporte, 1),
        "rendimento_estimado_pct": round(rendimento_estimado_pct, 2),
        "rendimento_estimado_r": _r(rendimento_estimado_r),
        "rendimento_periodo_r": _r(rendimento_periodo_r),
        "saldo_com_rendimento_estimado": _r(saldo_reserva + rendimento_estimado_r),
        "historico_dias": len(historico),
        "ultimos_movs": historico[-10:],
        "obs": ("Saldo = varreduras acumuladas menos resgates. Rendimento estimado usa "
                "CDI ~14,5% a.a. apropriado dia a dia sobre o saldo do dia — é estimativa, "
                "o valor oficial é o do app Stone."),
    }
    if aplicacao_reserva["ultimo_resgate"]:
        aplicacao_reserva["ultimo_resgate"] = aplicacao_reserva["ultimo_resgate"].isoformat()

    recebiveis_lista = [{"data": r["data"].isoformat() if r["data"] else None, "valor": _r(r["valor"])}
                       for r in sorted(cartao_stone_all, key=lambda x: x["data"] or date.min)]

    # ==== ANÁLISE DE ANTECIPAÇÃO (sobre o que ainda NÃO foi liberado) ====
    # A versão anterior somava as vendas do MÊS CORRENTE inteiro. Isso dava um número
    # que não fechava com o "aguardando liberação" por dois motivos ao mesmo tempo:
    #   1. incluía o débito do mês, que cai em D+1 e a essa altura já caiu — não dá
    #      para antecipar dinheiro que já está na conta;
    #   2. excluía o crédito 1x do mês ANTERIOR, que cai em D+30 e é justamente o
    #      grosso da fila de liberação.
    # Agora cada venda tem uma data prevista de liberação (D+1 débito · D+30 crédito)
    # e só entra na conta o que ainda não venceu. O custo da antecipação é proporcional
    # aos dias que faltam para cada venda, não 1,66% cheio para todo mundo.
    PRAZO_DIAS = {"debito": 1, "credito1x": 30}

    def _pendentes(vendas, prazo):
        out = []
        for x in vendas:
            if not x.get("data"): continue
            libera = x["data"] + timedelta(days=prazo)
            if libera > hoje:
                out.append({**x, "libera": libera, "dias_restantes": (libera - hoje).days})
        return out

    def _bloco_antec(vendas, mdr, prazo):
        bruto = sum(x["valor"] for x in vendas)
        liq_espera = bruto * (1 - mdr)
        # custo pro-rata: taxa mensal / 30 × dias que faltam, venda a venda
        custo = sum(x["valor"] * (1 - mdr) * TAXA_ANTECIPACAO_MENSAL / 30 * x["dias_restantes"]
                    for x in vendas)
        dias_med = (sum(x["valor"] * x["dias_restantes"] for x in vendas) / bruto) if bruto else 0
        return {
            "bruto": _r(bruto), "n": len(vendas),
            "mdr_pct": mdr * 100,
            "liq_espera": _r(liq_espera),
            "liq_antecipar": _r(liq_espera - custo),
            "custo_antecipacao": _r(custo),
            # prazo contratual da modalidade (D+N). NÃO mexer no significado: o ciclo
            # de caixa do painel lê este campo como o D+N da liquidação.
            "dias_medio_recebimento": prazo,
            # dias que ainda faltam, ponderados por valor — é o que precifica a antecipação
            "dias_medio_restante": round(dias_med, 1),
            "prazo_dias": prazo,
        }

    debito_pend = _pendentes(debito_trinks_all, PRAZO_DIAS["debito"])
    credito_pend = _pendentes(credito_trinks_all, PRAZO_DIAS["credito1x"])
    b_deb = _bloco_antec(debito_pend, TAXA_MDR["debito"], PRAZO_DIAS["debito"])
    b_cre = _bloco_antec(credito_pend, TAXA_MDR["credito1x"], PRAZO_DIAS["credito1x"])

    tot_liq_espera = b_deb["liq_espera"] + b_cre["liq_espera"]
    tot_custo = b_deb["custo_antecipacao"] + b_cre["custo_antecipacao"]

    # Fila de liberação por semana — quando cada lote cai, se não antecipar
    fila = defaultdict(float)
    for x in debito_pend + credito_pend:
        fila[x["libera"].isoformat()] += x["valor"]
    cronograma = [{"data": d, "bruto": _r(v)} for d, v in sorted(fila.items())]

    antecipacao = {
        "debito": b_deb,
        "credito": b_cre,
        "total": {
            "bruto": _r(b_deb["bruto"] + b_cre["bruto"]),
            "liq_espera": _r(tot_liq_espera),
            "liq_antecipar": _r(tot_liq_espera - tot_custo),
            "custo_antecipacao": _r(tot_custo),
            "custo_pct": round(tot_custo / max(tot_liq_espera, 1) * 100, 2),
        },
        # Confronto com o "aguardando liberação" do card de reconciliação. Os dois
        # números medem a mesma fila por caminhos diferentes: este parte das vendas
        # do Trinks ainda não vencidas; o outro parte do extrato Stone (vendido menos
        # creditado). Uma diferença pequena é normal (MDR médio × MDR por modalidade,
        # venda registrada fora do horário do extrato); uma diferença grande é sinal
        # de recebível atrasado e merece conferência no app da Stone.
        "confronto_a_receber": {
            "a_receber_extrato": _r(a_receber_total),
            "pendente_vendas": _r(tot_liq_espera),
            "diferenca": _r(tot_liq_espera - a_receber_total),
        },
        "cronograma_liberacao": cronograma[:30],
        "taxa_antecipacao_mensal_pct": TAXA_ANTECIPACAO_MENSAL * 100,
        "obs": ("Só vendas ainda não liberadas (débito D+1 · crédito 1x D+30). Taxas Stone "
                "oficiais SIIBELLO (Débito 1,46% · Crédito 1x 2,08% · Antecipação Automática "
                "1,66% a.m., cobrada pro-rata pelos dias que faltam). Todas as vendas são 1x."),
    }

    # ==== 7. GAP TEMPORAL Trinks × Stone (vendas apos ultimo lancamento CSV) ====
    # Trinks é ao vivo · CSV Stone é snapshot manual. Vendas Trinks feitas APÓS a última
    # movimentação do CSV Stone naturalmente NÃO aparecem na reconciliação.
    from datetime import datetime as _dt
    ultima_dt_stone = None
    for row in recs:
        try:
            data_str = row.get("Data", "")[:16]
            for fmt in ["%d/%m/%Y %H:%M", "%d/%m/%Y"]:
                try:
                    dt_row = _dt.strptime(data_str, fmt)
                    if ultima_dt_stone is None or dt_row > ultima_dt_stone:
                        ultima_dt_stone = dt_row
                    break
                except: pass
        except: pass

    vendas_apos = []
    if ultima_dt_stone:
        limite = ultima_dt_stone
        for t in transacoes_trinks:
            if not t.get("data") or not t.get("meio"): continue
            if t["meio"] not in (list(CARTAO_MEIOS) + ["PIX"]): continue
            # usa datetime completo se disponível, senão fim do dia
            t_dt = t.get("data_hora") or _dt.combine(t["data"], _dt.max.time())
            if t_dt > limite:
                vendas_apos.append({
                    "data": t_dt.isoformat(timespec="minutes") if hasattr(t_dt, 'isoformat') else t["data"].isoformat(),
                    "valor": _r(t["valor"]),
                    "meio": t["meio"],
                    "cliente": t.get("cliente", ""),
                })

    gap_trinks_stone = {
        "ultima_data_stone": ultima_dt_stone.isoformat() if ultima_dt_stone else None,
        "vendas_trinks_apos_n": len(vendas_apos),
        "vendas_trinks_apos_v": _r(sum(x["valor"] for x in vendas_apos)),
        "vendas_apos_lista": vendas_apos[:50],
        "horas_desatualizado": round((_agora_brt_naive() - ultima_dt_stone).total_seconds() / 3600, 1) if ultima_dt_stone else 0,
    }

    return {
        "periodo_ini": ini.isoformat() if ini else None,
        "periodo_fim": fim.isoformat() if fim else None,
        "total_lancamentos": len(recs),
        # taxa cobrada pelo Stone sobre volume PIX (custo médio efetivo)
        "pix_tarifa_pct": round(tot_pix_tarifa / max(tot_pix_bruto, 1) * 100, 3),
        # alias de compat — some quando o front for atualizado
        "taxa_pix_pct": round(tot_pix_tarifa / max(tot_pix_bruto, 1) * 100, 3),
        "nao_conciliado": nao_conciliado,
        "por_periodo": por_periodo,
        "fluxo_caixa": fluxo,
        "recebiveis_cartao": recebiveis_lista,
        "antecipacao_analise": antecipacao,
        "aplicacao_reserva": aplicacao_reserva,
        "gap_trinks_stone": gap_trinks_stone,
    }
