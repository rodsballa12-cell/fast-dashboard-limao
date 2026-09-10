"""Consolida os payloads das unidades (Escova + SPA) num único
data/consolidado/dashboard_data.json somando numéricos leaf-por-leaf,
concatenando rankings com badge (🥂 Escova / 🧖 SPA) e recalculando
percentuais/médias derivados.

Fonte:
  data/dashboard_data.json      (Escova · path atual)
  data/spa/dashboard_data.json  (SPA · mock por enquanto, real após conexão)

Saída:
  data/consolidado/dashboard_data.json
"""

import json, os, copy

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

# Chaves cujos itens agregam por 'nome' ou 'k' (categorias, categoria_native, top clientes)
ARRAY_POR_CHAVE = {
    "categoria_native": "nome",
    "clientes_top": "nome",
    "top": "nome",  # top ltv, top churn, etc
    "aniversariantes": "cliente",
    "cross_sell": "cliente",
}

# Chaves cujos itens são rankings de PROFISSIONAIS — concat com badge de unidade
ARRAY_CONCAT_BADGE = {
    "ranking_prof", "ranking_prof_executor", "ranking_serv",
    "rentabilidade_hora",
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
    # Rankings de prof — concat com badge, re-ordenar por v
    if key in ARRAY_CONCAT_BADGE:
        merged = [{**x, "nome": f"🥂 {x.get('nome','')}"} for x in a] + \
                 [{**x, "nome": f"🧖 {x.get('nome','')}"} for x in b]
        merged.sort(key=lambda z: -(z.get("v") or 0))
        return merged
    # Arrays por chave (categoria_native, clientes_top, aniv) — agrupa por nome
    if key in ARRAY_POR_CHAVE:
        kname = ARRAY_POR_CHAVE[key]
        idx = {}
        for x in a + b:
            k = x.get(kname) or "?"
            if k in idx:
                idx[k] = merge(idx[k], x, path)
            else:
                idx[k] = copy.deepcopy(x)
        return sorted(idx.values(), key=lambda z: -(z.get("v") or z.get("ltv") or 0))
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


def main():
    if not os.path.exists(ESC):
        raise SystemExit("Escova payload não existe.")
    if not os.path.exists(SPA):
        raise SystemExit("SPA payload não existe (rode scripts/mock_spa.py primeiro).")

    with open(ESC) as f: escova = json.load(f)
    with open(SPA) as f: spa = json.load(f)

    consolidado = merge(escova, spa)
    recalcular_derivados(consolidado)

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
