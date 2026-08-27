r"""Diag v3 · confirmar /v1/profissionais/comissoes vazio ou mal filtrado."""
import json
import os
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
            print(f"  keys: {sorted(data.keys()) if isinstance(data, dict) else '(lista)'}")
            if isinstance(data, dict):
                items = data.get("data") or []
                print(f"  totalRecords: {data.get('totalRecords')} · n items: {len(items)}")
                if items:
                    print(f"  1º item keys: {sorted(items[0].keys()) if isinstance(items[0], dict) else type(items[0]).__name__}")
                    print(f"  1º item: {json.dumps(items[0], ensure_ascii=False, default=str)[:500]}")
            elif isinstance(data, list):
                print(f"  lista · n={len(data)}")
                if data:
                    print(f"  1º item: {json.dumps(data[0], ensure_ascii=False, default=str)[:500]}")
        else:
            print(f"  body: {(r.text or '')[:200]}")
    except Exception as e:
        print(f"  exception: {type(e).__name__}: {e}")
    time.sleep(1.2)


# Primeiro: pegar 1 prof ativo do cadastro pra testar com ID real
print("[step 0] fetch profs pra pegar um ID real...")
r = requests.get(BASE + "/v1/profissionais", headers=HEADERS, params={"pageSize": 3}, timeout=30)
prof_id = None
if r.status_code == 200:
    for p in r.json().get("data", []):
        if p.get("id"):
            prof_id = p["id"]
            print(f"  prof ativo achado: id={prof_id} nome={p.get('nome')}")
            break
time.sleep(1)

# === TESTES DE COMISSÃO ===
probe("/v1/profissionais/comissoes", None, "T1 SEM filtros")
probe("/v1/profissionais/comissoes", {"pageSize": 20}, "T2 só pageSize=20")
probe("/v1/profissionais/comissoes", {"dataInicio": "2026-07-01", "dataFim": "2026-08-31"}, "T3 range amplo (jul+ago)")
if prof_id:
    probe(f"/v1/profissionais/{prof_id}/comissoes", None, f"T4 /profissionais/{prof_id}/comissoes")
    probe(f"/v1/profissionais/{prof_id}", None, f"T5 /profissionais/{prof_id} (detalhe)")

# Variantes que ainda não testei
probe("/v1/comissoes-agendamento", {"pageSize": 5}, "T6 /comissoes-agendamento")
probe("/v1/agendamentos/comissoes", None, "T7 /agendamentos/comissoes")
probe("/v1/servicos-profissionais", None, "T8 /servicos-profissionais")

# Talvez comissão esteja embutida no profissional detalhe
if prof_id:
    r = requests.get(BASE + f"/v1/profissionais", headers=HEADERS, params={"pageSize": 50}, timeout=30)
    if r.status_code == 200 and r.json().get("data"):
        first = r.json()["data"][0]
        print(f"\n=== T9 · Keys do profissional (do list) ===")
        print(f"  keys: {sorted(first.keys())}")
        print(f"  full: {json.dumps(first, ensure_ascii=False, default=str)[:500]}")

print("\n=== FIM diag v3 ===")
