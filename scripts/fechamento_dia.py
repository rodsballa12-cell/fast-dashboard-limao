#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confere o fechamento de um dia e procura a origem de uma diferenca.

Quando o caixa do Rodrigo nao bate com o Trinks, a pergunta nao e "quanto deu"
— o painel ja responde isso. E "de onde veio a diferenca". Este script abre o
dia transacao a transacao e, se voce disser o valor que esta sobrando ou
faltando, procura o que explica exatamente aquele numero: uma venda, um
desconto, um item, uma soma de dois, um cancelamento.

Uso:
    python scripts/fechamento_dia.py --data 2026-09-19
    python scripts/fechamento_dia.py --data 2026-09-19 --diferenca 174

Env: TRINKS_API_KEY e TRINKS_ESTABELECIMENTO_ID.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import date
from itertools import combinations

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from trinks_common import TrinksClient  # noqa: E402

TOL = 0.01  # a diferenca tem que bater no centavo; "parecido" nao serve


def brl(v) -> str:
    return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="AAAA-MM-DD")
    ap.add_argument("--diferenca", type=float, help="valor que sobra ou falta no seu fechamento")
    ap.add_argument("--unidade", default="escova", choices=["escova", "spa"], help="qual unidade (default: escova)")
    args = ap.parse_args()
    dia = date.fromisoformat(args.data)

    t = TrinksClient(unidade=args.unidade)
    print(f"[api] unidade={args.unidade} · transacoes e agendamentos de {dia}...")

    # A janela vai ate o dia seguinte e o filtro fino e feito aqui. Motivo: em
    # 19/09/2026 uma consulta com dataInicio = dataFim = 2026-09-19 devolveu
    # ZERO transacoes, com 37 existindo — o /v1/transacoes trata o dataFim como
    # exclusivo, ao contrario do /v1/agendamentos, que devolveu o dia certinho.
    # Pedir a janela maior e filtrar por data aqui funciona nos dois casos e nao
    # depende de adivinhar a regra de cada rota.
    from datetime import timedelta
    janela = {"dataInicio": dia.isoformat(), "dataFim": (dia + timedelta(days=1)).isoformat()}
    alvo_iso = dia.isoformat()
    transac = [x for x in t.paginate("/v1/transacoes", janela)
               if str(x.get("dataHora", ""))[:10] == alvo_iso]
    agend = [a for a in t.paginate("/v1/agendamentos", janela)
             if str(a.get("dataHoraInicio", ""))[:10] == alvo_iso]

    total = sum(float(x.get("totalPagar") or 0) for x in transac)
    descontos = sum(float(x.get("descontos") or 0) for x in transac)
    trocos = sum(float(x.get("troco") or 0) for x in transac)

    print(f"\n{'='*78}\nFECHAMENTO {dia}   ·   {len(transac)} transacoes   ·   total {brl(total)}\n{'='*78}")

    por_meio: dict[str, list[float]] = defaultdict(list)
    for x in transac:
        for f in (x.get("formasPagamentos") or []):
            por_meio[f.get("nome", "?")].append(float(f.get("valor") or 0))
    print("\n--- POR MEIO DE PAGAMENTO (confira cada um contra a sua fonte) ---")
    for nome, vals in sorted(por_meio.items(), key=lambda kv: -sum(kv[1])):
        print(f"  {nome:24s} {len(vals):>3} x   {brl(sum(vals)):>14s}")
    print(f"  {'TOTAL':24s} {len(transac):>3} t   {brl(total):>14s}")
    if descontos:
        print(f"\n  descontos concedidos no dia: {brl(descontos)}")
    if trocos:
        print(f"  trocos dados no dia:         {brl(trocos)}")

    print(f"\n--- TRANSACAO A TRANSACAO ---")
    for x in sorted(transac, key=lambda y: y.get("dataHora") or ""):
        hora = str(x.get("dataHora", ""))[11:16]
        cli = (x.get("cliente") or {}).get("nome", "(sem cliente)")
        tot = float(x.get("totalPagar") or 0)
        desc = float(x.get("descontos") or 0)
        meios = " + ".join(f"{f.get('nome')} {brl(f.get('valor'))}" for f in (x.get("formasPagamentos") or []))
        extra = f"   desconto {brl(desc)}" if desc else ""
        print(f"  {hora}  {brl(tot):>12s}  {cli[:30]:30s}  {meios}{extra}")

    canc = [a for a in agend if (a.get("status") or {}).get("nome") == "Cancelado"]
    if canc:
        vc = sum(float(a.get("valor") or 0) for a in canc)
        print(f"\n--- CANCELADOS ({len(canc)}, somando {brl(vc)}) ---")
        for a in canc:
            print(f"  {str(a.get('dataHoraInicio',''))[11:16]}  {brl(a.get('valor')):>10s}  "
                  f"{(a.get('servico') or {}).get('nome','?'):28s} {(a.get('cliente') or {}).get('nome','?')[:24]}")

    if args.diferenca is None:
        return 0

    alvo = abs(args.diferenca)
    print(f"\n{'='*78}\nCACA A DIFERENCA DE {brl(alvo)}\n{'='*78}")

    achou = False

    def bate(v) -> bool:
        return abs(abs(float(v or 0)) - alvo) <= TOL

    for x in transac:
        if bate(x.get("totalPagar")):
            achou = True
            print(f"  TRANSACAO INTEIRA  {str(x.get('dataHora',''))[11:16]}  "
                  f"{(x.get('cliente') or {}).get('nome','?')}  {brl(x.get('totalPagar'))}")
        if bate(x.get("descontos")):
            achou = True
            print(f"  DESCONTO           {str(x.get('dataHora',''))[11:16]}  "
                  f"{(x.get('cliente') or {}).get('nome','?')}  {brl(x.get('descontos'))}")
        for f in (x.get("formasPagamentos") or []):
            if bate(f.get("valor")):
                achou = True
                print(f"  UM PAGAMENTO       {str(x.get('dataHora',''))[11:16]}  "
                      f"{f.get('nome')}  {brl(f.get('valor'))}  "
                      f"({(x.get('cliente') or {}).get('nome','?')})")
        for chave, rot in (("servicos", "SERVICO"), ("produtos", "PRODUTO"), ("pacotes", "PACOTE")):
            for it in (x.get(chave) or []):
                v = it.get("preco") or it.get("precoUnitario") or it.get("valor")
                if bate(v):
                    achou = True
                    print(f"  {rot:18s} {str(x.get('dataHora',''))[11:16]}  "
                          f"{it.get('nome','?')}  {brl(v)}")

    for nome, vals in por_meio.items():
        if bate(sum(vals)):
            achou = True
            print(f"  MEIO INTEIRO       {nome} do dia soma {brl(sum(vals))}")

    if canc:
        vc = sum(float(a.get("valor") or 0) for a in canc)
        if bate(vc):
            achou = True
            print(f"  TODOS OS CANCELADOS somam {brl(vc)}")
        for r in (2, 3):
            for combo in combinations(canc, r):
                if bate(sum(float(a.get("valor") or 0) for a in combo)):
                    achou = True
                    print("  CANCELADOS  " + " + ".join(
                        f"{(a.get('servico') or {}).get('nome','?')} {brl(a.get('valor'))}" for a in combo))

    # Pares de transacoes: a duplicidade classica (mesma venda lancada duas vezes)
    for a, b in combinations(transac, 2):
        if bate(float(a.get("totalPagar") or 0) + float(b.get("totalPagar") or 0)):
            achou = True
            print(f"  DUAS TRANSACOES    {str(a.get('dataHora',''))[11:16]} {brl(a.get('totalPagar'))}"
                  f"  +  {str(b.get('dataHora',''))[11:16]} {brl(b.get('totalPagar'))}"
                  f"   ({(a.get('cliente') or {}).get('nome','?')[:18]} / "
                  f"{(b.get('cliente') or {}).get('nome','?')[:18]})")

    # --- Busca funda: itens, diferencas e taxa de maquininha ---------------
    # A diferenca raramente e uma venda inteira. Costuma ser um item a mais, um
    # item a menos, dois valores trocados, ou a taxa que a maquininha ja
    # desconta antes de o dinheiro cair.
    itens = []
    for x in transac:
        for chave in ("servicos", "produtos", "pacotes"):
            for it in (x.get(chave) or []):
                v = float(it.get("preco") or it.get("precoUnitario") or it.get("valor") or 0)
                if v > 0:
                    itens.append((v, it.get("nome", "?"), str(x.get("dataHora", ""))[11:16],
                                  (x.get("cliente") or {}).get("nome", "?")))
    for r in (2, 3):
        vistos = set()
        for combo in combinations(itens, r):
            if bate(sum(c[0] for c in combo)):
                assinatura = tuple(sorted(c[0] for c in combo))
                if assinatura in vistos:
                    continue
                vistos.add(assinatura)
                achou = True
                print("  ITENS SOMANDO       " + "  +  ".join(
                    f"{c[1]} {brl(c[0])} ({c[2]} {c[3][:16]})" for c in combo))

    # Dois valores trocados entre si: a diferenca vira o dobro do engano, mas
    # tambem pode aparecer como a propria diferenca entre duas vendas.
    for a, b in combinations(transac, 2):
        d = abs(float(a.get("totalPagar") or 0) - float(b.get("totalPagar") or 0))
        if bate(d):
            achou = True
            print(f"  DIFERENCA ENTRE DUAS VENDAS  {str(a.get('dataHora',''))[11:16]} "
                  f"{brl(a.get('totalPagar'))}  vs  {str(b.get('dataHora',''))[11:16]} "
                  f"{brl(b.get('totalPagar'))}")

    # Taxa Stone: debito 1,46% · credito 1x 2,08% (tabela oficial SIIBELLO).
    DEBITO = {"Maestro/Redeshop", "Visa Electron", "Elo Débito"}
    v_deb = sum(v for nome, vals in por_meio.items() if nome in DEBITO for v in vals)
    v_cred = sum(v for nome, vals in por_meio.items()
                 if nome not in DEBITO and nome not in ("Dinheiro", "PIX") for v in vals)
    taxa = v_deb * 0.0146 + v_cred * 0.0208
    print(f"\n  [referencia] taxa da maquininha no dia: debito {brl(v_deb)} x 1,46% + "
          f"credito {brl(v_cred)} x 2,08% = {brl(taxa)}")
    if bate(taxa):
        achou = True
        print("  >>> A DIFERENCA E EXATAMENTE A TAXA DA MAQUININHA.")

    if not achou:
        print("\n  Nada no Trinks soma exatamente esse valor.")
        print("  Isso empurra a origem para FORA do Trinks: conferencia de cedula,")
        print("  taxa de maquininha descontada na hora, ou uma venda que nunca foi")
        print("  lancada no sistema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
