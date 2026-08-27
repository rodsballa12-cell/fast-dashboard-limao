r"""Diagnóstico one-shot dos endpoints Trinks ainda não explorados.

Chamada 1x pra descobrir o que existe. Roda no GitHub Actions com
env vars TRINKS_API_KEY e TRINKS_ESTABELECIMENTO_ID.
"""
import json
import os
import sys
import time

import requests

BASE = "https://api.trinks.com"
HEADERS = {
    "X-Api-Key": os.environ["TRINKS_API_KEY"],
    "estabelecimentoId": os.environ["TRINKS_ESTABELECIMENTO_ID"],
    "Accept": "application/json",
    "User-Agent": "FAST-Dashboard-Limao/1.0-diag",
}

def probe(path, params=None, label=None):
    label = label or path
    print(f"\n=== {label} ===")
    print(f"GET {path} params={params or {}}")
    try:
        r = requests.get(BASE + path, headers=HEADERS, params=params or {}, timeout=30)
        print(f"  status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict):
                keys = sorted(data.keys())
                print(f"  keys: {keys}")
                if data.get("data"):
                    items = data["data"]
                    print(f"  n itens: {len(items)}")
                    if items:
                        print(f"  1º item keys: {sorted(items[0].keys()) if isinstance(items[0], dict) else type(items[0]).__name__}")
                        print(f"  1º item (200 chars): {json.dumps(items[0], ensure_ascii=False, default=str)[:200]}")
                elif "totalRecords" in data:
                    print(f"  totalRecords: {data.get('totalRecords')}")
            else:
                print(f"  type: {type(data).__name__} · sample: {str(data)[:150]}")
        else:
            print(f"  body: {(r.text or '')[:200]}")
    except Exception as e:
        print(f"  exception: {type(e).__name__}: {e}")
    time.sleep(1.2)  # throttle

# Endpoints a probar (7 requests)
probe("/v1/pacotes", {"pageSize": 5, "page": 1}, "1. Pacotes")
probe("/v1/comissoes", {"pageSize": 5, "page": 1, "dataInicio": "2026-08-01", "dataFim": "2026-08-31"}, "2. Comissões (ago)")
probe("/v1/produtos", {"pageSize": 5, "page": 1}, "4. Produtos (catálogo)")
probe("/v1/comandas", {"pageSize": 5, "page": 1}, "5a. Comandas")
probe("/v1/comandas-abertas", {"pageSize": 5, "page": 1}, "5b. Comandas abertas")
probe("/v1/despesas", {"pageSize": 5, "page": 1, "dataInicio": "2026-08-01", "dataFim": "2026-08-31"}, "7. Despesas (ago)")
probe("/v1/avaliacoes", {"pageSize": 5, "page": 1}, "9. Avaliações")
probe("/v1/servicos", {"pageSize": 5, "page": 1}, "BONUS. Serviços catálogo")

# Também: contar etiquetasAssociadas em transacoes já cacheadas seria via github_refresh main
print("\n=== FIM diag_endpoints ===")
