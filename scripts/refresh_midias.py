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
    """Devolve (top_posts_30d, ultimo_post, posts_na_janela)."""
    inicio, _fim = _janela("last_30d", hoje)
    try:
        resp = _graph_get(
            f"/{ig_user_id}/media",
            {
                "fields": "id,media_type,permalink,caption,timestamp,insights.metric(reach)",
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

    # posts na janela + top 10 by reach
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
        # extrair reach de insights
        reach = 0
        insights = (p.get("insights") or {}).get("data") or []
        for m in insights:
            if m.get("name") == "reach":
                for v in m.get("values", []) or []:
                    if isinstance(v.get("value"), (int, float)):
                        reach = int(v["value"])
        cap = (p.get("caption") or "").strip().replace("\n", " ")
        na_janela.append({
            "data": ts,
            "tipo": p.get("media_type"),
            "reach": reach,
            "url": p.get("permalink"),
            "caption_curta": cap[:80],
        })

    top10 = sorted(na_janela, key=lambda x: x["reach"], reverse=True)[:10]
    return top10, ultimo, len(na_janela)


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

        # Media / top posts
        top10, ultimo, na_janela = _fetch_ig_media(ig_id, token, hoje)
        if top10:
            _set_if_key(ig, "top_posts_30d", top10)
        if ultimo:
            _set_if_key(ig, "ultimo_post", ultimo)
        _set_if_key(ig, "posts_na_janela", na_janela)
        # SPA schema: "posts_30d"
        _set_if_key(ig, "posts_30d", na_janela)

    # ---------- Facebook Page ----------
    page_id = ids.get("facebook_page_id")
    if page_id:
        print(f"  [Facebook] page_id {page_id} — followers + posts 30d")
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
