#!/usr/bin/env python3
"""Sonda ONE-OFF: quais endpoints da API Trinks devolvem pacotes/saldo por cliente.
Imprime SO status e nomes de campos (o log do Actions e publico): nunca valores."""
import os, sys, time, requests
cid = sys.argv[1]
for suf in ("", "_SPA"):
    key = os.environ.get("TRINKS_API_KEY" + suf); eid = os.environ.get("TRINKS_ESTABELECIMENTO_ID" + suf)
    if not key or not eid:
        print("unidade", suf or "ESCOVA", "sem credencial"); continue
    h = {"X-Api-Key": key, "estabelecimentoId": eid, "Accept": "application/json"}
    print("== unidade", suf or "ESCOVA")
    for p in ["/v1/consumo", f"/v1/clientes/{cid}/pacotes", "/v1/pacotes", f"/v1/clientes/{cid}/saldo",
              f"/v1/clientes/{cid}/creditos", f"/v1/clientes/{cid}/pacotes-comprados", "/v1/clientes/pacotes",
              "/v1/pacotes-clientes", f"/v1/clientes/{cid}/historico"]:
        time.sleep(1.1)
        r = requests.get("https://api.trinks.com" + p, headers=h, params={"pageSize": 2}, timeout=30)
        campos = ""
        try:
            j = r.json()
            if isinstance(j, dict):
                campos = sorted(j.keys())
                d = j.get("data")
                if isinstance(d, list) and d and isinstance(d[0], dict):
                    campos = ("data[0]:", sorted(d[0].keys()))
            elif isinstance(j, list) and j and isinstance(j[0], dict):
                campos = ("lista[0]:", sorted(j[0].keys()))
        except Exception:
            pass
        print(f"  {r.status_code} {p.replace(cid, '{id}')} {campos}")
