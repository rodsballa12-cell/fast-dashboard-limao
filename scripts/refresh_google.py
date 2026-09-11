"""Refresh diario do Google Business Profile via Supermetrics REST API.

Complementa scripts/refresh_midias.py (Meta) atualizando somente o bloco
`google_business` de data/midias_sociais.json e data/spa/midias_sociais.json.

Por que Supermetrics em vez da Google API direta:
- Rodrigo assina Supermetrics; a auth ja esta feita (rods_balla12@hotmail.com
  tem GMB conectado).
- Google Business Profile Performance API exige OAuth 2.0 (client_id/secret/
  refresh_token) — mais coisa pra configurar e manter.
- Supermetrics uniformiza o formato — mesma linha de codigo cobre outras
  fontes no futuro (LinkedIn, TikTok, etc).

Env obrigatorio:
  SUPERMETRICS_API_KEY  — pego em https://hub.supermetrics.com/token-management

Env opcional:
  SUPERMETRICS_TEAM_ID  — default 1192722 (team Rodrigo)

O script MERGE campos calculaveis (kpis_30d, rating, serie_diaria_30d,
conta_id, nome) e preserva o resto (mensagem, endereco curado, categorias,
etc — igual ao padrao de refresh_midias.py).

CLI:
  python scripts/refresh_google.py                # ambas unidades
  python scripts/refresh_google.py --unidade escova
  python scripts/refresh_google.py --dry-run

Falha graciosa: unidade sem `google_business_location_id` no config pula
silenciosamente (SPA ainda nao criou o GBP — brief entregue ao Marketing).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timezone, timedelta
from typing import Any

try:
    import requests
except ImportError:
    print("ERRO: requests nao instalado. `pip install requests`")
    sys.exit(1)


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "data", "config.json")
BRT = timezone(timedelta(hours=-3))

SM_ENDPOINT = "https://api.supermetrics.com/enterprise/v2/query/data/json"
DEFAULT_TEAM_ID = "1192722"

CAMPOS_PERF = [
    "date", "views_total", "views_maps", "views_search",
    "actions_total", "actions_website", "actions_phone",
    "actions_driving_directions", "actions_messages",
]
CAMPOS_REVIEWS = ["total_review_count", "total_review_star_rating"]


# ---------------------------------------------------------------------------
# Supermetrics query
# ---------------------------------------------------------------------------

def _sm_query(payload: dict, api_key: str, team_id: str) -> dict:
    """POST no Enterprise API. Retorna dict `data` de sucesso ou {} em erro."""
    body = {
        "team_id": team_id,
        **payload,
    }
    for tentativa in range(3):
        try:
            r = requests.post(
                SM_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=90,
            )
            if r.status_code >= 400:
                print(f"  [warn] Supermetrics HTTP {r.status_code}: {r.text[:300]}")
                if r.status_code in (401, 403):
                    raise RuntimeError("auth falhou · verifique SUPERMETRICS_API_KEY")
                if r.status_code < 500:
                    return {}
                continue
            js = r.json()
            if not js.get("success"):
                print(f"  [warn] Supermetrics erro: {js.get('error')}")
                return {}
            return js.get("data", {})
        except requests.RequestException as e:
            print(f"  [warn] Supermetrics excecao: {e}")
    return {}


def _fetch_performance(loc_id: str, api_key: str, team_id: str) -> list[dict]:
    """Serie diaria 30d + KPIs agregados."""
    data = _sm_query({
        "ds_id": "GMB",
        "ds_accounts": [loc_id],
        "fields": CAMPOS_PERF,
        "date_range_type": "last_30_days",
        "settings": {"report_type": "Performance"},
    }, api_key, team_id)
    if not data or not data.get("data"):
        return []
    rows = data["data"][1:]  # pula header
    return [{
        "data": r[0],
        "views_total": int(r[1] or 0),
        "views_maps": int(r[2] or 0),
        "views_search": int(r[3] or 0),
        "actions_total": int(r[4] or 0),
        "actions_website": int(r[5] or 0),
        "actions_phone": int(r[6] or 0),
        "actions_directions": int(r[7] or 0),  # driving_directions -> directions
    } for r in rows]


def _fetch_reviews(loc_id: str, api_key: str, team_id: str) -> dict:
    """Total reviews + estrelas media (valores lifetime)."""
    data = _sm_query({
        "ds_id": "GMB",
        "ds_accounts": [loc_id],
        "fields": CAMPOS_REVIEWS,
        "date_range_type": "last_30_days",
        "settings": {"report_type": "ReviewsTotals"},
    }, api_key, team_id)
    if not data or not data.get("data") or len(data["data"]) < 2:
        return {}
    total, media = data["data"][1]
    return {
        "reviews_total": int(total or 0),
        "estrelas_media": round(float(media or 0), 1),
    }


# ---------------------------------------------------------------------------
# Merge no arquivo
# ---------------------------------------------------------------------------

def _agregar_kpis(serie: list[dict]) -> dict:
    if not serie: return {}
    def s(k): return sum(x[k] for x in serie)
    views = s("views_total")
    acoes = s("actions_total")
    return {
        "views_total": views,
        "views_maps": s("views_maps"),
        "views_search": s("views_search"),
        "actions_total": acoes,
        "actions_phone": s("actions_phone"),
        "actions_directions": s("actions_directions"),
        "actions_website": s("actions_website"),
        "taxa_conversao_pct": round(acoes/max(views,1)*100, 2),
    }


def _merge(base: dict, serie: list[dict], reviews: dict, loc_id: str,
           loc_nome: str | None) -> tuple[dict, dict]:
    """Aplica dados no bloco google_business. Retorna (base atualizada, resumo)."""
    gb = base.setdefault("google_business", {})
    resumo = {}

    if serie:
        gb["serie_diaria_30d"] = serie
        gb["kpis_30d"] = _agregar_kpis(serie)
        resumo["views_30d"] = gb["kpis_30d"]["views_total"]
        resumo["acoes_30d"] = gb["kpis_30d"]["actions_total"]

    if reviews:
        gb["rating"] = reviews
        resumo["reviews"] = reviews["reviews_total"]
        resumo["estrelas"] = reviews["estrelas_media"]

    if serie or reviews:
        gb["conectado"] = True
        gb["conectado_em"] = datetime.now(BRT).date().isoformat()
        gb["conta_id"] = loc_id
        if loc_nome:
            gb["nome"] = loc_nome
        gb["_fonte_refresh"] = "Supermetrics REST API · refresh diario automatico"

    return base, resumo


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

UNIDADES = {
    "escova": {"prefix": "", "cfg_path": ("unidades", "escova", "midia_ids")},
    "spa":    {"prefix": "spa/", "cfg_path": ("unidades", "spa", "midia_ids")},
}


def _load_cfg() -> dict:
    with open(CONFIG) as f: return json.load(f)


def _load_base(path: str) -> dict:
    if not os.path.exists(path): return {}
    with open(path) as f: return json.load(f)


def _write(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main() -> int:
    ap = argparse.ArgumentParser(description="Refresh GBP via Supermetrics")
    ap.add_argument("--unidade", choices=list(UNIDADES), help="Rodar so uma")
    ap.add_argument("--dry-run", action="store_true", help="Nao grava")
    args = ap.parse_args()

    api_key = os.environ.get("SUPERMETRICS_API_KEY")
    if not api_key:
        print("ERRO: SUPERMETRICS_API_KEY nao definido")
        return 1
    team_id = os.environ.get("SUPERMETRICS_TEAM_ID", DEFAULT_TEAM_ID)

    cfg = _load_cfg()
    unidades_run = [args.unidade] if args.unidade else list(UNIDADES)

    total_atualizadas = 0
    for u in unidades_run:
        info = UNIDADES[u]
        path = os.path.join(ROOT, "data", info["prefix"], "midias_sociais.json").replace("/./", "/")
        if info["prefix"]:
            path = os.path.join(ROOT, "data", info["prefix"].rstrip("/"), "midias_sociais.json")
        else:
            path = os.path.join(ROOT, "data", "midias_sociais.json")

        node = cfg
        for k in info["cfg_path"]:
            node = node.get(k, {}) if isinstance(node, dict) else {}

        loc_id = node.get("google_business_location_id")
        loc_nome = node.get("google_business_nome")

        print(f"\n[{u}] {path}")
        if not loc_id:
            print(f"  ↳ google_business_location_id nao configurado no config.json — pulando")
            continue

        base = _load_base(path)
        if not base:
            print(f"  ↳ arquivo base nao existe — pulando")
            continue

        print(f"  location: {loc_id}")
        serie = _fetch_performance(loc_id, api_key, team_id)
        reviews = _fetch_reviews(loc_id, api_key, team_id)

        if not serie and not reviews:
            print(f"  ↳ Supermetrics nao devolveu dados — arquivo preservado")
            continue

        updated, resumo = _merge(base, serie, reviews, loc_id, loc_nome)
        updated["gerado_em"] = datetime.now(BRT).isoformat(timespec="seconds")

        print(f"  resumo: {resumo}")
        if args.dry_run:
            print(f"  [dry-run] nao grava")
        else:
            _write(path, updated)
            print(f"  ✓ gravado")
        total_atualizadas += 1

    print(f"\n[done] {total_atualizadas}/{len(unidades_run)} unidades atualizadas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
