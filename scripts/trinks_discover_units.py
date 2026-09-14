"""Descobre estabelecimentos acessiveis via API key Trinks.

Rodrigo passou a ter acesso Trinks a ambas as unidades (Escova + SPA)
sob a mesma API key. Este script chama /v1/estabelecimentos (ou variantes)
pra listar todos os estabelecimentoIds visiveis e devolve pro workflow log.

Uso: python scripts/trinks_discover_units.py

Env obrigatorio:
  TRINKS_API_KEY — mesma key ja usada em github_refresh.py
"""

import os
import sys
import json
import requests

API_KEY = os.environ.get("TRINKS_API_KEY")
if not API_KEY:
    print("ERRO: TRINKS_API_KEY nao definido")
    sys.exit(1)

BASE = "https://api.trinks.com/v1"
HEADERS = {"X-Api-Key": API_KEY, "Accept": "application/json",
           "User-Agent": "FAST-Dashboard-Limao/discover"}

# Rotas candidatas — Trinks nao documenta bem, tentar as mais provaveis.
ROTAS = [
    "/estabelecimentos",
    "/estabelecimento",
    "/config/estabelecimentos",
    "/me/estabelecimentos",
]

for r in ROTAS:
    url = BASE + r
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        print(f"\n[GET {r}] HTTP {resp.status_code}")
        if resp.status_code == 200:
            try:
                js = resp.json()
                print(json.dumps(js, indent=2, ensure_ascii=False)[:2000])
            except Exception:
                print(f"body (nao JSON): {resp.text[:500]}")
        elif resp.status_code == 404:
            print("  → 404 (rota nao existe)")
        else:
            print(f"  body: {resp.text[:300]}")
    except Exception as e:
        print(f"[GET {r}] excecao: {e}")

# Tambem tentar /v1/estabelecimento com header estabelecimentoId=<id_escova>
# — algumas APIs devolvem lista de estabs vinculados quando autenticado
print("\n[GET /estabelecimentos com header estabelecimentoId=276461]")
try:
    resp = requests.get(BASE + "/estabelecimentos",
                        headers={**HEADERS, "estabelecimentoId": "276461"},
                        timeout=30)
    print(f"  HTTP {resp.status_code}")
    if resp.status_code == 200:
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False)[:2000])
    else:
        print(f"  body: {resp.text[:300]}")
except Exception as e:
    print(f"  excecao: {e}")
