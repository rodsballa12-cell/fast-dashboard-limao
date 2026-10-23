#!/usr/bin/env python3
"""Decisões sem resultado — tornar a NÃO-EXECUÇÃO visível.

Por que existe (23/10/2026): as três primeiras peças de saúde cuidam de
"a máquina parou". Esta cuida de "a máquina avisou e nada aconteceu", que
custa mais caro e não aparece em lugar nenhum.

A prova está no próprio repositório. A decisão sobre clientes sumidos foi
tomada em 11/10, 16/10, 17/10 e de novo em 20/10 — quatro vezes, com dono
nomeado e meta diária — e nenhuma ligação foi confirmada. O alarme tocou
todas as noites. Não faltou detecção; faltou execução, e a falta de execução
não tinha onde aparecer.

Medindo os 85 arquivos de `docs/decisoes/`:

    com "## Resultado" preenchido :  3
    com "## Resultado" em branco  : 81

A estrutura certa já existia — Executor, Em jogo, Revisão, Resultado. Ninguém
fecha o ciclo. Este script não inventa processo novo: ele conta o que já está
escrito e põe o número onde o Rodrigo olha.

O que NÃO faz, de propósito: não verifica se a decisão foi cumprida. Isso
exigiria uma regra escrita à mão por decisão, que envelhece e mente. Ele mede
o que é verdade para todas — há quanto tempo está aberta e se alguém registrou
desfecho — e deixa o julgamento com quem decide.

Uso:  python scripts/decisoes_abertas.py        # grava data/decisoes.json
      python scripts/decisoes_abertas.py ler    # imprime, para o olho humano
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "docs" / "decisoes"
SAIDA = RAIZ / "data" / "decisoes.json"
BRT = timezone(timedelta(hours=-3))

# Quantas aparecem no painel. O resto vira contagem. O conselho desta casa tem
# regra propria: "conselho que entrega dez itens nao decidiu nada, empurrou a
# fila". Despejar 81 cartoes seria o mesmo erro com outro nome.
NO_PAINEL = 5

# Marcadores de ciclo fechado. SUPERADA conta como fechada: a decisao foi
# absorvida por outra, nao abandonada.
FECHADA = re.compile(r"\*\*(?:SUPERADA|EXECUTADA|RECUSADA|APROVADA e EXECUTADA)\b", re.I)
PLACEHOLDER = re.compile(r"^_?\(?em branco", re.I)


def _secao(texto: str, nome: str) -> str:
    m = re.search(rf"^## {nome}\s*\n(.*?)(?=\n## |\Z)", texto, re.S | re.M)
    return m.group(1).strip() if m else ""


def _reais(txt: str) -> float | None:
    """R$ 8.724,99 -> 8724.99. Devolve None quando nao ha valor — e MUITA
    decisao nao tem: 'a visibilidade inteira do caixa do Spa' e um valor
    legitimo em jogo e nao vira numero."""
    m = re.search(r"R\$\s*([\d.]+(?:,\d{2})?)", txt)
    if not m:
        return None
    try:
        return float(m.group(1).replace(".", "").replace(",", "."))
    except ValueError:
        return None


def coletar() -> dict:
    hoje = datetime.now(BRT).date()
    abertas, fechadas = [], 0
    for f in sorted(PASTA.glob("*.md")) if PASTA.exists() else []:
        t = f.read_text(encoding="utf-8", errors="replace")
        resultado = _secao(t, "Resultado")
        tem_resultado = bool(resultado) and not PLACEHOLDER.match(resultado) and len(resultado) >= 25
        if tem_resultado or FECHADA.search(t):
            fechadas += 1
            continue

        titulo = (t.splitlines() or [""])[0].lstrip("# ").strip()
        titulo = re.sub(r"\*\*", "", titulo)
        # "Conselho 2026-10-17 · Decisão #1 · <titulo>" -> so o titulo
        titulo = re.sub(r"^Conselho \d{4}-\d{2}-\d{2} · Decisão #\d+ · ", "", titulo)
        try:
            quando = date.fromisoformat(f.name[:10])
        except ValueError:
            quando = hoje
        em_jogo = _secao(t, "Em jogo") or ""
        em_jogo = "" if em_jogo.startswith("(não capturado") else em_jogo.split("\n")[0]
        # Primeira oracao, sem markdown. O campo costuma trazer o acordo
        # inteiro ("voce com o Financeiro; o gatilho e **abaixo de R$ 1.000..."),
        # e no painel isso vira ruido que empurra o titulo para fora da tela.
        executor = (_secao(t, "Executor") or "").split("\n")[0]
        executor = re.sub(r"\*\*|`", "", executor).split(";")[0].split(" — ")[0].strip()
        abertas.append({
            "arquivo": f.name,
            "titulo": titulo[:140],
            "data": quando.isoformat(),
            "dias": (hoje - quando).days,
            "em_jogo": em_jogo[:120],
            "valor": _reais(em_jogo),
            "executor": "" if executor.lower().startswith("a definir") else executor[:60],
        })

    # Dinheiro primeiro; sem valor, as mais velhas. Idade sozinha colocaria uma
    # decisao de rotina de julho na frente dos R$ 8 mil de ontem.
    abertas.sort(key=lambda d: (-(d["valor"] or 0), -d["dias"]))
    return {
        "_desc": "Decisões sem desfecho registrado. Ver scripts/decisoes_abertas.py.",
        "gerado_em": datetime.now(BRT).replace(microsecond=0).isoformat(),
        "n_abertas": len(abertas),
        "n_fechadas": fechadas,
        "mais_antiga_dias": max((d["dias"] for d in abertas), default=0),
        "destaque": abertas[:NO_PAINEL],
    }


def main() -> int:
    d = coletar()
    if len(sys.argv) > 1 and sys.argv[1] == "ler":
        print(f"  {d['n_abertas']} sem resultado · {d['n_fechadas']} fechadas · "
              f"mais antiga: {d['mais_antiga_dias']} dias")
        for x in d["destaque"]:
            v = f"R$ {x['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if x["valor"] else (x["em_jogo"] or "—")
            print(f"    {x['dias']:>4}d  {v:<22} {x['titulo'][:60]}")
        return 0
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[decisoes] {d['n_abertas']} sem resultado, {d['n_fechadas']} fechadas -> {SAIDA.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
