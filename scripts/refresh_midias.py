"""Refresh diario automatico de data/midias_sociais.json (Escova) e
data/spa/midias_sociais.json (SPA) a partir da Meta Graph API v20.0.

O que o script faz:
  - Le data/config.json e escolhe as unidades a atualizar
    (unidades.escova.midia_ids e unidades.spa.midia_ids).
  - Pula a unidade se meta_ad_account_id for null.
  - Puxa Ad Account insights (5 janelas) + serie diaria 30d + IG User /
    IG media / FB Page.
  - CARREGA o arquivo existente como BASE e sobrescreve APENAS os campos
    de API (gerado_em, janelas, meta_ads.por_periodo/serie_diaria_30d,
    instagram.followers/posts_total/organico_*/serie_diaria_30d/
    ultimo_post/top_posts_30d, facebook_page.seguidores|followers/
    posts_30d). Campos curados (direcionamentos_estrategicos,
    recomendacoes, insights_narrativa, alertas_topo, kpi_estrela,
    benchmarks, google_business, google_ads, hubspot, whatsapp_cloud_api,
    funil_conversao) NAO sao tocados.
  - Falha graciosa: se uma chamada de API der erro, loga warning e mantem
    o campo antigo da base.

CLI:
  python scripts/refresh_midias.py                # ambas unidades
  python scripts/refresh_midias.py --unidade escova
  python scripts/refresh_midias.py --unidade spa
  python scripts/refresh_midias.py --dry-run      # diff sem escrever

Env:
  META_ACCESS_TOKEN  obrigatorio (mesmo token cobre Escova e SPA — admin
                     comum aos dois portfolios).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

import urllib.error
import urllib.parse
import urllib.request

try:
    # requests deixa o codigo mais limpo se disponivel (workflow instala).
    import requests  # type: ignore
    HAS_REQUESTS = True
except Exception:
    HAS_REQUESTS = False


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "data", "config.json")

BRT = timezone(timedelta(hours=-3))
GRAPH = "https://graph.facebook.com/v20.0"
REQ_TIMEOUT = 60


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _graph_get(path: str, params: dict[str, Any], token: str) -> dict[str, Any]:
    """GET no Graph API. Devolve JSON parseado ou levanta RuntimeError."""
    query = dict(params)
    query["access_token"] = token
    url = f"{GRAPH}{path}?{urllib.parse.urlencode(query, doseq=True)}"

    last_err: Exception | None = None
    for tentativa in range(3):
        try:
            if HAS_REQUESTS:
                r = requests.get(url, timeout=REQ_TIMEOUT)
                if r.status_code >= 400:
                    raise RuntimeError(f"HTTP {r.status_code} · {r.text[:400]}")
                return r.json()
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=REQ_TIMEOUT) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body)
        except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, TimeoutError) as e:
            last_err = e
            if tentativa < 2:
                time.sleep(2 ** tentativa)
            else:
                raise
    # inalcancavel — mas satisfaz o type checker
    raise last_err  # type: ignore[misc]


def _graph_get_all(path: str, params: dict[str, Any], token: str, max_pages: int = 10) -> list[dict[str, Any]]:
    """Paginacao simples: segue paging.next ate max_pages ou esgotar."""
    todos: list[dict[str, Any]] = []
    resp = _graph_get(path, params, token)
    todos.extend(resp.get("data", []))
    pagina = 1
    while pagina < max_pages:
        prox = resp.get("paging", {}).get("next")
        if not prox:
            break
        try:
            if HAS_REQUESTS:
                r = requests.get(prox, timeout=REQ_TIMEOUT)
                if r.status_code >= 400:
                    break
                resp = r.json()
            else:
                with urllib.request.urlopen(prox, timeout=REQ_TIMEOUT) as raw:
                    resp = json.loads(raw.read().decode("utf-8"))
        except Exception:
            break
        todos.extend(resp.get("data", []))
        pagina += 1
    return todos


# ---------------------------------------------------------------------------
# Utilidades de data
# ---------------------------------------------------------------------------

def _hoje_brt() -> date:
    return datetime.now(BRT).date()


def _iso(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def _janela(kind: str, hoje: date) -> tuple[date, date]:
    """Devolve (inicio, fim) BRT para cada janela."""
    if kind == "today":
        return hoje, hoje
    if kind == "last_7d":
        return hoje - timedelta(days=6), hoje
    if kind == "this_month":
        return hoje.replace(day=1), hoje
    if kind == "last_30d":
        return hoje - timedelta(days=29), hoje
    if kind == "last_90d":
        return hoje - timedelta(days=89), hoje
    raise ValueError(f"janela desconhecida: {kind}")


def _janelas_texto(hoje: date) -> dict[str, str]:
    def rng(a: date, b: date) -> str:
        return f"{_iso(a)} a {_iso(b)}"
    return {
        "hoje": _iso(hoje),
        "meta_ads_7d":  rng(*_janela("last_7d", hoje)),
        "mtd_setembro": rng(*_janela("this_month", hoje)),
        "meta_ads_30d": rng(*_janela("last_30d", hoje)),
        "meta_ads_90d": rng(*_janela("last_90d", hoje)),
        "instagram_30d": rng(*_janela("last_30d", hoje)),
        "instagram_7d":  rng(*_janela("last_7d", hoje)),
        "facebook_page_30d": rng(*_janela("last_30d", hoje)),
    }


# ---------------------------------------------------------------------------
# Meta Ads
# ---------------------------------------------------------------------------

INSIGHT_FIELDS = "spend,impressions,clicks,cpm,ctr,reach,frequency,actions,cost_per_action_type"
MSG_ACTION = "onsite_conversion.messaging_conversation_started_7d"


def _actions_val(actions: list[dict[str, Any]] | None, action_type: str) -> float:
    if not actions:
        return 0.0
    for a in actions:
        if a.get("action_type") == action_type:
            try:
                return float(a.get("value") or 0)
            except (TypeError, ValueError):
                return 0.0
    return 0.0


def _row_to_periodo(row: dict[str, Any] | None, label: str, inicio: date, fim: date, now_iso: str) -> dict[str, Any]:
    if not row:
        row = {}
    gasto = float(row.get("spend") or 0)
    impressoes = int(float(row.get("impressions") or 0))
    cliques = int(float(row.get("clicks") or 0))
    reach = int(float(row.get("reach") or 0))
    frequency = float(row.get("frequency") or 0)
    cpm = float(row.get("cpm") or 0)
    ctr = float(row.get("ctr") or 0)
    actions = row.get("actions") or []
    cost_per_action = row.get("cost_per_action_type") or []

    conversas = int(_actions_val(actions, MSG_ACTION))
    link_clicks = int(_actions_val(actions, "link_click"))
    cpa_msg = _actions_val(cost_per_action, MSG_ACTION) or None
    if cpa_msg == 0.0:
        cpa_msg = None

    link_ctr_pct = round((link_clicks / impressoes * 100), 2) if impressoes else 0.0
    cpc = round(gasto / cliques, 2) if cliques else 0.0
    cpc_link = round(gasto / link_clicks, 2) if link_clicks else 0.0

    return {
        "label": label,
        "inicio": _iso(inicio),
        "fim": _iso(fim),
        "gasto": round(gasto, 2),
        "impressoes": impressoes,
        "cliques": cliques,
        "clicks": cliques,  # alias — schema SPA usa "clicks"
        "link_clicks": link_clicks,
        "conversas_msg": conversas,
        "reach": reach,
        "frequency": round(frequency, 2),
        "ctr_pct": round(ctr, 2),
        "link_ctr_pct": link_ctr_pct,
        "cpm": round(cpm, 2),
        "cpc": cpc,
        "cpc_link": cpc_link,
        "cpa_msg": round(cpa_msg, 2) if cpa_msg else None,
        "atualizado_em": now_iso,
    }


def _fetch_ad_insights(act_id: str, token: str, hoje: date, now_iso: str) -> dict[str, dict[str, Any]]:
    """Devolve dict {periodo: dict_por_periodo} para hoje/7d/mtd/30d/90d.

    Cada chamada e independente — se uma falhar, so aquele periodo cai.
    """
    janelas = {
        "hoje": ("today", "Hoje"),
        "7d":   ("last_7d", "Ultimos 7 dias"),
        "mtd":  ("this_month", "Mes corrente"),
        "30d":  ("last_30d", "Ultimos 30 dias"),
        "90d":  ("last_90d", "Ultimos 90 dias"),
    }
    saida: dict[str, dict[str, Any]] = {}
    for chave, (dr, label) in janelas.items():
        inicio, fim = _janela(dr, hoje)
        # label com data pro periodo "hoje" (base tem "Hoje (07/09)")
        label_final = f"Hoje ({fim.strftime('%d/%m')})" if chave == "hoje" else label
        try:
            resp = _graph_get(
                f"/{act_id}/insights",
                {
                    "fields": INSIGHT_FIELDS,
                    "time_range": json.dumps({"since": _iso(inicio), "until": _iso(fim)}),
                    "level": "account",
                },
                token,
            )
            rows = resp.get("data") or []
            row = rows[0] if rows else None
            saida[chave] = _row_to_periodo(row, label_final, inicio, fim, now_iso)
        except Exception as e:
            print(f"  [WARN] Ad insights {chave} falhou: {e}", file=sys.stderr)
            saida[chave] = _row_to_periodo(None, label_final, inicio, fim, now_iso)
            saida[chave]["_erro"] = str(e)[:200]
    return saida


def _fetch_serie_diaria(act_id: str, token: str, hoje: date) -> list[dict[str, Any]]:
    """Serie diaria dos ultimos 30 dias (time_increment=1). Falha -> lista vazia."""
    inicio, fim = _janela("last_30d", hoje)
    try:
        rows: list[dict[str, Any]] = []
        params = {
            "fields": INSIGHT_FIELDS,
            "time_range": json.dumps({"since": _iso(inicio), "until": _iso(fim)}),
            "time_increment": 1,
            "level": "account",
            "limit": 100,
        }
        resp = _graph_get(f"/{act_id}/insights", params, token)
        rows.extend(resp.get("data", []))
        # paginacao caso passe do limit
        while resp.get("paging", {}).get("next") and len(rows) < 40:
            try:
                if HAS_REQUESTS:
                    r = requests.get(resp["paging"]["next"], timeout=REQ_TIMEOUT)
                    resp = r.json() if r.ok else {}
                else:
                    with urllib.request.urlopen(resp["paging"]["next"], timeout=REQ_TIMEOUT) as raw:
                        resp = json.loads(raw.read().decode("utf-8"))
                rows.extend(resp.get("data", []))
            except Exception:
                break
    except Exception as e:
        print(f"  [WARN] Serie diaria falhou: {e}", file=sys.stderr)
        return []

    saida = []
    for r in rows:
        dia = r.get("date_start") or r.get("date_stop")
        if not dia:
            continue
        gasto = float(r.get("spend") or 0)
        impr = int(float(r.get("impressions") or 0))
        cliques = int(float(r.get("clicks") or 0))
        reach = int(float(r.get("reach") or 0))
        conversas = int(_actions_val(r.get("actions"), MSG_ACTION))
        cpa = round(gasto / conversas, 2) if conversas > 0 else None
        saida.append({
            "data": dia,
            "gasto": round(gasto, 2),
            "impressoes": impr,
            "cliques": cliques,
            "clicks": cliques,  # alias SPA
            "reach": reach,
            "conversas_msg": conversas,
            "cpa_msg": cpa,
        })
    saida.sort(key=lambda x: x["data"])
    return saida


# ---------------------------------------------------------------------------
# Meta Ads — breakdowns (campanhas, adsets, ads, demografia, placement,
# geografia, por objetivo) por janela
# ---------------------------------------------------------------------------

def _fetch_insights_breakdown(
    act_id: str,
    token: str,
    since: date,
    until: date,
    level: str,
    extra_fields: str = "",
    breakdowns: str = "",
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Chamada generica /act_ID/insights com level/breakdowns configuraveis.

    level in {account,campaign,adset,ad}. `extra_fields` sao os fields alem
    do INSIGHT_FIELDS base + name-fields do nivel (campaign_name/adset_name/etc).
    breakdowns = "age,gender" ou "publisher_platform,platform_position" ou "region".
    Falha graciosa: devolve [] se der erro.
    """
    fields = INSIGHT_FIELDS
    if extra_fields:
        fields += "," + extra_fields
    params: dict[str, Any] = {
        "fields": fields,
        "time_range": json.dumps({"since": _iso(since), "until": _iso(until)}),
        "level": level,
        "limit": limit,
    }
    if breakdowns:
        params["breakdowns"] = breakdowns
    try:
        return _graph_get_all(f"/{act_id}/insights", params, token, max_pages=5)
    except Exception as e:
        print(f"  [WARN] Insights level={level} breakdowns={breakdowns or '-'} {since}..{until} falhou: {e}", file=sys.stderr)
        return []


def _row_metrics(r: dict[str, Any]) -> dict[str, Any]:
    """Extrai metricas comuns de uma linha /insights."""
    gasto = float(r.get("spend") or 0)
    impr = int(float(r.get("impressions") or 0))
    cliques = int(float(r.get("clicks") or 0))
    reach = int(float(r.get("reach") or 0))
    freq = float(r.get("frequency") or 0)
    cpm = float(r.get("cpm") or 0)
    ctr = float(r.get("ctr") or 0)
    actions = r.get("actions") or []
    cost_per_action = r.get("cost_per_action_type") or []
    conversas = int(_actions_val(actions, MSG_ACTION))
    link_clicks = int(_actions_val(actions, "link_click"))
    cpa_msg = _actions_val(cost_per_action, MSG_ACTION) or None
    cpc = round(gasto / cliques, 2) if cliques else 0.0
    return {
        "gasto": round(gasto, 2),
        "impressoes": impr,
        "cliques": cliques,
        "reach": reach,
        "frequency": round(freq, 2),
        "cpm": round(cpm, 2),
        "cpc": cpc,
        "ctr_pct": round(ctr, 2),
        "conversas_msg": conversas,
        "link_clicks": link_clicks,
        "cpa_msg": round(cpa_msg, 2) if cpa_msg else None,
    }


def _fetch_campanhas(act_id: str, token: str, since: date, until: date) -> list[dict[str, Any]]:
    rows = _fetch_insights_breakdown(
        act_id, token, since, until,
        level="campaign",
        extra_fields="campaign_name,objective",
    )
    total_gasto = sum(float(r.get("spend") or 0) for r in rows) or 0.0
    saida = []
    for r in rows:
        m = _row_metrics(r)
        saida.append({
            "nome": r.get("campaign_name") or "-",
            "objetivo": r.get("objective") or "-",
            "status": "ACTIVE" if m["gasto"] > 0 else "PAUSED",
            **m,
        })
    saida.sort(key=lambda x: x["gasto"], reverse=True)
    return saida[:15]


def _fetch_adsets(act_id: str, token: str, since: date, until: date) -> list[dict[str, Any]]:
    rows = _fetch_insights_breakdown(
        act_id, token, since, until,
        level="adset",
        extra_fields="adset_name,campaign_name",
    )
    saida = []
    for r in rows:
        m = _row_metrics(r)
        saida.append({
            "adset": r.get("adset_name") or "-",
            "campanha": r.get("campaign_name") or "-",
            "gasto": m["gasto"],
            "impressoes": m["impressoes"],
            "cliques": m["cliques"],
            "reach": m["reach"],
            "frequency": m["frequency"],
            "ctr_pct": m["ctr_pct"],
            "conversas_msg": m["conversas_msg"],
            "cpa_msg": m["cpa_msg"],
            "insight": None,
        })
    saida.sort(key=lambda x: x["gasto"], reverse=True)
    return saida[:20]


def _fetch_anuncios(act_id: str, token: str, since: date, until: date) -> list[dict[str, Any]]:
    """Ads com quality rankings + video insights."""
    rows = _fetch_insights_breakdown(
        act_id, token, since, until,
        level="ad",
        extra_fields=(
            "ad_name,campaign_name,quality_ranking,engagement_rate_ranking,"
            "conversion_rate_ranking,video_thruplay_watched_actions,"
            "video_avg_time_watched_actions,video_p25_watched_actions,"
            "video_p50_watched_actions,video_p75_watched_actions,"
            "video_p95_watched_actions,video_play_actions"
        ),
    )
    saida = []
    for r in rows:
        m = _row_metrics(r)

        def _first_action(field: str) -> int:
            arr = r.get(field) or []
            for a in arr:
                v = a.get("value")
                try:
                    return int(float(v))
                except (TypeError, ValueError):
                    continue
            return 0

        def _first_action_float(field: str) -> float:
            arr = r.get(field) or []
            for a in arr:
                v = a.get("value")
                try:
                    return round(float(v), 2)
                except (TypeError, ValueError):
                    continue
            return 0.0

        saida.append({
            "ad": r.get("ad_name") or "-",
            "campanha": r.get("campaign_name") or "-",
            "gasto": m["gasto"],
            "impressoes": m["impressoes"],
            "cliques": m["cliques"],
            "reach": m["reach"],
            "frequency": m["frequency"],
            "ctr_pct": m["ctr_pct"],
            "cpm": m["cpm"],
            "conversas_msg": m["conversas_msg"],
            "cpa_msg": m["cpa_msg"],
            "status": "ACTIVE" if m["gasto"] > 0 else "PAUSED",
            "copy_curto": None,
            "thumb": None,
            "quality_ranking": r.get("quality_ranking"),
            "engagement_rate_ranking": r.get("engagement_rate_ranking"),
            "conversion_rate_ranking": r.get("conversion_rate_ranking"),
            "video": {
                "plays": _first_action("video_play_actions"),
                "thruplay_watched": _first_action("video_thruplay_watched_actions"),
                "avg_time_watched_s": _first_action_float("video_avg_time_watched_actions"),
                "p25": _first_action("video_p25_watched_actions"),
                "p50": _first_action("video_p50_watched_actions"),
                "p75": _first_action("video_p75_watched_actions"),
                "p95": _first_action("video_p95_watched_actions"),
            },
        })
    saida.sort(key=lambda x: x["gasto"], reverse=True)
    return saida[:25]


def _fetch_device_platform(act_id: str, token: str, since: date, until: date) -> list[dict[str, Any]]:
    rows = _fetch_insights_breakdown(
        act_id, token, since, until,
        level="account",
        breakdowns="device_platform",
    )
    total = sum(float(r.get("spend") or 0) for r in rows) or 1.0
    saida = []
    for r in rows:
        m = _row_metrics(r)
        share = round(m["gasto"] / total * 100, 2) if total else 0.0
        saida.append({
            "device": r.get("device_platform") or "-",
            **m,
            "share_pct": share,
        })
    saida.sort(key=lambda x: x["gasto"], reverse=True)
    return saida


def _fetch_hourly(act_id: str, token: str, since: date, until: date) -> list[dict[str, Any]]:
    """Breakdown por hora do dia (agregado no periodo). Devolve 24 slots (0..23h)."""
    rows = _fetch_insights_breakdown(
        act_id, token, since, until,
        level="account",
        breakdowns="hourly_stats_aggregated_by_advertiser_time_zone",
    )
    por_hora: dict[str, dict[str, Any]] = {}
    for r in rows:
        hora = (r.get("hourly_stats_aggregated_by_advertiser_time_zone") or "-")[:5]  # ex "08:00"
        m = _row_metrics(r)
        slot = por_hora.setdefault(hora, {"hora": hora, "gasto": 0.0, "impressoes": 0, "cliques": 0,
                                          "conversas_msg": 0, "reach": 0, "cpa_msg": None})
        slot["gasto"] += m["gasto"]
        slot["impressoes"] += m["impressoes"]
        slot["cliques"] += m["cliques"]
        slot["conversas_msg"] += m["conversas_msg"]
        slot["reach"] += m["reach"]
    for s in por_hora.values():
        s["gasto"] = round(s["gasto"], 2)
        s["cpa_msg"] = round(s["gasto"] / s["conversas_msg"], 2) if s["conversas_msg"] else None
        s["ctr_pct"] = round((s["cliques"] / s["impressoes"] * 100), 2) if s["impressoes"] else 0.0
    return sorted(por_hora.values(), key=lambda x: x["hora"])


def _fetch_ads_recommendations(act_id: str, token: str) -> list[dict[str, Any]]:
    """Recomendacoes oficiais Meta para a conta (Meta Ads Recommendations API)."""
    try:
        resp = _graph_get(
            f"/{act_id}",
            {"fields": "recommendations{title,message,importance,recommendation_data,creation_time}"},
            token,
        )
    except Exception as e:
        print(f"  [INFO] Ads recommendations indisponivel: {str(e)[:120]}", file=sys.stderr)
        return []
    rec = (resp.get("recommendations") or {}).get("data") or []
    saida = []
    for r in rec[:25]:
        saida.append({
            "titulo": r.get("title") or "-",
            "mensagem": r.get("message") or "-",
            "importancia": r.get("importance") or "-",
            "data": (r.get("creation_time") or "")[:10],
            "dados": r.get("recommendation_data"),
        })
    return saida


def _agregar_video_insights(anuncios: list[dict[str, Any]]) -> dict[str, Any]:
    """Soma video insights de todos os anuncios."""
    agg = {"plays": 0, "thruplay_watched": 0, "p25": 0, "p50": 0, "p75": 0, "p95": 0}
    n_com_video = 0
    for a in anuncios:
        v = a.get("video") or {}
        if v.get("plays"):
            n_com_video += 1
        for k in agg:
            agg[k] += int(v.get(k) or 0)
    agg["taxa_conclusao_pct"] = round(agg["p95"] / agg["plays"] * 100, 2) if agg["plays"] else 0.0
    agg["taxa_meio_pct"] = round(agg["p50"] / agg["plays"] * 100, 2) if agg["plays"] else 0.0
    agg["anuncios_com_video"] = n_com_video
    return agg


def _fetch_demografia(act_id: str, token: str, since: date, until: date) -> list[dict[str, Any]]:
    rows = _fetch_insights_breakdown(
        act_id, token, since, until,
        level="account",
        breakdowns="age,gender",
    )
    total = sum(float(r.get("spend") or 0) for r in rows) or 1.0
    saida = []
    for r in rows:
        m = _row_metrics(r)
        share = round(m["gasto"] / total * 100, 2) if total else 0.0
        saida.append({
            "faixa": r.get("age") or "-",
            "genero": r.get("gender") or "-",
            "gasto": m["gasto"],
            "impressoes": m["impressoes"],
            "cliques": m["cliques"],
            "reach": m["reach"],
            "frequency": m["frequency"],
            "ctr_pct": m["ctr_pct"],
            "conversas_msg": m["conversas_msg"],
            "cpa_msg": m["cpa_msg"],
            "share_pct": share,
            "status": "ACTIVE" if m["gasto"] > 0 else "PAUSED",
        })
    saida.sort(key=lambda x: x["gasto"], reverse=True)
    return saida


def _fetch_placement(act_id: str, token: str, since: date, until: date) -> list[dict[str, Any]]:
    rows = _fetch_insights_breakdown(
        act_id, token, since, until,
        level="account",
        breakdowns="publisher_platform,platform_position",
    )
    total = sum(float(r.get("spend") or 0) for r in rows) or 1.0
    saida = []
    for r in rows:
        m = _row_metrics(r)
        share = round(m["gasto"] / total * 100, 2) if total else 0.0
        saida.append({
            "plataforma": r.get("publisher_platform") or "-",
            "posicao": r.get("platform_position") or "-",
            "gasto": m["gasto"],
            "impressoes": m["impressoes"],
            "cliques": m["cliques"],
            "reach": m["reach"],
            "frequency": m["frequency"],
            "ctr_pct": m["ctr_pct"],
            "cpm": m["cpm"],
            "conversas_msg": m["conversas_msg"],
            "cpa_msg": m["cpa_msg"],
            "share_pct": share,
            "status": "ACTIVE" if m["gasto"] > 0 else "PAUSED",
        })
    saida.sort(key=lambda x: x["gasto"], reverse=True)
    return saida


def _fetch_geografia(act_id: str, token: str, since: date, until: date) -> list[dict[str, Any]]:
    rows = _fetch_insights_breakdown(
        act_id, token, since, until,
        level="account",
        breakdowns="region",
    )
    total = sum(float(r.get("spend") or 0) for r in rows) or 1.0
    saida = []
    for r in rows:
        m = _row_metrics(r)
        share = round(m["gasto"] / total * 100, 2) if total else 0.0
        saida.append({
            "regiao": r.get("region") or "-",
            "gasto": m["gasto"],
            "impressoes": m["impressoes"],
            "cliques": m["cliques"],
            "reach": m["reach"],
            "ctr_pct": m["ctr_pct"],
            "cpm": m["cpm"],
            "conversas_msg": m["conversas_msg"],
            "share_pct": share,
            "alerta": None,
        })
    saida.sort(key=lambda x: x["gasto"], reverse=True)
    return saida[:20]


def _por_objetivo(campanhas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrupa campanhas por objetivo."""
    grupos: dict[str, dict[str, Any]] = {}
    total_gasto = sum(c["gasto"] for c in campanhas) or 1.0
    for c in campanhas:
        obj = c.get("objetivo") or "-"
        g = grupos.setdefault(obj, {
            "objetivo": obj,
            "gasto": 0.0, "impressoes": 0, "cliques": 0, "reach": 0,
            "conversas_msg": 0, "frequency": 0.0, "ctr_pct": 0.0,
            "cpm": 0.0, "cpa_msg": None, "insight": None,
        })
        g["gasto"] += c.get("gasto", 0)
        g["impressoes"] += c.get("impressoes", 0)
        g["cliques"] += c.get("cliques", 0)
        g["reach"] += c.get("reach", 0)
        g["conversas_msg"] += c.get("conversas_msg", 0)
    saida = []
    for obj, g in grupos.items():
        g["gasto"] = round(g["gasto"], 2)
        g["ctr_pct"] = round((g["cliques"] / g["impressoes"] * 100), 2) if g["impressoes"] else 0.0
        g["cpm"] = round((g["gasto"] / g["impressoes"] * 1000), 2) if g["impressoes"] else 0.0
        g["cpa_msg"] = round(g["gasto"] / g["conversas_msg"], 2) if g["conversas_msg"] else None
        g["share_gasto_pct"] = round(g["gasto"] / total_gasto * 100, 2) if total_gasto else 0.0
        saida.append(g)
    saida.sort(key=lambda x: x["gasto"], reverse=True)
    return saida


def _fetch_breakdowns_janela(act_id: str, token: str, since: date, until: date, incluir_pesados: bool = True) -> dict[str, Any]:
    """Puxa todos os breakdowns para UMA janela.

    incluir_pesados=False pula demografia/placement/geografia (usado na janela
    'hoje' pra evitar 5x mais chamadas por refresh).
    """
    campanhas = _fetch_campanhas(act_id, token, since, until)
    adsets = _fetch_adsets(act_id, token, since, until)
    por_obj = _por_objetivo(campanhas)
    saida: dict[str, Any] = {
        "top_campanhas": campanhas,
        "ad_sets": adsets,
        "por_objetivo": por_obj,
    }
    if incluir_pesados:
        saida["demografia"] = _fetch_demografia(act_id, token, since, until)
        saida["placement"] = _fetch_placement(act_id, token, since, until)
    return saida


# ---------------------------------------------------------------------------
# Facebook Page — organico 30d
# ---------------------------------------------------------------------------

def _fetch_fb_organico_30d(page_id: str, page_token: str, hoje: date) -> dict[str, Any] | None:
    """Puxa page_post_engagements + page_views + video_views organicos+pagos nos ultimos 30d.

    Precisa de Page Access Token. Se algum metric falhar so aquele fica 0.
    """
    inicio, fim = _janela("last_30d", hoje)
    since_ts = int(datetime.combine(inicio, datetime.min.time(), tzinfo=BRT).timestamp())
    until_ts = int(datetime.combine(fim, datetime.max.time(), tzinfo=BRT).timestamp())
    metrics = "page_post_engagements,page_views_total,page_video_views_organic,page_video_views_paid,page_video_views"
    try:
        resp = _graph_get(
            f"/{page_id}/insights",
            {"metric": metrics, "period": "day", "since": since_ts, "until": until_ts},
            page_token,
        )
    except Exception as e:
        print(f"  [WARN] FB organico 30d falhou: {e}", file=sys.stderr)
        return None
    saida = {
        "page_post_engagements": 0,
        "page_visits": 0,
        "video_views_organicos": 0,
        "video_views_pagos": 0,
        "total_video_views": 0,
        "insight": None,
    }
    for m in resp.get("data", []):
        name = m.get("name")
        total = 0
        for v in m.get("values", []) or []:
            val = v.get("value")
            if isinstance(val, (int, float)):
                total += int(val)
        if name == "page_post_engagements":
            saida["page_post_engagements"] = total
        elif name == "page_views_total":
            saida["page_visits"] = total
        elif name == "page_video_views_organic":
            saida["video_views_organicos"] = total
        elif name == "page_video_views_paid":
            saida["video_views_pagos"] = total
        elif name == "page_video_views":
            saida["total_video_views"] = total
    return saida


# ---------------------------------------------------------------------------
# Deltas + benchmarks
# ---------------------------------------------------------------------------

def _delta_pct(atual: float, anterior: float) -> float | None:
    if anterior in (0, None):
        return None
    return round((atual - anterior) / anterior * 100, 2)


def _calcular_deltas(periodos: dict[str, dict[str, Any]], act_id: str, token: str, hoje: date, now_iso: str) -> dict[str, Any]:
    """Compara 7d atual vs 7d anteriores + MTD vs mes anterior mesmo dia."""
    saida: dict[str, Any] = {}

    # 7d vs 7d anteriores
    inicio7, fim7 = _janela("last_7d", hoje)
    inicio7_ant = inicio7 - timedelta(days=7)
    fim7_ant = fim7 - timedelta(days=7)
    try:
        resp = _graph_get(
            f"/{act_id}/insights",
            {
                "fields": INSIGHT_FIELDS,
                "time_range": json.dumps({"since": _iso(inicio7_ant), "until": _iso(fim7_ant)}),
                "level": "account",
            },
            token,
        )
        rows = resp.get("data") or []
        ant = _row_metrics(rows[0]) if rows else _row_metrics({})
        atual = periodos.get("7d") or {}
        saida["7d"] = {
            "_base": f"{_iso(inicio7_ant)} a {_iso(fim7_ant)}",
            "gasto_pct": _delta_pct(atual.get("gasto", 0), ant["gasto"]),
            "impressoes_pct": _delta_pct(atual.get("impressoes", 0), ant["impressoes"]),
            "cliques_pct": _delta_pct(atual.get("cliques", 0), ant["cliques"]),
            "conversas_msg_pct": _delta_pct(atual.get("conversas_msg", 0), ant["conversas_msg"]),
            "cpa_msg_pct": _delta_pct(atual.get("cpa_msg") or 0, ant["cpa_msg"] or 0),
            "reach_pct": _delta_pct(atual.get("reach", 0), ant["reach"]),
        }
    except Exception as e:
        print(f"  [WARN] Delta 7d anterior falhou: {e}", file=sys.stderr)

    # MTD vs mesmo periodo mes anterior (dia 1 -> dia atual do mes anterior)
    inicio_mes = hoje.replace(day=1)
    if inicio_mes.month == 1:
        inicio_mes_ant = inicio_mes.replace(year=inicio_mes.year - 1, month=12)
    else:
        inicio_mes_ant = inicio_mes.replace(month=inicio_mes.month - 1)
    try:
        fim_mes_ant = inicio_mes_ant.replace(day=hoje.day)
    except ValueError:
        # dia atual nao existe no mes anterior (ex: 31 em fev) — usa ultimo dia
        proximo = (inicio_mes_ant.replace(day=28) + timedelta(days=4)).replace(day=1)
        fim_mes_ant = proximo - timedelta(days=1)
    try:
        resp = _graph_get(
            f"/{act_id}/insights",
            {
                "fields": INSIGHT_FIELDS,
                "time_range": json.dumps({"since": _iso(inicio_mes_ant), "until": _iso(fim_mes_ant)}),
                "level": "account",
            },
            token,
        )
        rows = resp.get("data") or []
        ant = _row_metrics(rows[0]) if rows else _row_metrics({})
        atual = periodos.get("mtd") or {}
        saida["mtd"] = {
            "_base": f"{_iso(inicio_mes_ant)} a {_iso(fim_mes_ant)}",
            "gasto_pct": _delta_pct(atual.get("gasto", 0), ant["gasto"]),
            "impressoes_pct": _delta_pct(atual.get("impressoes", 0), ant["impressoes"]),
            "cliques_pct": _delta_pct(atual.get("cliques", 0), ant["cliques"]),
            "conversas_msg_pct": _delta_pct(atual.get("conversas_msg", 0), ant["conversas_msg"]),
            "cpa_msg_pct": _delta_pct(atual.get("cpa_msg") or 0, ant["cpa_msg"] or 0),
            "reach_pct": _delta_pct(atual.get("reach", 0), ant["reach"]),
        }
    except Exception as e:
        print(f"  [WARN] Delta MTD anterior falhou: {e}", file=sys.stderr)

    return saida


def _atualizar_benchmarks(base_bench: dict[str, Any], periodos: dict[str, dict[str, Any]]) -> None:
    """Popula *_atual_30d e cpa_msg_mtd_setembro a partir dos periodos."""
    p30 = periodos.get("30d") or {}
    pm = periodos.get("mtd") or {}
    base_bench["cpa_msg_atual_30d"] = p30.get("cpa_msg")
    base_bench["cpm_atual_30d"] = p30.get("cpm", 0.0)
    base_bench["ctr_atual_30d"] = p30.get("ctr_pct", 0.0)
    base_bench["frequency_atual_30d"] = p30.get("frequency", 0.0)
    freq = p30.get("frequency", 0.0) or 0.0
    if freq >= 4:
        base_bench["frequency_alerta"] = "critico"
    elif freq >= 2.5:
        base_bench["frequency_alerta"] = "atencao"
    else:
        base_bench["frequency_alerta"] = "ok"
    base_bench["cpa_msg_mtd_setembro"] = pm.get("cpa_msg")


# ---------------------------------------------------------------------------
# Instagram
# ---------------------------------------------------------------------------

def _fetch_ig_profile(ig_user_id: str, token: str) -> dict[str, Any]:
    return _graph_get(f"/{ig_user_id}", {"fields": "followers_count,media_count,username"}, token)


def _fetch_ig_insights_range(ig_user_id: str, token: str, since: date, until: date) -> dict[str, int]:
    """Agrega reach + profile_views + follower_count no intervalo.

    Meta separou as APIs: reach + follower_count continuam period=day (metric_type
    implicito time_series). profile_views precisa de metric_type=total_value desde
    a v20 (retorna um unico total_value por metric no periodo).
    """
    agg: dict[str, int] = {"reach": 0, "profile_views": 0, "novos_seguidores": 0}
    since_ts = int(datetime.combine(since, datetime.min.time(), tzinfo=BRT).timestamp())
    until_ts = int(datetime.combine(until, datetime.max.time(), tzinfo=BRT).timestamp())

    # 1) reach + follower_count (time_series diario)
    try:
        resp = _graph_get(
            f"/{ig_user_id}/insights",
            {
                "metric": "reach,follower_count",
                "period": "day",
                "since": since_ts,
                "until": until_ts,
            },
            token,
        )
        for metric in resp.get("data", []):
            name = metric.get("name")
            total = 0
            for val in metric.get("values", []) or []:
                v = val.get("value")
                if isinstance(v, (int, float)):
                    total += int(v)
            if name == "reach":
                agg["reach"] = total
            elif name == "follower_count":
                agg["novos_seguidores"] = total
    except Exception as e:
        print(f"  [WARN] IG reach/follower {since}..{until} falhou: {e}", file=sys.stderr)

    # 2) profile_views (total_value no periodo)
    try:
        resp2 = _graph_get(
            f"/{ig_user_id}/insights",
            {
                "metric": "profile_views",
                "period": "day",
                "metric_type": "total_value",
                "since": since_ts,
                "until": until_ts,
            },
            token,
        )
        for metric in resp2.get("data", []):
            if metric.get("name") != "profile_views":
                continue
            tv = metric.get("total_value") or {}
            v = tv.get("value")
            if isinstance(v, (int, float)):
                agg["profile_views"] = int(v)
    except Exception as e:
        print(f"  [WARN] IG profile_views {since}..{until} falhou: {e}", file=sys.stderr)

    return agg


def _fetch_ig_daily(ig_user_id: str, token: str, hoje: date) -> list[dict[str, Any]]:
    """Serie diaria de reach + follower_count nos ultimos 30d.

    profile_views nao entra na serie diaria: com metric_type=total_value o Meta
    retorna um unico total pro periodo, sem breakdown por dia.
    """
    inicio, fim = _janela("last_30d", hoje)
    try:
        resp = _graph_get(
            f"/{ig_user_id}/insights",
            {
                "metric": "reach,follower_count",
                "period": "day",
                "since": int(datetime.combine(inicio, datetime.min.time(), tzinfo=BRT).timestamp()),
                "until": int(datetime.combine(fim, datetime.max.time(), tzinfo=BRT).timestamp()),
            },
            token,
        )
    except Exception as e:
        print(f"  [WARN] IG serie diaria falhou: {e}", file=sys.stderr)
        return []
    por_dia: dict[str, dict[str, int]] = {}
    for metric in resp.get("data", []):
        name = metric.get("name")
        for val in metric.get("values", []) or []:
            end = val.get("end_time", "")[:10]
            if not end:
                continue
            v = val.get("value")
            if not isinstance(v, (int, float)):
                continue
            slot = por_dia.setdefault(end, {"novos_seguidores": 0, "profile_views": 0, "reach": 0})
            if name == "reach":
                slot["reach"] = int(v)
            elif name == "follower_count":
                slot["novos_seguidores"] = int(v)
    return [
        {"data": d, **por_dia[d]}
        for d in sorted(por_dia)
    ]


def _fetch_ig_media(ig_user_id: str, token: str, hoje: date) -> tuple[list[dict[str, Any]], dict[str, Any] | None, int]:
    """Devolve (top_posts_30d, ultimo_post, posts_na_janela).

    Cada post: reach + like_count + comments_count + saved + shares + plays (reels).
    """
    inicio, _fim = _janela("last_30d", hoje)
    try:
        resp = _graph_get(
            f"/{ig_user_id}/media",
            {
                "fields": "id,media_type,media_product_type,permalink,caption,timestamp,like_count,comments_count",
                "limit": 25,
            },
            token,
        )
    except Exception as e:
        print(f"  [WARN] IG media falhou: {e}", file=sys.stderr)
        return [], None, 0

    posts = resp.get("data", []) or []
    if not posts:
        return [], None, 0

    # ultimo post
    ultimo = None
    try:
        last = max(posts, key=lambda p: p.get("timestamp") or "")
        ts = last.get("timestamp", "")[:10]
        if ts:
            dias = (hoje - datetime.strptime(ts, "%Y-%m-%d").date()).days
            ultimo = {"data": ts, "dias_sem_postar": max(0, dias)}
    except Exception:
        ultimo = None

    # Para cada post na janela, puxa insights (reach + saved + shares + plays/reels)
    na_janela: list[dict[str, Any]] = []
    for p in posts:
        ts = (p.get("timestamp") or "")[:10]
        if not ts:
            continue
        try:
            d_post = datetime.strptime(ts, "%Y-%m-%d").date()
        except ValueError:
            continue
        if d_post < inicio:
            continue

        mtype = (p.get("media_type") or "").upper()
        mprod = (p.get("media_product_type") or "").upper()
        # metrica base sempre: reach + saved + shares
        # reels/videos: adicionar plays + total_interactions
        metrics = ["reach", "saved", "shares"]
        if mprod == "REELS" or mtype == "VIDEO":
            metrics += ["plays", "total_interactions"]

        insights_dict = {"reach": 0, "saved": 0, "shares": 0, "plays": 0, "total_interactions": 0}
        try:
            ins_resp = _graph_get(
                f"/{p.get('id')}/insights",
                {"metric": ",".join(metrics)},
                token,
            )
            for m in ins_resp.get("data", []) or []:
                name = m.get("name")
                total = 0
                for v in m.get("values", []) or []:
                    if isinstance(v.get("value"), (int, float)):
                        total += int(v["value"])
                if name in insights_dict:
                    insights_dict[name] = total
        except Exception as e:
            print(f"  [WARN] IG insights post {p.get('id')} falhou: {e}", file=sys.stderr)

        cap = (p.get("caption") or "").strip().replace("\n", " ")
        na_janela.append({
            "data": ts,
            "tipo": p.get("media_type"),
            "produto": p.get("media_product_type"),
            "reach": insights_dict["reach"],
            "likes": int(p.get("like_count") or 0),
            "comments": int(p.get("comments_count") or 0),
            "saved": insights_dict["saved"],
            "shares": insights_dict["shares"],
            "plays": insights_dict["plays"],
            "total_interactions": insights_dict["total_interactions"],
            "url": p.get("permalink"),
            "caption_curta": cap[:80],
        })

    top10 = sorted(na_janela, key=lambda x: x["reach"], reverse=True)[:10]
    return top10, ultimo, len(na_janela)


def _fetch_ig_audience_demografia(ig_user_id: str, token: str) -> dict[str, Any] | None:
    """Demografia dos SEGUIDORES (age+gender+city+country).

    Meta descontinuando 'audience_gender_age' pra contas pequenas; v20 ainda
    aceita se followers >= 100. Fallback graceful.
    """
    saida = {"age_gender": [], "cidades_top10": [], "paises_top5": []}
    for metric, chave in [
        ("audience_gender_age", "age_gender"),
        ("audience_city", "cidades_top10"),
        ("audience_country", "paises_top5"),
    ]:
        try:
            resp = _graph_get(
                f"/{ig_user_id}/insights",
                {"metric": metric, "period": "lifetime"},
                token,
            )
            for m in resp.get("data", []) or []:
                vals = m.get("values", []) or []
                if not vals:
                    continue
                v = vals[0].get("value") or {}
                if not isinstance(v, dict):
                    continue
                items = sorted(
                    [(k, int(x)) for k, x in v.items() if isinstance(x, (int, float))],
                    key=lambda kv: kv[1], reverse=True,
                )
                if chave == "age_gender":
                    saida["age_gender"] = [{"faixa": k, "n": n} for k, n in items]
                elif chave == "cidades_top10":
                    saida["cidades_top10"] = [{"cidade": k, "n": n} for k, n in items[:10]]
                elif chave == "paises_top5":
                    saida["paises_top5"] = [{"pais": k, "n": n} for k, n in items[:5]]
        except Exception as e:
            print(f"  [INFO] IG audience {metric} indisponivel: {str(e)[:120]}", file=sys.stderr)
    if not saida["age_gender"] and not saida["cidades_top10"] and not saida["paises_top5"]:
        return None
    return saida


def _fetch_ig_stories(ig_user_id: str, token: str) -> dict[str, Any] | None:
    """Stories ativas + insights agregados.

    Stories somem em 24h — snapshot atual apenas.
    """
    try:
        resp = _graph_get(
            f"/{ig_user_id}/stories",
            {"fields": "id,media_type,timestamp,permalink"},
            token,
        )
    except Exception as e:
        print(f"  [INFO] IG stories indisponivel: {str(e)[:120]}", file=sys.stderr)
        return None
    stories = resp.get("data", []) or []
    if not stories:
        return {"ativas": 0, "impressions": 0, "reach": 0, "replies": 0, "exits": 0, "taps_forward": 0, "taps_back": 0, "detalhes": []}

    agg = {"impressions": 0, "reach": 0, "replies": 0, "exits": 0, "taps_forward": 0, "taps_back": 0}
    detalhes = []
    for s in stories[:20]:
        s_id = s.get("id")
        insights = {"impressions": 0, "reach": 0, "replies": 0, "exits": 0, "taps_forward": 0, "taps_back": 0}
        try:
            ins = _graph_get(
                f"/{s_id}/insights",
                {"metric": "impressions,reach,replies,exits,taps_forward,taps_back"},
                token,
            )
            for m in ins.get("data", []) or []:
                name = m.get("name")
                if name in insights:
                    vals = m.get("values", []) or []
                    if vals and isinstance(vals[0].get("value"), (int, float)):
                        insights[name] = int(vals[0]["value"])
        except Exception:
            pass
        for k, v in insights.items():
            agg[k] += v
        detalhes.append({
            "id": s_id,
            "tipo": s.get("media_type"),
            "data": (s.get("timestamp") or "")[:10],
            "url": s.get("permalink"),
            **insights,
        })
    return {"ativas": len(stories), **agg, "detalhes": detalhes}


# ---------------------------------------------------------------------------
# Facebook Page
# ---------------------------------------------------------------------------

def _get_page_access_token(page_id: str, user_token: str) -> str | None:
    """Busca Page Access Token para uma pagina especifica.

    A partir da nova experiencia de Paginas, listar posts exige token de pagina,
    nao user token. /me/accounts devolve todas as paginas admin com respectivo
    access_token; pegamos o da page_id procurada.
    """
    try:
        resp = _graph_get_all(
            "/me/accounts",
            {"fields": "id,access_token", "limit": 100},
            user_token,
            max_pages=3,
        )
    except Exception as e:
        print(f"  [WARN] /me/accounts falhou: {e}", file=sys.stderr)
        return None
    for p in resp:
        if str(p.get("id")) == str(page_id):
            tok = p.get("access_token")
            if tok:
                return tok
    return None


def _fetch_fb_posts_detalhes(page_id: str, page_token: str, hoje: date) -> list[dict[str, Any]]:
    """Lista posts ultimos 30d com insights por post (reach/impressions/engagement/reactions)."""
    inicio, fim = _janela("last_30d", hoje)
    try:
        posts = _graph_get_all(
            f"/{page_id}/posts",
            {
                "fields": "id,created_time,message,permalink_url,attachments{media_type}",
                "since": _iso(inicio),
                "until": _iso(fim),
                "limit": 50,
            },
            page_token,
            max_pages=4,
        )
    except Exception as e:
        print(f"  [WARN] FB posts detalhes list falhou: {e}", file=sys.stderr)
        return []
    saida = []
    for p in posts[:30]:
        pid = p.get("id")
        ins = {"post_impressions": 0, "post_impressions_unique": 0, "post_engaged_users": 0, "post_reactions_by_type_total": {}}
        try:
            resp = _graph_get(
                f"/{pid}/insights",
                {"metric": "post_impressions,post_impressions_unique,post_engaged_users,post_reactions_by_type_total"},
                page_token,
            )
            for m in resp.get("data", []) or []:
                name = m.get("name")
                vals = m.get("values", []) or []
                if not vals:
                    continue
                v = vals[0].get("value")
                ins[name] = v if isinstance(v, dict) else int(v or 0)
        except Exception:
            pass
        msg = (p.get("message") or "").strip().replace("\n", " ")
        attach = (((p.get("attachments") or {}).get("data") or [{}])[0]).get("media_type", "-")
        saida.append({
            "id": pid,
            "data": (p.get("created_time") or "")[:10],
            "tipo": attach,
            "impressions": ins["post_impressions"] if isinstance(ins["post_impressions"], int) else 0,
            "reach": ins["post_impressions_unique"] if isinstance(ins["post_impressions_unique"], int) else 0,
            "engajados": ins["post_engaged_users"] if isinstance(ins["post_engaged_users"], int) else 0,
            "reactions": ins["post_reactions_by_type_total"] if isinstance(ins["post_reactions_by_type_total"], dict) else {},
            "url": p.get("permalink_url"),
            "texto_curto": msg[:100],
        })
    saida.sort(key=lambda x: x["reach"], reverse=True)
    return saida


def _fetch_fb_serie_diaria_seguidores(page_id: str, page_token: str, hoje: date) -> list[dict[str, Any]]:
    """Serie diaria de page_fans + page_fan_adds + page_fan_removes nos ultimos 30d."""
    inicio, fim = _janela("last_30d", hoje)
    since_ts = int(datetime.combine(inicio, datetime.min.time(), tzinfo=BRT).timestamp())
    until_ts = int(datetime.combine(fim, datetime.max.time(), tzinfo=BRT).timestamp())
    try:
        resp = _graph_get(
            f"/{page_id}/insights",
            {"metric": "page_fans,page_fan_adds,page_fan_removes", "period": "day",
             "since": since_ts, "until": until_ts},
            page_token,
        )
    except Exception as e:
        print(f"  [WARN] FB serie diaria seguidores falhou: {e}", file=sys.stderr)
        return []
    por_dia: dict[str, dict[str, int]] = {}
    for m in resp.get("data", []) or []:
        name = m.get("name")
        for val in m.get("values", []) or []:
            end = (val.get("end_time") or "")[:10]
            if not end:
                continue
            v = val.get("value")
            if not isinstance(v, (int, float)):
                continue
            slot = por_dia.setdefault(end, {"page_fans": 0, "page_fan_adds": 0, "page_fan_removes": 0})
            slot[name] = int(v)
    return [{"data": d, **por_dia[d]} for d in sorted(por_dia)]


def _fb_reactions_from_posts(posts_det: list[dict[str, Any]]) -> dict[str, int] | None:
    """Agrega reactions por tipo dos posts ja puxados (evita chamada duplicada)."""
    agg: dict[str, int] = {"like": 0, "love": 0, "haha": 0, "wow": 0, "sad": 0, "angry": 0}
    for p in posts_det or []:
        r = p.get("reactions") or {}
        for tipo, n in r.items():
            if tipo in agg and isinstance(n, (int, float)):
                agg[tipo] += int(n)
    if sum(agg.values()) == 0:
        return None
    return agg


def _fetch_fb_page(page_id: str, token: str, hoje: date) -> dict[str, Any]:
    saida: dict[str, Any] = {}
    try:
        info = _graph_get(f"/{page_id}", {"fields": "followers_count,fan_count,name"}, token)
        saida["nome"] = info.get("name")
        saida["seguidores"] = int(info.get("followers_count") or info.get("fan_count") or 0)
    except Exception as e:
        print(f"  [WARN] FB page info falhou: {e}", file=sys.stderr)

    # posts 30d — precisa de Page Access Token
    page_token = _get_page_access_token(page_id, token)
    if not page_token:
        print(f"  [WARN] FB page {page_id}: sem Page Access Token disponivel (user nao admin da pagina?), pulando posts_30d", file=sys.stderr)
        return saida

    inicio, fim = _janela("last_30d", hoje)
    try:
        posts = _graph_get_all(
            f"/{page_id}/posts",
            {
                "fields": "id,created_time",
                "since": _iso(inicio),
                "until": _iso(fim),
                "limit": 50,
            },
            page_token,
            max_pages=4,
        )
        saida["posts_30d"] = len(posts)
    except Exception as e:
        print(f"  [WARN] FB page posts falhou: {e}", file=sys.stderr)

    return saida


# ---------------------------------------------------------------------------
# Merge (respeita schema base)
# ---------------------------------------------------------------------------

def _update_periodo(base_periodo: dict[str, Any], novo: dict[str, Any]) -> None:
    """Sobrescreve os campos numericos, preserva `alerta` da base (curado)."""
    for k, v in novo.items():
        if k == "_erro":
            base_periodo["_erro"] = v
            continue
        # nunca criar chaves que a base nao tenha (respeita schema)
        if k in base_periodo:
            base_periodo[k] = v
    # se veio label novo e a base nao tinha, ainda preserva um label sensato
    if "label" not in base_periodo and "label" in novo:
        base_periodo["label"] = novo["label"]
    # atualizado_em pode nao existir na base SPA — cria se novo trouxer
    if "atualizado_em" not in base_periodo and novo.get("atualizado_em"):
        base_periodo["atualizado_em"] = novo["atualizado_em"]


def _set_if_key(d: dict[str, Any], key: str, value: Any) -> None:
    if key in d:
        d[key] = value


def _merge_unidade(base: dict[str, Any], ids: dict[str, Any], token: str, hoje: date) -> dict[str, Any]:
    """Aplica dados frescos da API sobre a base. Retorna a base mutada."""
    now_iso = datetime.now(BRT).isoformat(timespec="seconds")
    gerado_anterior = base.get("gerado_em", "?")

    # ---------- Meta Ads ----------
    act_id = ids.get("meta_ad_account_id")
    if act_id:
        print(f"  [Meta Ads] {act_id} — insights hoje/7d/mtd/30d/90d + serie 30d")
        periodos = _fetch_ad_insights(act_id, token, hoje, now_iso)
        meta_ads = base.setdefault("meta_ads", {})
        pp = meta_ads.setdefault("por_periodo", {})
        for chave, novo in periodos.items():
            base_p = pp.setdefault(chave, {})
            if not base_p:
                # base nao tinha esse periodo — grava inteiro
                pp[chave] = novo
            else:
                _update_periodo(base_p, novo)

        serie = _fetch_serie_diaria(act_id, token, hoje)
        if serie:
            meta_ads["serie_diaria_30d"] = serie
        # ad_account_id/nome sempre coerentes com config
        meta_ads["ad_account_id"] = act_id
        if ids.get("meta_ad_account_nome"):
            meta_ads["ad_account_nome"] = ids["meta_ad_account_nome"]

        # Breakdowns 30d — top-level sections
        print(f"  [Meta Ads] {act_id} — breakdowns 30d (campanhas/adsets/anuncios/demografia/placement/geografia)")
        ini30, fim30 = _janela("last_30d", hoje)
        campanhas30 = _fetch_campanhas(act_id, token, ini30, fim30)
        adsets30 = _fetch_adsets(act_id, token, ini30, fim30)
        anuncios30 = _fetch_anuncios(act_id, token, ini30, fim30)
        demografia30 = _fetch_demografia(act_id, token, ini30, fim30)
        placement30 = _fetch_placement(act_id, token, ini30, fim30)
        geografia30 = _fetch_geografia(act_id, token, ini30, fim30)
        por_obj30 = _por_objetivo(campanhas30)

        meta_ads["top_campanhas_30d"] = campanhas30
        meta_ads["ad_sets_30d"] = adsets30
        meta_ads["anuncios_30d"] = anuncios30
        meta_ads["por_objetivo_30d"] = por_obj30
        meta_ads["demografia_30d"] = demografia30
        meta_ads["placement_30d"] = placement30
        meta_ads["geografia_30d"] = geografia30

        # Breakdowns por janela (hoje/7d/mtd/90d) — reusa 30d na chave 30d
        print(f"  [Meta Ads] {act_id} — breakdowns por janela (hoje/7d/mtd/90d)")
        breakdowns: dict[str, Any] = meta_ads.setdefault("breakdowns", {})
        breakdowns["_nota"] = "Breakdowns por janela agregados via /act/insights com level=campaign/adset + breakdowns age,gender / publisher_platform / region."
        # hoje = leve
        h_ini, h_fim = _janela("today", hoje)
        breakdowns["hoje"] = _fetch_breakdowns_janela(act_id, token, h_ini, h_fim, incluir_pesados=False)
        # 7d = completo
        s7, f7 = _janela("last_7d", hoje)
        breakdowns["7d"] = _fetch_breakdowns_janela(act_id, token, s7, f7, incluir_pesados=True)
        # mtd = completo
        sm, fm = _janela("this_month", hoje)
        breakdowns["mtd"] = _fetch_breakdowns_janela(act_id, token, sm, fm, incluir_pesados=True)
        # 90d = completo
        s90, f90 = _janela("last_90d", hoje)
        breakdowns["90d"] = _fetch_breakdowns_janela(act_id, token, s90, f90, incluir_pesados=True)

        # Deltas + benchmarks (derivados)
        print(f"  [Meta Ads] {act_id} — deltas 7d/MTD vs periodo anterior + benchmarks")
        deltas = _calcular_deltas(pp, act_id, token, hoje, now_iso)
        if deltas:
            base_deltas = base.setdefault("deltas_vs_periodo_anterior", {})
            base_deltas.update(deltas)
        base_bench = base.setdefault("benchmarks", {})
        _atualizar_benchmarks(base_bench, pp)

        # verba_setembro (ritmos derivados de MTD + budget diario ativo)
        if not isinstance(meta_ads.get("verba_setembro"), dict):
            # SPA base tinha verba_setembro=0 (int) — troca por dict
            meta_ads["verba_setembro"] = {}
        vs = meta_ads["verba_setembro"]
        mtd = pp.get("mtd") or {}
        m30 = pp.get("30d") or {}
        dia = hoje.day
        gasto_mtd = mtd.get("gasto", 0) or 0
        vs["ritmo_real_mtd_dia"] = round(gasto_mtd / dia, 2) if dia else 0.0
        # projeta mes com base no ritmo MTD atual
        # dias no mes:
        if hoje.month == 12:
            prox = hoje.replace(year=hoje.year + 1, month=1, day=1)
        else:
            prox = hoje.replace(month=hoje.month + 1, day=1)
        dias_mes = (prox - hoje.replace(day=1)).days
        vs["projecao_no_ritmo_atual"] = round(vs["ritmo_real_mtd_dia"] * dias_mes, 2)
        vs["projecao_mes_30d"] = round(m30.get("gasto", 0), 2)
        vs["ad_sets_ativos"] = sum(1 for a in adsets30 if a["gasto"] > 0)
        vs["verificado_em"] = now_iso
        vs["nota_verificacao"] = "Ritmo e projecao calculados automaticamente a partir de /act/insights (MTD + last_30d)."

        # Device platform + hourly breakdowns 30d
        print(f"  [Meta Ads] {act_id} — device + hourly breakdowns 30d")
        meta_ads["device_30d"] = _fetch_device_platform(act_id, token, ini30, fim30)
        meta_ads["hourly_30d"] = _fetch_hourly(act_id, token, ini30, fim30)

        # Video insights agregado (a partir dos anuncios ja puxados)
        meta_ads["video_insights_30d"] = _agregar_video_insights(anuncios30)

        # Meta Ads recomendacoes oficiais (endpoint /act/recommendations)
        print(f"  [Meta Ads] {act_id} — recomendacoes oficiais")
        recs = _fetch_ads_recommendations(act_id, token)
        rec_meta = meta_ads.setdefault("recomendacoes_meta", {})
        if not isinstance(rec_meta, dict):
            rec_meta = {}
            meta_ads["recomendacoes_meta"] = rec_meta
        rec_meta["fonte"] = "Meta Ads Recommendations API"
        rec_meta["lido_em"] = now_iso
        rec_meta["itens_api"] = recs
        rec_meta["nota"] = f"{len(recs)} recomendacoes ativas da Meta para esta conta."

    # ---------- Instagram ----------
    ig_id = ids.get("ig_user_id")
    if ig_id:
        print(f"  [Instagram] user_id {ig_id} — profile + insights 30d/7d + media 25")
        ig = base.setdefault("instagram", {})
        try:
            prof = _fetch_ig_profile(ig_id, token)
            _set_if_key(ig, "followers", int(prof.get("followers_count") or 0))
            # SPA schema tem "followers" mas nao "posts_total"; Escova tem
            # "posts_total". So gravamos onde ja existir.
            _set_if_key(ig, "posts_total", int(prof.get("media_count") or 0))
            # se schema base nao tinha followers (improvavel), cria pra nao perder
            if "followers" not in ig:
                ig["followers"] = int(prof.get("followers_count") or 0)
            ig["handle"] = prof.get("username") or ig.get("handle") or ids.get("ig_handle")
        except Exception as e:
            print(f"  [WARN] IG profile falhou: {e}", file=sys.stderr)

        # Insights 30d
        inicio30, fim30 = _janela("last_30d", hoje)
        inicio7, fim7 = _janela("last_7d", hoje)
        ins30 = _fetch_ig_insights_range(ig_id, token, inicio30, fim30)
        ins7 = _fetch_ig_insights_range(ig_id, token, inicio7, fim7)

        # organico_30d: preserva notas/keys existentes
        if ins30:
            org30 = ig.setdefault("organico_30d", {})
            if isinstance(org30, dict):
                _set_if_key(org30, "novos_seguidores", ins30["novos_seguidores"])
                dias = 30
                _set_if_key(org30, "novos_seguidores_dia_medio", round(ins30["novos_seguidores"] / dias, 2))
                _set_if_key(org30, "profile_views", ins30["profile_views"])
                _set_if_key(org30, "profile_views_dia_medio", round(ins30["profile_views"] / dias, 2))
                # SPA usa "alcance_organico_30d" solto (int)
            # SPA tem "alcance_organico_30d" no nivel do instagram
            _set_if_key(ig, "alcance_organico_30d", ins30["reach"])
            # SPA tem "posts_30d" no nivel do instagram (contagem)

        if ins7:
            org7 = ig.setdefault("organico_7d", {})
            if isinstance(org7, dict):
                _set_if_key(org7, "novos_seguidores", ins7["novos_seguidores"])
                _set_if_key(org7, "profile_views", ins7["profile_views"])
                _set_if_key(org7, "reach", ins7["reach"])

        # Serie diaria IG
        serie_ig = _fetch_ig_daily(ig_id, token, hoje)
        if serie_ig:
            _set_if_key(ig, "serie_diaria_30d", serie_ig)

        # Media / top posts (agora com likes/comments/saved/shares/plays por post)
        top10, ultimo, na_janela = _fetch_ig_media(ig_id, token, hoje)
        if top10:
            ig["top_posts_30d"] = top10
        if ultimo:
            ig["ultimo_post"] = ultimo
        _set_if_key(ig, "posts_na_janela", na_janela)
        # SPA schema: "posts_30d"
        _set_if_key(ig, "posts_30d", na_janela)

        # Audience demografia (age+gender+cidade+pais dos SEGUIDORES)
        print(f"  [Instagram] {ig_id} — audience demografia (seguidores) + stories")
        aud = _fetch_ig_audience_demografia(ig_id, token)
        if aud is not None:
            ig["audience_demografia"] = aud
        # Stories ativas + insights
        stories = _fetch_ig_stories(ig_id, token)
        if stories is not None:
            ig["stories_insights"] = stories

    # ---------- Facebook Page ----------
    page_id = ids.get("facebook_page_id")
    if page_id:
        print(f"  [Facebook] page_id {page_id} — followers + posts 30d + organico 30d")
        fb = base.setdefault("facebook_page", {})
        info = _fetch_fb_page(page_id, token, hoje)
        if info.get("nome"):
            _set_if_key(fb, "nome", info["nome"])
        # FB Page core metrics: grava incondicionalmente (chaves criticas —
        # se nao existirem na base, cria; se existirem, atualiza).
        if "seguidores" in info:
            fb["seguidores"] = info["seguidores"]
            fb["followers"] = info["seguidores"]
        if "posts_30d" in info:
            fb["posts_30d"] = info["posts_30d"]
        fb["page_id"] = page_id
        fb["conectado"] = True

        # organico_30d + posts detalhados + serie diaria seguidores + reactions
        # (todos precisam de Page Access Token)
        page_token = _get_page_access_token(page_id, token)
        if page_token:
            org = _fetch_fb_organico_30d(page_id, page_token, hoje)
            if org is not None:
                fb["organico_30d"] = org

            print(f"  [Facebook] page_id {page_id} — posts detalhados 30d + serie diaria seguidores + reactions breakdown")
            posts_det = _fetch_fb_posts_detalhes(page_id, page_token, hoje)
            fb["posts_30d_detalhes"] = posts_det

            serie = _fetch_fb_serie_diaria_seguidores(page_id, page_token, hoje)
            if serie:
                fb["serie_diaria_30d"] = serie

            reactions = _fb_reactions_from_posts(posts_det)
            if reactions is not None:
                fb["reactions_by_type_30d"] = reactions

    # ---------- Janelas + fonte + gerado_em ----------
    base["janelas"] = _janelas_texto(hoje)
    base["gerado_em"] = now_iso
    base["fonte"] = (
        f"Meta Graph API v20.0 · refresh diario automatico · "
        f"ultimo manual/curado {gerado_anterior}"
    )
    return base


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

UNIDADES = {
    "escova": {"config_key": "escova", "path": os.path.join(ROOT, "data", "midias_sociais.json")},
    "spa":    {"config_key": "spa",    "path": os.path.join(ROOT, "data", "spa", "midias_sociais.json")},
}


def _load_base(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        print(f"  [WARN] base nao existe: {path} — criando dict vazio", file=sys.stderr)
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_base(path: str, data: dict[str, Any]) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def _diff_resumo(antes: dict[str, Any], depois: dict[str, Any], nome: str) -> str:
    """Diff curto pro dry-run."""
    linhas = [f"=== {nome} ==="]
    def num(d, *keys):
        cur = d
        for k in keys:
            if not isinstance(cur, dict):
                return None
            cur = cur.get(k)
        return cur

    campos = [
        ("gerado_em", ("gerado_em",)),
        ("meta_ads.7d.gasto", ("meta_ads", "por_periodo", "7d", "gasto")),
        ("meta_ads.7d.conversas_msg", ("meta_ads", "por_periodo", "7d", "conversas_msg")),
        ("meta_ads.30d.gasto", ("meta_ads", "por_periodo", "30d", "gasto")),
        ("meta_ads.30d.conversas_msg", ("meta_ads", "por_periodo", "30d", "conversas_msg")),
        ("instagram.followers", ("instagram", "followers")),
        ("instagram.posts_total", ("instagram", "posts_total")),
        ("facebook_page.seguidores", ("facebook_page", "seguidores")),
        ("facebook_page.posts_30d", ("facebook_page", "posts_30d")),
    ]
    for label, path in campos:
        a = num(antes, *path)
        d = num(depois, *path)
        if a != d:
            linhas.append(f"  {label}: {a!r} -> {d!r}")
    if len(linhas) == 1:
        linhas.append("  (sem mudancas nos campos-chave)")
    return "\n".join(linhas)


def main() -> int:
    ap = argparse.ArgumentParser(description="Refresh diario de midias_sociais.json via Meta Graph API")
    ap.add_argument("--unidade", choices=list(UNIDADES.keys()), help="Rodar so uma unidade")
    ap.add_argument("--dry-run", action="store_true", help="Imprime diff sem gravar")
    args = ap.parse_args()

    token = os.environ.get("META_ACCESS_TOKEN")
    if not token:
        print("ERRO: variavel de ambiente META_ACCESS_TOKEN nao definida", file=sys.stderr)
        return 2

    with open(CONFIG, encoding="utf-8") as f:
        cfg = json.load(f)

    alvo = [args.unidade] if args.unidade else list(UNIDADES.keys())
    hoje = _hoje_brt()
    print(f"[refresh_midias] hoje BRT = {hoje.isoformat()} · unidades = {alvo}")

    rc = 0
    for u in alvo:
        meta = UNIDADES[u]
        ids = cfg.get("unidades", {}).get(meta["config_key"], {}).get("midia_ids", {}) or {}
        if not ids.get("meta_ad_account_id"):
            print(f"[{u}] meta_ad_account_id null — pulando")
            continue

        print(f"\n[{u}] refresh iniciado")
        base = _load_base(meta["path"])
        antes = json.loads(json.dumps(base))  # snapshot pre-merge

        try:
            depois = _merge_unidade(base, ids, token, hoje)
        except Exception as e:
            print(f"[{u}] FALHA no merge: {e}", file=sys.stderr)
            rc = 1
            continue

        if args.dry_run:
            print(_diff_resumo(antes, depois, u))
        else:
            _write_base(meta["path"], depois)
            print(f"[{u}] gravado {meta['path']}")

    return rc


if __name__ == "__main__":
    sys.exit(main())
