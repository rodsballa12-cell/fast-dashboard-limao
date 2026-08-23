r"""Dispatcher da fila de aniversários — envia via Meta Cloud API (ou dry-run).

Chamado pelo workflow aniversarios_dispatch.yml quando alguém comenta
"approve all" ou "approve 1 3" ou "skip" num issue de aniversário.

Env vars:
  META_ACCESS_TOKEN   — token permanente do system user (opcional; ausente = dry-run)
  META_PHONE_NUMBER_ID — Phone Number ID do WhatsApp Business (opcional)
  APROVACAO_COMANDO   — comando cru vindo do comentário (obrigatório)
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
FILA_JSON = REPO_ROOT / "data" / "aniversarios_fila.json"

BRT = timezone(timedelta(hours=-3))
META_API_BASE = "https://graph.facebook.com/v20.0"


def parse_comando(cmd: str, ids_disponiveis: set[int]) -> tuple[str, set[int]]:
    """Retorna (acao, set_de_ids). acao ∈ {'approve','skip'}."""
    cmd = (cmd or "").strip().lower()
    if not cmd:
        return "unknown", set()
    if cmd.startswith("skip"):
        acao = "skip"
        resto = cmd[4:].strip()
    elif cmd.startswith("approve"):
        acao = "approve"
        resto = cmd[7:].strip()
    else:
        return "unknown", set()
    if resto == "all" or not resto:
        return acao, set(ids_disponiveis)
    nums = {int(x) for x in re.findall(r"\d+", resto) if int(x) in ids_disponiveis}
    return acao, nums


def _formatar_e164(telefone: str) -> str | None:
    """+55 (11) 99123-0296 → 5511991230296. Retorna None se inválido."""
    if not telefone:
        return None
    so_digitos = re.sub(r"\D", "", telefone)
    if not so_digitos.startswith("55"):
        so_digitos = "55" + so_digitos
    if len(so_digitos) < 12:
        return None
    return so_digitos


def enviar_meta(phone_number_id: str, token: str, e164: str, template_nome: str,
                lingua: str, params: list[str]) -> tuple[bool, str]:
    """Chama Meta Cloud API. Retorna (ok, mensagem_de_status)."""
    url = f"{META_API_BASE}/{phone_number_id}/messages"
    body = {
        "messaging_product": "whatsapp",
        "to": e164,
        "type": "template",
        "template": {
            "name": template_nome,
            "language": {"code": lingua},
            "components": [{
                "type": "body",
                "parameters": [{"type": "text", "text": p} for p in params],
            }],
        },
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, json=body, headers=headers, timeout=20)
        if r.status_code // 100 == 2:
            wa_id = ((r.json() or {}).get("messages") or [{}])[0].get("id", "sem-id")
            return True, f"enviado · wa_id={wa_id}"
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except requests.exceptions.RequestException as e:
        return False, f"exception: {type(e).__name__}: {e}"


def main():
    cmd_raw = os.environ.get("APROVACAO_COMANDO", "")
    if not FILA_JSON.exists():
        _print_relatorio("❌ Fila não encontrada", ["Arquivo `data/aniversarios_fila.json` ausente. Rode a fila diária primeiro."])
        return 2
    fila_data = json.loads(FILA_JSON.read_text(encoding="utf-8"))
    fila = fila_data.get("fila") or []
    if not fila:
        _print_relatorio("ℹ️ Fila vazia", ["Sem aniversariantes hoje. Nada a enviar."])
        return 0

    ids_disp = {item["id"] for item in fila}
    acao, ids_alvo = parse_comando(cmd_raw, ids_disp)
    if acao == "unknown":
        _print_relatorio("⚠️ Comando não reconhecido",
                         [f"Comando recebido: `{cmd_raw}`",
                          "",
                          "Use: `approve all`, `approve 1 3`, `skip`, ou `skip 2`."])
        return 3

    if acao == "skip":
        # Se veio "skip 2" → todos MENOS os listados
        alvo = ids_disp - ids_alvo if ids_alvo else set()
        if not alvo:
            _print_relatorio("🚫 Encerrado sem envios",
                             [f"Comando: `{cmd_raw}` → não envia pra ninguém."])
            return 0
        ids_alvo = alvo
        acao = "approve"

    # acao == 'approve' com ids_alvo definido
    token = os.environ.get("META_ACCESS_TOKEN", "").strip()
    phone_id = os.environ.get("META_PHONE_NUMBER_ID", "").strip()
    dry_run = not (token and phone_id)

    linhas = [
        f"**Comando:** `{cmd_raw}`",
        f"**Aprovados:** {sorted(ids_alvo)}",
        f"**Modo:** {'🧪 DRY-RUN (Meta secrets ausentes)' if dry_run else '📱 ENVIO REAL via Meta Cloud API'}",
        "",
        "| # | Cliente | Telefone (E.164) | Status |",
        "|---|---|---|---|",
    ]
    ok, fail = 0, 0
    for item in fila:
        if item["id"] not in ids_alvo:
            continue
        e164 = _formatar_e164(item.get("telefone", ""))
        if not e164:
            linhas.append(f"| {item['id']} | {item['cliente']} | — | ❌ telefone inválido |")
            fail += 1
            continue
        if dry_run:
            linhas.append(f"| {item['id']} | {item['cliente']} | `{e164}` | 🧪 dry-run (mensagem pronta) |")
            ok += 1
            continue
        sucesso, status = enviar_meta(
            phone_id, token, e164,
            item.get("template_meta_nome", "aniversario_fast_v1"),
            item.get("template_meta_lingua", "pt_BR"),
            item.get("template_params", []),
        )
        if sucesso:
            linhas.append(f"| {item['id']} | {item['cliente']} | `{e164}` | ✅ {status} |")
            ok += 1
        else:
            linhas.append(f"| {item['id']} | {item['cliente']} | `{e164}` | ❌ {status} |")
            fail += 1

    linhas.extend([
        "",
        f"**Resumo:** {ok} sucesso · {fail} falha",
        f"**Executado em:** {datetime.now(BRT).strftime('%Y-%m-%d %H:%M:%S BRT')}",
    ])
    modo = "dry-run" if dry_run else ("envio real")
    titulo = f"{'✅' if fail == 0 else '⚠️'} Disparo {modo}: {ok} enviado(s), {fail} falha(s)"
    _print_relatorio(titulo, linhas)
    return 0


def _print_relatorio(titulo: str, linhas: list[str]):
    """Emite bloco delimitado que o workflow captura pra comentar no issue."""
    print("<<<RESULT_INI>>>")
    print(f"## {titulo}")
    print("")
    print("\n".join(linhas))
    print("<<<RESULT_FIM>>>")


if __name__ == "__main__":
    sys.exit(main())
