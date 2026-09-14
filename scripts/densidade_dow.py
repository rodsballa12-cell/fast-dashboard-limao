#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Densidade de atendimento por dia da semana × hora, a partir dos agendamentos.

POR QUE EXISTE
O painel traz `densidade_hora` já agregada: uma média de todos os dias juntos.
Em 14/09/2026 essa média disse que o pico era 1,67 simultâneos às 16h. Separando
por dia da semana apareceu outra coisa: sábado às 17h tem 3,90, e sábado às 11h
(2,76) é mais cheio que o pico de segunda, terça ou quarta.

São dois negócios no mesmo endereço, e a média não descreve nenhum dos dois. Pior:
a média levou a uma recomendação errada — "abrir às 10h em vez de 9h" mataria a
melhor manhã da semana, porque sábado às 9h já tem 1,98 simultâneos.

COMO CALCULA
Cada agendamento ocupa cadeira do início até início+duração. O script distribui
essa duração pelas horas que ela atravessa, soma por (dia da semana, hora) e
divide pelo número de datas distintas daquele dia — o resultado é quantos
atendimentos, em média, estão acontecendo ao mesmo tempo naquela hora.

Cancelados ficam de fora: reservam agenda, não ocupam cadeira.

USO
    python3 scripts/densidade_dow.py [--unidade escova|spa]
"""
from __future__ import annotations
import argparse, json, sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOW = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
H_INI, H_FIM = 9, 21


def brl(v: float) -> str:
    return f"R$ {v:,.0f}".replace(",", ".")


def carregar(unidade: str):
    sub = "" if unidade == "escova" else f"{unidade}/"
    p = REPO / "data" / sub / "agendamentos_ano_cache.json"
    if not p.exists():
        return None, p
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("payload") or [], p
    except Exception:
        return None, p


def calcular(itens):
    ocup = defaultdict(float)
    receita = defaultdict(float)
    datas = defaultdict(set)
    n = 0
    for a in itens:
        status = ((a.get("status") or {}).get("nome") or "")
        if "ancel" in status.lower():
            continue
        ini = a.get("dataHoraInicio")
        if not ini:
            continue
        try:
            t0 = datetime.fromisoformat(ini)
        except Exception:
            continue
        dur = int(a.get("duracaoEmMinutos") or 0) or 30
        t1 = t0 + timedelta(minutes=dur)
        dw = t0.weekday()
        datas[dw].add(t0.date())
        receita[(dw, t0.hour)] += float(a.get("valor") or 0)
        n += 1
        cur = t0
        while cur < t1:
            prox = cur.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            ocup[(dw, cur.hour)] += (min(t1, prox) - cur).total_seconds() / 3600
            cur = prox
    return ocup, receita, datas, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--unidade", default="escova")
    args = ap.parse_args()

    itens, caminho = carregar(args.unidade)
    if itens is None:
        print(f"⚠️  Sem agendamentos em {caminho} — nada a calcular.")
        return 2
    ocup, receita, datas, n = calcular(itens)
    if not n:
        print("⚠️  Nenhum agendamento válido.")
        return 2

    cobertura = ", ".join(f"{DOW[k]}:{len(v)}" for k, v in sorted(datas.items()))
    print(f"📊 {args.unidade.upper()} · {n} agendamentos · dias medidos por DOW → {cobertura}")
    print()
    print("ATENDIMENTOS SIMULTÂNEOS (média) — por dia da semana × hora")
    print("      " + "".join(f"{h:>6}" for h in range(H_INI, H_FIM + 1)))
    picos = {}
    for dw in range(7):
        if not datas[dw]:
            continue
        nd = len(datas[dw])
        linha = f"  {DOW[dw]} "
        melhor = (0.0, None)
        for h in range(H_INI, H_FIM + 1):
            v = ocup[(dw, h)] / nd
            linha += f"{v:6.2f}" if v >= 0.005 else "     ·"
            if v > melhor[0]:
                melhor = (v, h)
        picos[dw] = melhor
        print(linha)

    print()
    print("PICO DE CADA DIA")
    for dw, (v, h) in sorted(picos.items(), key=lambda kv: -kv[1][0]):
        print(f"  {DOW[dw]}  {v:.2f} simultâneos às {h}h")

    # Manhãs vazias: onde abrir mais tarde custaria pouco.
    print()
    print("MANHÃS (9h–11h) — onde abrir mais tarde custaria pouco")
    for dw in range(7):
        if not datas[dw]:
            continue
        nd = len(datas[dw])
        manha = sum(ocup[(dw, h)] for h in (9, 10, 11)) / nd / 3
        marca = "🔴 deserta" if manha < 0.25 else ("🟡 fraca" if manha < 0.8 else "🟢 cheia")
        print(f"  {DOW[dw]}  {manha:.2f} média 9h-11h  {marca}")

    # O que se perde fechando mais cedo.
    print()
    print("O QUE COMEÇA DEPOIS DAS 20h — o custo de fechar às 20h")
    total = 0.0
    for dw in range(7):
        if not datas[dw]:
            continue
        r = receita[(dw, 20)] + receita[(dw, 21)]
        total += r
        if r > 0:
            nd = len(datas[dw])
            print(f"  {DOW[dw]}  {brl(r)} em {nd} dias  →  {brl(r/nd)} por dia")
    print(f"  ─────────  {brl(total)} no período medido")

    print()
    print("A média de todos os dias juntos não descreve nenhum deles. "
          "Leia sempre a linha do dia que você vai escalar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
