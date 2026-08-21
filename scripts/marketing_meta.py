r"""Coletor Meta — Instagram Business + Página do Facebook (Graph API).

Puxa seguidores, alcance, engajamento e as publicações recentes.
Também publica no Instagram (imagem + legenda).

Env vars necessárias:
  META_ACCESS_TOKEN   — token de longa duração da Página (nunca o de usuário curto)
  META_IG_USER_ID     — id da conta Instagram Business
  META_PAGE_ID        — id da Página do Facebook (opcional)
  META_API_VERSION    — opcional; default v21.0. Se a Graph API responder
                        "Unsupported get request" por versão expirada, suba aqui.

Sem credenciais o coletor não falha: marca conectado=false e segue.
Setup completo: docs/MARKETING_SETUP.md
"""
from __future__ import annotations

import sys
from datetime import timedelta

import requests

from marketing_common import (
    carregar,
    env,
    hoje,
    registrar_erro,
    salvar,
    tem_credenciais,
)

API_VERSION = env("META_API_VERSION", "v21.0")
BASE = f"https://graph.facebook.com/{API_VERSION}"


class Meta:
    def __init__(self):
        self.token = env("META_ACCESS_TOKEN")
        self.ig_id = env("META_IG_USER_ID")
        self.page_id = env("META_PAGE_ID")
        self.s = requests.Session()

    def get(self, path: str, params: dict | None = None) -> dict:
        p = dict(params or {})
        p["access_token"] = self.token
        r = self.s.get(f"{BASE}/{path.lstrip('/')}", params=p, timeout=30)
        if r.status_code != 200:
            erro = (r.json().get("error", {}) if "json" in r.headers.get("content-type", "") else {})
            msg = erro.get("message") or r.text[:200]
            raise RuntimeError(f"Graph {path} → {r.status_code}: {msg}")
        return r.json()

    def post(self, path: str, params: dict) -> dict:
        p = dict(params)
        p["access_token"] = self.token
        r = self.s.post(f"{BASE}/{path.lstrip('/')}", data=p, timeout=60)
        if r.status_code != 200:
            raise RuntimeError(f"Graph POST {path} → {r.status_code}: {r.text[:300]}")
        return r.json()

    # ---------- instagram ----------
    def ig_perfil(self) -> dict:
        d = self.get(
            self.ig_id,
            {"fields": "username,name,followers_count,follows_count,media_count,profile_picture_url"},
        )
        return {
            "usuario": d.get("username", ""),
            "nome": d.get("name", ""),
            "seguidores": d.get("followers_count", 0),
            "seguindo": d.get("follows_count", 0),
            "publicacoes": d.get("media_count", 0),
            "foto": d.get("profile_picture_url", ""),
        }

    def ig_insights(self, dias: int = 28) -> dict:
        """Alcance e engajamento. Cada métrica é tolerante a falha individual."""
        fim = hoje()
        ini = fim - timedelta(days=dias)
        janela = {"since": ini.isoformat(), "until": fim.isoformat(), "period": "day"}
        out = {"periodo_dias": dias, "series": {}}

        # métricas de série temporal
        try:
            d = self.get(f"{self.ig_id}/insights", {**janela, "metric": "reach"})
            for m in d.get("data", []):
                serie = [
                    {"data": (v.get("end_time") or "")[:10], "v": int(v.get("value", 0) or 0)}
                    for v in m.get("values", [])
                ]
                out["series"][m["name"]] = serie
                out[m["name"]] = sum(p["v"] for p in serie)
        except (requests.RequestException, RuntimeError) as e:
            out["aviso_reach"] = str(e)[:160]

        # métricas de total agregado (exigem metric_type=total_value)
        try:
            d = self.get(
                f"{self.ig_id}/insights",
                {**janela, "metric": "accounts_engaged,total_interactions,profile_views",
                 "metric_type": "total_value"},
            )
            for m in d.get("data", []):
                out[m["name"]] = int((m.get("total_value", {}) or {}).get("value", 0) or 0)
        except (requests.RequestException, RuntimeError) as e:
            out["aviso_engajamento"] = str(e)[:160]

        return out

    def ig_publicacoes(self, limite: int = 12) -> list[dict]:
        d = self.get(
            f"{self.ig_id}/media",
            {
                "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,"
                          "like_count,comments_count",
                "limit": limite,
            },
        )
        itens = []
        for m in d.get("data", []):
            itens.append(
                {
                    "id": m.get("id"),
                    "canal": "instagram",
                    "tipo": (m.get("media_type") or "").lower(),
                    "legenda": (m.get("caption") or "")[:400],
                    "url": m.get("permalink", ""),
                    "midia": m.get("thumbnail_url") or m.get("media_url", ""),
                    "quando": m.get("timestamp", ""),
                    "curtidas": m.get("like_count", 0),
                    "comentarios": m.get("comments_count", 0),
                }
            )
        return itens

    def ig_publicar(self, legenda: str, url_img: str) -> dict:
        """Publicação em 2 etapas: cria o container, depois publica."""
        cont = self.post(f"{self.ig_id}/media", {"image_url": url_img, "caption": legenda})
        creation_id = cont.get("id")
        if not creation_id:
            raise RuntimeError(f"Container não criado: {cont}")
        return self.post(f"{self.ig_id}/media_publish", {"creation_id": creation_id})

    # ---------- facebook ----------
    def fb_perfil(self) -> dict:
        d = self.get(self.page_id, {"fields": "name,fan_count,followers_count,link"})
        return {
            "nome": d.get("name", ""),
            "curtidas": d.get("fan_count", 0),
            "seguidores": d.get("followers_count", 0),
            "url": d.get("link", ""),
        }

    def fb_insights(self, dias: int = 28) -> dict:
        fim = hoje()
        ini = fim - timedelta(days=dias)
        d = self.get(
            f"{self.page_id}/insights",
            {
                "metric": "page_impressions,page_post_engagements",
                "period": "day",
                "since": ini.isoformat(),
                "until": fim.isoformat(),
            },
        )
        out = {"periodo_dias": dias}
        for m in d.get("data", []):
            out[m["name"]] = sum(int(v.get("value", 0) or 0) for v in m.get("values", []))
        return out

    def fb_publicar(self, texto: str, link: str = "") -> dict:
        params = {"message": texto}
        if link:
            params["link"] = link
        return self.post(f"{self.page_id}/feed", params)


def coletar(dados: dict) -> dict:
    """Preenche dados['meta']. Instagram e Facebook falham de forma independente."""
    if not tem_credenciais("META_ACCESS_TOKEN", "META_IG_USER_ID"):
        dados["meta"]["conectado"] = False
        dados["meta"]["motivo"] = "Credenciais Meta não configuradas (ver docs/MARKETING_SETUP.md)"
        return dados

    m = Meta()
    bloco = {"conectado": False, "instagram": {}, "facebook": {}, "publicacoes": []}
    try:
        bloco["instagram"] = {**m.ig_perfil(), "insights": m.ig_insights()}
        bloco["publicacoes"] = m.ig_publicacoes()
        bloco["conectado"] = True
    except (requests.RequestException, RuntimeError, KeyError) as e:
        bloco["motivo"] = str(e)[:200]
        registrar_erro(dados, "meta/instagram", e)

    if m.page_id:
        try:
            bloco["facebook"] = {**m.fb_perfil(), "insights": m.fb_insights()}
        except (requests.RequestException, RuntimeError, KeyError) as e:
            bloco["facebook"] = {"motivo": str(e)[:200]}
            registrar_erro(dados, "meta/facebook", e)

    dados["meta"] = bloco
    return dados


def main() -> int:
    dados = carregar()
    coletar(dados)
    salvar(dados)
    mt = dados["meta"]
    if mt.get("conectado"):
        ig = mt["instagram"]
        print(f"Meta OK · @{ig.get('usuario')} · {ig.get('seguidores')} seguidores "
              f"· {len(mt.get('publicacoes', []))} posts recentes")
    else:
        print(f"Meta não conectado: {mt.get('motivo')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
