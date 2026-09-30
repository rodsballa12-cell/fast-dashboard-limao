"""Consolida os payloads das unidades (Escova + SPA) num único
data/consolidado/dashboard_data.json somando numéricos leaf-por-leaf,
concatenando rankings com _unidade (escova/spa) — o frontend renderiza
o ícone certo (secador / maca de massagem) — e recalculando
percentuais/médias derivados.

Fonte:
  data/dashboard_data.json      (Escova · path atual)
  data/spa/dashboard_data.json  (SPA · mock por enquanto, real após conexão)

Saída:
  data/consolidado/dashboard_data.json
"""

import json, os, copy
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESC = os.path.join(ROOT, "data", "dashboard_data.json")
SPA = os.path.join(ROOT, "data", "spa", "dashboard_data.json")
DST_DIR = os.path.join(ROOT, "data", "consolidado")
DST = os.path.join(DST_DIR, "dashboard_data.json")

# Chaves que representam PERCENTUAIS ou MÉDIAS — não somam, recalculam ou pegam da Escova
NAO_SOMAR = {
    "pct", "pct_receita", "pct_uso", "pct_atingimento", "utilizacao_pct",
    "cobertura_pct", "delta_pct", "caixa_delta_pct", "atend_delta_pct",
    "ticket_delta_pct", "cliente_dia_delta_pct", "caixa_delta_perdia_pct",
    "atend_delta_perdia_pct", "cliente_dia_delta_perdia_pct",
    "caixa_delta_bruto_pct", "pct_recorrentes", "pareto20_pct",
    "pct_faturamento", "estrelas_media", "rating",
    "ticket_medio", "ticket_medio_serv", "ticket_medio_visita",
    "ltv_medio", "freq_media_visitas", "rs_hora", "rs_hora_salao",
    "media_dia",
}

# Chaves de identidade — pega da Escova (baseline)
IDENTIDADE = {
    "gerado_em", "ano", "mes", "semana", "dia", "dia_semana",
    "periodo_ini", "periodo_fim", "periodo_ini_ref", "periodo_fim_ref",
    "estabelecimento_id", "cnpj", "razao_social", "cor", "cor_bar",
    "descricao", "status", "url", "produto", "marca", "filial",
    "cidade", "data_inauguracao", "cor_accent", "emoji", "data_prefix",
    "trinks_estabelecimento_id", "plano", "cotaTotal", "totalUtilizado",
    "saldoRestante",
}

# Chaves cujos arrays PRESERVAM ordem por índice (dow, hora, meses)
ARRAY_POR_INDICE = {"por_dow", "hora_media", "hora_abs", "meses", "por_dia_mes", "dow_hist"}

# Chaves cujos itens agregam por 'nome' ou 'k' — soma numérico e marca _unidade
# ('escova' / 'spa' / 'ambas') pra o frontend renderizar o ícone certo.
# Categorias/serviços têm taxonomia compartilhada (Unhas, Escova etc.) → não
# marca unidade, só soma.
ARRAY_POR_CHAVE = {
    "categoria_native":     None,   # taxonomia compartilhada, sem _unidade
    "clientes_top":         "nome",
    "top":                  "nome",
    "aniversariantes":      "cliente",
    "cross_sell":           "cliente",
    "obs_alertas":          "cliente",
    "obs_agend_alertas":    "cliente",
}

# Rankings de profissionais — MESMA lógica de ARRAY_POR_CHAVE (agrega por nome
# e marca _unidade), pra prof que trabalha nas duas unidades vire UMA linha
# com ícone 'ambas' em vez de duas linhas duplicadas.
ARRAY_RANKING_PROF = {
    "ranking_prof":          "nome",
    "ranking_prof_executor": "nome",
    "ranking_serv":          "nome",
    "rentabilidade_hora":    "nome",
}


def merge(a, b, path=""):
    if a is None: return copy.deepcopy(b)
    if b is None: return copy.deepcopy(a)
    if isinstance(a, bool) or isinstance(b, bool):
        return a  # bools da escova
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + b  # soma direta
    if isinstance(a, str): return a
    if isinstance(a, list) and isinstance(b, list):
        return merge_list(a, b, path)
    if isinstance(a, dict) and isinstance(b, dict):
        return merge_dict(a, b, path)
    return copy.deepcopy(a)


def merge_dict(a, b, path=""):
    out = {}
    for k in set(a.keys()) | set(b.keys()):
        new_path = f"{path}.{k}" if path else k
        va, vb = a.get(k), b.get(k)
        if k in IDENTIDADE:
            out[k] = copy.deepcopy(va if va is not None else vb)
        elif k in NAO_SOMAR:
            # % e médias: recalcula quando possível depois. Por enquanto, escova.
            out[k] = copy.deepcopy(va if va is not None else vb)
        else:
            out[k] = merge(va, vb, new_path)
    return out


def merge_list(a, b, path=""):
    key = path.split(".")[-1]
    # Arrays por índice (dow, hora, etc.) — soma item-a-item se mesmo tamanho
    if key in ARRAY_POR_INDICE and len(a) == len(b):
        return [merge(x, y, path) for x, y in zip(a, b)]
    # Rankings de prof e agregações por chave (clientes/aniv/cross-sell/…):
    # agrega por nome e anota _unidade: 'escova' | 'spa' | 'ambas'.
    if key in ARRAY_RANKING_PROF or key in ARRAY_POR_CHAVE:
        kname = (ARRAY_RANKING_PROF.get(key) or ARRAY_POR_CHAVE.get(key))
        if kname is None:
            # taxonomia compartilhada (categoria_native) — só soma por nome
            idx = {}
            for x in a + b:
                k = x.get("nome") or "?"
                idx[k] = merge(idx[k], x, path) if k in idx else copy.deepcopy(x)
            return sorted(idx.values(), key=lambda z: -(z.get("v") or 0))
        idx = {}
        origens = {}
        for x in a:
            k = x.get(kname) or "?"
            idx[k] = copy.deepcopy(x); origens[k] = ["escova"]
        for x in b:
            k = x.get(kname) or "?"
            if k in idx:
                idx[k] = merge(idx[k], x, path); origens[k].append("spa")
            else:
                idx[k] = copy.deepcopy(x); origens[k] = ["spa"]
        for k, v in idx.items():
            origs = origens[k]
            v["_unidade"] = "ambas" if len(origs) == 2 else origs[0]
        sort_key = lambda z: -(z.get("v") or z.get("ltv") or 0)
        return sorted(idx.values(), key=sort_key)
    # Categorias top-level (pacotes/servicos/produtos) — merge por índice se dict com 'k'
    if len(a) == len(b) and all(isinstance(x, dict) for x in a) and all(isinstance(y, dict) for y in b):
        # tenta match por 'k' ou 'nome'
        keys_a = [x.get("k") or x.get("nome") for x in a]
        keys_b = [y.get("k") or y.get("nome") for y in b]
        if keys_a == keys_b:
            return [merge(x, y, path) for x, y in zip(a, b)]
    # Fallback: concat
    return a + b


def recalcular_derivados(d):
    """Após somar, alguns campos derivados precisam ser recalculados."""
    for aba_nome in ("anual", "mensal", "semanal", "diario"):
        aba = d.get("abas", {}).get(aba_nome)
        if not aba: continue
        k = aba.get("kpis") or {}
        caixa = k.get("caixa") or 0
        atend = k.get("atend_fin") or 0
        cliente_dia = k.get("cliente_dia") or 0
        if cliente_dia > 0:
            k["ticket_medio"] = round(caixa / cliente_dia, 2)
        # categorias.pct
        cat = aba.get("categorias") or {}
        for tipo, v in cat.items():
            if isinstance(v, dict) and caixa > 0:
                v["pct"] = round((v.get("v") or 0) / caixa * 100, 1)


# ---------------------------------------------------------------------------
# CORREÇÃO DE METAS, DIAS E TICKET DO CONSOLIDADO
#
# A soma cega folha-a-folha (merge) produzia, em 30/09/2026:
#   · "36 dias de 36" (30 do Escova + 6 do Spa) e meta de R$ 80.000 — a meta de
#     um mês CHEIO do Spa, que abriu há 6 dias;
#   · "128,7% do ritmo" e "atrasado em R$ 21 mil" na mesma tela;
#   · ticket alvo de R$ 750 por visita (meta inflada ÷ visitas projetadas com
#     dias dobrados);
#   · sazonalidade somada: peso por dia da semana passando de 100%, n de
#     sábados = 8, horas por dia = 24.
# Dia, semana e mês têm UM calendário; a meta do Spa só conta a partir da
# abertura; projeção = realizado + ritmo somado × dias que faltam.
# ---------------------------------------------------------------------------

def _d(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def _inicio_spa(spa):
    return _d((spa.get("unidade_config") or {}).get("data_inauguracao") or "2026-09-25")


def _janela(aba, hoje):
    """(ini, fim) da aba mensal/semanal/diaria no calendário comum."""
    if aba == "diario":
        return hoje, hoje
    if aba == "semanal":
        ini = hoje - timedelta(days=hoje.weekday())
        return ini, ini + timedelta(days=6)
    if aba == "mensal":
        ini = hoje.replace(day=1)
        prox = (ini.replace(day=28) + timedelta(days=4)).replace(day=1)
        return ini, prox - timedelta(days=1)
    return None, None


def _meta_spa_efetiva(spa, aba, hoje, inicio):
    """(meta_total, meta_ate_hoje) do Spa na janela, contando só depois da abertura."""
    mp = (spa.get("sazonalidade") or {}).get("meta_por_data") or {}
    ini, fim = _janela(aba, hoje)
    if ini is None:  # anual: o Spa já conta a partir da abertura
        m = (spa.get("abas", {}).get("anual", {}).get("meta") or {})
        return m.get("meta") or 0, m.get("meta_ate_hoje") or 0
    tot = ate = 0.0
    for ds, v in mp.items():
        dd = _d(ds)
        if ini <= dd <= fim and dd >= inicio:
            tot += v
            # mesma régua do Escova: "dias realizados" não inclui o dia corrente,
            # exceto na aba do dia, onde o próprio dia é a janela
            if dd < hoje or aba == "diario":
                ate += v
    return round(tot, 2), round(ate, 2)


def _ticket_meta(k, meta, dias_rest, ritmo_vis):
    """Mesma regra do refresh (_inject_ticket_meta), sobre o total consolidado."""
    v_atual = k.get("cliente_dia") or 0
    visitas_proj = round(v_atual + ritmo_vis * dias_rest)
    realizado = meta.get("realizado") or 0
    falta_caixa = (meta.get("meta") or 0) - realizado
    visitas_rest = max(visitas_proj - v_atual, 0)
    ticket_atual = k.get("ticket_medio") or 0
    ticket_alvo_total = (meta.get("meta") or 0) / visitas_proj if visitas_proj > 0 else 0
    if v_atual == 0 and dias_rest == 0:
        status, alvo_rest = "fechado", 0
    elif visitas_rest == 0:
        status = "encerrado_batido" if falta_caixa <= 0 else "encerrado_deficit"
        alvo_rest = 0
    else:
        status = "em_curso"
        alvo_rest = max(falta_caixa, 0) / visitas_rest
    gap = max(alvo_rest - ticket_atual, 0)
    k["ticket_meta"] = round(alvo_rest, 2)
    k["ticket_meta_periodo"] = round(ticket_alvo_total, 2)
    k["ticket_atingimento_pct"] = round(ticket_atual / max(alvo_rest, 1) * 100, 1) if alvo_rest > 0 else (100.0 if status == "encerrado_batido" else 0.0)
    k["ticket_gap_por_atend"] = round(gap, 2)
    k["visitas_projetadas"] = visitas_proj
    k["visitas_restantes"] = visitas_rest
    k["ticket_meta_status"] = status
    k["ticket_meta_deficit_caixa"] = round(max(falta_caixa, 0), 2)
    k["ticket_meta_supera_caixa"] = round(max(-falta_caixa, 0), 2)


def corrigir_consolidado(c, esc, spa):
    hoje = _d(esc.get("hoje") or date.today().isoformat())
    inicio = _inicio_spa(spa)
    esc_saz, spa_saz = esc.get("sazonalidade") or {}, spa.get("sazonalidade") or {}

    # -- sazonalidade: forma (dia da semana, hora, semanas) é a do Escova, que
    #    tem histórico; a meta diária é Escova + Spa depois da abertura.
    saz = copy.deepcopy(esc_saz)
    mp = {}
    for ds, v in (esc_saz.get("meta_por_data") or {}).items():
        mp[ds] = round(v + (((spa_saz.get("meta_por_data") or {}).get(ds) or 0) if _d(ds) >= inicio else 0), 2)
    saz["meta_por_data"] = mp
    soma, cont = {}, {}
    nomes = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    for ds, v in mp.items():
        n = nomes[_d(ds).weekday()]
        soma[n] = soma.get(n, 0) + v
        cont[n] = cont.get(n, 0) + 1
    saz["meta_dia_por_dow"] = {n: round(soma[n] / cont[n], 2) for n in soma}
    saz["_nota_consolidado"] = ("Forma semanal/horária = Escova (tem histórico). Meta diária = Escova + Spa "
                                "contada só a partir da abertura do Spa (%s)." % inicio.isoformat())
    c["sazonalidade"] = saz
    c["dias_atipicos"] = copy.deepcopy(esc.get("dias_atipicos") or {})
    c["dias_op_mes"] = esc.get("dias_op_mes")

    # -- metas, projeção e ticket por aba
    for aba in ("diario", "semanal", "mensal", "anual"):
        ca, ea, sa = (x.get("abas", {}).get(aba) or {} for x in (c, esc, spa))
        if not ca:
            continue
        em, sm = ea.get("meta") or {}, sa.get("meta") or {}
        ek, sk, ck = ea.get("kpis") or {}, sa.get("kpis") or {}, ca.get("kpis") or {}
        if not em:
            continue
        spa_tot, spa_ate = _meta_spa_efetiva(spa, aba, hoje, inicio)
        meta_tot = round((em.get("meta") or 0) + spa_tot, 2)
        meta_ate = round((em.get("meta_ate_hoje") or 0) + spa_ate, 2)
        real = ck.get("caixa") or 0
        rest = em.get("dias_restantes") or 0
        ritmo = (em.get("ritmo_dia") or 0) + (sm.get("ritmo_dia") or 0)
        proj = real + ritmo * rest
        falta = meta_tot - real
        cm = ca.setdefault("meta", {})
        cm.update({
            "meta": meta_tot, "realizado": round(real, 2), "pct": round(real / max(meta_tot, 1) * 100, 1),
            "falta": round(falta, 2), "dias_realizados": em.get("dias_realizados"), "dias_total": em.get("dias_total"),
            "dias_restantes": rest, "necessario_dia": round(falta / rest, 2) if rest else 0.0,
            "ritmo_dia": round(ritmo, 2), "projecao": round(proj, 2),
            "projecao_pct": round(proj / max(meta_tot, 1) * 100, 1),
            "meta_ate_hoje": meta_ate,
            "pct_ate_hoje": round(real / meta_ate * 100, 1) if meta_ate > 0 else None,
            "saldo_ate_hoje": round(real - meta_ate, 2),
            "_meta_escova": em.get("meta"), "_meta_spa": spa_tot,
        })
        # dias operados = calendário comum (não soma de dois calendários)
        ck["dias_op"] = max(ek.get("dias_op") or 0, sk.get("dias_op") or 0)
        horas = ck.get("horas_operacao_periodo") or 0
        if horas > 0:
            ck["rs_hora_salao"] = round(real / horas, 2)
        vis_dia = lambda k: (k.get("cliente_dia") or 0) / max(k.get("dias_op") or 1, 1)
        _ticket_meta(ck, cm, rest, vis_dia(ek) + vis_dia(sk))

    mes = c["abas"]["mensal"]["meta"]
    c["meta_mensal_valor"] = mes["meta"]
    c["metas_franqueadora"] = copy.deepcopy(esc.get("metas_franqueadora") or {})
    # a escala das categorias (meta consolidada ÷ meta Escova) sai do que o front calcula


def _lado(k, m):
    return {
        "faturamento": round(k.get("caixa") or 0, 2), "meta": m.get("meta"), "meta_ate_hoje": m.get("meta_ate_hoje"),
        "pct_meta_ate_hoje": m.get("pct_ate_hoje"), "projecao": m.get("projecao"),
        "visitas": k.get("cliente_dia") or 0, "ticket_medio": k.get("ticket_medio") or 0,
        "dias_op": k.get("dias_op") or 0, "dias_total": m.get("dias_total"),
    }


def anexar_lado_a_lado(c, esc, spa):
    hoje = _d(esc.get("hoje"))
    out = {}
    for aba in ("diario", "semanal", "mensal", "anual"):
        ea, sa, ca = (x.get("abas", {}).get(aba) or {} for x in (esc, spa, c))
        if not ca:
            continue
        spa_tot, spa_ate = _meta_spa_efetiva(spa, aba, hoje, _inicio_spa(spa))
        sm = dict(sa.get("meta") or {}); sm["meta"] = spa_tot; sm["meta_ate_hoje"] = spa_ate
        sm["pct_ate_hoje"] = round((sa.get("kpis", {}).get("caixa") or 0) / spa_ate * 100, 1) if spa_ate else None
        sm["projecao"] = round((sa.get("kpis", {}).get("caixa") or 0) + (sm.get("ritmo_dia") or 0) * (ea.get("meta", {}).get("dias_restantes") or 0), 2)
        sm["dias_total"] = (ea.get("meta") or {}).get("dias_total")  # um calendário só
        out[aba] = {"escova": _lado(ea.get("kpis") or {}, ea.get("meta") or {}),
                    "spa": _lado(sa.get("kpis") or {}, sm),
                    "total": _lado(ca.get("kpis") or {}, ca.get("meta") or {})}
    c["_lado_a_lado"] = out
    ini_e = (esc.get("unidade_config") or {}).get("data_inauguracao") or "2026-07-23"
    ini_s = (spa.get("unidade_config") or {}).get("data_inauguracao") or "2026-09-25"
    dias = lambda i: (hoje - _d(i)).days + 1
    c["_contexto"] = {
        "escova": {"aberta_desde": ini_e, "dias_aberta": dias(ini_e)},
        "spa": {"aberta_desde": ini_s, "dias_aberta": dias(ini_s)},
        "aviso": ("Escova aberta há %d dias, Spa há %d. Comparar mês cheio de uma loja com mês parcial da outra "
                  "inventa queda: a meta do Spa conta só a partir da abertura." % (dias(ini_e), dias(ini_s))),
    }
    st = (esc.get("stone") or {})
    c["_frescor"] = {
        "escova_dashboard": esc.get("gerado_em"), "spa_dashboard": spa.get("gerado_em"),
        "stone_extrato_ate": st.get("periodo_fim"),
    }


def main():
    if not os.path.exists(ESC):
        raise SystemExit("Escova payload não existe.")
    if not os.path.exists(SPA):
        raise SystemExit("SPA payload não existe (rode scripts/build_spa_dashboard.py primeiro).")

    with open(ESC) as f: escova = json.load(f)
    with open(SPA) as f: spa = json.load(f)

    consolidado = merge(escova, spa)
    recalcular_derivados(consolidado)
    corrigir_consolidado(consolidado, escova, spa)
    anexar_lado_a_lado(consolidado, escova, spa)

    consolidado["_consolidado"] = True
    consolidado["_fontes"] = ["escova", "spa"]

    os.makedirs(DST_DIR, exist_ok=True)
    with open(DST, "w") as f:
        json.dump(consolidado, f, indent=2, ensure_ascii=False)
    print(f"[consolida] gerado {DST}")
    esc_c = (escova.get("abas", {}).get("anual", {}).get("kpis", {}).get("caixa") or 0)
    spa_c = (spa.get("abas", {}).get("anual", {}).get("kpis", {}).get("caixa") or 0)
    con_c = (consolidado.get("abas", {}).get("anual", {}).get("kpis", {}).get("caixa") or 0)
    print(f"[consolida] Anual · Escova R$ {esc_c:,.2f} + SPA R$ {spa_c:,.2f} = Consolidado R$ {con_c:,.2f}")


if __name__ == "__main__":
    main()
