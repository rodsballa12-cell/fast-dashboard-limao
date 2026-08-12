r"""Refresh completo do dashboard para GitHub Actions.

Puxa dados frescos da API Trinks e grava data/dashboard_data.json.
Não depende de xlsx pré-existentes — faz extract, calcula agregações e escreve JSON direto.

Requer env vars: TRINKS_API_KEY, TRINKS_ESTABELECIMENTO_ID
"""
from __future__ import annotations

import json
import os
import sys
import time
from calendar import monthrange
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

BASE_URL = "https://api.trinks.com"
MIN_INTERVAL = 1.05
META_MENSAL = 60000
DIAS_OP_MES = 26
DOW_NOMES = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = REPO_ROOT / "data" / "dashboard_data.json"


class Trinks:
    def __init__(self):
        api_key = os.environ["TRINKS_API_KEY"]
        eid = os.environ["TRINKS_ESTABELECIMENTO_ID"]
        self.headers = {"X-Api-Key": api_key, "estabelecimentoId": eid, "Accept": "application/json"}
        self.s = requests.Session()
        self._last = 0.0

    def _throttle(self):
        dt = time.time() - self._last
        if dt < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - dt)
        self._last = time.time()

    def get(self, path, params=None, retries=3):
        url = BASE_URL + path
        for i in range(retries):
            self._throttle()
            r = self.s.get(url, headers=self.headers, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(15 * (i + 1)); continue
            if 500 <= r.status_code < 600:
                time.sleep(5 * (i + 1)); continue
            if r.status_code == 404:
                return {"data": [], "totalPages": 0}
            r.raise_for_status()
            return r.json()
        raise RuntimeError(f"Falha após {retries}: {url}")

    def paginate(self, path, params=None):
        params = dict(params or {}); params.setdefault("pageSize", 100)
        page = 1
        while True:
            params["page"] = page
            p = self.get(path, params)
            data = p.get("data", [])
            if not data: return
            for it in data: yield it
            if page >= (p.get("totalPages") or 1): return
            page += 1

    def consumo(self):
        return self.get("/v1/consumo")


def brl_round(v): return round(float(v or 0), 2)


def analisar(agend, transac, ini: date, fim: date):
    """Retorna dict com kpis, categorias, hora_abs, dow, ranking_prof, ranking_serv, meios_pagamento, por_dia_mes, rentabilidade_hora, clientes_top."""
    ag = [a for a in agend if a.get("dataHoraInicio") and ini <= datetime.fromisoformat(a["dataHoraInicio"]).date() <= fim]
    fin = [a for a in ag if (a.get("status") or {}).get("nome") == "Finalizado"]
    canc = [a for a in ag if (a.get("status") or {}).get("nome") == "Cancelado"]
    em_at = [a for a in ag if (a.get("status") or {}).get("nome") == "Em atendimento"]

    tr = [t for t in transac if t.get("dataHora") and ini <= datetime.fromisoformat(t["dataHora"]).date() <= fim]

    # KPIs base
    receita_serv = sum(float(a.get("valor") or 0) for a in fin)
    dias_com_op = len({datetime.fromisoformat(a["dataHoraInicio"]).date() for a in fin})
    unicos = len({(a.get("cliente") or {}).get("id") for a in fin if (a.get("cliente") or {}).get("id")})

    # Categorias + caixa via transações
    caixa = 0.0
    pac_v = pac_n = 0
    prod_v = prod_n = 0
    serv_v = serv_n = 0
    descontos = 0.0
    trocos = 0.0
    mp_c = Counter(); mp_v = defaultdict(float)
    hora_c = defaultdict(int); hora_v = defaultdict(float)

    for t in tr:
        for fp in (t.get("formasPagamentos") or []):
            v = float(fp.get("valor") or 0)
            caixa += v
            nome = fp.get("nome") or "outros"
            mp_c[nome] += 1; mp_v[nome] += v
        for p in (t.get("pacotes") or []):
            q = int(p.get("quantidade") or 1)
            pac_v += float(p.get("valorUnitario") or 0) * q
            pac_n += q
        for p in (t.get("produtos") or []):
            q = int(p.get("quantidade") or 1)
            prod_v += float(p.get("valorUnitario") or 0) * q
            prod_n += q
        for s in (t.get("servicos") or []):
            serv_v += float(s.get("preco") or 0)
            serv_n += 1
        descontos += float(t.get("descontos") or 0)
        trocos += float(t.get("troco") or 0)
        dt = datetime.fromisoformat(t["dataHora"])
        hora_c[dt.hour] += 1
        hora_v[dt.hour] += float(t.get("totalPagar") or 0)

    # rankings
    prof = defaultdict(lambda: {"n": 0, "v": 0.0})
    for a in fin:
        nome = ((a.get("profissional") or {}).get("nome") or "").strip().title() or "—"
        prof[nome]["n"] += 1; prof[nome]["v"] += float(a.get("valor") or 0)
    ranking_prof = sorted(
        [{"nome": k, "n": v["n"], "v": brl_round(v["v"])} for k, v in prof.items()],
        key=lambda x: -x["v"]
    )[:12]

    serv = defaultdict(lambda: {"n": 0, "v": 0.0, "min": 0})
    for a in fin:
        s = (a.get("servico") or {}).get("nome") or "sem"
        serv[s]["n"] += 1
        serv[s]["v"] += float(a.get("valor") or 0)
        serv[s]["min"] += int(a.get("duracaoEmMinutos") or 0)
    ranking_serv = sorted(
        [{"nome": k, "n": v["n"], "v": brl_round(v["v"]), "min": v["min"]} for k, v in serv.items()],
        key=lambda x: -x["v"]
    )[:12]

    rent_hora = []
    for k, v in serv.items():
        if v["min"] > 0:
            rent_hora.append({
                "nome": k, "n": v["n"], "v": brl_round(v["v"]),
                "min_medio": round(v["min"] / max(v["n"], 1)),
                "ticket": brl_round(v["v"] / max(v["n"], 1)),
                "rs_hora": brl_round(v["v"] / v["min"] * 60),
            })
    rent_hora.sort(key=lambda x: -x["rs_hora"])

    by_dow = defaultdict(lambda: {"n": 0, "v": 0.0})
    for a in fin:
        dt = datetime.fromisoformat(a["dataHoraInicio"])
        by_dow[DOW_NOMES[dt.weekday()]]["n"] += 1
        by_dow[DOW_NOMES[dt.weekday()]]["v"] += float(a.get("valor") or 0)
    dow_list = [{"nome": n, "n": by_dow[n]["n"], "v": brl_round(by_dow[n]["v"])} for n in DOW_NOMES]

    by_day = defaultdict(lambda: {"n": 0, "v": 0.0})
    for a in fin:
        dt = datetime.fromisoformat(a["dataHoraInicio"])
        by_day[dt.day]["n"] += 1
        by_day[dt.day]["v"] += float(a.get("valor") or 0)
    dia_list = [{"d": d, "n": by_day[d]["n"], "v": brl_round(by_day[d]["v"])} for d in sorted(by_day)]

    cli_c = Counter((a.get("cliente") or {}).get("nome") for a in fin if (a.get("cliente") or {}).get("nome"))
    top_cli = [{"nome": (k or "").title(), "n": v} for k, v in cli_c.most_common(10)]

    meios = sorted(
        [{"nome": k, "n": mp_c[k], "v": brl_round(mp_v[k]), "pct": round(mp_v[k] / max(caixa, 1) * 100, 1)} for k in mp_c],
        key=lambda x: -x["v"]
    )
    hora_abs = [{"h": h, "n": hora_c.get(h, 0), "v": brl_round(hora_v.get(h, 0))} for h in range(8, 21)]

    return {
        "kpis": {
            "caixa": brl_round(caixa),
            "receita_serv": brl_round(receita_serv),
            "atend_fin": len(fin),
            "atend_canc": len(canc),
            "atend_total": len(ag),
            "n_trans": len(tr),
            "ticket_trans": brl_round(caixa / max(len(tr), 1)),
            "taxa_canc": round(len(canc) / max(len(ag), 1) * 100, 1),
            "dias_op": dias_com_op,
            "clientes_unicos": unicos,
            "em_atendimento": len(em_at),
        },
        "categorias": {
            "pacotes": {"v": brl_round(pac_v), "n": pac_n, "pct": round(pac_v / max(caixa, 1) * 100, 1)},
            "servicos": {"v": brl_round(serv_v), "n": serv_n, "pct": round(serv_v / max(caixa, 1) * 100, 1)},
            "produtos": {"v": brl_round(prod_v), "n": prod_n, "pct": round(prod_v / max(caixa, 1) * 100, 1)},
        },
        "meios_pagamento": meios,
        "hora_abs": hora_abs,
        "por_dow": dow_list,
        "por_dia_mes": dia_list,
        "ranking_prof": ranking_prof,
        "ranking_serv": ranking_serv,
        "rentabilidade_hora": rent_hora[:15],
        "clientes_top": top_cli,
        "descontos": brl_round(descontos),
        "trocos": brl_round(trocos),
    }


def calc_meta(caixa, meta, dias_real, dias_total):
    pct = caixa / max(meta, 1) * 100
    falta = meta - caixa
    dias_rest = max(dias_total - dias_real, 0)
    necessario = falta / max(dias_rest, 1) if dias_rest else 0
    ritmo = caixa / max(dias_real, 1)
    proj = ritmo * dias_total
    return {
        "meta": meta, "realizado": brl_round(caixa), "pct": round(pct, 1),
        "falta": brl_round(falta), "dias_realizados": dias_real, "dias_total": dias_total,
        "dias_restantes": dias_rest, "necessario_dia": brl_round(necessario),
        "ritmo_dia": brl_round(ritmo), "projecao": brl_round(proj),
        "projecao_pct": round(proj / max(meta, 1) * 100, 1),
    }


def top_ltv(agend, ini: date, fim: date, limite=15):
    ltv = defaultdict(lambda: {"n": 0, "v": 0.0, "nome": ""})
    for a in agend:
        if (a.get("status") or {}).get("nome") != "Finalizado": continue
        dt = datetime.fromisoformat(a["dataHoraInicio"]).date() if a.get("dataHoraInicio") else None
        if not dt or not (ini <= dt <= fim): continue
        cid = (a.get("cliente") or {}).get("id")
        if cid is None: continue
        ltv[cid]["n"] += 1
        ltv[cid]["v"] += float(a.get("valor") or 0)
        ltv[cid]["nome"] = (a.get("cliente") or {}).get("nome") or ""
    lst = sorted(
        [{"nome": (d["nome"] or "").title(), "n": d["n"], "v": brl_round(d["v"])} for d in ltv.values()],
        key=lambda x: -x["v"]
    )
    total = sum(x["v"] for x in lst)
    uma = sum(1 for x in lst if x["n"] == 1)
    p20 = max(1, len(lst) * 20 // 100)
    p20v = sum(x["v"] for x in lst[:p20])
    return {
        "total_clientes": len(lst), "receita_total": brl_round(total),
        "uma_vez": uma, "duas_mais": len(lst) - uma,
        "pareto20_n": p20, "pareto20_v": brl_round(p20v),
        "pareto20_pct": round(p20v / max(total, 1) * 100, 1),
        "top": lst[:limite],
    }


def novos_vs_recorr(fin_mes, cadastro_map, ini_mes: date):
    novos_ids, rec_ids = set(), set()
    for a in fin_mes:
        cid = (a.get("cliente") or {}).get("id")
        if cid is None: continue
        cad = cadastro_map.get(cid)
        if cad is None: continue
        if cad.date() >= ini_mes: novos_ids.add(cid)
        else: rec_ids.add(cid)
    r_novos = sum(float(a.get("valor") or 0) for a in fin_mes if (a.get("cliente") or {}).get("id") in novos_ids)
    r_rec = sum(float(a.get("valor") or 0) for a in fin_mes if (a.get("cliente") or {}).get("id") in rec_ids)
    a_novos = sum(1 for a in fin_mes if (a.get("cliente") or {}).get("id") in novos_ids)
    a_rec = sum(1 for a in fin_mes if (a.get("cliente") or {}).get("id") in rec_ids)
    return {
        "novos": {"clientes": len(novos_ids), "atend": a_novos, "receita": brl_round(r_novos)},
        "recorrentes": {"clientes": len(rec_ids), "atend": a_rec, "receita": brl_round(r_rec)},
    }


def main():
    t = Trinks()
    hoje = date.today()
    ini_ano = date(hoje.year, 1, 1)
    fim_ano = date(hoje.year, 12, 31)
    ini_mes = date(hoje.year, hoje.month, 1)
    fim_mes = date(hoje.year, hoje.month, monthrange(hoje.year, hoje.month)[1])
    seg = hoje - timedelta(days=hoje.weekday())
    dom = seg + timedelta(days=6)

    print(f"[github_refresh] Períodos: ano={ini_ano}..{fim_ano} · mês={ini_mes}..{fim_mes} · sem={seg}..{dom} · hoje={hoje}")
    print(f"[github_refresh] Cota: {t.consumo()}")

    # Puxar ANO INTEIRO (loja abriu 23/07, então só jul+ago-set-dez interessa)
    print("[fetch] agendamentos ano...")
    agend = list(t.paginate("/v1/agendamentos", {"dataInicio": ini_ano.isoformat(), "dataFim": fim_ano.isoformat()}))
    print(f"  {len(agend)} agendamentos")
    print("[fetch] transacoes ano...")
    transac = list(t.paginate("/v1/transacoes", {"dataInicio": ini_ano.isoformat(), "dataFim": fim_ano.isoformat()}))
    print(f"  {len(transac)} transações")
    print("[fetch] clientes...")
    clientes = list(t.paginate("/v1/clientes"))
    print(f"  {len(clientes)} clientes")
    cad_map = {}
    for c in clientes:
        if c.get("id") and c.get("dataCadastro"):
            try: cad_map[c["id"]] = datetime.fromisoformat(c["dataCadastro"])
            except Exception: pass

    # Análises por período
    a_anual = analisar(agend, transac, ini_ano, fim_ano)
    a_mensal = analisar(agend, transac, ini_mes, fim_mes)
    a_semanal = analisar(agend, transac, seg, dom)
    a_diario = analisar(agend, transac, hoje, hoje)

    fin_mes = [a for a in agend if (a.get("status") or {}).get("nome") == "Finalizado"
               and a.get("dataHoraInicio")
               and ini_mes <= datetime.fromisoformat(a["dataHoraInicio"]).date() <= fim_mes]
    nvr = novos_vs_recorr(fin_mes, cad_map, ini_mes)
    ltv_ano = top_ltv(agend, ini_ano, fim_ano)

    # meses do ano
    meses = {}
    for m in range(1, 13):
        mi = date(hoje.year, m, 1)
        mf = date(hoje.year, m, monthrange(hoje.year, m)[1])
        am = analisar(agend, transac, mi, mf)
        if am["kpis"]["atend_fin"] > 0 or am["kpis"]["n_trans"] > 0:
            meses[f"{hoje.year}-{m:02d}"] = {
                "caixa": am["kpis"]["caixa"], "receita_serv": am["kpis"]["receita_serv"],
                "atend_fin": am["kpis"]["atend_fin"], "clientes_unicos": am["kpis"]["clientes_unicos"],
                "n_trans": am["kpis"]["n_trans"], "ticket_trans": am["kpis"]["ticket_trans"],
                "taxa_canc": am["kpis"]["taxa_canc"], "categorias": am["categorias"],
                "dias_op": am["kpis"]["dias_op"],
            }

    # metas
    meta_mensal = calc_meta(a_mensal["kpis"]["caixa"], META_MENSAL, a_mensal["kpis"]["dias_op"], DIAS_OP_MES)
    meta_dia = calc_meta(a_diario["kpis"]["caixa"], round(META_MENSAL / DIAS_OP_MES, 2), 1, 1)
    dias_op_sem = 6
    meta_sem = calc_meta(a_semanal["kpis"]["caixa"], round(META_MENSAL / DIAS_OP_MES * dias_op_sem, 2),
                         a_semanal["kpis"]["dias_op"], dias_op_sem)
    real_pre_atual = sum(m["caixa"] for k, m in meses.items() if k < f"{hoje.year}-{hoje.month:02d}")
    meses_rest = 12 - hoje.month + 1
    meta_ano_valor = round(real_pre_atual + META_MENSAL * meses_rest, 2)
    meta_ano = calc_meta(a_anual["kpis"]["caixa"], meta_ano_valor, hoje.month, 12) if meta_ano_valor > 0 else {}

    def hora_media(hora_list, dias):
        return [{"h": x["h"], "media": round(x["n"] / max(dias, 1), 2), "n_total": x["n"]} for x in hora_list]

    cota_final = t.consumo()

    payload = {
        # UTC com sufixo Z para JavaScript interpretar corretamente
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z"),
        "hoje": hoje.isoformat(),
        "meta_mensal_valor": META_MENSAL,
        "dias_op_mes": DIAS_OP_MES,
        "cota_api": cota_final,
        "abas": {
            "anual": {
                "kpis": a_anual["kpis"], "meta": meta_ano, "categorias": a_anual["categorias"],
                "meses": meses, "top_ltv": ltv_ano,
                "rentabilidade_hora": a_anual["rentabilidade_hora"],
                "hora_media": hora_media(a_anual["hora_abs"], a_anual["kpis"]["dias_op"]),
                "ranking_prof": a_anual["ranking_prof"], "ranking_serv": a_anual["ranking_serv"],
                "meios_pagamento": a_anual["meios_pagamento"], "descontos": a_anual["descontos"],
                "clientes_top": a_anual["clientes_top"],
            },
            "mensal": {
                "kpis": a_mensal["kpis"], "meta": meta_mensal, "categorias": a_mensal["categorias"],
                "novos_vs_recorr": nvr, "rentabilidade_hora": a_mensal["rentabilidade_hora"],
                "por_dia_mes": a_mensal["por_dia_mes"],
                "hora_media": hora_media(a_mensal["hora_abs"], a_mensal["kpis"]["dias_op"]),
                "ranking_prof": a_mensal["ranking_prof"], "ranking_serv": a_mensal["ranking_serv"],
                "meios_pagamento": a_mensal["meios_pagamento"], "descontos": a_mensal["descontos"],
                "clientes_top": a_mensal["clientes_top"],
            },
            "semanal": {
                "kpis": {**a_semanal["kpis"], "periodo_ini": seg.isoformat(), "periodo_fim": dom.isoformat()},
                "meta": meta_sem, "categorias": a_semanal["categorias"],
                "por_dow": a_semanal["por_dow"],
                "hora_media": hora_media(a_semanal["hora_abs"], a_semanal["kpis"]["dias_op"]),
                "ranking_prof": a_semanal["ranking_prof"], "ranking_serv": a_semanal["ranking_serv"],
                "meios_pagamento": a_semanal["meios_pagamento"],
                "clientes_top": a_semanal["clientes_top"],
            },
            "diario": {
                "kpis": {**a_diario["kpis"], "dia_semana": DOW_NOMES[hoje.weekday()], "data": hoje.isoformat()},
                "meta": meta_dia, "categorias": a_diario["categorias"],
                "hora_abs": a_diario["hora_abs"], "ranking_prof": a_diario["ranking_prof"],
                "ranking_serv": a_diario["ranking_serv"], "meios_pagamento": a_diario["meios_pagamento"],
                "clientes_top": a_diario["clientes_top"],
            },
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[github_refresh] OK · {OUT_JSON}")
    print(f"  Ano R$ {a_anual['kpis']['caixa']:.2f} · Mês R$ {a_mensal['kpis']['caixa']:.2f} · Sem R$ {a_semanal['kpis']['caixa']:.2f} · Hoje R$ {a_diario['kpis']['caixa']:.2f}")


if __name__ == "__main__":
    main()
