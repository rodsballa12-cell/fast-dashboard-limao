#!/usr/bin/env python3
"""Carimba na faixa de saúde há quanto tempo não sai parecer e não há Conselho.

Por que existe (26/10/2026): em 23/10 a faixa nasceu com cinco itens e só três
tinham quem carimbasse. `conselho` e `cargos` rodam no PC, e nenhum workflow
escrevia neles — ficavam em "nunca carimbou" para sempre.

Nos três dias seguintes os seis cargos pararam. O watchdog detectou na primeira
rodada e seguiu avisando por 77 horas **na issue #32 do GitHub**, que já tinha
sete comentários que ninguém leu. Enquanto isso a faixa, no topo do painel,
mostrava dois ✅ e duas interrogações — e a interrogação estava exatamente em
cima da única coisa que tinha parado.

Alarme no lugar certo é metade do trabalho. A outra metade é o lugar onde a
pessoa já está olhando.

O que conta como parecer de verdade é a mesma regra do watchdog: ata que não
seja só "Credit balance is too low" e tenha corpo. Carimbo é sobre CONTEÚDO —
"a ata foi escrita" nunca foi "a reunião aconteceu".
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ATAS = RAIZ / "docs" / "atas"
BRT = timezone(timedelta(hours=-3))

# O que separa parecer de desculpa é TAMANHO, não a frase.
#
# A primeira versão disto (e o watchdog, desde 23/10) descartava qualquer ata
# que contivesse "credit balance". Resultado: a ata do Conselho de 22/10 — 9.320
# bytes, parecer completo — foi jogada fora porque *falava sobre* os cinco dias
# sem crédito. O detector acusou a reunião que estava relatando a falha.
#
# Medido no repositório: ata-desculpa tem 206 bytes; ata de verdade, 8.800 a
# 9.300. O corte em 1.200 tem margem de 6x para cada lado.
#
# E atenção: parecer de verdade PODE começar com um erro. Os cinco de 23/10
# abrem com um bloco de erro de permissão e trazem o parecer inteiro embaixo.
# Por isso "começa com erro" também não serve como regra.
CORPO_MINIMO = 1200


def _commit_ts(rel: Path) -> int | None:
    """Quando a ata entrou no repositório. Data de arquivo não serve: num
    checkout novo toda ata tem a idade do checkout."""
    r = subprocess.run(["git", "log", "-1", "--format=%ct", "--", str(rel)],
                       cwd=RAIZ, capture_output=True, text=True)
    saida = r.stdout.strip()
    return int(saida) if saida.isdigit() else None


def mais_recente(so_conselho: bool = False) -> tuple[int | None, str]:
    melhor_ts, melhor_nome = None, ""
    for f in sorted(ATAS.glob("*.md"), reverse=True):
        if f.name == "README.md":
            continue
        if so_conselho and not f.name.endswith("-conselho.md"):
            continue
        try:
            corpo = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if len(corpo) < CORPO_MINIMO:
            continue
        ts = _commit_ts(f.relative_to(RAIZ))
        if ts and (melhor_ts is None or ts > melhor_ts):
            melhor_ts, melhor_nome = ts, f.name
        # as atas vêm em ordem de nome (= data) decrescente; a primeira válida
        # com commit é quase sempre a mais nova, mas seguimos mais duas por
        # segurança contra ata recomitada fora de ordem
        if melhor_ts and f.name[:10] < melhor_nome[:10]:
            break
    return melhor_ts, melhor_nome


def para_o_watchdog() -> int:
    """Imprime no formato do GITHUB_OUTPUT. O watchdog tinha a mesma conta
    escrita em bash, com o mesmo filtro errado -- dois leitores do mesmo fato
    divergem sempre, e já custou caro nesta casa (ver
    docs/aprendizados/campo-novo-de-config-tem-mais-de-um-leitor.md)."""
    agora = int(datetime.now(timezone.utc).timestamp())
    ts, nome = mais_recente(False)
    if ts is None:
        print("status=critico"); print("motivo=nenhuma ata de verdade no historico")
        return 0
    horas = (agora - ts) // 3600
    print(f"ultimo_commit={nome}")
    print(f"horas={horas}")
    print("status=" + ("alerta" if horas >= 24 else "ok"))
    print(f"motivo=ultima ata ha {horas}h" + (" (>24h)" if horas >= 24 else ""))
    return 0


def main() -> int:
    if "--github-output" in sys.argv:
        return para_o_watchdog()
    sys.path.insert(0, str(RAIZ / "scripts"))
    import saude

    agora = int(datetime.now(timezone.utc).timestamp())
    saida = 0
    for chave, so_cons in (("cargos", False), ("conselho", True)):
        ts, nome = mais_recente(so_cons)
        limite = saude.LIMITES[chave]["horas"]
        rotulo = saude.LIMITES[chave]["rotulo"]
        if ts is None:
            saude.carimbar(chave, "falha", "nenhum parecer de verdade no histórico")
            print(f"[saude-atas] {rotulo}: NENHUM encontrado")
            saida = 1
            continue
        horas = (agora - ts) // 3600
        estado = "ok" if horas < limite else "falha"
        quando = datetime.fromtimestamp(ts, BRT).strftime("%d/%m %H:%M")
        # Curto de proposito: isto vai para uma faixa de uma linha no topo do
        # painel, no celular. Nome de arquivo nao cabe e nao ajuda ninguem --
        # o que o Rodrigo precisa saber e HA QUANTO TEMPO.
        detalhe = (f"sem parecer há {horas}h" if estado == "falha"
                   else f"último há {horas}h") + f" · {quando}"
        saude.carimbar(chave, estado, detalhe)
        print(f"[saude-atas] {rotulo}: {estado} · {detalhe}")
        if estado == "falha":
            saida = 1
    return saida


if __name__ == "__main__":
    sys.exit(main())
