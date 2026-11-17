#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sonda SÓ DE LEITURA: o que o META_ACCESS_TOKEN enxerga para ligar o WhatsApp oficial.

POR QUE EXISTE (17/11/2026)
O Rodrigo decidiu configurar a API do WhatsApp nos números das duas lojas
(docs/decisoes/2026-11-17-whatsapp-api-coexistencia-numeros-das-lojas.md). Antes
de propor qualquer passo, é preciso saber o que já existe: quais portfolios
(Business Manager) o token alcança, com que papel, se há conta de WhatsApp
(WABA) e número cadastrados, que textos (templates) já foram aprovados, se a
empresa é verificada e que permissões o token tem.

SÓ GET. Nada é criado, alterado ou enviado.

O REPOSITÓRIO É PÚBLICO e o log do Actions também: este script nunca imprime o
token, e-mail ou nome de pessoa. Imprime nome de portfolio, de página e de conta,
IDs (não são segredo: sem token não servem para nada) e o número das lojas (já
público no Google e no Instagram).

Uso (Actions): workflow "Meta · sonda" com alvo=whatsapp.
"""
from __future__ import annotations

import json
import os
import sys

import requests

API = "https://graph.facebook.com/v20.0"
TOKEN = (os.environ.get("META_ACCESS_TOKEN") or "").strip()


def get(caminho: str, **params):
    params["access_token"] = TOKEN
    try:
        r = requests.get(f"{API}/{caminho.lstrip('/')}", params=params, timeout=25)
        d = r.json()
    except Exception as e:  # rede, JSON
        return None, f"{type(e).__name__}"
    if "error" in d:
        e = d["error"]
        return None, f"erro {e.get('code')}/{e.get('error_subcode', '-')}: {str(e.get('message'))[:160]}"
    return d, None


def lista(caminho: str, **params):
    d, err = get(caminho, **params)
    if err:
        return None, err
    return d.get("data", []), None


def linha(rotulo, valor):
    print(f"  {rotulo:<34} {valor}")


def main() -> int:
    if not TOKEN:
        print("META_ACCESS_TOKEN ausente nos Secrets — nada a sondar.")
        return 1

    print("=" * 72)
    print("1. O TOKEN")
    me, err = get("me", fields="id")
    linha("dono do token responde?", "sim" if me else err)
    app, err = get("app", fields="id,name")
    linha("app do token", f"{app.get('name')} (id {app.get('id')})" if app else err)
    perms, err = lista("me/permissions")
    if perms is not None:
        conc = sorted(p["permission"] for p in perms if p.get("status") == "granted")
        neg = sorted(p["permission"] for p in perms if p.get("status") != "granted")
        linha("permissões concedidas", ", ".join(conc) or "nenhuma")
        if neg:
            linha("permissões recusadas/expiradas", ", ".join(neg))
        for p in ("business_management", "whatsapp_business_management", "whatsapp_business_messaging"):
            linha(f"  tem {p}?", "SIM" if p in conc else "NÃO")
    else:
        linha("permissões", err)

    print("=" * 72)
    print("2. PÁGINAS DO FACEBOOK (e o WhatsApp ligado a cada uma)")
    pags, err = lista("me/accounts", fields="id,name,whatsapp_number,tasks", limit=50)
    if pags is None:
        linha("páginas", err)
    for p in pags or []:
        linha(p.get("name", "?"), f"id {p.get('id')} · WhatsApp ligado: {p.get('whatsapp_number') or '—'} · "
                                  f"tarefas: {','.join(p.get('tasks') or [])}")

    print("=" * 72)
    print("3. PORTFOLIOS (Business Manager) que o token alcança")
    bms, err = lista("me/businesses", fields="id,name,verification_status,permitted_roles", limit=50)
    if bms is None:
        linha("portfolios", err)
        bms = []
    if not bms:
        print("  (nenhum portfolio visível — sem business_management o token não lista portfolios)")
    wabas = {}
    for b in bms:
        print(f"\n  ▶ {b.get('name')}  (id {b.get('id')})")
        linha("verificação do negócio", b.get("verification_status") or "—")
        linha("papel do dono do token", ", ".join(b.get("permitted_roles") or []) or "—")
        users, err = lista(f"{b['id']}/business_users", fields="role", limit=100)
        if users is not None:
            papeis = {}
            for u in users:
                papeis[u.get("role", "?")] = papeis.get(u.get("role", "?"), 0) + 1
            linha("pessoas por papel (sem nomes)", json.dumps(papeis, ensure_ascii=False))
        else:
            linha("pessoas por papel", err)
        sus, err = lista(f"{b['id']}/system_users", fields="id,role", limit=50)
        linha("usuários do sistema", f"{len(sus)} ({', '.join(sorted({s.get('role','?') for s in sus}))})" if sus is not None else err)
        for rel in ("owned_whatsapp_business_accounts", "client_whatsapp_business_accounts"):
            ws, err = lista(f"{b['id']}/{rel}", fields="id,name", limit=50)
            if ws is None:
                linha(rel, err)
                continue
            linha(rel, f"{len(ws)}")
            for w in ws:
                wabas[w["id"]] = (w.get("name"), b.get("name"), rel)
        apps, err = lista(f"{b['id']}/owned_apps", fields="id,name", limit=50)
        linha("apps do portfolio", ", ".join(f"{a.get('name')} ({a.get('id')})" for a in apps) if apps is not None else err)

    print("=" * 72)
    print("4. CONTAS DE WHATSAPP (WABA), NÚMEROS E TEXTOS APROVADOS")
    if not wabas:
        print("  nenhuma WABA visível para este token")
    for wid, (nome, bm, rel) in wabas.items():
        print(f"\n  ▶ WABA {nome}  (id {wid}) · portfolio {bm} · {rel}")
        w, err = get(wid, fields="name,currency,timezone_id,account_review_status,"
                                  "business_verification_status,ownership_type,message_template_namespace")
        if w:
            for k in ("account_review_status", "business_verification_status", "ownership_type", "currency"):
                linha(k, w.get(k, "—"))
        else:
            linha("detalhes", err)
        nums, err = lista(f"{wid}/phone_numbers",
                          fields="id,display_phone_number,verified_name,name_status,code_verification_status,"
                                 "quality_rating,platform_type,status,messaging_limit_tier,is_official_business_account")
        if nums is None:
            linha("números", err)
        for n in nums or []:
            print(f"    · {n.get('display_phone_number')} — {n.get('verified_name')}")
            for k in ("id", "status", "platform_type", "name_status", "code_verification_status",
                      "quality_rating", "messaging_limit_tier"):
                linha(f"      {k}", n.get(k, "—"))
        tpls, err = lista(f"{wid}/message_templates", fields="name,status,category,language", limit=100)
        if tpls is None:
            linha("templates", err)
        else:
            linha("templates", f"{len(tpls)}")
            for t in tpls:
                linha(f"      {t.get('name')}", f"{t.get('status')} · {t.get('category')} · {t.get('language')}")
        apps, err = lista(f"{wid}/subscribed_apps")
        linha("apps assinando a WABA", ", ".join((a.get("whatsapp_business_api_data") or {}).get("name", "?") for a in apps)
              if apps is not None else err)

    print("=" * 72)
    print("Fim. Nada foi alterado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
