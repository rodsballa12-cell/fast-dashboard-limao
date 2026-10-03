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
    # Taxas do bloco Stone — somar duas taxas da 1,286 em vez de 0,643.
    # So aparecem no consolidado quando as duas unidades tem extrato proprio.
    "taxa_pix_pct", "pix_tarifa_pct", "taxa_antecipacao_mensal_pct",
    "rendimento_estimado_pct",
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
    "top":                  "nome",   # default; subcontextos abaixo tem chave propria
    "aniversariantes":      "cliente",
    "cross_sell":           "cliente",
    "obs_alertas":          "cliente",
    "obs_agend_alertas":    "cliente",
}

# Alguns 'top' sao de clientes (cross_sell.top / churn_early.top) e portanto
# usam a chave 'cliente', nao 'nome'. Sem este override, o merge agrupava
# todos no mesmo bucket "?" e sobrava 1 linha no consolidado — era por isso
# que, em 03/10, cross_sell e churn apareciam com 1 so cliente.
TOP_KEY_POR_PARENT = {
    "cross_sell":   "cliente",
    "churn_early":  "cliente",
    "top_ltv":      "nome",
}
# Ordenacao especifica por caminho (lambda sobre o item). Preserva a
# priorizacao original de cada card do backend quando o merge do consolidado
# junta duas listas ja ordenadas.
SORT_POR_PATH = {
    "aniversariantes":   lambda z: (z.get("dias", 999), -(z.get("ltv") or 0)),
    "cross_sell.top":    lambda z: -(z.get("ltv") or 0),
    "churn_early.top":   lambda z: -(z.get("ltv") or 0),
    "top_ltv.top":       lambda z: -(z.get("v") or 0),
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
    parts = path.split(".")
    parent = parts[-2] if len(parts) >= 2 else ""
    # SEGMENTAÇÕES (seg_canal/seg_bairro/seg_genero) · top por nome
    # Rodrigo (03/10): no consolidado, cada linha mostra uma barra empilhada
    # entre Escova (amarelo) e SPA (teal). Pra isso, carregamos no item do
    # consolidado as receitas separadas por unidade além do total somado.
    # pct_receita é recalculado em recalcular_derivados() porque o cálculo
    # depende do total consolidado da base (não da soma dos tops).
    if key == "top" and parent in ("seg_canal", "seg_bairro", "seg_genero"):
        idx = {}
        for src_unit, items in (("escova", a or []), ("spa", b or [])):
            for x in items:
                k = (x.get("nome") or "?")
                if k not in idx:
                    idx[k] = {
                        "nome": x.get("nome"),
                        "n_clientes": 0,
                        "receita": 0.0,
                        "receita_escova": 0.0,
                        "receita_spa": 0.0,
                        "n_escova": 0,
                        "n_spa": 0,
                    }
                r = float(x.get("receita") or 0)
                n = int(x.get("n_clientes") or 0)
                idx[k]["n_clientes"] += n
                idx[k]["receita"] += r
                if src_unit == "escova":
                    idx[k]["receita_escova"] += r
                    idx[k]["n_escova"] += n
                else:
                    idx[k]["receita_spa"] += r
                    idx[k]["n_spa"] += n
        for v in idx.values():
            v["receita"] = round(v["receita"], 2)
            v["receita_escova"] = round(v["receita_escova"], 2)
            v["receita_spa"] = round(v["receita_spa"], 2)
            if v["n_clientes"] > 0:
                v["ticket_medio_cliente"] = round(v["receita"] / v["n_clientes"], 2)
            v["_unidade"] = ("ambas" if v["n_escova"] > 0 and v["n_spa"] > 0
                             else ("escova" if v["n_escova"] > 0 else "spa"))
        return sorted(idx.values(), key=lambda z: -(z.get("receita") or 0))
    # Arrays por índice (dow, hora, etc.) — soma item-a-item se mesmo tamanho
    if key in ARRAY_POR_INDICE and len(a) == len(b):
        return [merge(x, y, path) for x, y in zip(a, b)]
    # Rankings de prof e agregações por chave (clientes/aniv/cross-sell/…):
    # agrega por nome e anota _unidade: 'escova' | 'spa' | 'ambas'.
    if key in ARRAY_RANKING_PROF or key in ARRAY_POR_CHAVE:
        # Para 'top' aninhado em cross_sell/churn_early/top_ltv, respeita o
        # pai pra escolher a chave de agregacao (cliente vs nome). Antes
        # (03/10) o merge usava 'nome' sempre em 'top' — mas cross_sell.top
        # e churn_early.top tem 'cliente', e todos caiam em k='?'.
        if key == "top" and parent in TOP_KEY_POR_PARENT:
            kname = TOP_KEY_POR_PARENT[parent]
        else:
            kname = (ARRAY_RANKING_PROF.get(key) or ARRAY_POR_CHAVE.get(key))
        if kname is None:
            # taxonomia compartilhada (categoria_native) — soma por nome +
            # guarda v_escova / v_spa pra o frontend pintar barras empilhadas
            # Esc (amarelo) × SPA (teal). Rodrigo (03/10): "aplique em todas
            # as barras".
            idx = {}
            for src_unit, items in (("escova", a or []), ("spa", b or [])):
                for x in items:
                    k = x.get("nome") or "?"
                    if k not in idx:
                        base = copy.deepcopy(x)
                        base["v"] = 0.0
                        base["n"] = 0
                        base["v_escova"] = 0.0
                        base["v_spa"] = 0.0
                        base["n_escova"] = 0
                        base["n_spa"] = 0
                        idx[k] = base
                    v = float(x.get("v") or 0)
                    n = int(x.get("n") or 0)
                    idx[k]["v"] += v
                    idx[k]["n"] += n
                    if src_unit == "escova":
                        idx[k]["v_escova"] += v
                        idx[k]["n_escova"] += n
                    else:
                        idx[k]["v_spa"] += v
                        idx[k]["n_spa"] += n
            for v in idx.values():
                v["v"] = round(v["v"], 2)
                v["v_escova"] = round(v["v_escova"], 2)
                v["v_spa"] = round(v["v_spa"], 2)
                # pct_receita precisa recalcular — merge cego preservou da Escova
                # (sera refeito em recalcular_derivados sobre o total consolidado)
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
        # Priorizacao por path respeita o criterio original do card. Fallback
        # para o antigo (v -> ltv) em paths nao mapeados.
        # Testamos tanto o caminho completo quanto parent+key, porque path
        # cresce com abas.anual.* e etc.
        sort_fn = None
        for sp, fn in SORT_POR_PATH.items():
            if path.endswith("." + sp) or path == sp or path.endswith(sp):
                sort_fn = fn; break
        if sort_fn is None and key in SORT_POR_PATH:
            sort_fn = SORT_POR_PATH[key]
        if sort_fn is None:
            sort_fn = lambda z: -(z.get("v") or z.get("ltv") or 0)
        return sorted(idx.values(), key=sort_fn)
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
        # categoria_native: recalcular pct_receita sobre o caixa consolidado
        # (merge cego preservava o pct da Escova — somava mas o percentual
        # ficava subavaliado no consolidado).
        cnat = aba.get("categoria_native") or []
        if cnat and caixa > 0:
            for c in cnat:
                if isinstance(c, dict):
                    c["pct_receita"] = round((c.get("v") or 0) / caixa * 100, 1)
        # segmentações: pct_receita, cobertura_pct, sem_dado — merge cego do
        # NAO_SOMAR preservava os valores da Escova; aqui recalculamos sobre a
        # base consolidada. "Está somando os percentuais" (Rodrigo, 03/10): a
        # soma dos pct_receita do top passava a cobertura por causa disso.
        for seg_key in ("seg_canal", "seg_bairro", "seg_genero"):
            seg = aba.get(seg_key)
            if not isinstance(seg, dict): continue
            top = seg.get("top") or []
            sem = seg.get("sem_dado") or {}
            soma_top_r = sum((t.get("receita") or 0) for t in top)
            sem_r = sem.get("receita") or 0
            total_r = soma_top_r + sem_r
            if total_r > 0:
                for t in top:
                    t["pct_receita"] = round((t.get("receita") or 0) / total_r * 100, 1)
                seg["cobertura_pct"] = round(soma_top_r / total_r * 100, 1)
            # n absolutos de sem_dado também somam dos dois (merge cego ignorou)
            # e cobertura por N: n_com_canal / n_total
            soma_top_n = sum((t.get("n_clientes") or 0) for t in top)
            sem_n = sem.get("n") or 0
            total_n = soma_top_n + sem_n
            if total_n > 0 and total_r > 0:
                # usa receita como medida principal (padrão original); n fica informativo
                pass


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
    """Desde quando a meta do Spa conta.

    Rodrigo, 28/09/2026: "20k para o mês de setembro, não rateado". A meta do
    Spa vale CHEIA no mês da abertura — o mesmo critério do Financeiro e do
    painel do próprio Spa. (Em 30/09 eu tinha ratado por conta própria; isso
    deixava o Painel em R$ 63,9 mil e o Financeiro em R$ 80 mil para o mesmo mês.)
    Para voltar a ratear, devolva a data de inauguração aqui.
    """
    return date(2000, 1, 1)


def _inauguracao_spa(spa):
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
    # janela toda coberta: usa a meta da própria unidade, sem a poeira de arredondar dia a dia
    if inicio <= ini:
        tot = (spa.get("abas", {}).get(aba, {}).get("meta") or {}).get("meta") or tot
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
    saz["_nota_consolidado"] = ("Forma semanal/horária = Escova (tem histórico). Meta diária = Escova + Spa, "
                                "a do Spa cheia no mês (sem ratear, decisão de 28/09/2026).")
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


# ---------------------------------------------------------------------------
# MIGRAÇÃO CRUZADA (03/10/2026 · Rodrigo)
# "Preciso no consolidado algo que me ajude a migrar cliente do escova pro
# spa e vice-versa." São dois negócios no mesmo endereço — o cliente da Escova
# é o lead mais barato pro SPA e vice-versa.
# Regras:
#   - escova_para_spa: cliente que SÓ foi na Escova e tem base pra justificar
#     a mensagem (>= 2 visitas · LTV > 0 · tem telefone)
#   - spa_para_escova: cliente que SÓ foi no SPA (>= 1 visita, SPA é mais
#     esporádico) com LTV > 0 e telefone
#   - "ambas" sai dos dois (já migrou organicamente)
# Match por nome normalizado (title-case strip espaço), aproximação suficiente
# porque o Trinks exige nome completo e o top_ltv já title-case.
# ---------------------------------------------------------------------------
def _norm_nome(s):
    return (s or "").strip().lower()


# Qualidade do cadastro (clientes_cadastro.cobertura): o merge somava
# leaf-by-leaf (telefone 100% esc + 93% spa = 193%). Aqui recalculamos a
# cobertura consolidada como media PONDERADA por total de clientes de cada
# unidade, e expomos cobertura_escova / cobertura_spa pra o frontend pintar
# a divisao nas cores das unidades.
def anexar_cadastro_consolidado(c, esc, spa):
    cad_esc = (esc.get("abas", {}).get("anual", {}) or {}).get("clientes_cadastro") or {}
    cad_spa = (spa.get("abas", {}).get("anual", {}) or {}).get("clientes_cadastro") or {}
    cob_esc = cad_esc.get("cobertura") or {}
    cob_spa = cad_spa.get("cobertura") or {}
    tot_esc = int(cad_esc.get("total") or 0)
    tot_spa = int(cad_spa.get("total") or 0)
    tot = tot_esc + tot_spa
    if tot <= 0: return
    campos = set(cob_esc) | set(cob_spa)
    cob_cons = {}
    for k in campos:
        pe = float(cob_esc.get(k) or 0)
        ps = float(cob_spa.get(k) or 0)
        # ponderado: (pe * tot_esc + ps * tot_spa) / tot
        cob_cons[k] = round((pe * tot_esc + ps * tot_spa) / tot, 1)
    anual = c.setdefault("abas", {}).setdefault("anual", {})
    cad_cons = anual.setdefault("clientes_cadastro", {})
    cad_cons["cobertura"] = cob_cons
    cad_cons["cobertura_escova"] = {k: round(float(cob_esc.get(k) or 0), 1) for k in campos}
    cad_cons["cobertura_spa"]    = {k: round(float(cob_spa.get(k) or 0), 1) for k in campos}
    cad_cons["total"] = tot
    cad_cons["total_escova"] = tot_esc
    cad_cons["total_spa"] = tot_spa


def anexar_migracao_cruzada(c, esc, spa):
    esc_top = (esc.get("abas", {}).get("anual", {}).get("top_ltv", {}) or {}).get("top") or []
    spa_top = (spa.get("abas", {}).get("anual", {}).get("top_ltv", {}) or {}).get("top") or []
    esc_nomes = {_norm_nome(x.get("nome")) for x in esc_top}
    spa_nomes = {_norm_nome(x.get("nome")) for x in spa_top}
    ambas = esc_nomes & spa_nomes

    def _row(cli, origem, destino):
        return {
            "nome": cli.get("nome"),
            "ltv": cli.get("v") or 0,
            "n_visitas": cli.get("n") or 0,
            "telefone": cli.get("telefone") or "",
            "data_aniversario": cli.get("data_aniversario") or "",
            "data_aniversario_txt": cli.get("data_aniversario_txt") or "",
            "origem": origem,
            "destino": destino,
            "_unidade": origem,
        }

    e2s = [_row(x, "escova", "spa") for x in esc_top
           if _norm_nome(x.get("nome")) not in ambas
           and (x.get("n") or 0) >= 2
           and (x.get("v") or 0) > 0]
    s2e = [_row(x, "spa", "escova") for x in spa_top
           if _norm_nome(x.get("nome")) not in ambas
           and (x.get("n") or 0) >= 1
           and (x.get("v") or 0) > 0]

    e2s.sort(key=lambda z: -z["ltv"])
    s2e.sort(key=lambda z: -z["ltv"])

    anual = c.setdefault("abas", {}).setdefault("anual", {})
    anual["migracao_cruzada"] = {
        "escova_para_spa": e2s[:50],
        "spa_para_escova": s2e[:50],
        "ja_cruzam": sorted(ambas),
        "n_ja_cruzam": len(ambas),
        "n_candidatos_e2s": len(e2s),
        "n_candidatos_s2e": len(s2e),
        "nota_amostra": (
            "Base: top_ltv de cada unidade (até 50 por lado após próximo "
            "refresh completo). Cliente que já foi nas duas unidades sai da "
            "lista — já migrou organicamente."
        ),
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
    sup = spa.get("super_meta_mensal_valor")
    if sup and "mensal" in out:
        out["mensal"]["spa"]["super_meta"] = sup
        out["mensal"]["total"]["super_meta"] = round((out["mensal"]["total"].get("meta") or 0) - (out["mensal"]["spa"].get("meta") or 0) + sup, 2)
    c["_lado_a_lado"] = out
    ini_e = (esc.get("unidade_config") or {}).get("data_inauguracao") or "2026-07-23"
    ini_s = _inauguracao_spa(spa).isoformat()
    dias = lambda i: (hoje - _d(i)).days + 1
    c["_contexto"] = {
        "escova": {"aberta_desde": ini_e, "dias_aberta": dias(ini_e)},
        "spa": {"aberta_desde": ini_s, "dias_aberta": dias(ini_s)},
        "aviso": ("Escova aberta há %d dias, Spa há %d. Comparar mês cheio de uma loja com mês parcial da outra "
                  "inventa queda — e a meta do Spa no mês da abertura é a cheia, sem ratear." % (dias(ini_e), dias(ini_s))),
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
    anexar_cadastro_consolidado(consolidado, escova, spa)
    anexar_migracao_cruzada(consolidado, escova, spa)

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
