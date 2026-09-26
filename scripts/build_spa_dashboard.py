"""Gera data/spa/dashboard_data.json.

DOIS MODOS:
 1. Trinks REAL: se TRINKS_API_KEY_SPA + TRINKS_ESTABELECIMENTO_ID_SPA existem
    no ambiente, delega pro github_refresh.py --unidade spa (mesmo pipeline
    da Escova, dados frescos, arquivos em data/spa/*).
 2. Zero-state (fallback): sem secrets, gera JSON estruturalmente igual ao
    da Escova mas com todos os numericos zerados e arrays de pessoa vazios.
    Usado pre-abertura ou enquanto integracao Trinks nao esta pronta.

Preserva no zero-state:
- estrutura (todas as chaves)
- arrays estruturais (por_dow 7 items, hora_abs 24 items, meses 12 items)
- unidade (produto/marca/tipo)
- flag _mock=true pra frontend detectar
"""

import json, os, copy, subprocess, sys
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




def _meta_anual_spa() -> float:
    """Meta do ano = meta mensal × meses operados de fato até 31/12.

    Estava fixa em 180000, que era 3 × 60000 quando a mensal valia 60000.
    Ao baixar a mensal para 15000 em 14/09/2026 a anual não acompanhou e o
    painel passou a mostrar meta anual de 180k com meta mensal de 15k —
    doze meses de alvo numa loja que abre em setembro. Agora deriva, então
    mudar a mensal no config.json ajusta as duas.

    O mês de abertura entra proporcional aos dias que sobram dele.
    """
    import json as _json, os as _os
    from calendar import monthrange
    from datetime import date
    try:
        caminho = _os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "data", "config.json")
        with open(caminho, encoding="utf-8") as fh:
            u = _json.load(fh)["unidades"]["spa"]
        mensal = float(u.get("meta_mensal") or 20000.0)
        ab = date.fromisoformat(u["data_inauguracao"])
    except Exception:
        return 45000.0
    dias_no_mes = monthrange(ab.year, ab.month)[1]
    meses = (dias_no_mes - ab.day + 1) / dias_no_mes + (12 - ab.month)
    return round(mensal * meses, 2)


def _meta_mensal_spa() -> float:
    """Meta mensal do SPA — do config.json, fonte única.

    Estava fixa em 60000 aqui enquanto o financeiro já lia 15000 do config:
    metade do conserto de 14/09/2026 passou batido, e por um dia o painel do
    SPA mostrou meta diferente do DRE do SPA. Duas fontes da verdade divergem
    sempre — inclusive quando uma delas acabou de ser corrigida.
    """
    import json as _json, os as _os
    try:
        caminho = _os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "data", "config.json")
        with open(caminho, encoding="utf-8") as fh:
            v = _json.load(fh)["unidades"]["spa"].get("meta_mensal")
        return float(v) if v is not None else 20000.0
    except Exception:
        return 20000.0


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
    # Modo 1: Trinks real via github_refresh --unidade spa
    if os.environ.get("TRINKS_API_KEY_SPA") and os.environ.get("TRINKS_ESTABELECIMENTO_ID_SPA"):
        print("[build_spa_dashboard] TRINKS_API_KEY_SPA presente · delegando pra github_refresh --unidade spa")
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "github_refresh.py")
        r = subprocess.run([sys.executable, script, "--unidade", "spa"], check=False)
        if r.returncode == 0:
            print(f"[build_spa_dashboard] pull real Trinks concluido · exit={r.returncode}")
            return
        print(f"[build_spa_dashboard] github_refresh falhou (exit={r.returncode}) · caindo pro zero-state")

    # Modo 2: zero-state (sem secrets SPA ou refresh falhou)
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
                meta["meta"] = _meta_mensal_spa()
            elif aba == "anual":
                meta["meta"] = _meta_anual_spa()
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
