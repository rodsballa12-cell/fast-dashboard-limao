r"""Cliente HTTP para a API Trinks.

Cuida de:
- Carregar credenciais de %USERPROFILE%\.trinks\.env
- Rate limit (60 req/min) com pausa automatica
- Paginacao (pageSize=50 padrao da API)
- Monitoramento da cota mensal via /v1/consumo
- Retentativa em 429/5xx
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Iterator

import requests
from dotenv import load_dotenv

BASE_URL = "https://api.trinks.com"
DEFAULT_PAGE_SIZE = 50
MIN_INTERVAL_SEC = 1.05  # ~57 req/min, folga sobre o limite de 60/min


class TrinksClient:
    def __init__(self) -> None:
        # 1) tenta variáveis de ambiente diretas (GitHub Actions, Docker etc.)
        api_key = os.getenv("TRINKS_API_KEY")
        eid = os.getenv("TRINKS_ESTABELECIMENTO_ID")
        # 2) fallback: .env em %USERPROFILE%/.trinks/ (setup local Windows)
        if (not api_key or not eid) and "USERPROFILE" in os.environ:
            env_path = Path(os.environ["USERPROFILE"]) / ".trinks" / ".env"
            if env_path.exists():
                load_dotenv(env_path)
                api_key = api_key or os.getenv("TRINKS_API_KEY")
                eid = eid or os.getenv("TRINKS_ESTABELECIMENTO_ID")
        if not api_key or not eid:
            raise ValueError("TRINKS_API_KEY e TRINKS_ESTABELECIMENTO_ID obrigatórios (via env ou ~/.trinks/.env)")
        self.headers = {
            "X-Api-Key": api_key,
            "estabelecimentoId": eid,
            "Accept": "application/json",
        }
        self._last_call = 0.0
        self.session = requests.Session()

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_call
        if elapsed < MIN_INTERVAL_SEC:
            time.sleep(MIN_INTERVAL_SEC - elapsed)
        self._last_call = time.time()

    def get(self, path: str, params: dict[str, Any] | None = None, retries: int = 3) -> dict:
        url = f"{BASE_URL}{path}"
        for attempt in range(retries):
            self._throttle()
            r = self.session.get(url, headers=self.headers, params=params, timeout=30)
            if r.status_code == 429:
                wait = 15 * (attempt + 1)
                print(f"  [429] rate limit — aguardando {wait}s")
                time.sleep(wait)
                continue
            if 500 <= r.status_code < 600:
                wait = 5 * (attempt + 1)
                print(f"  [{r.status_code}] servidor — aguardando {wait}s")
                time.sleep(wait)
                continue
            if r.status_code == 404:
                return {"data": [], "totalRecords": 0, "totalPages": 0}
            r.raise_for_status()
            return r.json()
        raise RuntimeError(f"Falhou apos {retries} tentativas: GET {url}")

    def paginate(self, path: str, params: dict[str, Any] | None = None) -> Iterator[dict]:
        """Itera todas as paginas de um endpoint que retorna {data, page, totalPages}."""
        params = dict(params or {})
        params.setdefault("pageSize", DEFAULT_PAGE_SIZE)
        page = 1
        while True:
            params["page"] = page
            payload = self.get(path, params)
            data = payload.get("data", [])
            if not data:
                return
            for item in data:
                yield item
            total_pages = payload.get("totalPages", 1) or 1
            if page >= total_pages:
                return
            page += 1

    def consumo(self) -> dict:
        return self.get("/v1/consumo")
