"""Discovery Trinks v2 — throttled, focado em /profissionais/producao
que retornou 200 na primeira rodada (mas totalRecords=0 no default).
Testa varias combinacoes de parametros pra descobrir schema real.
"""
import os, sys, json, time

try:
    import requests
except ImportError:
    print("pip install requests"); sys.exit(1)

API_BASE = "https://api.trinks.com/v1"
KEY = os.environ.get("TRINKS_API_KEY")
EID = os.environ.get("TRINKS_ESTABELECIMENTO_ID")
if not (KEY and EID):
    print("ERRO: TRINKS_API_KEY e TRINKS_ESTABELECIMENTO_ID obrigatorios"); sys.exit(1)

HEADERS = {"X-Api-Key": KEY, "estabelecimentoId": EID, "Accept": "application/json"}
INI = "2026-09-01"; FIM = "2026-09-11"

def get(path, params=None):
    time.sleep(2.5)  # throttle: <30 req/min
    url = f"{API_BASE}{path}"
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        return r.status_code, r
    except Exception as e:
        return None, e

# Testes focados no /profissionais/producao
TESTS = [
    # variacoes de nome de parametro
    ("/profissionais/producao", {"dataInicio": INI, "dataFim": FIM}),
    ("/profissionais/producao", {"dataInicio": INI, "dataFim": FIM, "pageSize": 100}),
    ("/profissionais/producao", {"dataInicio": INI, "dataFim": FIM, "tipo": "PAGAMENTO"}),
    ("/profissionais/producao", {"dataInicio": INI, "dataFim": FIM, "tipoData": "pagamento"}),
    ("/profissionais/producao", {"dataInicio": INI, "dataFim": FIM, "tipoData": "PAGAMENTO"}),
    ("/profissionais/producao", {"dataPagamentoInicio": INI, "dataPagamentoFim": FIM}),
    ("/profissionais/producao", {"dataPagamentoInicial": INI, "dataPagamentoFinal": FIM}),
    ("/profissionais/producao", {"pageSize": 100}),  # sem data pra ver default
    ("/profissionais/producao", None),  # tudo default
    # variantes de nome
    ("/profissionais/producoes", {"dataInicio": INI, "dataFim": FIM}),
    ("/profissional/producao", {"dataInicio": INI, "dataFim": FIM}),
    ("/producao", {"dataInicio": INI, "dataFim": FIM}),
    ("/relatorios/producao", {"dataInicio": INI, "dataFim": FIM}),
    # tenta com id do estabelecimento como query
    ("/profissionais/producao", {"dataInicio": INI, "dataFim": FIM, "estabelecimentoId": EID}),
    # comandas throttled
    ("/comandas", {"dataInicio": INI, "dataFim": FIM}),
    ("/comandas", {"dataInicial": INI, "dataFinal": FIM}),
    ("/comissoes", {"dataInicio": INI, "dataFim": FIM}),
    ("/comissoes", {"dataInicial": INI, "dataFinal": FIM}),
    ("/pagamentos", {"dataInicio": INI, "dataFim": FIM}),
    ("/recebiveis", {"dataInicio": INI, "dataFim": FIM}),
]

print(f"[discover-v2] testando {len(TESTS)} chamadas (throttled 2.5s)\n")

for path, params in TESTS:
    label = f"{path}?{'&'.join(f'{k}={v}' for k,v in (params or {}).items())}"[:110]
    status, r = get(path, params)
    if status is None:
        print(f"  ! erro · {label}"); continue
    if status == 404:
        continue
    if status == 401 or status == 403:
        print(f"  ✗ {status} · {label}")
    elif status == 400:
        try: msg = r.json().get("mensagem") or r.json().get("message") or r.text[:150]
        except: msg = r.text[:150]
        print(f"  ~ 400 · {label} · {msg[:150]}")
    elif status == 200:
        try:
            body = r.json()
            if isinstance(body, dict):
                keys = list(body.keys())[:8]
                tot = body.get("totalRegistros") or body.get("totalRecords") or body.get("total") or len(body.get("data", []) or [])
                items = body.get("data") or body.get("items") or body.get("results") or []
                print(f"  ✓ 200 · {label}")
                print(f"    keys={keys} · total={tot} · items={len(items) if isinstance(items,list) else '?'}")
                if items and isinstance(items, list) and items:
                    it0 = items[0]
                    if isinstance(it0, dict):
                        print(f"    chaves item[0]: {list(it0.keys())}")
                        print(f"    amostra: {json.dumps(it0, indent=2, ensure_ascii=False, default=str)[:400]}")
                    # Grava payload se tem items uteis
                    fname = "discovery_" + path.strip("/").replace("/", "_") + "_" + "_".join(f"{k}-{v}" for k,v in (params or {}).items())[:60] + ".json"
                    fname = fname.replace(" ", "_")[:180]
                    with open(fname, "w") as f:
                        json.dump(body, f, indent=2, ensure_ascii=False, default=str)
                    print(f"    salvo: {fname}")
            elif isinstance(body, list):
                print(f"  ✓ 200 · {label} · lista len={len(body)}")
                if body:
                    print(f"    amostra: {json.dumps(body[0], indent=2, ensure_ascii=False, default=str)[:400]}")
        except Exception as e:
            print(f"  ? 200 · {label} · JSON invalido ({e})")
    elif status == 429:
        print(f"  ⏸ 429 rate limit · {label} — aguardando 30s")
        time.sleep(30)
    else:
        print(f"  ? {status} · {label} · {r.text[:150]}")

print(f"\n[discover-v2] fim")
