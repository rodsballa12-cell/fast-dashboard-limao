r"""Coletor Google Meu Negócio (Google Business Profile API).

Puxa perfil, avaliações e métricas de performance da ficha do Google.
Também publica posts e responde avaliações.

Env vars necessárias:
  GMN_CLIENT_ID       — OAuth client id (Google Cloud Console)
  GMN_CLIENT_SECRET   — OAuth client secret
  GMN_REFRESH_TOKEN   — refresh token com escopo business.manage
  GMN_LOCATION_ID     — opcional; se ausente, descobre a 1ª location da conta

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

TOKEN_URL = "https://oauth2.googleapis.com/token"
ACCOUNTS_API = "https://mybusinessaccountmanagement.googleapis.com/v1"
INFO_API = "https://mybusinessbusinessinformation.googleapis.com/v1"
PERF_API = "https://businessprofileperformance.googleapis.com/v1"
LEGACY_API = "https://mybusiness.googleapis.com/v4"  # avaliações e posts ainda vivem na v4

# Métricas diárias da ficha (Business Profile Performance API)
METRICAS = [
    "BUSINESS_IMPRESSIONS_DESKTOP_MAPS",
    "BUSINESS_IMPRESSIONS_DESKTOP_SEARCH",
    "BUSINESS_IMPRESSIONS_MOBILE_MAPS",
    "BUSINESS_IMPRESSIONS_MOBILE_SEARCH",
    "BUSINESS_DIRECTION_REQUESTS",
    "CALL_CLICKS",
    "WEBSITE_CLICKS",
    "BUSINESS_BOOKINGS",
]

ROTULOS = {
    "impressoes": "Impressões da ficha",
    "rotas": "Pedidos de rota",
    "ligacoes": "Cliques em ligar",
    "site": "Cliques no site",
    "agendamentos": "Agendamentos pelo Google",
}


class GMN:
    def __init__(self):
        self.client_id = env("GMN_CLIENT_ID")
        self.client_secret = env("GMN_CLIENT_SECRET")
        self.refresh_token = env("GMN_REFRESH_TOKEN")
        self.location_id = env("GMN_LOCATION_ID")
        self.account_id = env("GMN_ACCOUNT_ID")
        self.s = requests.Session()
        self._token = None

    # ---------- auth ----------
    def token(self) -> str:
        if self._token:
            return self._token
        r = self.s.post(
            TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=30,
        )
        if r.status_code != 200:
            raise RuntimeError(f"OAuth falhou ({r.status_code}): {r.text[:200]}")
        self._token = r.json()["access_token"]
        return self._token

    def get(self, url: str, params: dict | list | None = None) -> dict:
        r = self.s.get(
            url,
            headers={"Authorization": f"Bearer {self.token()}"},
            params=params,
            timeout=30,
        )
        if r.status_code == 404:
            return {}
        if r.status_code != 200:
            raise RuntimeError(f"GET {url.split('/')[-1]} → {r.status_code}: {r.text[:200]}")
        return r.json()

    def post(self, url: str, payload: dict) -> dict:
        r = self.s.post(
            url,
            headers={"Authorization": f"Bearer {self.token()}"},
            json=payload,
            timeout=30,
        )
        if r.status_code not in (200, 201):
            raise RuntimeError(f"POST {url.split('/')[-1]} → {r.status_code}: {r.text[:300]}")
        return r.json()

    def put(self, url: str, payload: dict) -> dict:
        r = self.s.put(
            url,
            headers={"Authorization": f"Bearer {self.token()}"},
            json=payload,
            timeout=30,
        )
        if r.status_code not in (200, 201):
            raise RuntimeError(f"PUT {url.split('/')[-1]} → {r.status_code}: {r.text[:300]}")
        return r.json()

    # ---------- descoberta ----------
    def resolver_location(self) -> tuple[str, str]:
        """Devolve (account_name, location_name) no formato da API."""
        account = f"accounts/{self.account_id}" if self.account_id else None
        if not account:
            contas = self.get(f"{ACCOUNTS_API}/accounts").get("accounts", [])
            if not contas:
                raise RuntimeError("Nenhuma conta GMN visível para este refresh token")
            account = contas[0]["name"]

        if self.location_id:
            return account, f"locations/{self.location_id}"

        resp = self.get(
            f"{INFO_API}/{account}/locations",
            params={"readMask": "name,title,storefrontAddress,phoneNumbers,websiteUri", "pageSize": 10},
        )
        locs = resp.get("locations", [])
        if not locs:
            raise RuntimeError(f"Nenhuma location em {account}")
        return account, locs[0]["name"]

    # ---------- coleta ----------
    def perfil(self, location: str) -> dict:
        d = self.get(
            f"{INFO_API}/{location}",
            params={"readMask": "name,title,storefrontAddress,phoneNumbers,websiteUri,metadata"},
        )
        end = d.get("storefrontAddress", {})
        return {
            "nome": d.get("title", ""),
            "endereco": ", ".join(end.get("addressLines", []) or []),
            "cidade": end.get("locality", ""),
            "telefone": (d.get("phoneNumbers", {}) or {}).get("primaryPhone", ""),
            "site": d.get("websiteUri", ""),
            "url_maps": (d.get("metadata", {}) or {}).get("mapsUri", ""),
            "url_avaliacao": (d.get("metadata", {}) or {}).get("newReviewUri", ""),
        }

    def insights(self, location: str, dias: int = 30) -> dict:
        fim = hoje()
        ini = fim - timedelta(days=dias)
        params = [
            ("dailyMetrics", m) for m in METRICAS
        ] + [
            ("dailyRange.start_date.year", ini.year),
            ("dailyRange.start_date.month", ini.month),
            ("dailyRange.start_date.day", ini.day),
            ("dailyRange.end_date.year", fim.year),
            ("dailyRange.end_date.month", fim.month),
            ("dailyRange.end_date.day", fim.day),
        ]
        d = self.get(f"{PERF_API}/{location}:fetchMultiDailyMetricsTimeSeries", params=params)

        totais = {}
        series = {}
        for bloco in d.get("multiDailyMetricTimeSeries", []):
            for item in bloco.get("dailyMetricTimeSeries", []):
                metrica = item.get("dailyMetric", "")
                pontos = (item.get("timeSeries", {}) or {}).get("datedValues", []) or []
                valores = []
                for p in pontos:
                    dt = p.get("date", {})
                    valores.append(
                        {
                            "data": f"{dt.get('year')}-{dt.get('month', 1):02d}-{dt.get('day', 1):02d}",
                            "v": int(p.get("value", 0) or 0),
                        }
                    )
                totais[metrica] = sum(v["v"] for v in valores)
                series[metrica] = valores

        impressoes = sum(v for k, v in totais.items() if k.startswith("BUSINESS_IMPRESSIONS"))
        return {
            "periodo_dias": dias,
            "impressoes": impressoes,
            "rotas": totais.get("BUSINESS_DIRECTION_REQUESTS", 0),
            "ligacoes": totais.get("CALL_CLICKS", 0),
            "site": totais.get("WEBSITE_CLICKS", 0),
            "agendamentos": totais.get("BUSINESS_BOOKINGS", 0),
            "series": series,
            "rotulos": ROTULOS,
        }

    def avaliacoes(self, account: str, location: str, limite: int = 50) -> dict:
        loc_id = location.split("/")[-1]
        d = self.get(
            f"{LEGACY_API}/{account}/locations/{loc_id}/reviews",
            params={"pageSize": min(limite, 50), "orderBy": "updateTime desc"},
        )
        estrelas = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5}
        itens = []
        for r in d.get("reviews", []) or []:
            resposta = r.get("reviewReply") or {}
            itens.append(
                {
                    "id": r.get("reviewId", ""),
                    "autor": (r.get("reviewer", {}) or {}).get("displayName", "Cliente"),
                    "nota": estrelas.get(r.get("starRating", ""), 0),
                    "texto": (r.get("comment") or "").strip(),
                    "quando": r.get("createTime", ""),
                    "respondida": bool(resposta.get("comment")),
                    "resposta": (resposta.get("comment") or "").strip(),
                }
            )
        return {
            "itens": itens,
            "total": d.get("totalReviewCount", len(itens)),
            "nota_media": round(float(d.get("averageRating", 0) or 0), 2),
            "sem_resposta": sum(1 for i in itens if not i["respondida"]),
        }

    # ---------- ações ----------
    def responder_avaliacao(self, account: str, location: str, review_id: str, texto: str) -> dict:
        loc_id = location.split("/")[-1]
        return self.put(
            f"{LEGACY_API}/{account}/locations/{loc_id}/reviews/{review_id}/reply",
            {"comment": texto},
        )

    def publicar_post(self, account: str, location: str, texto: str, url_img: str = "",
                      cta_url: str = "") -> dict:
        loc_id = location.split("/")[-1]
        payload: dict = {
            "languageCode": "pt-BR",
            "summary": texto,
            "topicType": "STANDARD",
        }
        if url_img:
            payload["media"] = [{"mediaFormat": "PHOTO", "sourceUrl": url_img}]
        if cta_url:
            payload["callToAction"] = {"actionType": "BOOK", "url": cta_url}
        return self.post(f"{LEGACY_API}/{account}/locations/{loc_id}/localPosts", payload)


def coletar(dados: dict) -> dict:
    """Preenche dados['gmn']. Degrada com elegância se faltar credencial."""
    if not tem_credenciais("GMN_CLIENT_ID", "GMN_CLIENT_SECRET", "GMN_REFRESH_TOKEN"):
        dados["gmn"]["conectado"] = False
        dados["gmn"]["motivo"] = "Credenciais GMN não configuradas (ver docs/MARKETING_SETUP.md)"
        return dados

    g = GMN()
    try:
        account, location = g.resolver_location()
        aval = g.avaliacoes(account, location)
        dados["gmn"] = {
            "conectado": True,
            "account": account,
            "location": location,
            "perfil": g.perfil(location),
            "insights": g.insights(location),
            "avaliacoes": aval["itens"],
            "resumo_avaliacoes": {
                "total": aval["total"],
                "nota_media": aval["nota_media"],
                "sem_resposta": aval["sem_resposta"],
            },
            "posts": dados["gmn"].get("posts", []),
        }
    except (requests.RequestException, RuntimeError, KeyError) as e:
        dados["gmn"]["conectado"] = False
        dados["gmn"]["motivo"] = str(e)[:200]
        registrar_erro(dados, "gmn", e)
    return dados


def main() -> int:
    dados = carregar()
    coletar(dados)
    salvar(dados)
    g = dados["gmn"]
    if g.get("conectado"):
        r = g.get("resumo_avaliacoes", {})
        print(f"GMN OK · nota {r.get('nota_media')} · {r.get('total')} avaliações "
              f"· {r.get('sem_resposta')} sem resposta")
    else:
        print(f"GMN não conectado: {g.get('motivo')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
