#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confere se a empresa digital se reuniu ontem — e grita quando nao se reuniu.

As sete tarefas agendadas no PC do Rodrigo deveriam produzir uma ata por cargo
por dia em docs/atas/. Em 20/09/2026 descobrimos que os seis departamentos
tinham rodado UMA vez desde que a agenda foi instalada, e o Conselho quatro
vezes em sete dias. Ninguem percebeu porque a ausencia de uma ata nao faz
barulho nenhum: o arquivo simplesmente nao existe, e nao existir e silencioso.

Este script transforma a ausencia em falha visivel. Roda no GitHub Actions; se
faltar cargo, sai com codigo 1, o run fica vermelho e o GitHub manda e-mail
para o dono do repositorio. E o mesmo canal que o alerta de entrega de midia
ja usa.

Uso:  python scripts/auditoria_agenda.py [--dia AAAA-MM-DD]
"""
from __future__ import annotations

import argparse
import os
import re
from datetime import date, datetime, timedelta, timezone

BRT = timezone(timedelta(hours=-3))
ATAS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "atas")

# Quem deveria comparecer, e o horario que a agenda reserva para cada um.
CARGOS = [
    ("memoria", "07:30"),
    ("marketing", "08:00"),
    ("financeiro", "08:30"),
    ("relacionamento", "09:00"),
    ("pessoas", "09:30"),
    ("operacao-diaria", "11:30"),
    ("conselho", "22:30"),
]


def atas_do_dia(dia: date) -> set[str]:
    if not os.path.isdir(ATAS):
        return set()
    alvo = dia.isoformat()
    achadas = set()
    for nome in os.listdir(ATAS):
        m = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)\.md$", nome)
        if m and m.group(1) == alvo:
            achadas.add(m.group(2))
    return achadas


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dia", help="AAAA-MM-DD (padrao: ontem em BRT)")
    args = ap.parse_args()

    dia = date.fromisoformat(args.dia) if args.dia else (datetime.now(BRT).date() - timedelta(days=1))
    presentes = atas_do_dia(dia)

    print(f"Reuniao de {dia} ({['seg','ter','qua','qui','sex','sab','dom'][dia.weekday()]})")
    faltaram = []
    for cargo, hora in CARGOS:
        if cargo in presentes:
            print(f"  OK       {hora}  {cargo}")
        else:
            print(f"  FALTOU   {hora}  {cargo}")
            faltaram.append(cargo)

    # Sete dias para tras: uma falha isolada e ruido, um padrao e outra coisa.
    print("\nUltimos 7 dias:")
    streak_conselho = 0
    for i in range(7, 0, -1):
        d = dia - timedelta(days=i - 1)
        p = atas_do_dia(d)
        marcas = "".join("#" if c in p else "." for c, _ in CARGOS)
        # Conta so os sete cargos da agenda. docs/atas/ tambem recebe atas
        # avulsas (uma sessao rodando um cargo a mao, com sufixo no nome), e
        # contar len(p) fazia 15/09 aparecer como "8/7".
        n = sum(1 for c, _ in CARGOS if c in p)
        print(f"  {d} {['seg','ter','qua','qui','sex','sab','dom'][d.weekday()]}  {marcas}  ({n}/{len(CARGOS)})")
        streak_conselho = streak_conselho + 1 if "conselho" not in p else 0
    print("  legenda: " + " ".join(c[:4] for c, _ in CARGOS))

    if not faltaram:
        print("\nTodos compareceram.")
        return 0

    print(f"\n{len(faltaram)} de {len(CARGOS)} nao compareceram: {', '.join(faltaram)}")
    if streak_conselho >= 2:
        print(f"E o Conselho ja nao fecha o dia ha {streak_conselho} dias seguidos.")
    print("\nA agenda roda no PC do Rodrigo (tarefas 'FAST\\...' no Agendador de Tarefas).")
    print("Para ver o que aconteceu, abrir no vault:")
    print("  Cerebro_Claude\\Briefings\\_execucoes.log")
    print("Para reinstalar as tarefas, no PowerShell como administrador:")
    print("  powershell -File scripts\\agenda\\instalar_tarefas.ps1")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
