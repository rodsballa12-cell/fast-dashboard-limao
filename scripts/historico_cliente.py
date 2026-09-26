#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Histórico completo de UMA cliente: tudo que ela agendou e tudo que pagou.

Por que existe: o painel foi feito para olhar o negócio inteiro, e os caches do
repositório guardam o ano menos o mês corrente — os últimos dias só existem na
API. Quando o Rodrigo pergunta "o que a fulana já consumiu", a resposta tem que
varrer TODOS os dias, inclusive os de hoje e ontem, e para isso é preciso ir na
API na hora.

Uso:
    python scripts/historico_cliente.py --nome "Gabriela Cristina"
    python scripts/historico_cliente.py --id 91481841
    python scripts/historico_cliente.py --nome "Maria" --desde 2026-08-01

Nome é busca parcial e sem acento: "gabriela cristina" acha
"Gabriela Cristina Resende". Se mais de uma cliente casar, lista as candidatas
e não escolhe sozinho.

Env obrigatório: TRINKS_API_KEY e TRINKS_ESTABELECIMENTO_ID (os mesmos do
refresh). Roda pelo workflow historico_cliente.yml, que já os fornece.

NÃO imprime CPF nem telefone completo. O log do workflow fica guardado no
GitHub, e nada que identifique a cliente além do nome precisa estar lá para
responder à pergunta.
"""
from __future__ import annotations

import argparse
import sys
import unicodedata
from collections import Counter
from datetime import date, datetime

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from trinks_common import TrinksClient  # noqa: E402

# 23/07/2026 foi o primeiro dia de operação da Escova. Nada existe antes disso.
PRIMEIRO_DIA = date(2026, 7, 22)


def norm(s) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(s.split())


def brl(v) -> str:
    return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def achar_cliente(t: TrinksClient, nome: str | None, cid: int | None) -> dict | None:
    if cid:
        det = t.get(f"/v1/clientes/{cid}")
        d = det.get("data") if isinstance(det, dict) and "data" in det else det
        if d:
            return d if isinstance(d, dict) else d[0]
        print(f"Nenhuma cliente com id {cid}.")
        return None

    alvo = norm(nome)
    todos = list(t.paginate("/v1/clientes"))
    hits = [c for c in todos if alvo in norm(c.get("nome"))]
    print(f"[busca] {len(todos)} clientes cadastradas · {len(hits)} com \"{nome}\" no nome")
    if not hits:
        # ajuda o próximo passo em vez de só dizer não
        primeiro = alvo.split()[0] if alvo.split() else alvo
        quase = sorted({c.get("nome") for c in todos if primeiro in norm(c.get("nome"))})
        if quase:
            print(f"  Nenhuma exata. Com \"{primeiro}\": " + " · ".join(quase[:15]))
        return None
    if len(hits) > 1:
        # Escolher por conta própria arrisca entregar o histórico da pessoa
        # errada — pior que não responder.
        print("  Mais de uma casou. Rode de novo com --id de uma delas:")
        for c in hits:
            print(f"    id={c['id']}  {c['nome']}  (cadastro {str(c.get('dataCadastro',''))[:10]})")
        return None
    return hits[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nome", help="busca parcial, sem precisar de acento")
    ap.add_argument("--id", type=int, help="id da cliente no Trinks")
    ap.add_argument("--desde", help="AAAA-MM-DD (padrão: abertura da loja)")
    ap.add_argument("--unidade", default="escova", choices=["escova", "spa"], help="qual unidade (default: escova)")
    args = ap.parse_args()
    if not args.nome and not args.id:
        print("Informe --nome ou --id.")
        return 2

    ini = date.fromisoformat(args.desde) if args.desde else PRIMEIRO_DIA
    fim = date.today()

    t = TrinksClient(unidade=args.unidade)
    cli = achar_cliente(t, args.nome, args.id)
    if not cli:
        return 1

    cid, cnome = cli["id"], cli.get("nome", "?")
    cad = str(cli.get("dataCadastro", ""))[:10]
    print(f"\n{'='*70}\nCLIENTE  {cnome}   (id {cid})")
    print(f"Cadastro {cad} · janela consultada {ini} a {fim}\n{'='*70}")

    # A API não filtra agendamento/transação por cliente, então varre a janela
    # inteira e filtra aqui. É a mesma varredura que o refresh já faz todo dia.
    print("[api] buscando agendamentos...")
    agend = [a for a in t.paginate("/v1/agendamentos",
                                   {"dataInicio": ini.isoformat(), "dataFim": fim.isoformat()})
             if (a.get("cliente") or {}).get("id") == cid]
    print("[api] buscando transacoes...")
    transac = [x for x in t.paginate("/v1/transacoes",
                                     {"dataInicio": ini.isoformat(), "dataFim": fim.isoformat()})
               if (x.get("cliente") or {}).get("id") == cid]

    print(f"\n--- AGENDAMENTOS ({len(agend)}) ---")
    if not agend:
        print("  nenhum")
    for a in sorted(agend, key=lambda x: x.get("dataHoraInicio") or ""):
        q = str(a.get("dataHoraInicio", ""))[:16].replace("T", " ")
        st = (a.get("status") or {}).get("nome", "?")
        sv = (a.get("servico") or {}).get("nome", "?")
        pr = ((a.get("profissional") or {}).get("nome") or "?").strip()
        print(f"  {q}  {st:14s} {sv:36s} {brl(a.get('valor')):>12s}  {pr}")

    print(f"\n--- O QUE FOI PAGO ({len(transac)} transacoes) ---")
    if not transac:
        print("  nenhuma")
    total = 0.0
    itens: Counter = Counter()
    for x in sorted(transac, key=lambda y: y.get("dataHora") or ""):
        q = str(x.get("dataHora", ""))[:16].replace("T", " ")
        tot = float(x.get("totalPagar") or 0)
        total += tot
        desc = float(x.get("descontos") or 0)
        print(f"  {q}  total {brl(tot)}" + (f"  (desconto {brl(desc)})" if desc else ""))
        for s in (x.get("servicos") or []):
            itens[s.get("nome", "?")] += 1
            print(f"       servico  {s.get('nome','?'):40s} {brl(s.get('preco')):>12s}")
        for p in (x.get("produtos") or []):
            itens[f"[produto] {p.get('nome','?')}"] += 1
            print(f"       produto  {p.get('nome','?'):40s} {brl(p.get('precoUnitario') or p.get('preco')):>12s}")
        for p in (x.get("pacotes") or []):
            itens[f"[pacote] {p.get('nome','?')}"] += 1
            print(f"       pacote   {p.get('nome','?'):40s} {brl(p.get('preco')):>12s}")
        for f in (x.get("formasPagamentos") or []):
            print(f"       pagou    {f.get('nome','?'):40s} {brl(f.get('valor')):>12s}")

    print(f"\n--- RESUMO ---")
    print(f"  visitas pagas ....... {len(transac)}")
    print(f"  total gasto ......... {brl(total)}")
    if transac:
        print(f"  ticket medio ........ {brl(total/len(transac))}")
        dias = sorted(str(x.get('dataHora',''))[:10] for x in transac)
        print(f"  primeira visita ..... {dias[0]}")
        print(f"  ultima visita ....... {dias[-1]}")
        try:
            print(f"  dias sem vir ........ {(fim - date.fromisoformat(dias[-1])).days}")
        except Exception:
            pass
    if itens:
        print("  o que consumiu:")
        for nome_item, n in itens.most_common():
            print(f"     {n}x  {nome_item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
