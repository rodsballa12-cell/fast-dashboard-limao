#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Saldo de pacotes por cliente -> data/recepcao_pacotes.json.enc (cofre da recepcao).

A fonte e o relatorio do Trinks  Pacotes > Saldo > Visualizar por Clientes
(coluna "Qtd a consumir"). A API do Trinks NAO entrega esse saldo, entao o dado
entra por arquivo, como o extrato da Stone. Pacote nao tem validade: a lista e
de quem ainda tem sessao a consumir.

Entrada: TSV com 5 colunas, separadas por TAB, sem cabecalho:
    unidade(escova|spa)  cliente  pacote  servico  qtd_a_consumir

Uso:  python scripts/recepcao_pacotes.py <arquivo.tsv> [AAAA-MM-DD da leitura]
Depois: git add data/recepcao_pacotes.json.enc e push (a senha e a mesma da
recepcao: FAST_RECEPCAO_SENHA em .cofre/chaves.env).
"""
import csv
import json
import pathlib
import sys
from datetime import date

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from recepcao_gerar import senha  # noqa: E402
from cofre import cifrar  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    posicao = sys.argv[2] if len(sys.argv) > 2 else date.today().isoformat()
    s = senha()
    if not s:
        print("ERRO: falta FAST_RECEPCAO_SENHA em .cofre/chaves.env")
        return 1
    grupos: dict = {}
    n = 0
    with open(sys.argv[1], encoding="utf-8", newline="") as f:
        for lin in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if len(lin) != 5:
                print(f"ERRO: linha com {len(lin)} colunas (esperado 5): {lin}")
                return 1
            u, cli, pac, serv, qtd = [c.strip() for c in lin]
            if u not in ("escova", "spa"):
                print(f"ERRO: unidade invalida '{u}'")
                return 1
            grupos.setdefault((u, cli, pac), []).append({"servico": serv, "restante": int(qtd)})
            n += 1
    saida = {"posicao": posicao, "fonte": "Trinks · Pacotes · Saldo (por cliente)",
             "escova": [], "spa": []}
    for (u, cli, pac), itens in sorted(grupos.items(), key=lambda k: (k[0][0], k[0][1].lower(), k[0][2])):
        saida[u].append({"cliente": cli, "pacote": pac, "itens": itens})
    enc = REPO / "data" / "recepcao_pacotes.json.enc"
    enc.write_bytes(cifrar(json.dumps(saida, ensure_ascii=False).encode("utf-8"), s))
    print(f"{n} linhas · escova: {len(saida['escova'])} pacotes · spa: {len(saida['spa'])} pacotes · posicao {posicao}")
    print(f"gravado {enc.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
