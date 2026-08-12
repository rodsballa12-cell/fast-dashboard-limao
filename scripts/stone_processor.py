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
from datetime import date, datetime, timedelta
from pathlib import Path

CARTAO_MEIOS = {"Mastercard", "Visa", "Elo Débito", "Maestro/Redeshop",
                "Visa Electron", "American Express", "Elo Crédito", "Hipercard"}


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


def _agregar_periodo(pix_stone, pix_trinks, cartao_stone_recebiveis, cartao_trinks_vendas):
    """Calcula agregados de um recorte já filtrado por período."""
    matches, orf_s, orf_t = _matchear_pix(pix_stone, pix_trinks)
    pix_bruto = sum(x["valor"] for x in pix_stone)
    pix_tarifa = sum(x["tarifa"] for x in pix_stone)
    pix_trinks_tot = sum(x["valor"] for x in pix_trinks)
    cart_recebido = sum(x["valor"] for x in cartao_stone_recebiveis)
    cart_vendido = sum(x["valor"] for x in cartao_trinks_vendas)
    a_receber = max(0, cart_vendido * 0.965 - cart_recebido)

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
        "resumo": {
            "recebido_total": _r(pix_bruto - pix_tarifa + cart_recebido),
            "a_receber": _r(a_receber),
        },
    }


def processar_stone_csv(csv_path: Path, transacoes_trinks: list, hoje: date | None = None) -> dict | None:
    if not csv_path.exists():
        return None
    hoje = hoje or date.today()

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

    for r in recs:
        tipo = r.get("Tipo", "")
        mov = r.get("Movimentação", "")
        origem = r.get("Origem", "")
        data = _parse_dt(r.get("Data"))
        valor = _pv(r.get("Valor"))
        tarifa = _pv(r.get("Tarifa"))

        if mov == "Crédito" and (tipo == "Pix" or (tipo == "Transação" and origem and origem != "Desconhecido")):
            pix_stone_all.append({"data": data, "valor": valor, "tarifa": tarifa, "origem": origem or ""})
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

    # ==== 2. NORMALIZAR TRINKS ====
    pix_trinks_all = []
    cartao_trinks_all = []
    for t in transacoes_trinks:
        if not t.get("data") or not t.get("meio"): continue
        if t["meio"] == "PIX":
            pix_trinks_all.append({"data": t["data"], "valor": t["valor"], "cliente": t.get("cliente", "")})
        elif t["meio"] in CARTAO_MEIOS:
            cartao_trinks_all.append({"data": t["data"], "valor": t["valor"], "cliente": t.get("cliente", ""), "meio": t["meio"]})

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

    valor_orf_stone = sum(o["valor"] for o in orf_s_all)
    valor_orf_trinks = sum(o["valor"] for o in orf_t_all)
    total_risco = valor_orf_stone + valor_orf_trinks + a_receber_total

    nao_conciliado = {
        "total_valor_risco": _r(total_risco),
        "orfaos_stone_n": len(orf_s_all),
        "orfaos_stone_v": _r(valor_orf_stone),
        "orfaos_stone": orf_s_all[:50],
        "orfaos_trinks_n": len(orf_t_all),
        "orfaos_trinks_v": _r(valor_orf_trinks),
        "orfaos_trinks": orf_t_all[:50],
        "a_receber_d30": _r(a_receber_total),
        "matches_consolidados": len(matches_all),
    }

    # ==== 5. FLUXO CAIXA + META ====
    tot_pix_bruto = sum(x["valor"] for x in pix_stone_all)
    tot_pix_tarifa = sum(x["tarifa"] for x in pix_stone_all)
    tot_cart_liq = sum(x["valor"] for x in cartao_stone_all)
    fluxo = {
        "entradas_pix_liq": _r(tot_pix_bruto - tot_pix_tarifa),
        "entradas_cartao_liq": _r(tot_cart_liq),
        "transf_stone": _r(sum(x["valor"] for x in transf_stone)),
        "saidas_transacao": _r(sum(x["valor"] for x in debitos_transacao)),
        "pix_enviados_v": _r(sum(x["valor"] for x in pix_enviados)),
        "pix_enviados_n": len(pix_enviados),
    }

    recebiveis_lista = [{"data": r["data"].isoformat() if r["data"] else None, "valor": _r(r["valor"])}
                       for r in sorted(cartao_stone_all, key=lambda x: x["data"] or date.min)]

    return {
        "periodo_ini": ini.isoformat() if ini else None,
        "periodo_fim": fim.isoformat() if fim else None,
        "total_lancamentos": len(recs),
        "taxa_pix_pct": round(tot_pix_tarifa / max(tot_pix_bruto, 1) * 100, 3),
        "nao_conciliado": nao_conciliado,
        "por_periodo": por_periodo,
        "fluxo_caixa": fluxo,
        "recebiveis_cartao": recebiveis_lista,
    }
