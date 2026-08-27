r"""Diag v2 · foco em comissões + endpoints alternativos.

Testa múltiplas variações de nomes que Trinks pode usar.
Rodar com env vars TRINKS_API_KEY e TRINKS_ESTABELECIMENTO_ID.
"""
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
            if isinstance(data, dict):
                keys = sorted(data.keys())
                print(f"  keys: {keys}")
                if data.get("data"):
                    items = data["data"]
                    print(f"  n itens: {len(items)}")
                    if items:
                        it = items[0]
                        if isinstance(it, dict):
                            print(f"  1º item keys: {sorted(it.keys())}")
                            print(f"  1º item: {json.dumps(it, ensure_ascii=False, default=str)[:400]}")
                        else:
                            print(f"  1º item: {str(it)[:200]}")
                elif "totalRecords" in data:
                    print(f"  totalRecords: {data.get('totalRecords')}")
                else:
                    print(f"  payload direto: {json.dumps(data, ensure_ascii=False, default=str)[:300]}")
            elif isinstance(data, list):
                print(f"  lista · n itens: {len(data)}")
                if data:
                    print(f"  1º item: {json.dumps(data[0], ensure_ascii=False, default=str)[:400]}")
            else:
                print(f"  type: {type(data).__name__} · sample: {str(data)[:200]}")
        elif r.status_code == 400:
            print(f"  400 (bad request · endpoint existe): {(r.text or '')[:200]}")
        elif r.status_code == 401:
            print(f"  401 (unauthorized · endpoint existe): {(r.text or '')[:200]}")
        elif r.status_code == 403:
            print(f"  403 (forbidden · endpoint existe mas sem permissão): {(r.text or '')[:200]}")
        else:
            print(f"  body: {(r.text or '')[:150]}")
    except Exception as e:
        print(f"  exception: {type(e).__name__}: {e}")
    time.sleep(1.2)


# === COMISSÕES · múltiplas variantes ===
probe("/v1/comissao", {"pageSize": 5}, "COM.1 /comissao (singular)")
probe("/v1/comissoes-profissionais", {"pageSize": 5}, "COM.2 /comissoes-profissionais")
probe("/v1/relatorios/comissoes", {"dataInicio": "2026-08-01", "dataFim": "2026-08-31"}, "COM.3 /relatorios/comissoes")
probe("/v1/relatorios/comissao", {"dataInicio": "2026-08-01", "dataFim": "2026-08-31"}, "COM.4 /relatorios/comissao")
probe("/v1/relatorio/comissoes", {"dataInicio": "2026-08-01", "dataFim": "2026-08-31"}, "COM.5 /relatorio/comissoes")
probe("/v1/comissionamento", {"pageSize": 5}, "COM.6 /comissionamento")
probe("/v1/comissionamentos", {"pageSize": 5}, "COM.7 /comissionamentos")
probe("/v1/profissional/comissoes", {"pageSize": 5, "dataInicio": "2026-08-01", "dataFim": "2026-08-31"}, "COM.8 /profissional/comissoes")
probe("/v1/profissionais/comissoes", {"pageSize": 5, "dataInicio": "2026-08-01", "dataFim": "2026-08-31"}, "COM.9 /profissionais/comissoes")

# Um serviço específico — ver se traz comissão embutida
probe("/v1/servicos/15450779", None, "COM.10 /servicos/{id} (detalhe)")
# Um profissional específico
probe("/v1/profissionais/49392", None, "COM.11 /profissionais/{id} (detalhe)")

# === FINANCEIRO · variantes ===
probe("/v1/financeiro", {"pageSize": 5}, "FIN.1 /financeiro")
probe("/v1/plano-de-contas", {"pageSize": 5}, "FIN.2 /plano-de-contas")
probe("/v1/gastos", {"pageSize": 5, "dataInicio": "2026-08-01", "dataFim": "2026-08-31"}, "FIN.3 /gastos")
probe("/v1/notas-fiscais", {"pageSize": 5}, "FIN.4 /notas-fiscais")
probe("/v1/relatorios/vendas", {"dataInicio": "2026-08-01", "dataFim": "2026-08-31"}, "FIN.5 /relatorios/vendas")
probe("/v1/relatorios/financeiro", {"dataInicio": "2026-08-01", "dataFim": "2026-08-31"}, "FIN.6 /relatorios/financeiro")

# === OUTROS ===
probe("/v1/carteira", {"pageSize": 5}, "OUT.1 /carteira")
probe("/v1/wallet", {"pageSize": 5}, "OUT.2 /wallet")
probe("/v1/anamneses", {"pageSize": 5}, "OUT.3 /anamneses")
probe("/v1/orcamentos", {"pageSize": 5}, "OUT.4 /orcamentos")
probe("/v1/agendamentos-online", {"pageSize": 5}, "OUT.5 /agendamentos-online")

# === UM AGENDAMENTO ESPECÍFICO — ver se traz comissão embutida ===
# ID do primeiro agendamento (vai variar, mas testa se o endpoint /{id} existe)
probe("/v1/agendamentos/1", None, "AGEND.1 /agendamentos/{id} (id fake)")

print("\n=== FIM diag_endpoints v2 ===")
