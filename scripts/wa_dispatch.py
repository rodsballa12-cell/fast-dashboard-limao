#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Envia a fila de data/wa_fila.json pela Meta Cloud API e registra o histórico.

Sem META_ACCESS_TOKEN e META_PHONE_NUMBER_ID roda em dry-run: imprime o que
faria e NÃO grava histórico. Isso é importante — se dry-run gravasse, o cooldown
bloquearia o envio real quando os secrets finalmente existissem.

Env:
  META_ACCESS_TOKEN     token permanente do system user
  META_PHONE_NUMBER_ID  Phone Number ID do WhatsApp Business
  WA_FORCA_HORARIO      "1" ignora a janela de horário (só para teste manual)

Uso:  python scripts/wa_dispatch.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parent.parent
FILA = REPO / "data" / "wa_fila.json"
HIST = REPO / "data" / "wa_historico.json"
BRT = timezone(timedelta(hours=-3))
API = "https://graph.facebook.com/v20.0"


def enviar(phone_id: str, token: str, item: dict) -> tuple[bool, str]:
    body = {
        "messaging_product": "whatsapp",
        "to": item["telefone_e164"],
        "type": "template",
        "template": {
            "name": item["template"],
            "language": {"code": item["lingua"]},
            "components": [{"type": "body",
                            "parameters": [{"type": "text", "text": p} for p in item["params"]]}],
        },
    }
    try:
        r = requests.post(f"{API}/{phone_id}/messages", json=body, timeout=20,
                          headers={"Authorization": f"Bearer {token}",
                                   "Content-Type": "application/json"})
        if r.status_code // 100 == 2:
            return True, ((r.json() or {}).get("messages") or [{}])[0].get("id", "sem-id")
        return False, f"HTTP {r.status_code}: {r.text[:180]}"
    except requests.exceptions.RequestException as e:
        return False, f"{type(e).__name__}: {e}"


def main() -> int:
    if not FILA.exists():
        print("[wa] sem data/wa_fila.json — rode campanhas_wa.py antes")
        return 0
    fila_data = json.loads(FILA.read_text(encoding="utf-8"))
    fila = fila_data.get("fila") or []

    if not fila_data.get("ativo"):
        print("[wa] disparo desligado no config (disparo_wa.ativo = false) — nada enviado")
        return 0
    if not fila:
        print("[wa] fila vazia — nada a enviar")
        return 0

    agora = datetime.now(BRT)
    jan = fila_data.get("janela_envio") or {"inicio": 9, "fim": 20}
    if os.environ.get("WA_FORCA_HORARIO") != "1" and not (jan["inicio"] <= agora.hour < jan["fim"]):
        # Mensagem de salão fora de hora é a forma mais rápida de virar bloqueio.
        print(f"[wa] {agora:%H:%M} fora da janela {jan['inicio']}h–{jan['fim']}h — nada enviado")
        return 0

    token = (os.environ.get("META_ACCESS_TOKEN") or "").strip()
    phone_id = (os.environ.get("META_PHONE_NUMBER_ID") or "").strip()
    dry = not (token and phone_id)

    modo = "🧪 DRY-RUN (secrets da Meta ausentes)" if dry else "📱 ENVIO REAL"
    print(f"[wa] {modo} · {len(fila)} mensagem(ns) · {agora:%d/%m %H:%M} BRT")

    hist = json.loads(HIST.read_text(encoding="utf-8")) if HIST.exists() else {"envios": []}
    ok = fail = 0
    for it in fila:
        rot = f"  #{it['id']} {it['campanha']:11} {it['cliente'][:28]:28}"
        if dry:
            print(f"{rot} 🧪 pronta ({it['template']})")
            ok += 1
            continue
        sucesso, det = enviar(phone_id, token, it)
        print(f"{rot} {'✅' if sucesso else '❌'} {det}")
        # Só o envio real entra no histórico. Um dry-run registrado acionaria o
        # cooldown e impediria o primeiro envio de verdade.
        hist["envios"].append({
            "chave": it["chave"], "campanha": it["campanha"],
            "data": agora.date().isoformat(), "hora": agora.strftime("%H:%M"),
            "status": "enviado" if sucesso else "falha",
            "detalhe": det if not sucesso else None,
        })
        ok, fail = (ok + 1, fail) if sucesso else (ok, fail + 1)

    if not dry:
        hist["atualizado_em"] = agora.isoformat(timespec="seconds")
        HIST.write_text(json.dumps(hist, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[wa] resumo: {ok} ok · {fail} falha" + ("  (dry-run, histórico não gravado)" if dry else ""))
    return 1 if fail and not dry else 0


if __name__ == "__main__":
    sys.exit(main())
