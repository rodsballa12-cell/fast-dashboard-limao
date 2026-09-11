"""Descoberta de endpoints Trinks — testa nomes candidatos pra o relatorio
de comissoes que o BackOffice mostra. Rodrigo tirou print do relatorio e
constatou divergencias com /v1/transacoes (MIRIAN e Claudia sumidas,
totais nao batem). A hipotese e que o BackOffice puxa de um endpoint
que a documentacao publica nao lista.

Este script tenta uma lista de URLs candidatas com o TRINKS_ESTABELECIMENTO_ID
e TRINKS_API_KEY do env. Para cada URL:
  - GET com/sem parametros basicos (dataInicio/dataFim setembro 1-11)
  - Reporta status HTTP, tamanho da resposta, primeiras chaves do JSON

Endpoints candidatos:
- /v1/comissoes (report geral)
- /v1/relatorios/comissoes
- /v1/relatorios/pagamentos
- /v1/recebiveis
- /v1/pagamentos
- /v1/comandas
- /v1/comandas/pagamentos
- /v1/servicos/executados
- /v1/atendimentos
- /v1/lancamentos
- /v1/relatorios (index)
- /v1/relatorios/comissao-por-profissional
- /v1/relatorio/comissoes

Uso: gh workflow dispatch (via workflow_dispatch handler) ou local com
TRINKS_API_KEY e TRINKS_ESTABELECIMENTO_ID no env.
"""
import os, sys, json
from datetime import date

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

API_BASE = "https://api.trinks.com/v1"
KEY = os.environ.get("TRINKS_API_KEY")
EID = os.environ.get("TRINKS_ESTABELECIMENTO_ID")
if not (KEY and EID):
    print("ERRO: TRINKS_API_KEY e TRINKS_ESTABELECIMENTO_ID obrigatorios")
    sys.exit(1)

# Headers corretos (bate com scripts/trinks_common.py)
HEADERS = {
    "X-Api-Key": KEY,
    "estabelecimentoId": EID,
    "Accept": "application/json",
}

# Setembro 1-11 pra bater com o report que Rodrigo tirou print
INI = "2026-09-01"
FIM = "2026-09-11"

ENDPOINTS = [
    # Relatorios candidatos
    ("/relatorios", None),
    ("/relatorios", {"dataInicio": INI, "dataFim": FIM}),
    ("/relatorios/comissoes", {"dataInicio": INI, "dataFim": FIM}),
    ("/relatorios/comissao", {"dataInicio": INI, "dataFim": FIM}),
    ("/relatorios/pagamentos", {"dataInicio": INI, "dataFim": FIM}),
    ("/relatorios/comandas", {"dataInicio": INI, "dataFim": FIM}),
    ("/relatorio/comissoes", {"dataInicio": INI, "dataFim": FIM}),
    # Endpoints mais especificos
    ("/comissoes", {"dataInicio": INI, "dataFim": FIM}),
    ("/pagamentos", {"dataInicio": INI, "dataFim": FIM}),
    ("/pagamentos/comissoes", {"dataInicio": INI, "dataFim": FIM}),
    ("/recebiveis", {"dataInicio": INI, "dataFim": FIM}),
    ("/comandas", {"dataInicio": INI, "dataFim": FIM}),
    ("/comandas/pagamentos", {"dataInicio": INI, "dataFim": FIM}),
    ("/atendimentos", {"dataInicio": INI, "dataFim": FIM}),
    ("/servicos-executados", {"dataInicio": INI, "dataFim": FIM}),
    ("/servicos/executados", {"dataInicio": INI, "dataFim": FIM}),
    ("/lancamentos", {"dataInicio": INI, "dataFim": FIM}),
    ("/lancamentos-financeiros", {"dataInicio": INI, "dataFim": FIM}),
    # Comissoes com parametros alternativos (dataPagamento)
    ("/comissoes", {"dataPagamentoInicio": INI, "dataPagamentoFim": FIM}),
    ("/pagamentos", {"dataPagamentoInicio": INI, "dataPagamentoFim": FIM}),
    # Endpoints com nome PT
    ("/relatorio-comissoes", {"dataInicio": INI, "dataFim": FIM}),
    ("/faturamento", {"dataInicio": INI, "dataFim": FIM}),
    ("/faturamento/comissoes", {"dataInicio": INI, "dataFim": FIM}),
    ("/profissionais/producao", {"dataInicio": INI, "dataFim": FIM}),
    ("/profissionais/comissoes/lancamentos", {"dataInicio": INI, "dataFim": FIM}),
    ("/profissionais/comissoes/relatorio", {"dataInicio": INI, "dataFim": FIM}),
]

print(f"[discover] testando {len(ENDPOINTS)} endpoints · janela {INI}..{FIM}\n")

achados_uteis = []
for path, params in ENDPOINTS:
    url = f"{API_BASE}{path}"
    label = f"{path}?{'&'.join(f'{k}={v}' for k,v in (params or {}).items())}"[:80]
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        status = r.status_code
        if status == 200:
            try:
                body = r.json()
                # Tenta identificar shape
                if isinstance(body, dict):
                    keys = list(body.keys())[:6]
                    tot = body.get("totalRegistros") or body.get("totalRecords") or body.get("total") or len(body.get("data", []) or body.get("items", []) or [])
                    print(f"  ✓ 200 · {label}")
                    print(f"    keys: {keys} · total_items: {tot}")
                    if tot:
                        achados_uteis.append((path, params, tot, body))
                elif isinstance(body, list):
                    print(f"  ✓ 200 · {label} · lista {len(body)} items")
                    if body: achados_uteis.append((path, params, len(body), body))
            except Exception as e:
                print(f"  ? 200 · {label} · JSON invalido ({e})")
        elif status == 404:
            pass  # endpoint nao existe, silencioso
        elif status == 401 or status == 403:
            print(f"  ✗ {status} · {label} · sem permissao")
        elif status == 400:
            # bad request pode significar endpoint existe mas params errados
            try:
                msg = r.json().get("mensagem") or r.json().get("message") or r.text[:200]
            except Exception:
                msg = r.text[:200]
            print(f"  ~ 400 · {label} · {msg[:120]}")
        else:
            print(f"  ? {status} · {label}")
    except requests.RequestException as e:
        print(f"  ! erro · {label} · {type(e).__name__}")

print(f"\n[discover] {len(achados_uteis)} endpoints devolveram dado util")
if achados_uteis:
    print("\n=== AMOSTRA dos achados ===\n")
    for path, params, tot, body in achados_uteis[:3]:
        print(f"--- {path} · {tot} items ---")
        # Escreve o payload cru pra investigacao offline
        fname = "discovery_" + path.strip("/").replace("/", "_") + ".json"
        with open(fname, "w") as f:
            json.dump(body, f, indent=2, ensure_ascii=False, default=str)
        print(f"  salvo em: {fname}")
        # Amostra do primeiro item
        items = body if isinstance(body, list) else (body.get("data") or body.get("items") or body.get("results") or [])
        if items and isinstance(items[0], dict):
            print(f"  chaves item[0]: {list(items[0].keys())}")
            print(f"  amostra: {json.dumps(items[0], indent=2, ensure_ascii=False, default=str)[:500]}")
