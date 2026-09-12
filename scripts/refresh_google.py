"""Refresh diario do Google Business Profile via Google API oficial.

Antes usava Supermetrics REST (Enterprise API) mas a licenca CNCT
"Supermetrics for Claude" NAO inclui Google My Business como data source
(precisaria add-on US$ 37/mes). Rota gratuita: Google Business Profile
Performance API + My Business Business Information API — ambas oficiais
do Google, gratis com quotas generosas.

Auth: OAuth 2.0 refresh_token flow (a conta que assina o Business Profile
faz consent uma vez, gera refresh_token que persiste e permite renovar
access_tokens indefinidamente).

Env obrigatorio:
  GBP_OAUTH_CLIENT_ID       — Client ID OAuth 2.0 Desktop app (Google Cloud Console)
  GBP_OAUTH_CLIENT_SECRET   — Client secret do mesmo Desktop app
  GBP_OAUTH_REFRESH_TOKEN   — Refresh token gerado localmente uma vez

Setup (uma vez por conta):
  1. Google Cloud Console > New Project > "Business Profile Performance API" + "My Business Business Information API" > Enable
  2. OAuth consent screen > External > publish app > adiciona seu email como Test user
  3. Credentials > Create OAuth client ID > Desktop app > download client_secret.json
  4. Rodar localmente scripts/gbp_oauth_init.py (ele cospe o refresh_token)
  5. Adicionar 3 secrets no repo: GBP_OAUTH_CLIENT_ID/CLIENT_SECRET/REFRESH_TOKEN

CLI:
  python scripts/refresh_google.py                # ambas unidades
  python scripts/refresh_google.py --unidade escova
  python scripts/refresh_google.py --dry-run

Falha graciosa: unidade sem google_business_location_id no config pula
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

GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
GBP_PERFORMANCE_BASE = "https://businessprofileperformance.googleapis.com/v1"
GBP_MYBUSINESS_BASE = "https://mybusinessbusinessinformation.googleapis.com/v1"
GBP_ACCOUNT_MGMT_BASE = "https://mybusinessaccountmanagement.googleapis.com/v1"
REQ_TIMEOUT = 60

# Metricas oficiais Google Business Profile Performance API v1
# https://developers.google.com/my-business/reference/performance/rest/v1/locations/getDailyMetricsTimeSeries
METRICS_PERFORMANCE = [
    "BUSINESS_IMPRESSIONS_DESKTOP_MAPS",
    "BUSINESS_IMPRESSIONS_DESKTOP_SEARCH",
    "BUSINESS_IMPRESSIONS_MOBILE_MAPS",
    "BUSINESS_IMPRESSIONS_MOBILE_SEARCH",
    "BUSINESS_CONVERSATIONS",
    "BUSINESS_DIRECTION_REQUESTS",
    "CALL_CLICKS",
    "WEBSITE_CLICKS",
    "BUSINESS_BOOKINGS",
    "BUSINESS_FOOD_ORDERS",
    "BUSINESS_FOOD_MENU_CLICKS",
]


# ---------------------------------------------------------------------------
# OAuth
# ---------------------------------------------------------------------------

def _get_access_token(client_id: str, client_secret: str, refresh_token: str) -> str | None:
    """Troca refresh_token por access_token curto prazo (~1h)."""
    try:
        r = requests.post(
            GOOGLE_OAUTH_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=REQ_TIMEOUT,
        )
        if r.status_code >= 400:
            print(f"  [warn] OAuth refresh falhou HTTP {r.status_code}: {r.text[:200]}")
            return None
        return r.json().get("access_token")
    except requests.RequestException as e:
        print(f"  [warn] OAuth exception: {e}")
        return None


# ---------------------------------------------------------------------------
# Google Business Profile API calls
# ---------------------------------------------------------------------------

def _iso(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def _fetch_performance(location_id: str, access_token: str, hoje: date) -> list[dict]:
    """Serie diaria 30d de metricas de performance (views, actions, calls, etc)."""
    # location_id vem no formato "accounts/XXX_YYY" (do Supermetrics). Google
    # espera "locations/YYY" — extrai a parte apos "_" ou "/".
    if "_" in location_id:
        loc_num = location_id.split("_")[-1]
    elif "/" in location_id:
        loc_num = location_id.split("/")[-1]
    else:
        loc_num = location_id

    fim = hoje - timedelta(days=1)  # Google exclui hoje
    ini = fim - timedelta(days=29)

    # Google API pede uma metric por chamada — vamos batch em paralelo depois
    por_dia: dict[str, dict[str, int]] = {}
    for metric in METRICS_PERFORMANCE:
        try:
            r = requests.get(
                f"{GBP_PERFORMANCE_BASE}/locations/{loc_num}:getDailyMetricsTimeSeries",
                params={
                    "dailyMetric": metric,
                    "dailyRange.startDate.year": ini.year,
                    "dailyRange.startDate.month": ini.month,
                    "dailyRange.startDate.day": ini.day,
                    "dailyRange.endDate.year": fim.year,
                    "dailyRange.endDate.month": fim.month,
                    "dailyRange.endDate.day": fim.day,
                },
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=REQ_TIMEOUT,
            )
            if r.status_code >= 400:
                print(f"  [warn] GBP {metric} HTTP {r.status_code}: {r.text[:200]}")
                continue
            data = r.json()
            series = (data.get("timeSeries") or {}).get("datedValues") or []
            for pt in series:
                d = pt.get("date", {})
                dstr = f"{d.get('year'):04d}-{d.get('month'):02d}-{d.get('day'):02d}"
                val = int(pt.get("value") or 0)
                slot = por_dia.setdefault(dstr, {})
                slot[metric] = val
        except requests.RequestException as e:
            print(f"  [warn] GBP {metric} exception: {e}")

    # Consolidar em nossa estrutura
    saida = []
    for dstr in sorted(por_dia):
        m = por_dia[dstr]
        maps = (m.get("BUSINESS_IMPRESSIONS_DESKTOP_MAPS", 0)
                + m.get("BUSINESS_IMPRESSIONS_MOBILE_MAPS", 0))
        search = (m.get("BUSINESS_IMPRESSIONS_DESKTOP_SEARCH", 0)
                  + m.get("BUSINESS_IMPRESSIONS_MOBILE_SEARCH", 0))
        actions_website = m.get("WEBSITE_CLICKS", 0)
        actions_phone = m.get("CALL_CLICKS", 0)
        actions_directions = m.get("BUSINESS_DIRECTION_REQUESTS", 0)
        actions_messages = m.get("BUSINESS_CONVERSATIONS", 0)
        actions_total = actions_website + actions_phone + actions_directions + actions_messages
        saida.append({
            "data": dstr,
            "views_total": maps + search,
            "views_maps": maps,
            "views_search": search,
            "actions_total": actions_total,
            "actions_website": actions_website,
            "actions_phone": actions_phone,
            "actions_directions": actions_directions,
        })
    return saida


def _fetch_reviews(location_id: str, access_token: str) -> dict:
    """Pega rating agregado + total de reviews.

    Nao existe endpoint dedicado a esse total no v1 novo — usamos o endpoint
    de reviews (v4 legacy ainda ativo pra listar reviews individuais). Se
    quisermos so o agregado: My Business Business Information API tem
    'metadata.hasVoiceOfMerchant' mas nao total de reviews. Solucao: chamar
    /reviews (v4 legacy) e agregar.

    Se v4 legacy nao estiver disponivel ou o account_id nao for descoberto,
    devolve dict vazio (dados curados anteriores permanecem).
    """
    # v4 legacy endpoint: https://mybusiness.googleapis.com/v4/{accounts/X/locations/Y}/reviews
    # Precisa do formato completo accounts/XXX/locations/YYY.
    if "/" in location_id and location_id.startswith("accounts/"):
        full_path = location_id  # ja no formato accounts/X/locations/Y
    elif "_" in location_id:
        parts = location_id.split("_")
        full_path = f"accounts/{parts[0]}/locations/{parts[1]}"
    else:
        return {}

    try:
        r = requests.get(
            f"https://mybusiness.googleapis.com/v4/{full_path}/reviews",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"pageSize": 50},
            timeout=REQ_TIMEOUT,
        )
        if r.status_code >= 400:
            print(f"  [warn] GBP reviews HTTP {r.status_code}: {r.text[:200]}")
            return {}
        data = r.json()
        return {
            "reviews_total": int(data.get("totalReviewCount") or 0),
            "estrelas_media": round(float(data.get("averageRating") or 0), 1),
        }
    except requests.RequestException as e:
        print(f"  [warn] GBP reviews exception: {e}")
        return {}


# ---------------------------------------------------------------------------
# Merge no arquivo
# ---------------------------------------------------------------------------

def _agregar_kpis(serie: list[dict]) -> dict:
    if not serie:
        return {}
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
        "taxa_conversao_pct": round(acoes / max(views, 1) * 100, 2),
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
        gb["_fonte_refresh"] = "Google Business Profile Performance API oficial (grátis) · cron diario 07h BRT"

    return base, resumo


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

UNIDADES = {
    "escova": {"path": os.path.join(ROOT, "data", "midias_sociais.json"),
               "cfg_path": ("unidades", "escova", "midia_ids")},
    "spa":    {"path": os.path.join(ROOT, "data", "spa", "midias_sociais.json"),
               "cfg_path": ("unidades", "spa", "midia_ids")},
}


def _load_cfg() -> dict:
    with open(CONFIG) as f:
        return json.load(f)


def _load_base(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def _write(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main() -> int:
    ap = argparse.ArgumentParser(description="Refresh GBP via Google Business Profile API oficial")
    ap.add_argument("--unidade", choices=list(UNIDADES), help="Rodar so uma")
    ap.add_argument("--dry-run", action="store_true", help="Nao grava")
    args = ap.parse_args()

    client_id = os.environ.get("GBP_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("GBP_OAUTH_CLIENT_SECRET")
    refresh_token = os.environ.get("GBP_OAUTH_REFRESH_TOKEN")
    missing = [k for k, v in [
        ("GBP_OAUTH_CLIENT_ID", client_id),
        ("GBP_OAUTH_CLIENT_SECRET", client_secret),
        ("GBP_OAUTH_REFRESH_TOKEN", refresh_token),
    ] if not v]
    if missing:
        print(f"ERRO: variaveis de ambiente faltando: {', '.join(missing)}")
        print("Setup: veja o docstring deste script pra passos OAuth 2.0.")
        return 1

    access_token = _get_access_token(client_id, client_secret, refresh_token)
    if not access_token:
        print("ERRO: nao consegui obter access_token via refresh_token OAuth.")
        return 1

    cfg = _load_cfg()
    unidades_run = [args.unidade] if args.unidade else list(UNIDADES)
    hoje = datetime.now(BRT).date()

    total_atualizadas = 0
    for u in unidades_run:
        info = UNIDADES[u]
        node = cfg
        for k in info["cfg_path"]:
            node = node.get(k, {}) if isinstance(node, dict) else {}

        loc_id = node.get("google_business_location_id")
        loc_nome = node.get("google_business_nome")

        print(f"\n[{u}] {info['path']}")
        if not loc_id:
            print(f"  ↳ google_business_location_id nao configurado — pulando")
            continue

        base = _load_base(info["path"])
        if not base:
            print(f"  ↳ arquivo base nao existe — pulando")
            continue

        print(f"  location: {loc_id}")
        serie = _fetch_performance(loc_id, access_token, hoje)
        reviews = _fetch_reviews(loc_id, access_token)

        if not serie and not reviews:
            print(f"  ↳ Google API nao devolveu dados — arquivo preservado")
            continue

        updated, resumo = _merge(base, serie, reviews, loc_id, loc_nome)
        updated["gerado_em"] = datetime.now(BRT).isoformat(timespec="seconds")

        print(f"  resumo: {resumo}")
        if args.dry_run:
            print(f"  [dry-run] nao grava")
        else:
            _write(info["path"], updated)
            print(f"  ✓ gravado")
        total_atualizadas += 1

    print(f"\n[done] {total_atualizadas}/{len(unidades_run)} unidades atualizadas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
