#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quem vendeu cada pacote e cada produto — a meta da recepção com nome.

POR QUE ESTE SCRIPT EXISTE (16/09/2026)

As metas das duas recepcionistas do Escova são nominais e por categoria:
R$ 7.200 em pacotes, R$ 4.200 em Fast Retoque, R$ 1.800 em produtos, cada uma.
Elas sabem disso. O painel não sabia — mostrava só o total da loja, e a
pergunta "quanto a Mirian já fez?" não tinha resposta em lugar nenhum.

Tinha, sim: o Trinks grava `IdProfissionalQueRealizouAVenda` em cada linha de
pacote e de produto da transação. O campo estava no cache desde 23/07 e nunca
foi lido. Nenhum conector novo, nenhuma chamada de API a mais.

O QUE NÃO DÁ PARA ATRIBUIR, E POR QUÊ

Fast Retoque é SERVIÇO, não item de balcão. A transação registra
`idProfissionalQueRealizouServico` — quem executou, não quem vendeu. Atribuir
a venda a quem passou a escova seria inventar um dado que não existe. Então o
retoque aparece só no total da loja, e isso fica dito no card, não escondido.

ONDE ISTO RODA DE VERDADE

Em `github_refresh.py`, que chama `apurar()` com a lista de transações já
mesclada em memória. O cache em disco guarda o ano MENOS o mês corrente (o mês
é buscado fresco a cada execução e mesclado), então este CLI, que só lê o
cache, **não enxerga o mês corrente**. Serve para conferência histórica; o
número que vale é o que sai no payload.

Uso:
    python3 scripts/balcao_por_pessoa.py                    # confere o histórico
    python3 scripts/balcao_por_pessoa.py --gravar           # grava (sem o mês corrente!)
    python3 scripts/balcao_por_pessoa.py --unidade spa
"""
from __future__ import annotations
import argparse, json, sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
JANELAS = ("dia", "semana", "mes", "ano")


def _dir(unidade: str) -> Path:
    return REPO / "data" / ("" if unidade == "escova" else unidade)


def _carregar(unidade: str):
    base = _dir(unidade)
    dash_p = base / "dashboard_data.json"
    tx_p = base / "transacoes_ano_cache.json"
    if not dash_p.exists() or not tx_p.exists():
        return None, None, dash_p
    dash = json.loads(dash_p.read_text(encoding="utf-8"))
    tx = json.loads(tx_p.read_text(encoding="utf-8")).get("payload") or []
    return dash, tx, dash_p


def _indice_nomes(dash: dict) -> dict:
    """Dois espaços de ID convivem no payload: a chave do prof_meta e o
    id_profissional de dentro dele. As vendas usam ora um, ora outro."""
    idx = {}
    for chave, v in (dash.get("prof_meta") or {}).items():
        nome = v.get("nome")
        if not nome:
            continue
        idx[str(chave)] = (nome, v.get("funcao") or "")
        if v.get("id_profissional"):
            idx[str(v["id_profissional"])] = (nome, v.get("funcao") or "")
    try:
        ov = json.loads((REPO / "data" / "prof_overrides.json").read_text(encoding="utf-8"))
        for pid, nome in (ov.get("profs") or {}).items():
            if nome:
                idx.setdefault(str(pid), (nome, ""))
    except Exception:
        pass
    return idx


def _janelas(hoje: date) -> dict:
    seg = hoje - timedelta(days=hoje.weekday())
    return {
        "dia":    (hoje, hoje),
        "semana": (seg, seg + timedelta(days=6)),
        "mes":    (hoje.replace(day=1), hoje),
        "ano":    (date(hoje.year, 1, 1), hoje),
    }


def apurar(dash: dict, tx: list) -> dict:
    hoje = date.fromisoformat(dash.get("hoje") or date.today().isoformat())
    jan = _janelas(hoje)
    nomes = _indice_nomes(dash)

    # acc[janela][id] = {pac_n, pac_v, prod_n, prod_v}
    acc = {j: defaultdict(lambda: {"pac_n": 0, "pac_v": 0.0, "prod_n": 0, "prod_v": 0.0})
           for j in JANELAS}
    for t in tx:
        bruto = t.get("dataHora") or t.get("dataReferencia")
        if not bruto:
            continue
        try:
            d = datetime.fromisoformat(str(bruto).replace("Z", "+00:00")).date()
        except Exception:
            continue
        linhas = [("pac", p) for p in (t.get("pacotes") or [])]
        linhas += [("prod", p) for p in (t.get("produtos") or [])]
        if not linhas:
            continue
        for j, (ini, fim) in jan.items():
            if not (ini <= d <= fim):
                continue
            for tipo, p in linhas:
                vid = p.get("IdProfissionalQueRealizouAVenda")
                # Venda sem vendedor não vira linha fantasma nem some: cai num
                # balde nomeado, para o total do card fechar com o card de
                # categorias. Somem discretamente é como um dado errado dura.
                chave = str(vid) if vid else "__sem_vendedor__"
                qtd = int(p.get("quantidade") or 1)
                val = float(p.get("valorUnitario") or 0) * qtd
                a = acc[j][chave]
                a[f"{tipo}_n"] += qtd
                a[f"{tipo}_v"] += val

    out = {}
    for j in JANELAS:
        linhas = []
        for chave, a in acc[j].items():
            if chave == "__sem_vendedor__":
                nome, funcao = "Sem vendedor no lançamento", "—"
            else:
                nome, funcao = nomes.get(chave, (f"Não identificado #{chave}", ""))
            linhas.append({
                "id": chave, "nome": nome, "funcao": funcao,
                "pacotes_n": a["pac_n"], "pacotes_v": round(a["pac_v"], 2),
                "produtos_n": a["prod_n"], "produtos_v": round(a["prod_v"], 2),
                "total_v": round(a["pac_v"] + a["prod_v"], 2),
                "identificado": not chave.startswith("__") and chave in nomes,
            })
        linhas.sort(key=lambda x: -x["total_v"])
        out[j] = linhas
    return {
        "_desc": ("Quem vendeu cada pacote e cada produto, do campo "
                  "IdProfissionalQueRealizouAVenda do Trinks. Fast Retoque NÃO entra: "
                  "é serviço, e o Trinks só grava quem executou, não quem vendeu."),
        "gerado_em": datetime.now(timezone(timedelta(hours=-3))).isoformat(timespec="seconds"),  # BRT, nao UTC do runner
        "hoje": hoje.isoformat(),
        "retoque_atribuivel": False,
        "por_janela": out,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--unidade", default="escova", choices=["escova", "spa"])
    ap.add_argument("--gravar", action="store_true")
    args = ap.parse_args()

    dash, tx, dash_p = _carregar(args.unidade)
    if dash is None:
        print(f"⚠️  Faltam arquivos em {dash_p.parent} — nada a calcular.")
        return 2

    bloco = apurar(dash, tx)
    cache_ate = (json.loads((_dir(args.unidade) / "transacoes_ano_cache.json")
                            .read_text(encoding="utf-8")).get("gerado_em") or "?")[:10]
    print(f"⚠️  Lendo só o cache (até {cache_ate}). O mês corrente é buscado fresco "
          f"pelo github_refresh e NÃO está aqui — veja balcao_vendedor no payload.")
    for j in JANELAS:
        linhas = bloco["por_janela"][j]
        if not linhas:
            continue
        print(f"\n== {j.upper()} ==")
        print(f"{'quem vendeu':<40}{'função':<12}{'pac':>5}{'R$':>9}{'prod':>6}{'R$':>9}{'TOTAL':>10}")
        for l in linhas:
            marca = "" if l["identificado"] else "  ⚠"
            print(f"{l['nome'][:39]:<40}{(l['funcao'] or '—')[:11]:<12}"
                  f"{l['pacotes_n']:>5}{l['pacotes_v']:>9.0f}"
                  f"{l['produtos_n']:>6}{l['produtos_v']:>9.0f}{l['total_v']:>10.0f}{marca}")

    if args.gravar:
        dash["balcao_vendedor"] = bloco
        dash_p.write_text(json.dumps(dash, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\n✍️  balcao_vendedor gravado em {dash_p.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
