# -*- coding: utf-8 -*-
"""Probe: descobre qual endpoint Trinks retorna as comissões por serviço/profissional.

Faz requests HTTP diretas pra ver o status code REAL (o TrinksClient
esconde 404 devolvendo stub vazio, mascarando "não achou" como "0 regras").
"""
import json, os, sys, traceback
import requests

API_KEY = os.getenv("TRINKS_API_KEY", "").strip()
EID = os.getenv("TRINKS_ESTABELECIMENTO_ID", "").strip()
BASE = "https://api.trinks.com"
HEADERS = {
    "X-Api-Key": API_KEY,
    "estabelecimentoId": EID,
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def try_get(path, params=None, label=None):
    label = label or path
    url = BASE + path
    try:
        r = requests.get(url, headers=HEADERS, params=params or {}, timeout=15)
        status = r.status_code
        body = None
        try:
            body = r.json()
        except Exception:
            body = r.text[:400]
        print(f"\n[{status}] GET {path} params={params or {}}")
        # Sumariza body
        if isinstance(body, dict):
            keys = list(body.keys())
            print(f"  keys: {keys[:20]}")
            data = body.get("data")
            if isinstance(data, list):
                print(f"  data: {len(data)} items · totalRecords={body.get('totalRecords','?')}")
                if data:
                    print(f"  amostra[0]:", json.dumps(data[0], ensure_ascii=False, indent=2)[:800])
            else:
                snippet = json.dumps(body, ensure_ascii=False, indent=2)
                print(f"  body:", snippet[:800])
        else:
            print(f"  text: {body[:400]}")
        return status, body
    except Exception as e:
        print(f"\n[ERR] GET {path}: {type(e).__name__}: {str(e)[:200]}")
        return None, None


def main():
    if not API_KEY or not EID:
        print("❌ TRINKS_API_KEY / TRINKS_ESTABELECIMENTO_ID ausentes")
        sys.exit(1)
    print(f"Estabelecimento: {EID[:6]}...")

    print("\n" + "=" * 70)
    print("PROBE COMPLETO: comissões Trinks")
    print("=" * 70)

    # 1) Baseline
    try_get("/v1/profissionais/comissoes", {"pageSize": 200})

    # 2) Serviços — pega ID de amostra
    _, sv = try_get("/v1/servicos", {"pageSize": 3})
    servs = (sv or {}).get("data", []) if isinstance(sv, dict) else []
    sid = servs[0].get("id") if servs else None

    # 3) Profissionais
    _, pv = try_get("/v1/profissionais", {"pageSize": 3})
    profs = (pv or {}).get("data", []) if isinstance(pv, dict) else []
    pid = profs[0].get("id") if profs else None
    print(f"\n[info] IDs pra probing: servico={sid} profissional={pid}")

    # 4) Endpoints aninhados
    if sid:
        try_get(f"/v1/servicos/{sid}/profissionais")
        try_get(f"/v1/servicos/{sid}/comissoes")
        try_get(f"/v1/servicos/{sid}")  # ver campos completos
    if pid:
        try_get(f"/v1/profissionais/{pid}/servicos")
        try_get(f"/v1/profissionais/{pid}/comissoes")
        try_get(f"/v1/profissionais/{pid}")  # ver campos completos

    # 5) Outros paths raiz
    try_get("/v1/servicos/comissoes")
    try_get("/v1/comissoes")
    try_get("/v1/backoffice/comissoes")
    try_get("/v1/cadastros/comissoes")
    try_get("/v1/configuracoes/comissoes")

    # 6) Serviços × profissionais (relação N:N)
    try_get("/v1/servicos-profissionais")
    if sid and pid:
        try_get(f"/v1/servicos/{sid}/profissionais/{pid}")
        try_get(f"/v1/profissionais/{pid}/servicos/{sid}")

    # 7) Include query
    if sid:
        try_get(f"/v1/servicos/{sid}", {"include": "profissionais"})
        try_get(f"/v1/servicos/{sid}", {"include": "comissoes"})

    print("\n" + "=" * 70)
    print("Fim do probe. Endpoints que retornam 200 + data preenchido = provável hit.")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
