#!/usr/bin/env python3
"""Grava a ata de um cargo em docs/atas/ e diz se ela é um parecer de verdade.

Por que existe (31/10/2026): de 23 a 31/10 as rotinas rodaram todos os dias e
nenhum parecer de verdade saiu. Primeiro veio "Credit balance is too low",
depois "o comando /conselho não existe nesta sessão", e depois o PC parou de
mandar ata. A cada vez o alarme procurava a frase do erro anterior e não
reconheceu a nova. Por isso este verificador não procura frase de erro: ele
exige o FORMATO do parecer (PROTOCOLO.md). Um texto sem esse formato é falha,
seja qual for o motivo.

Uso:
    python3 scripts/agenda/gravar_ata.py <agente> <arquivo_com_a_saida> [--origem nuvem]
Imprime "ok" ou "falha" na última linha e, no GitHub Actions, grava
`resultado=` e `arquivo=` em $GITHUB_OUTPUT.
"""
from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

# O pedido feito ao claude. Não usa o atalho "/<cargo>": desde a noite de
# 23/10/2026 o claude do PC respondia "o comando /conselho não existe nesta
# sessão". Pedir para ler a ficha funciona com ou sem atalho registrado.
PEDIDO = (
    "Você é o cargo '{agente}' da FAST Limão. Leia .claude/skills/{agente}/SKILL.md "
    "e .claude/skills/PROTOCOLO.md e execute agora a rotina dessa ficha sobre os dados "
    "reais do repositório (o cofre já está aberto). Responda somente com a entrega final "
    "no formato da ficha, sem comentar a execução. Não altere arquivos, não faça commit "
    "nem push e não envie mensagens: a ata é gravada por fora."
)
ATAS = RAIZ / "docs" / "atas"
BRT = timezone(timedelta(hours=-3))

# O que um parecer precisa ter para contar como parecer.
# Cargos: o PROTOCOLO (SITUAÇÃO / FATOS / ... / DECISÃO).
# Conselho: a ata dele (AS QUATRO JANELAS ... DECISÕES).
EXIGE = {
    "conselho": [r"JANELAS", r"DECIS[ÕO]ES|DECIS[ÃA]O"],
    # A Operação tem entrega própria, de 12 linhas (ver a ficha dela).
    "operacao-diaria": [r"O DIA", r"VIGIAR|EXIGE A[ÇC][ÃA]O"],
    "_cargo": [r"SITUA[ÇC][ÃA]O", r"FATOS"],
}
# Um parecer de dia parado é curto ("Sem novidade: ..."), e a ficha de cada
# cargo autoriza isso. Então texto curto SEM o formato só é aceito se disser
# explicitamente que nada mudou.
DIA_PARADO = re.compile(r"\bsem novidade\b|\bnada mudou\b|\bnada a decidir\b", re.I)
TAMANHO_MINIMO = {"operacao-diaria": 120, "_": 250}


def avaliar(agente: str, texto: str) -> tuple[bool, str]:
    t = texto.strip()
    if not t:
        return False, "o claude não devolveu texto"
    # Erro de acesso não é "formato errado": diga o que fazer (12/11/2026, a
    # chave venceu e por dois dias o painel culpou um aviso de permissão).
    if re.search(r"401|Invalid bearer token|Failed to authenticate|OAuth token has expired", t):
        return False, "chave de acesso do Claude recusada (401) — gerar outra no PC com 'claude setup-token' e trocar o segredo CLAUDE_CODE_OAUTH_TOKEN no GitHub"
    if re.search(r"credit balance|usage limit|rate limit", t, re.I) and len(t) < 600:
        return False, "limite de uso do Claude atingido"
    regras = EXIGE.get(agente, EXIGE["_cargo"])
    faltam = [r for r in regras if not re.search(r, t, re.I)]
    if not faltam and len(t) >= TAMANHO_MINIMO.get(agente, TAMANHO_MINIMO["_"]):
        return True, "parecer no formato do protocolo"
    if agente != "conselho" and DIA_PARADO.search(t) and len(t) < 1200:
        return True, "dia parado declarado"
    trecho = re.sub(r"\s+", " ", t)[:160]
    return False, f"sem o formato do protocolo (falta {', '.join(faltam) or 'tamanho'}): {trecho}"


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    agente, saida_arq = argv[1], Path(argv[2])
    origem = argv[argv.index("--origem") + 1] if "--origem" in argv else "nuvem"
    texto = saida_arq.read_text(encoding="utf-8", errors="replace") if saida_arq.exists() else ""

    ok, motivo = avaliar(agente, texto)
    agora = datetime.now(BRT)
    data, hora = agora.strftime("%Y-%m-%d"), agora.strftime("%H:%M")

    cabecalho = (
        "---\n"
        f"agente: {agente}\n"
        f"data: {data}\n"
        f"hora: {hora}\n"
        f"gerado_por: {origem}\n"
        f"resultado: {'ok' if ok else 'falha'}\n"
        "---\n\n"
        f"# {agente} · {data} às {hora}\n\n"
        "↑ [[76_Briefings_Agentes/00-INDEX|Briefings dos Agentes]]\n\n"
    )
    if ok:
        corpo = texto.strip() + "\n"
    else:
        corpo = (
            f"> [!danger] FALHOU: não saiu parecer hoje.\n> Motivo: {motivo}\n\n"
            "Saída do claude, como veio:\n\n```\n" + texto.strip()[:4000] + "\n```\n"
        )

    ATAS.mkdir(parents=True, exist_ok=True)
    arq = ATAS / f"{data}-{agente}.md"
    arq.write_text(cabecalho + corpo, encoding="utf-8")

    resultado = "ok" if ok else "falha"
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a", encoding="utf-8") as f:
            f.write(f"resultado={resultado}\narquivo={arq.relative_to(RAIZ).as_posix()}\n")
            f.write(f"motivo={motivo[:200]}\n")
    print(f"[ata] {arq.relative_to(RAIZ)} · {motivo}")
    print(resultado)
    return 0


def ja_tem_parecer(agente: str, data: str | None = None) -> bool:
    """True se docs/atas/<data>-<agente>.md já existe e é parecer válido."""
    data = data or datetime.now(BRT).strftime("%Y-%m-%d")
    arq = ATAS / f"{data}-{agente}.md"
    if not arq.exists():
        return False
    txt = arq.read_text(encoding="utf-8", errors="replace")
    if re.search(r"^resultado:\s*falha", txt, re.M):
        return False
    corpo = txt.split("---", 2)[-1]
    return avaliar(agente, corpo)[0]


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--pedido":
        # python3 scripts/agenda/gravar_ata.py --pedido <agente> -> o texto para o claude -p
        print(PEDIDO.format(agente=sys.argv[2]))
        sys.exit(0)
    if len(sys.argv) >= 4 and sys.argv[1] == "--avaliar":
        # python3 scripts/agenda/gravar_ata.py --avaliar <agente> <arquivo> -> ok/falha (para o PC)
        t = Path(sys.argv[3]).read_text(encoding="utf-8", errors="replace") if Path(sys.argv[3]).exists() else ""
        ok, motivo = avaliar(sys.argv[2], t)
        print(("ok" if ok else "falha") + " | " + motivo)
        sys.exit(0)
    if len(sys.argv) >= 3 and sys.argv[1] == "--ja-tem":
        # python3 scripts/agenda/gravar_ata.py --ja-tem <agente>  -> imprime sim/nao
        print("sim" if ja_tem_parecer(sys.argv[2]) else "nao")
        sys.exit(0)
    sys.exit(main(sys.argv))
