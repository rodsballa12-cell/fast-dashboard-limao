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

# === PROBE 2: parametros de filtro que podem esconder inativos/pendentes ===
print("\n=== PROBES ADICIONAIS ===")
for params in [{"pageSize": 200}, {"ativo": "false"}, {"ativo": "todos"},
               {"todos": "true"}, {"incluir_inativos": "true"}]:
    label = "&".join(f"{k}={v}" for k,v in params.items())
    try:
        resp = requests.get(BASE + "/estabelecimentos", headers=HEADERS,
                            params=params, timeout=30)
        js = resp.json() if resp.status_code == 200 else {}
        n = js.get("totalRecords", "?")
        ids = [str(x.get("id")) for x in (js.get("data") or [])]
        print(f"  ?{label}: HTTP {resp.status_code} · {n} registros · ids={ids}")
    except Exception as e:
        print(f"  ?{label}: {e}")

# === PROBE 3: acessar SPA por ID chutado ===
# Se a mesma API key acessa a SPA, GET /v1/agendamentos com header
# estabelecimentoId=<outro_id> retorna dado ou 401. Se retornar 200 com
# dado ou vazio, a key funciona; se 401/403, precisa key propria.
# Chutes: IDs proximos (Trinks costuma dar IDs sequenciais)
print("\n=== TESTE ACESSO SPA POR HEADER ===")
# Buscar IDs proximos a 276461 (Escova) — franquia geralmente sequencial
candidatos = [276460, 276462, 276463, 276464, 276465, 276466, 276467, 276468,
              280000, 285000, 290000, 300000, 350000, 400000]
for cid in candidatos:
    try:
        # Tenta GET /v1/config (endpoint leve) com esse estabelecimentoId
        resp = requests.get(BASE + "/estabelecimentos/" + str(cid),
                            headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            js = resp.json()
            nome = ""
            if isinstance(js, dict):
                nome = js.get("nome") or (js.get("data") or {}).get("nome", "")
            print(f"  ID {cid}: HTTP 200 · nome={nome!r}")
        elif resp.status_code in (401, 403):
            print(f"  ID {cid}: HTTP {resp.status_code} (denied)")
        # 404 = ID nao existe · silencia
    except Exception:
        pass

print("\n[fim] Se nada apareceu alem de 276461, a API key nao tem acesso a SPA.")
