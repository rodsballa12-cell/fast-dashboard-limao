"""Gera data/spa/dashboard_data.json em zero-state honesto — estrutura da
Escova preservada, mas TODAS as métricas zeradas e arrays de pessoa
(rankings, clientes, aniversariantes, obs) vazios. Substitui mock_spa.py
(que era clone escalado de Escova × 42%, enganava).

Loja SPA abre 25/09/2026 — enquanto Trinks estabelecimentoId não existe,
não há trans/cliente/prof/receita reais. Zerar é o único jeito honesto
de mostrar a estrutura sem inventar dado.

Preserva:
- estrutura (todas as chaves)
- arrays estruturais (por_dow 7 items, hora_abs 24 items, meses 12 items) com valores zerados
- unidade (produto/marca/tipo)
- flag _mock=true pra frontend detectar e trocar cross-cards por placeholder

Zera:
- todos os numéricos
- kpis, meta (mantendo meta.meta franqueadora quando conhecida)
- todas as listas de pessoa/cliente/prof
"""

import json, os, copy
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "data", "config.json")
SRC = os.path.join(ROOT, "data", "dashboard_data.json")
DST_DIR = os.path.join(ROOT, "data", "spa")
DST = os.path.join(DST_DIR, "dashboard_data.json")
BRT = timezone(timedelta(hours=-3))

# Chaves de arrays cujo conteúdo deve ser LIMPO (rankings, listas de pessoa).
# Estrutura vazia é ok — frontend já trata (ranking vazio, obs vazias, etc).
LIMPAR_ARRAY = {
    "ranking_prof", "ranking_prof_executor", "ranking_serv",
    "rentabilidade_hora", "clientes_top", "aniversariantes",
    "cross_sell", "obs_alertas", "obs_agend_alertas",
    "categoria_native", "top", "meios_pagamento", "parcelas",
    "novos", "recorrentes",  # (dentro de novos_vs_recorr, listas)
    "insights", "direcionamentos_estrategicos", "recomendacoes",
    "insights_narrativa", "alertas_topo",
    "servicos", "servicos_gerais", "fast_retoque_lista",
}

# Chaves cujo array é ESTRUTURAL (posição importa) — zera valores mantendo N items
ARRAY_ESTRUTURAL = {"por_dow", "hora_abs", "hora_media", "meses", "por_dia_mes", "dow_hist"}

# Chaves que devem preservar valor (identidade, config, datas)
PRESERVAR = {
    "gerado_em", "ano", "mes", "semana", "dia", "dia_semana",
    "periodo_ini", "periodo_fim", "dia_ini", "dia_fim",
    "estabelecimento_id", "id", "cnpj", "razao_social", "nome",
    "produto", "marca", "tipo", "filial", "cidade",
    "cor_accent", "emoji", "data_prefix",
    "data_inauguracao", "trinks_estabelecimento_id",
    "categoria", "descricao", "cor", "cor_bar", "status",
}


def zero_state(obj, key_path=""):
    """Walk recursivo: zera numéricos, limpa arrays de pessoa, preserva estrutura."""
    if obj is None or isinstance(obj, bool):
        return obj
    if isinstance(obj, (int, float)):
        return type(obj)(0)
    if isinstance(obj, str):
        return obj  # nomes/rótulos genéricos preservados
    if isinstance(obj, list):
        # arrays estruturais: mantém N items mas zera valores
        parent_key = key_path.split(".")[-1] if key_path else ""
        if parent_key in ARRAY_ESTRUTURAL:
            return [zero_state(x, key_path) for x in obj]
        # arrays de pessoa/ranking: esvazia
        if parent_key in LIMPAR_ARRAY:
            return []
        # arrays de dicts simples (numéricos) sem key conhecida: zera
        return [zero_state(x, key_path) for x in obj]
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            new_path = f"{key_path}.{k}" if key_path else k
            if k in PRESERVAR:
                out[k] = copy.deepcopy(v)
            elif k in LIMPAR_ARRAY and isinstance(v, list):
                out[k] = []
            else:
                out[k] = zero_state(v, new_path)
        return out
    return copy.deepcopy(obj)


def main():
    if not os.path.exists(SRC):
        raise SystemExit(f"Escova payload não existe em {SRC}")
    with open(CONFIG) as f:
        cfg = json.load(f)
    spa = cfg["unidades"]["spa"]

    with open(SRC) as f:
        escova = json.load(f)

    payload = zero_state(escova)

    # Identidade da unidade SPA (não escova)
    now = datetime.now(BRT).isoformat(timespec="seconds")
    payload["gerado_em"] = now
    payload["unidade"] = {
        "produto": spa["produto"],
        "marca": spa["marca"],
        "tipo": spa["tipo"],
        "filial": spa["filial"],
        "cidade": spa["cidade"],
    }
    payload["_mock"] = True
    payload["_pre_abertura"] = True
    payload["_data_inauguracao"] = spa["data_inauguracao"]
    payload["_estado"] = "zero-state · SPA em pré-abertura · Trinks estabelecimentoId pendente"

    # Meta franqueadora preservada (60k/mês × ~5 meses operados) — quando
    # trinks_estabelecimento_id subir, backend real calcula com dias_op corretos
    for aba in ("anual", "mensal", "semanal", "diario"):
        if aba in payload.get("abas", {}):
            meta = payload["abas"][aba].get("meta", {})
            if aba == "mensal":
                meta["meta"] = 60000
            elif aba == "anual":
                # Meta franqueadora anual · 60k × meses do ano operados (post-abertura)
                # Loja abre 25/09 · ~3 meses até 31/12 · 3 × 60k = 180k
                meta["meta"] = 180000
            # realizado/projecao/pct ficam 0

    os.makedirs(DST_DIR, exist_ok=True)
    with open(DST, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"[build_spa_dashboard] gerado {DST}")
    print(f"  estado: zero-state (loja abre {spa['data_inauguracao']})")
    a = payload["abas"]["anual"]
    m = payload["abas"]["mensal"]
    print(f"  ano · caixa={a['kpis']['caixa']} meta={a['meta'].get('meta',0)} ranking_prof={len(a.get('ranking_prof',[]))}")
    print(f"  mês · caixa={m['kpis']['caixa']} meta={m['meta'].get('meta',0)}")


if __name__ == "__main__":
    main()
