#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comissão de cada profissional por QUINZENA DE PAGAMENTO, a partir do Trinks.

POR QUE EXISTE (17/11/2026)
O Rodrigo passou a receber as notas fiscais das profissionais por um Microsoft
Forms, e quer uma aba no painel que mostre, quinzena a quinzena, o que o Trinks
diz que cada uma tem a receber ao lado do valor que veio na nota. Este script
faz o lado Trinks; `notas_forms.py` faz o lado nota; a aba "Comissões" do
index.html junta os dois.

A REGRA DA QUINZENA (dita pelo Rodrigo em 17/11/2026)
    1ª quinzena: dia 1 ao dia 14   -> paga no dia 15
    2ª quinzena: dia 15 ao último  -> paga no dia 30 (fevereiro: último dia)
A nota tem de chegar até o dia do pagamento. ATENÇÃO: até 17/11 a conciliação
contra os Pix (`conciliacao_comissoes.py`) cortava em 1–15 / 16–fim. As duas
agora importam a regra DESTE arquivo — uma regra só, para os números se
conversarem.

COMO CALCULA (a mesma conta da conciliação, que bate com os Pix pagos)
    serviço do Trinks (preço; serviço de pacote pelo preço de tabela)
      × taxa da categoria em data/comissoes.json  (Spa: 25% uniforme)
    pela data de referência da transação.
É REFERÊNCIA para conferir a nota, não a decisão de pagamento: a regra de
comissão não está cadastrada por profissional no Trinks (`comissoes.habilitado`
falso). Quem extrai o valor a pagar do Trinks é o Lucas.

USO
    python3 scripts/comissao_quinzena.py                 # imprime a quinzena atual
    python3 scripts/comissao_quinzena.py --gravar        # grava o bloco nas 3 unidades
Roda depois do github_refresh/consolida_dashboard, como o densidade_dow.
"""
from __future__ import annotations

import argparse
import calendar
import collections
import datetime as dt
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
N_QUINZENAS = 6           # a atual + as 5 anteriores (3 meses)
TAXA_SPA = 0.25           # "SPA uniforme 25% em todas as categorias" (comissoes.json)
UNIDADES = {"escova": RAIZ / "data", "spa": RAIZ / "data" / "spa"}


# ------------------------------------------------------------------ calendário
def quinzena(d: dt.date) -> tuple[int, int, int]:
    """(ano, mês, 1|2) da quinzena de pagamento em que o dia `d` cai."""
    return (d.year, d.month, 1 if d.day <= 14 else 2)


def limites(q: tuple[int, int, int]) -> tuple[dt.date, dt.date]:
    y, m, h = q
    ultimo = calendar.monthrange(y, m)[1]
    if h == 1:
        return dt.date(y, m, 1), dt.date(y, m, 14)
    return dt.date(y, m, 15), dt.date(y, m, ultimo)


def dia_pagamento(q: tuple[int, int, int]) -> dt.date:
    y, m, h = q
    if h == 1:
        return dt.date(y, m, 15)
    return dt.date(y, m, min(30, calendar.monthrange(y, m)[1]))


def anterior(q):
    y, m, h = q
    if h == 2:
        return (y, m, 1)
    return (y - 1, 12, 2) if m == 1 else (y, m - 1, 2)


def qid(q) -> str:
    return f"{q[0]}-{q[1]:02d}-Q{q[2]}"


def rotulo(q) -> str:
    ini, fim = limites(q)
    return f"{ini.day:02d} a {fim.day:02d}/{fim.month:02d}"


# ------------------------------------------------------------------ leitura
def _ler(p: Path, padrao=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _data_tx(tx) -> dt.date | None:
    s = tx.get("dataReferencia") or tx.get("dataHora")
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(str(s)[:19]).date()
    except ValueError:
        return None


def devido(unidade: str, pasta: Path):
    """{quinzena: {nome: {n_serv, base, base_pacote, comissao}}} e o último dia com dado."""
    regras = _ler(RAIZ / "data" / "comissoes.json", {}) or {}
    taxa = {k.lower().strip(): v for k, v in (regras.get("por_categoria") or {}).items()}
    padrao = regras.get("regra_padrao_pct", 0.30)
    over = ((_ler(RAIZ / "data" / "prof_overrides.json", {}) or {}).get("profs") or {})
    pm = ((_ler(pasta / "profissionais_cache.json", {}) or {}).get("payload") or {}).get("prof_map", {}) or {}
    cat_preco = {s.get("id"): float(s.get("preco") or 0)
                 for s in ((_ler(pasta / "servicos_cache.json", {}) or {}).get("payload") or [])
                 if isinstance(s, dict)}
    cache = _ler(pasta / "transacoes_ano_cache.json")
    if cache is None:
        return None, None
    out = collections.defaultdict(lambda: collections.defaultdict(
        lambda: {"n_serv": 0, "base": 0.0, "base_pacote": 0.0, "comissao": 0.0}))
    ate = None
    for tx in (cache.get("payload") or []):
        d = _data_tx(tx)
        if not d:
            continue
        ate = d if ate is None or d > ate else ate
        for s in tx.get("servicos") or []:
            pid = s.get("idProfissionalQueRealizouServico")
            if not pid:
                continue
            o = over.get(str(pid))
            nome_over = o if isinstance(o, str) else (o or {}).get("nome") if isinstance(o, dict) else None
            nome = pm.get(str(pid)) or nome_over or f"Desligada #{pid}"
            preco = float(s.get("preco") or 0)
            pacote = preco == 0
            v = preco or cat_preco.get(s.get("id"), 0)
            t = TAXA_SPA if unidade == "spa" else taxa.get((s.get("categoria") or "").lower().strip(), padrao)
            r = out[quinzena(d)][nome]
            r["n_serv"] += 1
            r["base"] += v
            if pacote:
                r["base_pacote"] += v
            r["comissao"] += v * t
    return out, ate


def bloco(unidade: str, pasta: Path, hoje: dt.date) -> dict | None:
    dev, ate = devido(unidade, pasta)
    if dev is None:
        return None
    qs, q = [], quinzena(hoje)
    for _ in range(N_QUINZENAS):
        qs.append(q)
        q = anterior(q)
    quinzenas = []
    for q in qs:
        ini, fim = limites(q)
        pag = dia_pagamento(q)
        profs = [{"nome": n, "unidade": unidade, "n_serv": r["n_serv"],
                  "base": round(r["base"], 2), "base_pacote": round(r["base_pacote"], 2),
                  "comissao": round(r["comissao"], 2)}
                 for n, r in (dev.get(q) or {}).items() if r["comissao"] >= 0.01]
        profs.sort(key=lambda x: -x["comissao"])
        quinzenas.append({
            "id": qid(q), "rotulo": rotulo(q), "ini": ini.isoformat(), "fim": fim.isoformat(),
            "pagamento": pag.isoformat(),
            # aberta = a quinzena ainda está correndo; o valor vai mudar
            "situacao": "aberta" if hoje <= fim else ("a_pagar" if hoje <= pag else "vencida"),
            "trinks_ate": ate.isoformat() if ate else None,
            "total_comissao": round(sum(p["comissao"] for p in profs), 2),
            "profissionais": profs,
        })
    return {
        "gerado_em": dt.datetime.now(dt.timezone(dt.timedelta(hours=-3))).isoformat(timespec="seconds"),
        "regra": "1ª quinzena: dia 1 a 14, paga dia 15 · 2ª: dia 15 ao último, paga dia 30. "
                 "Comissão = serviço × taxa da categoria (data/comissoes.json; Spa 25%). Referência, não decisão.",
        "trinks_ate": ate.isoformat() if ate else None,
        "quinzenas": quinzenas,
    }


def consolidar(blocos: dict) -> dict | None:
    validos = {u: b for u, b in blocos.items() if b}
    if not validos:
        return None
    base = next(iter(validos.values()))
    quinzenas = []
    for i, q in enumerate(base["quinzenas"]):
        profs = []
        for b in validos.values():
            profs += b["quinzenas"][i]["profissionais"]
        profs.sort(key=lambda x: -x["comissao"])
        quinzenas.append({**q, "profissionais": profs,
                          "total_comissao": round(sum(p["comissao"] for p in profs), 2),
                          "trinks_ate": min((b["quinzenas"][i]["trinks_ate"] or "") for b in validos.values()) or None})
    return {**base, "quinzenas": quinzenas, "unidades": sorted(validos),
            "trinks_ate": min((b["trinks_ate"] or "") for b in validos.values()) or None}


def gravar(rel: Path, b: dict) -> bool:
    p = RAIZ / rel
    d = _ler(p)
    if not isinstance(d, dict):
        print(f"[comissao_quinzena] {rel} ausente (cofre fechado?) — não gravei")
        return False
    d["comissoes_quinzena"] = b
    p.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gravar", action="store_true")
    ap.add_argument("--hoje", help="AAAA-MM-DD (teste)")
    a = ap.parse_args()
    hoje = dt.date.fromisoformat(a.hoje) if a.hoje else dt.datetime.now(dt.timezone(dt.timedelta(hours=-3))).date()

    blocos = {u: bloco(u, p, hoje) for u, p in UNIDADES.items()}
    blocos["consolidado"] = consolidar({"escova": blocos["escova"], "spa": blocos["spa"]})
    destino = {"escova": Path("data/dashboard_data.json"), "spa": Path("data/spa/dashboard_data.json"),
               "consolidado": Path("data/consolidado/dashboard_data.json")}
    falhou = False
    for u, b in blocos.items():
        if not b:
            print(f"[comissao_quinzena] {u}: sem transacoes_ano_cache.json (cofre fechado?)")
            falhou = True
            continue
        q = b["quinzenas"][0]
        print(f"[comissao_quinzena] {u}: {q['rotulo']} (paga {q['pagamento'][8:10]}/{q['pagamento'][5:7]}) "
              f"{len(q['profissionais'])} profissionais, R$ {q['total_comissao']:,.2f} até {b['trinks_ate']}")
        if a.gravar and not gravar(destino[u], b):
            falhou = True
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main())
