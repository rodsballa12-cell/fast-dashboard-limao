#!/usr/bin/env python3
"""Sonda ONE-OFF: o que o token da Meta enxerga sobre leads/conversas.
Imprime SO status, contagens e nomes de permissao (o log do Actions e publico)."""
import os, sys, requests
G = "https://graph.facebook.com/v20.0"
tok = os.environ.get("META_ACCESS_TOKEN", "")
if not tok:
    sys.exit("sem META_ACCESS_TOKEN")

def get(path, **p):
    p["access_token"] = tok
    r = requests.get(G + path, params=p, timeout=30)
    try:
        j = r.json()
    except Exception:
        j = {}
    return r.status_code, j

s, j = get("/me/permissions")
print("permissoes concedidas:", sorted(x["permission"] for x in j.get("data", []) if x.get("status") == "granted"))
print("permissoes recusadas/expiradas:", sorted(x["permission"] for x in j.get("data", []) if x.get("status") != "granted"))
s, j = get("/me/accounts", fields="id,name,instagram_business_account,access_token", limit=25)
print("paginas:", s, len(j.get("data", [])))
for pg in j.get("data", []):
    nome = pg.get("name", "")[:30]
    pt = pg.get("access_token")
    print("==", nome, "| IG vinculado:", bool(pg.get("instagram_business_account")))
    def pget(path, **p):
        p["access_token"] = pt
        r = requests.get(G + path, params=p, timeout=30)
        try: return r.status_code, r.json()
        except Exception: return r.status_code, {}
    for plat in ("messenger", "instagram"):
        s2, j2 = pget(f"/{pg['id']}/conversations", platform=plat, limit=5, fields="updated_time")
        err = (j2.get("error") or {}).get("message", "")[:110]
        print(f"   conversas {plat}: HTTP {s2} | itens na 1a pagina: {len(j2.get('data', []))} | {err}")
    s3, j3 = pget(f"/{pg['id']}/leadgen_forms", limit=5, fields="id,status,leads_count")
    err = (j3.get("error") or {}).get("message", "")[:110]
    print(f"   formularios de lead: HTTP {s3} | formularios: {len(j3.get('data', []))} | leads_count: {[f.get('leads_count') for f in j3.get('data', [])]} | {err}")
