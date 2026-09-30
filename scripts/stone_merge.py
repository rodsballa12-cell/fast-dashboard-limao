# -*- coding: utf-8 -*-
"""Soma um extrato Stone recem-exportado ao historico, em vez de substitui-lo.

Por que existe: a exportacao da Stone traz uma janela (tipicamente o mes
corrente), nao o historico inteiro. Trocar `data/stone_extrato.csv` pelo
arquivo novo apaga os meses anteriores — e com eles a visao do ano, o
historico da Reserva Stone e a base de recebiveis em D+30. Entre 19/09 e
30/09/2026 isso foi feito tres vezes a mao, sempre com o mesmo cuidado
manual; o cuidado agora mora aqui.

Como usar: largue o CSV exportado em `data/stone_entrada/` e rode

    python3 scripts/stone_merge.py

O script soma, descarta as linhas repetidas, ordena do mais recente para o
mais antigo, grava `data/stone_extrato.csv` e apaga o que foi consumido. Roda
sozinho pelo workflow `stone_entrada.yml` quando um CSV e commitado naquela
pasta.

Garantias:
- Nunca remove lancamento. A saida e sempre a uniao dos dois lados.
- Idempotente: rodar de novo com o mesmo arquivo nao muda nada.
- Recusa arquivo de OUTRA conta Stone. Um extrato descreve uma conta, e
  misturar duas transforma o dinheiro de uma loja em "nao conciliado" da
  outra — foi exatamente o que aconteceu com o painel do Spa em 25/09/2026.
  Arquivo recusado fica na pasta, intacto, para uma pessoa olhar.
- Formato preservado: UTF-8 sem BOM e fim de linha CRLF, como a Stone entrega.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import io
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINO = ROOT / "data" / "stone_extrato.csv"
ENTRADA = ROOT / "data" / "stone_entrada"

COL_DATA = "Data"
COL_HORA = "Horário"
COLS_CONTA = ("Destino Conta", "Origem Conta")
DESCONHECIDO = "Desconhecido"


def ler(path: Path) -> tuple[list[str], list[tuple[str, ...]]]:
    """Le um CSV da Stone. Tolera BOM; devolve (cabecalho, linhas nao vazias)."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        linhas = list(csv.reader(fh))
    if not linhas:
        return [], []
    return linhas[0], [tuple(x) for x in linhas[1:] if any(v.strip() for v in x)]


def idx(cab: list[str], nome: str) -> int:
    try:
        return cab.index(nome)
    except ValueError:
        raise SystemExit(f"[stone_merge] coluna '{nome}' nao existe no CSV. Cabecalho: {cab}")


def quando(linha: tuple[str, ...], i_data: int, i_hora: int) -> datetime.datetime:
    """Momento do lancamento. A coluna Data traz 'dd/mm/aaaa HH:MM' e a coluna
    Horário traz o segundo e o milissegundo — juntas ordenam sem empate."""
    d = datetime.datetime.strptime(linha[i_data][:10], "%d/%m/%Y").date()
    try:
        h = datetime.datetime.strptime(linha[i_hora][:12], "%H:%M:%S.%f").time()
    except ValueError:
        try:
            h = datetime.datetime.strptime(linha[i_data][11:16], "%H:%M").time()
        except ValueError:
            h = datetime.time(0, 0)
    return datetime.datetime.combine(d, h)


def conta_dominante(cab: list[str], linhas: list[tuple[str, ...]]) -> str | None:
    """A conta Stone do extrato: a mais frequente entre origem e destino.

    Nao exige que TODA linha seja da mesma conta — a sangria para o banco
    principal traz a conta de destino do outro lado, e isso e normal.
    """
    c = Counter()
    for i in (idx(cab, k) for k in COLS_CONTA):
        for linha in linhas:
            v = (linha[i] or "").strip()
            if v and v != DESCONHECIDO:
                c[v] += 1
    return c.most_common(1)[0][0] if c else None


def escrever(path: Path, cab: list[str], linhas: list[tuple[str, ...]]) -> None:
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
    w.writerow(cab)
    w.writerows(linhas)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(buf.getvalue())


def main() -> int:
    ap = argparse.ArgumentParser(description="Soma extratos Stone novos ao historico.")
    ap.add_argument("--dry-run", action="store_true", help="mostra o que faria, sem gravar nem apagar")
    ap.add_argument("--entrada", default=str(ENTRADA), help="pasta de entrada")
    ap.add_argument("--destino", default=str(DESTINO), help="arquivo historico")
    args = ap.parse_args()

    entrada, destino = Path(args.entrada), Path(args.destino)
    novos = sorted(p for p in entrada.glob("*") if p.suffix.lower() == ".csv")
    if not novos:
        print("[stone_merge] pasta de entrada vazia. Nada a fazer.")
        return 0

    if not destino.exists():
        raise SystemExit(f"[stone_merge] {destino} nao existe. Nao vou criar historico do zero sem uma pessoa olhar.")

    cab, antigas = ler(destino)
    i_data, i_hora = idx(cab, COL_DATA), idx(cab, COL_HORA)
    conta_ok = conta_dominante(cab, antigas)
    vistos = set(antigas)
    total_antes = len(antigas)
    acumulado = list(antigas)

    consumidos: list[Path] = []
    recusados: list[tuple[Path, str]] = []

    for p in novos:
        cab_n, linhas_n = ler(p)
        if not linhas_n:
            recusados.append((p, "arquivo sem lancamento"))
            continue
        if cab_n != cab:
            recusados.append((p, "cabecalho diferente do historico — nao parece extrato da Stone"))
            continue
        conta_n = conta_dominante(cab_n, linhas_n)
        if conta_ok and conta_n and conta_n != conta_ok:
            recusados.append((p, f"conta {conta_n}, e o historico e da conta {conta_ok}. "
                                 "Se for o terminal de outra loja, o arquivo dela e data/<unidade>/stone_extrato.csv"))
            continue

        add = [x for x in linhas_n if x not in vistos]
        vistos.update(add)
        acumulado.extend(add)
        consumidos.append(p)
        print(f"[stone_merge] {p.name}: {len(linhas_n)} lancamentos lidos · {len(add)} novos · "
              f"{len(linhas_n) - len(add)} ja tinha")

    for p, motivo in recusados:
        print(f"[stone_merge] RECUSADO {p.name}: {motivo}", file=sys.stderr)

    if not consumidos:
        print("[stone_merge] nenhum arquivo aproveitado.")
        return 1 if recusados else 0

    acumulado.sort(key=lambda r: quando(r, i_data, i_hora), reverse=True)
    novos_n = len(acumulado) - total_antes
    ini, fim = quando(acumulado[-1], i_data, i_hora), quando(acumulado[0], i_data, i_hora)
    resumo = (f"{total_antes} -> {len(acumulado)} lancamentos (+{novos_n}) · "
              f"cobertura {ini.date().strftime('%d/%m')} a {fim.strftime('%d/%m %Hh%M')}")

    if args.dry_run:
        print(f"[stone_merge] (dry-run) {resumo}")
        print(f"[stone_merge] (dry-run) apagaria: {', '.join(p.name for p in consumidos)}")
        return 0

    escrever(destino, cab, acumulado)
    for p in consumidos:
        p.unlink()
    print(f"[stone_merge] {resumo}")
    print(f"[stone_merge] consumidos e apagados: {', '.join(p.name for p in consumidos)}")
    print(f"RESUMO={resumo}")
    return 1 if recusados else 0


if __name__ == "__main__":
    sys.exit(main())
