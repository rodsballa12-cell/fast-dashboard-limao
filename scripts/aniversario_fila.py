r"""Fila de aprovação de aniversários — gera issue diária no GitHub com preview.

Fluxo:
  1. Este script roda 08h BRT (workflow aniversarios.yml).
  2. Lê data/dashboard_data.json, filtra aniversariantes de HOJE.
  3. Monta mensagem personalizada por cliente + preview.
  4. Cria issue no repo com checklist e comandos de aprovação.
  5. Quando alguém comenta "approve all" / "approve 1 3" no issue,
     o workflow aniversarios_dispatch.yml dispara via Meta API (ou dry-run).

Sem side effects se não houver aniversariante hoje.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DASH_JSON = REPO_ROOT / "data" / "dashboard_data.json"
CONFIG_JSON = REPO_ROOT / "data" / "config.json"
FILA_JSON = REPO_ROOT / "data" / "aniversarios_fila.json"

BRT = timezone(timedelta(hours=-3))


def montar_mensagem(cliente: dict, cfg: dict) -> str:
    nome_curto = (cliente.get("cliente") or "").split()[0].title()
    presente = cfg.get("presente_nome", "Escova grátis")
    validade = cfg.get("validade_dias", 15)
    loja = cfg.get("loja_nome", "FAST Escova")
    end = cfg.get("loja_endereco_curto", "")
    ass = cfg.get("assinatura", "Equipe")
    return (
        f"Feliz aniversário, {nome_curto}! 🎂✨\n\n"
        f"A {loja} preparou um presente pra você: {presente}, "
        f"válido pelos próximos {validade} dias.\n\n"
        f"É só aparecer aqui na loja pra comemorar com a gente 💛\n"
        f"{end}\n\n"
        f"— {ass}"
    )


def main():
    if not DASH_JSON.exists():
        print("[aniv] dashboard_data.json não existe — sem dados pra processar")
        return 0
    dash = json.loads(DASH_JSON.read_text(encoding="utf-8"))
    cfg_all = json.loads(CONFIG_JSON.read_text(encoding="utf-8")) if CONFIG_JSON.exists() else {}
    cfg = cfg_all.get("aniversario_campanha", {})

    hoje = datetime.now(BRT).date()
    aniv_list = ((dash.get("abas") or {}).get("anual") or {}).get("aniversariantes") or []
    # Só quem faz hoje (dias=0)
    hoje_aniv = [a for a in aniv_list if a.get("dias") == 0]

    fila = []
    for i, cli in enumerate(hoje_aniv, 1):
        msg = montar_mensagem(cli, cfg)
        fila.append({
            "id": i,
            "cliente": cli.get("cliente", ""),
            "telefone": cli.get("telefone", ""),
            "n_visitas": cli.get("n_visitas", 0),
            "ltv": cli.get("ltv", 0),
            "data_aniv": cli.get("data_aniv", ""),
            "mensagem": msg,
            "template_meta_nome": cfg.get("template_meta_nome", "aniversario_fast_v1"),
            "template_meta_lingua": cfg.get("template_meta_lingua", "pt_BR"),
            "template_params": [
                (cli.get("cliente") or "").split()[0].title(),
                cfg.get("presente_nome", "Escova grátis"),
                str(cfg.get("validade_dias", 15)),
            ],
        })

    FILA_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "gerado_em": datetime.now(BRT).isoformat(timespec="seconds"),
        "data_execucao": hoje.isoformat(),
        "n_aniversariantes": len(fila),
        "fila": fila,
    }
    FILA_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[aniv] {len(fila)} aniversariantes hoje ({hoje.isoformat()})")

    # Marker de saída pro workflow decidir se cria issue
    print(f"::set-output name=n_aniv::{len(fila)}")
    # Novo formato (GITHUB_OUTPUT)
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as fh:
            fh.write(f"n_aniv={len(fila)}\n")

    # Também retorna corpo pronto pra issue
    if fila:
        body = _issue_body(fila, hoje, cfg)
        # Print delimitado pra workflow capturar
        marker_ini = "<<<ISSUE_BODY_INI>>>"
        marker_fim = "<<<ISSUE_BODY_FIM>>>"
        print(marker_ini)
        print(body)
        print(marker_fim)
        # Grava em arquivo temporário também (mais robusto que capturar stdout)
        Path(REPO_ROOT / "data" / ".issue_body.md").write_text(body, encoding="utf-8")

    return 0


def _issue_body(fila: list[dict], hoje: date, cfg: dict) -> str:
    linhas = [
        f"**{len(fila)} aniversariante{'s' if len(fila) > 1 else ''} hoje ({hoje.strftime('%d/%m/%Y')})**",
        "",
        "Presente configurado: **" + cfg.get("presente_nome", "—")
        + f"** (válido {cfg.get('validade_dias', 15)} dias · custo est. R$ {cfg.get('presente_valor_est', 0)}/pessoa)",
        "",
        "---",
        "",
    ]
    for item in fila:
        linhas.extend([
            f"### #{item['id']} — {item['cliente']}",
            f"- 📱 Telefone: `{item['telefone'] or 'SEM TELEFONE'}`",
            f"- 📊 Histórico: {item['n_visitas']} visita(s) · LTV R$ {item['ltv']:.2f}",
            "",
            "**Prévia da mensagem:**",
            "```",
            item['mensagem'],
            "```",
            "",
        ])
    linhas.extend([
        "---",
        "",
        "## Como aprovar",
        "",
        "Comente neste issue com um dos comandos abaixo:",
        "",
        "- `approve all` — envia pra todos os aniversariantes acima",
        "- `approve 1 3` — envia só pros IDs listados (ex: 1 e 3)",
        "- `skip` — não envia pra ninguém hoje (só encerra a fila)",
        "- `skip 2` — envia pra todos exceto o ID 2",
        "",
        "⏱ Sem resposta em **6 horas** → workflow encerra sem enviar (não spamar por engano).",
        "",
        "🧪 **Modo atual:** verifica se `META_ACCESS_TOKEN` está configurado nos Secrets. "
        "Se estiver ausente, roda em **dry-run** (só posta o que faria).",
    ])
    return "\n".join(linhas)


if __name__ == "__main__":
    sys.exit(main())
