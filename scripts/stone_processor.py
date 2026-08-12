"""Processa CSV extrato Stone e cruza com transações Trinks.
Portable: roda tanto local quanto no GitHub Actions.

Se CSV_PATH existe, retorna dict com dados prontos pro JSON do dashboard.
Se não, retorna None (aba Stone fica com placeholder).
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path


def _pv(s):
    s = str(s or "").replace("R$", "").replace(".", "").replace(",", ".").strip()
    try: return float(s)
    except: return 0.0


def _parse_dt(s):
    if not s: return None
    for fmt in ["%d/%m/%Y", "%d/%m/%Y %H:%M"]:
        try: return datetime.strptime(s[:16] if len(s) > 10 else s[:10], fmt).date()
        except: pass
    return None


def _brl_round(v): return round(float(v or 0), 2)


def processar_stone_csv(csv_path: Path, transacoes_trinks: list) -> dict | None:
    """
    csv_path: Path para o extrato Stone (CSV portal)
    transacoes_trinks: lista de dicts [{"data":date, "meio":str, "valor":float, "cliente":str}, ...]
    """
    if not csv_path.exists():
        return None

    # ==== Ler CSV Stone ====
    recs = []
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            with open(csv_path, encoding=enc, newline="") as f:
                for row in csv.DictReader(f): recs.append(row)
            break
        except Exception:
            continue

    if not recs:
        return None

    # Categorizar
    pix_recebidos = []
    cartao_recebiveis = []
    transfer_stone = []
    debitos_transacao = []
    pix_enviados = []

    for r in recs:
        tipo = r.get("Tipo", "")
        mov = r.get("Movimentação", "")
        origem = r.get("Origem", "")
        if mov == "Crédito" and tipo == "Pix":
            pix_recebidos.append(r)
        elif mov == "Crédito" and tipo == "Transação" and origem and origem != "Desconhecido":
            pix_recebidos.append(r)
        elif mov == "Crédito" and tipo == "Recebível de Cartão":
            cartao_recebiveis.append(r)
        elif mov == "Crédito" and tipo == "Transferência entre contas Stone":
            transfer_stone.append(r)
        elif mov == "Débito" and tipo == "Transação":
            debitos_transacao.append(r)
        elif mov == "Débito" and tipo == "Pix":
            pix_enviados.append(r)

    pix_bruto = sum(_pv(r["Valor"]) for r in pix_recebidos)
    pix_tarifa = sum(_pv(r["Tarifa"]) for r in pix_recebidos)
    pix_liq = pix_bruto - pix_tarifa
    cartao_liq = sum(_pv(r["Valor"]) for r in cartao_recebiveis)
    transf_v = sum(_pv(r["Valor"]) for r in transfer_stone)
    saidas_v = -sum(_pv(r["Valor"]) for r in debitos_transacao)

    datas = sorted({_parse_dt(r["Data"]) for r in recs if _parse_dt(r["Data"])})
    ini = datas[0] if datas else None
    fim = datas[-1] if datas else None

    # ==== Filtrar Trinks pelo mesmo período e match PIX ====
    trinks_periodo = [t for t in transacoes_trinks
                      if t.get("data") and ini and fim and ini <= t["data"] <= fim]
    trinks_pix = [t for t in trinks_periodo if t["meio"] == "PIX"]
    trinks_cartoes = [t for t in trinks_periodo if t["meio"] in
                      ("Mastercard", "Visa", "Elo Débito", "Maestro/Redeshop",
                       "Visa Electron", "American Express", "Elo Crédito", "Hipercard")]

    pix_trinks_tot = sum(t["valor"] for t in trinks_pix)
    cartao_trinks_tot = sum(t["valor"] for t in trinks_cartoes)

    # Match PIX por (data, valor ± R$ 0,50)
    matches_pix = []
    orfaos_stone_pix = []
    usados_trinks = set()
    for s in pix_recebidos:
        ds = _parse_dt(s["Data"])
        vs = _pv(s["Valor"])
        best_i, best_diff = None, 1e9
        for i, t in enumerate(trinks_pix):
            if i in usados_trinks: continue
            if t["data"] != ds: continue
            diff = abs(t["valor"] - vs)
            if diff < best_diff and diff <= 0.5:
                best_diff, best_i = diff, i
        if best_i is not None:
            usados_trinks.add(best_i)
            matches_pix.append({
                "data": ds.isoformat(), "valor": vs,
                "cliente_trinks": trinks_pix[best_i]["cliente"],
                "origem_stone": s.get("Origem", ""),
            })
        else:
            orfaos_stone_pix.append({
                "data": ds.isoformat() if ds else None,
                "valor": vs, "origem": s.get("Origem", ""),
                "tarifa": _pv(s["Tarifa"]),
            })
    orfaos_trinks_pix = [
        {"data": trinks_pix[i]["data"].isoformat(), "valor": trinks_pix[i]["valor"],
         "cliente": trinks_pix[i]["cliente"]}
        for i in range(len(trinks_pix)) if i not in usados_trinks
    ]

    # Recebíveis cartão (só listagem)
    recebiveis_lista = [{
        "data": _parse_dt(r["Data"]).isoformat() if _parse_dt(r["Data"]) else None,
        "valor": _pv(r["Valor"]),
    } for r in cartao_recebiveis]
    recebiveis_lista.sort(key=lambda x: x["data"] or "")

    # A receber D+30 (estimativa: cartões trinks × 96,5% − já recebido)
    a_receber_estim = max(0, cartao_trinks_tot * 0.965 - cartao_liq)

    return {
        "periodo_ini": ini.isoformat() if ini else None,
        "periodo_fim": fim.isoformat() if fim else None,
        "total_lancamentos": len(recs),
        "pix": {
            "recebidos_n": len(pix_recebidos),
            "bruto": _brl_round(pix_bruto),
            "tarifa": _brl_round(pix_tarifa),
            "liquido": _brl_round(pix_liq),
            "taxa_pct": round(pix_tarifa / max(pix_bruto, 1) * 100, 3),
            "trinks_registrado_n": len(trinks_pix),
            "trinks_registrado_v": _brl_round(pix_trinks_tot),
            "matches_n": len(matches_pix),
            "orfaos_stone": orfaos_stone_pix[:30],
            "orfaos_trinks": orfaos_trinks_pix[:30],
        },
        "cartao": {
            "recebiveis_n": len(cartao_recebiveis),
            "recebiveis_liquido": _brl_round(cartao_liq),
            "trinks_bruto_periodo": _brl_round(cartao_trinks_tot),
            "a_receber_estim": _brl_round(a_receber_estim),
            "recebiveis_lista": recebiveis_lista,
        },
        "outros": {
            "transferencias_stone": _brl_round(transf_v),
            "saidas_transacao": _brl_round(saidas_v),
            "pix_enviados_n": len(pix_enviados),
            "pix_enviados_v": _brl_round(sum(_pv(r["Valor"]) for r in pix_enviados)),
        },
    }
