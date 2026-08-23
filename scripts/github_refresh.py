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
STONE_CSV = REPO_ROOT / "data" / "stone_extrato.csv"
CONFIG_JSON = REPO_ROOT / "data" / "config.json"

# Config da loja (cadeiras físicas, horas de operação, mapping serviço→cadeira)
try:
    _cfg = json.loads(CONFIG_JSON.read_text(encoding="utf-8"))
except Exception:
    _cfg = {}
CADEIRAS_FIS = _cfg.get("cadeiras") or {"cabelo": 5, "maquiagem": 3, "unhas": 8}
HORAS_OPERACAO_DIA = _cfg.get("horas_operacao_dia", 12)
CADEIRA_KEYWORDS = _cfg.get("cadeira_por_servico_keywords") or {}


def classificar_cadeira(nome_serv):
    """Retorna 'cabelo' | 'maquiagem' | 'unhas' | 'outro' pelo nome do serviço."""
    if not nome_serv: return "outro"
    n = nome_serv.upper()
    for tipo, kws in CADEIRA_KEYWORDS.items():
        for kw in kws:
            if kw.upper() in n:
                return tipo
    return "outro"


class Trinks:
    def __init__(self):
        api_key = os.environ["TRINKS_API_KEY"]
        eid = os.environ["TRINKS_ESTABELECIMENTO_ID"]
        # User-Agent: alguns WAFs bloqueiam requests sem UA (retornando 500 em vez de 403)
        self.headers = {
            "X-Api-Key": api_key,
            "estabelecimentoId": eid,
            "Accept": "application/json",
            "User-Agent": "FAST-Dashboard-Limao/1.0 (+https://github.com/rodsballa12-cell/fast-dashboard-limao)",
        }
        self.s = requests.Session()
        self._last = 0.0

    def _throttle(self):
        dt = time.time() - self._last
        if dt < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - dt)
        self._last = time.time()

    def get(self, path, params=None, retries=6):
        url = BASE_URL + path
        last_status = None
        for i in range(retries):
            self._throttle()
            try:
                r = self.s.get(url, headers=self.headers, params=params, timeout=45)
            except requests.exceptions.RequestException as e:
                # Timeout/conexão — backoff exponencial (2, 4, 8, 16, 32, 64s)
                delay = 2 ** (i + 1)
                print(f"[trinks] {path} tentativa {i+1}/{retries} · {type(e).__name__}: {e} · aguarda {delay}s")
                time.sleep(delay)
                continue
            last_status = r.status_code
            if r.status_code == 429:
                delay = 30 * (i + 1)
                print(f"[trinks] {path} 429 rate-limit · aguarda {delay}s")
                time.sleep(delay); continue
            if 500 <= r.status_code < 600:
                # Log corpo da resposta na PRIMEIRA tentativa pra revelar o que Trinks retorna
                if i == 0:
                    body_preview = (r.text or "")[:500].replace("\n", " ")
                    print(f"[trinks] {path} {r.status_code} · body: {body_preview!r}")
                delay = 10 * (i + 1)
                print(f"[trinks] {path} {r.status_code} · aguarda {delay}s")
                time.sleep(delay); continue
            if r.status_code == 404:
                return {"data": [], "totalPages": 0}
            r.raise_for_status()
            return r.json()
        raise RuntimeError(f"Falha após {retries}: {url} (último status: {last_status})")

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
        # Não-fatal: se o endpoint de cota falhar, retornar estrutura vazia
        # em vez de matar o pipeline inteiro (só telemetria).
        try:
            return self.get("/v1/consumo")
        except Exception as e:
            print(f"[consumo] falhou (não-fatal): {e}")
            return {"plano": "desconhecido", "cotaTotal": 0, "totalUtilizado": 0, "saldoRestante": 0}


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
    # clientes-dia = ticket médio do Trinks (1 cliente em 1 dia = 1 visita)
    # mesmo cliente com N serviços no mesmo dia conta como 1; se voltar noutro dia, +1
    cliente_dia = {((a.get("cliente") or {}).get("id"),
                    datetime.fromisoformat(a["dataHoraInicio"]).date())
                   for a in fin if (a.get("cliente") or {}).get("id")}
    n_cliente_dia = len(cliente_dia)

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

    # rankings — inclui ticket médio e minutos ocupados
    prof = defaultdict(lambda: {"n": 0, "v": 0.0, "min": 0})
    for a in fin:
        nome = ((a.get("profissional") or {}).get("nome") or "").strip().title() or "—"
        prof[nome]["n"] += 1
        prof[nome]["v"] += float(a.get("valor") or 0)
        prof[nome]["min"] += int(a.get("duracaoEmMinutos") or 0)
    n_prof_ativos = len(prof)  # profissionais que atenderam alguém no período
    ranking_prof_full = sorted(
        [{"nome": k, "n": v["n"], "v": brl_round(v["v"]),
          "ticket_medio": brl_round(v["v"] / max(v["n"], 1)),
          "horas_trab": round(v["min"] / 60, 1)} for k, v in prof.items()],
        key=lambda x: -x["v"]
    )
    ranking_prof = ranking_prof_full[:12]
    ranking_prof_total_n = len(ranking_prof_full)  # útil pra badge "de N total"

    # === Utilização de CADEIRA FÍSICA (por tipo) ===
    # Modelo PJ: capacidade é do imóvel, não das profissionais.
    # Denominador: N cadeiras físicas × horas de operação × dias operados
    # Numerador: soma de duração dos atendimentos que usam esse tipo de cadeira
    ocup_por_cadeira = {tipo: 0.0 for tipo in CADEIRAS_FIS}
    ocup_por_cadeira["outro"] = 0.0
    for a in fin:
        s = (a.get("servico") or {}).get("nome") or ""
        min_a = int(a.get("duracaoEmMinutos") or 0)
        tipo = classificar_cadeira(s)
        ocup_por_cadeira[tipo] += min_a / 60

    cadeiras_detalhe = {}
    dias_ref = max(dias_com_op, 1)
    for tipo, n_cad in CADEIRAS_FIS.items():
        cap_h = n_cad * HORAS_OPERACAO_DIA * dias_ref
        oc_h = ocup_por_cadeira.get(tipo, 0)
        util_pct = min(100, oc_h / max(cap_h, 1) * 100)
        cadeiras_detalhe[tipo] = {
            "n_cadeiras": n_cad,
            "capacidade_horas": round(cap_h, 1),
            "horas_ocupadas": round(oc_h, 1),
            "utilizacao_pct": round(util_pct, 1),
        }
    # Agregado
    total_ocup = sum(ocup_por_cadeira.values())
    total_cap = sum(v["capacidade_horas"] for v in cadeiras_detalhe.values())
    util_agregada = min(100, total_ocup / max(total_cap, 1) * 100)

    # === R$/hora útil do salão ===
    horas_operacao_periodo = HORAS_OPERACAO_DIA * dias_ref
    rs_hora_salao = caixa / max(horas_operacao_periodo, 1)

    # === Densidade horária (média atendimentos simultâneos por hora do dia) ===
    # Pra cada atendimento, alocar sua duração nas horas afetadas
    from collections import defaultdict as _dd
    ocup_por_hora = _dd(float)  # {hora: horas-cliente totais nessa hora do dia}
    for a in fin:
        dt = a.get("dataHoraInicio")
        min_a = int(a.get("duracaoEmMinutos") or 0)
        if not dt or min_a <= 0: continue
        try:
            inicio = datetime.fromisoformat(dt)
        except Exception:
            continue
        # Distribuir min_a entre as horas afetadas
        restante = min_a
        pos = inicio
        while restante > 0:
            h = pos.hour
            fim_hora = pos.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            gap_min = (fim_hora - pos).total_seconds() / 60
            uso = min(restante, gap_min)
            ocup_por_hora[h] += uso / 60
            restante -= uso
            pos = fim_hora
    # Média por hora (dividido por dias)
    densidade_hora = [
        {"h": h, "media_simultaneos": round(ocup_por_hora.get(h, 0) / dias_ref, 2)}
        for h in range(8, 21)
    ]

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

    # Rentabilidade por hora de CADEIRA
    # Serviços com duração muito baixa (<15 min médio) são add-ons/produtos aplicados
    # em paralelo a outro serviço — não consomem cadeira exclusiva. Marcados como
    # tipo="addon" e mostrados em seção separada (não competem no ranking R$/h).
    MIN_CADEIRA_EXCLUSIVA = 15  # abaixo disso = add-on/aplicação, não ocupa cadeira
    rent_hora = []
    total_caixa_ref = max(caixa, 1)
    for k, v in serv.items():
        if v["min"] > 0:
            min_medio = round(v["min"] / max(v["n"], 1))
            horas_total = v["min"] / 60
            pct_fat = v["v"] / total_caixa_ref * 100
            conf = "alta" if v["n"] >= 5 else ("media" if v["n"] >= 3 else "baixa")
            tipo = "addon" if min_medio < MIN_CADEIRA_EXCLUSIVA else "cadeira"
            rent_hora.append({
                "nome": k, "n": v["n"], "v": brl_round(v["v"]),
                "min_medio": min_medio,
                "ticket": brl_round(v["v"] / max(v["n"], 1)),
                "rs_hora": brl_round(v["v"] / v["min"] * 60),
                "horas_total": round(horas_total, 1),
                "pct_faturamento": round(pct_fat, 1),
                "confianca": conf,
                "tipo": tipo,  # "cadeira" (serviço exclusivo) | "addon" (paralelo a outro)
            })
    # Ordena: cadeira primeiro (por R$/h desc), depois addons (por valor desc)
    rent_hora.sort(key=lambda x: (0 if x["tipo"] == "cadeira" else 1, -x["rs_hora"] if x["tipo"]=="cadeira" else -x["v"]))
    # Limita a 15 cadeira + todos add-ons (add-ons são poucos: aplicações, tratamentos rápidos)
    cadeira_top = [x for x in rent_hora if x["tipo"] == "cadeira"][:15]
    addons_all  = [x for x in rent_hora if x["tipo"] == "addon"]
    rent_hora = cadeira_top + addons_all

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
            "cliente_dia": n_cliente_dia,
            "ticket_medio": brl_round(caixa / max(n_cliente_dia, 1)),
            "taxa_canc": round(len(canc) / max(len(ag), 1) * 100, 1),
            "dias_op": dias_com_op,
            "clientes_unicos": unicos,
            "em_atendimento": len(em_at),
            "n_prof_ativos": n_prof_ativos,
            "rs_hora_salao": brl_round(rs_hora_salao),
            "horas_operacao_periodo": round(horas_operacao_periodo, 0),
            "utilizacao_agregada_pct": round(util_agregada, 1),
        },
        "cadeiras_utilizacao": cadeiras_detalhe,
        "densidade_hora": densidade_hora,
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
        "ranking_prof_total_n": ranking_prof_total_n,
        "ranking_serv": ranking_serv,
        "rentabilidade_hora": rent_hora,
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
    # Sempre operar no fuso de Brasília (UTC-3, sem DST desde 2019)
    from datetime import timezone as _tz
    BRT = _tz(timedelta(hours=-3))
    hoje = datetime.now(BRT).date()
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
    aniv_map = {}  # {id: (mm, dd, nome)}
    for c in clientes:
        cid = c.get("id")
        if not cid: continue
        if c.get("dataCadastro"):
            try: cad_map[cid] = datetime.fromisoformat(c["dataCadastro"])
            except Exception: pass
        # Aniversário — Trinks usa dataNascimento
        if c.get("dataNascimento"):
            try:
                dn = datetime.fromisoformat(c["dataNascimento"])
                aniv_map[cid] = (dn.month, dn.day, c.get("nome") or "")
            except Exception: pass

    # Análises por período
    a_anual = analisar(agend, transac, ini_ano, fim_ano)
    a_mensal = analisar(agend, transac, ini_mes, fim_mes)
    a_semanal = analisar(agend, transac, seg, dom)
    a_diario = analisar(agend, transac, hoje, hoje)

    fin_mes = [a for a in agend if (a.get("status") or {}).get("nome") == "Finalizado"
               and a.get("dataHoraInicio")
               and ini_mes <= datetime.fromisoformat(a["dataHoraInicio"]).date() <= fim_mes]
    nvr_mes = novos_vs_recorr(fin_mes, cad_map, ini_mes)

    # novos_vs_recorr também pra semanal e anual
    fin_sem = [a for a in agend if (a.get("status") or {}).get("nome") == "Finalizado"
               and a.get("dataHoraInicio") and seg <= datetime.fromisoformat(a["dataHoraInicio"]).date() <= dom]
    nvr_sem = novos_vs_recorr(fin_sem, cad_map, seg)
    fin_ano = [a for a in agend if (a.get("status") or {}).get("nome") == "Finalizado"
               and a.get("dataHoraInicio") and ini_ano <= datetime.fromisoformat(a["dataHoraInicio"]).date() <= fim_ano]
    nvr_ano = novos_vs_recorr(fin_ano, cad_map, ini_ano)

    ltv_ano = top_ltv(agend, ini_ano, fim_ano)

    # === Semana anterior (pra comparação semana × semana) ===
    seg_ant = seg - timedelta(days=7)
    dom_ant = seg_ant + timedelta(days=6)
    a_sem_ant = analisar(agend, transac, seg_ant, dom_ant)
    semana_anterior = {
        "periodo_ini": seg_ant.isoformat(), "periodo_fim": dom_ant.isoformat(),
        "caixa": a_sem_ant["kpis"]["caixa"], "atend_fin": a_sem_ant["kpis"]["atend_fin"],
        "n_trans": a_sem_ant["kpis"]["n_trans"], "ticket_trans": a_sem_ant["kpis"]["ticket_trans"],
        "ticket_medio": a_sem_ant["kpis"]["ticket_medio"],
        "dias_op": a_sem_ant["kpis"]["dias_op"],
    }

    # === Churn early warning: clientes ≥3 visitas nos primeiros 30 dias e sumidos há 14+ dias ===
    churn_candidatos = []
    cli_visitas = defaultdict(list)  # {id: [dates]}
    cli_nome = {}
    cli_valor = defaultdict(float)
    for a in agend:
        if (a.get("status") or {}).get("nome") != "Finalizado": continue
        cid = (a.get("cliente") or {}).get("id")
        if cid is None: continue
        try:
            dt = datetime.fromisoformat(a["dataHoraInicio"]).date()
        except Exception:
            continue
        cli_visitas[cid].append(dt)
        cli_nome[cid] = (a.get("cliente") or {}).get("nome") or ""
        cli_valor[cid] += float(a.get("valor") or 0)
    for cid, datas in cli_visitas.items():
        if len(datas) < 3: continue
        datas_sorted = sorted(datas)
        ultima = datas_sorted[-1]
        dias_sem_vir = (hoje - ultima).days
        if dias_sem_vir >= 14:
            churn_candidatos.append({
                "cliente": cli_nome[cid].title(),
                "n_visitas": len(datas),
                "ltv": brl_round(cli_valor[cid]),
                "ultima_visita": ultima.isoformat(),
                "dias_sem_vir": dias_sem_vir,
            })
    churn_candidatos.sort(key=lambda x: -x["ltv"])
    churn = {
        "n_alerta": len(churn_candidatos),
        "ltv_em_risco": brl_round(sum(c["ltv"] for c in churn_candidatos)),
        "top": churn_candidatos[:20],
    }

    # === Aniversariantes próximos (14 dias) ===
    aniversariantes = []
    for cid, (mm, dd, nome) in aniv_map.items():
        # Ignora sem visita registrada (não é cliente ativo)
        if cid not in cli_visitas: continue
        try:
            aniv_ano = date(hoje.year, mm, dd)
        except ValueError:
            continue  # 29/fev em ano não-bissexto
        delta = (aniv_ano - hoje).days
        if delta < 0:
            # já passou este ano, olha ano que vem
            try:
                aniv_ano = date(hoje.year + 1, mm, dd)
                delta = (aniv_ano - hoje).days
            except ValueError:
                continue
        if 0 <= delta <= 14:
            aniversariantes.append({
                "cliente": (nome or "").title(),
                "data_aniv": f"{dd:02d}/{mm:02d}",
                "dias": delta,
                "n_visitas": len(cli_visitas.get(cid, [])),
                "ltv": brl_round(cli_valor.get(cid, 0)),
            })
    aniversariantes.sort(key=lambda x: (x["dias"], -x["ltv"]))

    # === Cross-sell: clientes recorrentes (2+ visitas) que ainda não fizeram serviços populares ===
    # Popularidade: serviço com >= 30 atendimentos no ano é "popular"
    from collections import Counter as _Cnt
    serv_pop = _Cnt()
    cli_servs = defaultdict(set)  # {id: set(serv_nome)}
    for a in agend:
        if (a.get("status") or {}).get("nome") != "Finalizado": continue
        s = (a.get("servico") or {}).get("nome")
        cid = (a.get("cliente") or {}).get("id")
        if s: serv_pop[s] += 1
        if s and cid: cli_servs[cid].add(s)
    servs_populares = {s for s, n in serv_pop.items() if n >= 30}

    # Pra cada cliente recorrente (2+ visitas), listar até 3 populares que nunca fez
    cross_sell = []
    for cid, visitas in cli_visitas.items():
        if len(visitas) < 2: continue
        feitos = cli_servs.get(cid, set())
        nao_feitos = servs_populares - feitos
        if not nao_feitos: continue
        # Ordena por popularidade (mais popular primeiro)
        recomendados = sorted(nao_feitos, key=lambda s: -serv_pop[s])[:3]
        cross_sell.append({
            "cliente": cli_nome.get(cid, "").title(),
            "n_visitas": len(visitas),
            "ltv": brl_round(cli_valor.get(cid, 0)),
            "ja_faz": sorted(feitos & servs_populares, key=lambda s: -serv_pop[s])[:2],
            "recomendar": recomendados,
        })
    # Ordena por LTV — clientes valiosos primeiro
    cross_sell.sort(key=lambda x: -x["ltv"])
    cross_sell_data = {
        "servs_populares": sorted(servs_populares, key=lambda s: -serv_pop[s]),
        "n_clientes_com_oportunidade": len(cross_sell),
        "top": cross_sell[:20],
    }

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

    # === SAZONALIDADE: pesos por dia da semana + curva horária ===
    # Fonte: histórico anual acumulado (por_dow do ano). Se ainda não temos ≥3 ocorrências
    # de algum dow, usamos peso uniforme como fallback.
    dow_hist_v = {i: 0.0 for i in range(7)}  # seg=0 ... dom=6
    dow_hist_n = {i: 0 for i in range(7)}    # nº de dias observados
    for a in fin_ano:
        try:
            dt = datetime.fromisoformat(a["dataHoraInicio"]).date()
            dow_hist_v[dt.weekday()] += float(a.get("valor") or 0)
        except Exception: pass
    dias_vistos = {datetime.fromisoformat(a["dataHoraInicio"]).date() for a in fin_ano if a.get("dataHoraInicio")}
    for d in dias_vistos:
        dow_hist_n[d.weekday()] += 1

    # Peso normalizado por DOW = caixa médio de 1 dia daquele dow / soma dos caixas médios (seg-sáb).
    # Domingo = 0 (fechado). Se um dow ainda não tem dado, usa 1/6 uniforme.
    caixa_medio_dow = {}
    for i in range(6):  # seg-sáb (dom fica fora)
        if dow_hist_n[i] >= 3:
            caixa_medio_dow[i] = dow_hist_v[i] / dow_hist_n[i]
        else:
            caixa_medio_dow[i] = 0  # marca como "sem dado suficiente"
    if all(v == 0 for v in caixa_medio_dow.values()):
        # sem dado nenhum → uniforme
        peso_dow = {i: 1/6 for i in range(6)}
    else:
        # dias sem dado suficiente ganham a média dos dias que têm dado
        media_conhecidos = sum(v for v in caixa_medio_dow.values() if v > 0) / max(sum(1 for v in caixa_medio_dow.values() if v > 0), 1)
        for i in range(6):
            if caixa_medio_dow[i] == 0: caixa_medio_dow[i] = media_conhecidos
        total = sum(caixa_medio_dow.values())
        peso_dow = {i: caixa_medio_dow[i] / total for i in range(6)}
    peso_dow[6] = 0.0  # dom fechado

    # META por DOW no mês corrente: distribui META_MENSAL pelos pesos, respeitando quantos
    # dias de cada DOW há no mês. Ex: se sáb pesa 40% e o mês tem 4 sábados, cada sáb = 40%*60k/4 = 6k.
    n_dias_dow_mes = {i: 0 for i in range(7)}
    for d in range(1, monthrange(hoje.year, hoje.month)[1] + 1):
        n_dias_dow_mes[date(hoje.year, hoje.month, d).weekday()] += 1
    meta_dia_por_dow = {}
    for i in range(7):
        if n_dias_dow_mes[i] > 0 and peso_dow[i] > 0:
            meta_dia_por_dow[i] = round(META_MENSAL * peso_dow[i] / n_dias_dow_mes[i], 2)
        else:
            meta_dia_por_dow[i] = 0.0

    # Curva horária esperada (pct do caixa do dia acumulado até hora H)
    # Fonte: hora_abs anual dividido por total. Usamos como pace guide intraday.
    hora_v_hist = Counter()
    for tr in transac:
        if not tr.get("dataHora"): continue
        try:
            dt = datetime.fromisoformat(tr["dataHora"])
            if not (ini_ano <= dt.date() <= fim_ano): continue
            v = sum(float(fp.get("valor") or 0) for fp in (tr.get("formasPagamentos") or []))
            hora_v_hist[dt.hour] += v
        except Exception: pass
    total_hora_hist = sum(hora_v_hist.values()) or 1
    curva_horaria = []
    acum = 0
    for h in range(8, 22):
        acum += hora_v_hist.get(h, 0)
        curva_horaria.append({"h": h, "pct_acum": round(acum / total_hora_hist * 100, 1)})

    # metas
    meta_mensal = calc_meta(a_mensal["kpis"]["caixa"], META_MENSAL, a_mensal["kpis"]["dias_op"], DIAS_OP_MES)

    # Meta do DIA: usa peso do dow de hoje. Fallback pra média se dow=dom (0).
    meta_dia_valor = meta_dia_por_dow[hoje.weekday()] or round(META_MENSAL / DIAS_OP_MES, 2)
    meta_dia = calc_meta(a_diario["kpis"]["caixa"], meta_dia_valor, 1, 1)

    # Meta da SEMANA: soma das metas dos dias reais da semana (respeita pesos).
    dias_op_sem = 6
    meta_sem_valor = sum(meta_dia_por_dow[(seg + timedelta(days=i)).weekday()] for i in range(7))
    if meta_sem_valor == 0:
        meta_sem_valor = round(META_MENSAL / DIAS_OP_MES * dias_op_sem, 2)
    meta_sem = calc_meta(a_semanal["kpis"]["caixa"], round(meta_sem_valor, 2),
                         a_semanal["kpis"]["dias_op"], dias_op_sem)
    real_pre_atual = sum(m["caixa"] for k, m in meses.items() if k < f"{hoje.year}-{hoje.month:02d}")
    meses_rest = 12 - hoje.month + 1
    meta_ano_valor = round(real_pre_atual + META_MENSAL * meses_rest, 2)

    # dias operacionais reais desde abertura da loja (23/07/26) até 31/12/26 · exclui domingos
    def _dias_op(ini_d: date, fim_d: date) -> int:
        n, d = 0, ini_d
        while d <= fim_d:
            if d.weekday() != 6: n += 1
            d += timedelta(days=1)
        return n

    data_abertura = date(2026, 7, 23)
    fim_ano_dt = date(2026, 12, 31)
    dias_op_total = _dias_op(data_abertura, fim_ano_dt)
    dias_op_realizados = _dias_op(data_abertura, min(hoje, fim_ano_dt))
    meta_ano = calc_meta(a_anual["kpis"]["caixa"], meta_ano_valor, dias_op_realizados, dias_op_total) if meta_ano_valor > 0 else {}

    # === Ticket meta OPERACIONAL: derivado da meta de caixa e das visitas projetadas ===
    # Racional: se o ritmo de visitas atual continuar até o fim do período, quanto precisa
    # cada visita render pra bater a meta de caixa? Esse é o alvo REAL de ticket, não
    # um número fixo. Se a loja atrai muitas visitas, o ticket alvo cai; se atrai poucas,
    # o ticket alvo sobe. Assim o alvo se auto-ajusta ao mix operacional real.
    def _inject_ticket_meta(aba_kpis, meta_periodo, dias_realizados, dias_total):
        v_atual = aba_kpis.get("cliente_dia", 0)
        ritmo_visitas = v_atual / max(dias_realizados, 1)
        visitas_proj = round(ritmo_visitas * dias_total)
        meta_v = meta_periodo.get("meta", 0)
        realizado = meta_periodo.get("realizado", 0)
        falta_caixa = meta_v - realizado
        visitas_rest = max(visitas_proj - v_atual, 0)
        ticket_atual = aba_kpis.get("ticket_medio", 0)
        ticket_alvo_total = meta_v / max(visitas_proj, 1) if visitas_proj > 0 else 0

        # Status da janela
        if v_atual == 0 and dias_realizados >= dias_total:
            status = "fechado"   # período sem operação (ex: dom)
            ticket_alvo_restante = 0
        elif visitas_rest == 0:
            status = "encerrado_batido" if falta_caixa <= 0 else "encerrado_deficit"
            ticket_alvo_restante = 0
        else:
            status = "em_curso"
            ticket_alvo_restante = max(falta_caixa, 0) / visitas_rest

        gap = max(ticket_alvo_restante - ticket_atual, 0)
        aba_kpis["ticket_meta"] = brl_round(ticket_alvo_restante)
        aba_kpis["ticket_meta_periodo"] = brl_round(ticket_alvo_total)
        aba_kpis["ticket_atingimento_pct"] = round(ticket_atual / max(ticket_alvo_restante, 1) * 100, 1) if ticket_alvo_restante > 0 else (100.0 if status == "encerrado_batido" else 0.0)
        aba_kpis["ticket_gap_por_atend"] = brl_round(gap)
        aba_kpis["visitas_projetadas"] = visitas_proj
        aba_kpis["visitas_restantes"] = visitas_rest
        aba_kpis["ticket_meta_status"] = status
        aba_kpis["ticket_meta_deficit_caixa"] = brl_round(max(falta_caixa, 0))
        aba_kpis["ticket_meta_supera_caixa"] = brl_round(max(-falta_caixa, 0))

    _inject_ticket_meta(a_diario["kpis"], meta_dia, 1, 1)
    _inject_ticket_meta(a_semanal["kpis"], meta_sem, a_semanal["kpis"]["dias_op"], dias_op_sem)
    _inject_ticket_meta(a_mensal["kpis"], meta_mensal, a_mensal["kpis"]["dias_op"], DIAS_OP_MES)
    if meta_ano_valor > 0:
        _inject_ticket_meta(a_anual["kpis"], meta_ano, dias_op_realizados, dias_op_total)

    def hora_media(hora_list, dias):
        return [{"h": x["h"], "media": round(x["n"] / max(dias, 1), 2), "n_total": x["n"]} for x in hora_list]

    cota_final = t.consumo()

    # ==== STONE reconciliação (se CSV existe) ====
    stone_data = None
    try:
        from stone_processor import processar_stone_csv
        # extrair transações Trinks (só cartão/PIX/dinheiro) para o matcher
        trinks_tx = []
        for tr in transac:
            dt = None
            dt_full = None
            try:
                if tr.get("dataHora"):
                    dt_full = datetime.fromisoformat(tr["dataHora"])
                    dt = dt_full.date()
            except Exception:
                pass
            cli = (tr.get("cliente") or {}).get("nome", "")
            for fp in (tr.get("formasPagamentos") or []):
                trinks_tx.append({
                    "data": dt,
                    "data_hora": dt_full,  # datetime completo (para gap temporal)
                    "meio": fp.get("nome", ""),
                    "valor": float(fp.get("valor") or 0),
                    "cliente": cli,
                })
        stone_data = processar_stone_csv(STONE_CSV, trinks_tx)
        print(f"[stone] {'OK · ' + str(stone_data['total_lancamentos']) + ' lancamentos' if stone_data else 'sem CSV · aba vazia'}")
    except Exception as e:
        print(f"[stone] erro: {e}")
        stone_data = None

    # === Auditoria de cancelados com valor > 0 (walk-in only) ===
    # Preço mediano por serviço · POR MÊS (respeita correções de tabela)
    from statistics import median
    from unicodedata import normalize as _norm
    servico_precos_mes = defaultdict(lambda: defaultdict(list))  # {ym: {serv: [valores]}}
    servico_precos_geral = defaultdict(list)                     # fallback global
    for a in agend:
        if (a.get("status") or {}).get("nome") == "Finalizado":
            v = float(a.get("valor") or 0)
            s = (a.get("servico") or {}).get("nome") or ""
            dt_iso = (a.get("dataHoraInicio") or "")[:7]  # YYYY-MM
            if v > 0 and s and dt_iso:
                servico_precos_mes[dt_iso][s].append(v)
                servico_precos_geral[s].append(v)
    preco_mediano_mes = {
        ym: {s: median(vs) for s, vs in servs.items() if len(vs) >= 2}
        for ym, servs in servico_precos_mes.items()
    }
    preco_mediano_geral = {s: median(vs) for s, vs in servico_precos_geral.items() if len(vs) >= 2}

    def _preco_ref(serv, data_iso):
        """Retorna o preço mediano do serviço no MÊS do cancelamento (fallback: geral)."""
        if not serv:
            return None
        if data_iso:
            ym = data_iso[:7]
            p = preco_mediano_mes.get(ym, {}).get(serv)
            if p:
                return p
        return preco_mediano_geral.get(serv)

    # Índice Stone: (data_iso, valor_rounded) → lista de origens (nome do pagador)
    def _dstr_to_iso(s):
        try: return datetime.strptime(s.split()[0], "%d/%m/%Y").date().isoformat()
        except Exception: return None
    def _norm_nome(s):
        # remove acentos, normaliza pra minúsculo, tokeniza por palavra
        s = _norm("NFKD", (s or "").lower()).encode("ascii", "ignore").decode()
        # substitui não-alfanuméricos por espaço, split, filtra stop-tokens curtos/comuns
        import re as _re
        stop = {"da", "de", "do", "das", "dos", "e", "ltda", "ltd", "sa", "junior", "jr"}
        tokens = _re.findall(r"[a-z0-9]+", s)
        return [t for t in tokens if len(t) >= 3 and t not in stop]

    stone_idx = defaultdict(list)
    if stone_data:
        try:
            import csv as _csv
            with open(STONE_CSV, encoding="utf-8") as fh:
                rows = list(_csv.reader(fh))
            hdr = rows[0]; icol = {c: i for i, c in enumerate(hdr)}
            for r in rows[1:]:
                if not r or len(r) < 8: continue
                if r[0] == "Crédito" and r[1] in ("Transação", "Pix", "Recebível de Cartão"):
                    d = _dstr_to_iso(r[icol["Data"]])
                    if not d: continue
                    try:
                        v = float(r[2].replace(".", "").replace(",", ".").replace("R$", "").strip())
                    except Exception:
                        continue
                    stone_idx[(d, round(v, 2))].append({
                        "origem": r[icol["Origem"]],
                        "tipo": r[1],
                    })
        except Exception:
            pass

    # Data de corte: dia da inauguração (23/07) — cancelamentos até essa data
    # são testes de setup do Trinks. Filtrados da auditoria mas contados no total_excluidos.
    DATA_INAUGURACAO = "2026-07-23"
    canc_excluidos_inaug = 0
    canc_excluidos_valor = 0.0

    canc_com_valor = []
    for a in agend:
        if (a.get("status") or {}).get("nome") == "Cancelado":
            dt = a.get("dataHoraInicio", "")
            v = float(a.get("valor") or 0)
            prof = (a.get("profissional") or {}).get("nome") or ""
            cli = (a.get("cliente") or {}).get("nome") or ""
            serv = (a.get("servico") or {}).get("nome") or ""
            data_iso = dt.split("T")[0] if dt else None

            # Filtra testes de inauguração (até 23/07 inclusive)
            if data_iso and data_iso <= DATA_INAUGURACAO:
                canc_excluidos_inaug += 1
                canc_excluidos_valor += v
                continue

            valor_zero = v == 0

            # Flag 1: sem profissional atribuído
            sem_prof = not prof.strip()

            # Flag 2: valor atípico — compara com mediana do MÊS do cancelamento
            preco_ref = _preco_ref(serv, data_iso)
            valor_atipico = False
            if not valor_zero and preco_ref and preco_ref > 0:
                valor_atipico = abs(v - preco_ref) / preco_ref > 0.20

            # Flag 3: match Stone (só faz sentido se tem valor)
            stone_matches = []
            match_por_nome = False
            if not valor_zero:
                stone_matches = stone_idx.get((data_iso, round(v, 2)), []) if data_iso else []
                cli_tokens = set(_norm_nome(cli))
                for m in stone_matches:
                    orig_tokens = set(_norm_nome(m["origem"]))
                    if cli_tokens & orig_tokens and len(cli_tokens & orig_tokens) >= 2:
                        match_por_nome = True
                        break

            # Nível de risco (valor_zero = 'info' por padrão, exceto se sem prof também)
            if match_por_nome:
                risco = "critico"
            elif stone_matches and not valor_atipico:
                risco = "revisar"
            elif valor_zero and sem_prof:
                risco = "atencao"       # zero valor E sem prof — anomalia dupla
            elif valor_zero:
                risco = "info"          # zero valor · walk-in que não virou venda
            elif sem_prof or valor_atipico:
                risco = "atencao"
            else:
                risco = "ok"

            canc_com_valor.append({
                "data": dt,
                "valor": v,
                "profissional": prof,
                "cliente": cli,
                "servico": serv,
                "sem_prof": sem_prof,
                "valor_atipico": valor_atipico,
                "valor_zero": valor_zero,
                "preco_ref": preco_ref,
                "stone_match_n": len(stone_matches),
                "stone_match_nomes": [m["origem"] for m in stone_matches],
                "match_por_nome": match_por_nome,
                "risco": risco,
            })
    canc_com_valor.sort(key=lambda x: x["data"], reverse=True)

    # Agregações
    canc_por_prof = defaultdict(lambda: {"n": 0, "v": 0.0})
    canc_por_serv = defaultdict(lambda: {"n": 0, "v": 0.0})
    for x in canc_com_valor:
        p = x["profissional"] or "—"
        s = x["servico"] or "—"
        canc_por_prof[p]["n"] += 1; canc_por_prof[p]["v"] += x["valor"]
        canc_por_serv[s]["n"] += 1; canc_por_serv[s]["v"] += x["valor"]

    resumo_risco = Counter(x["risco"] for x in canc_com_valor)

    payload = {
        # UTC com sufixo Z para JavaScript interpretar corretamente
        "gerado_em": datetime.now(BRT).isoformat(timespec="seconds"),
        "hoje": hoje.isoformat(),
        "meta_mensal_valor": META_MENSAL,
        "dias_op_mes": DIAS_OP_MES,
        "sazonalidade": {
            "peso_dow": {DOW_NOMES[i]: round(peso_dow[i]*100, 1) for i in range(7)},
            "meta_dia_por_dow": {DOW_NOMES[i]: meta_dia_por_dow[i] for i in range(7)},
            "n_dias_dow_mes": {DOW_NOMES[i]: n_dias_dow_mes[i] for i in range(7)},
            "curva_horaria": curva_horaria,
            "amostra_dias_ano": len(dias_vistos),
        },
        "cota_api": cota_final,
        "stone": stone_data,
        "auditoria_cancelados": {
            "n_com_valor": len(canc_com_valor),
            "v_total": round(sum(x["valor"] for x in canc_com_valor), 2),
            "excluidos_inauguracao_n": canc_excluidos_inaug,
            "excluidos_inauguracao_v": round(canc_excluidos_valor, 2),
            "data_corte": "2026-07-23",
            "resumo_risco": dict(resumo_risco),
            "por_profissional": sorted(
                [{"nome": p, "n": d["n"], "v": round(d["v"], 2)} for p, d in canc_por_prof.items()],
                key=lambda x: -x["v"],
            ),
            "por_servico": sorted(
                [{"nome": s, "n": d["n"], "v": round(d["v"], 2)} for s, d in canc_por_serv.items()],
                key=lambda x: -x["v"],
            ),
            "lista": canc_com_valor,
        },
        "abas": {
            "anual": {
                "kpis": a_anual["kpis"], "meta": meta_ano, "categorias": a_anual["categorias"],
                "meses": meses, "top_ltv": ltv_ano,
                "novos_vs_recorr": nvr_ano,
                "rentabilidade_hora": a_anual["rentabilidade_hora"],
                "hora_media": hora_media(a_anual["hora_abs"], a_anual["kpis"]["dias_op"]),
                "ranking_prof": a_anual["ranking_prof"],
                "ranking_prof_total_n": a_anual.get("ranking_prof_total_n", 0),
                "ranking_serv": a_anual["ranking_serv"],
                "meios_pagamento": a_anual["meios_pagamento"], "descontos": a_anual["descontos"],
                "clientes_top": a_anual["clientes_top"],
                "cadeiras_utilizacao": a_anual["cadeiras_utilizacao"],
                "densidade_hora": a_anual["densidade_hora"],
                "churn_early": churn,
                "cross_sell": cross_sell_data,
                "aniversariantes": aniversariantes,
            },
            "mensal": {
                "kpis": a_mensal["kpis"], "meta": meta_mensal, "categorias": a_mensal["categorias"],
                "novos_vs_recorr": nvr_mes, "rentabilidade_hora": a_mensal["rentabilidade_hora"],
                "por_dia_mes": a_mensal["por_dia_mes"],
                "hora_media": hora_media(a_mensal["hora_abs"], a_mensal["kpis"]["dias_op"]),
                "ranking_prof": a_mensal["ranking_prof"],
                "ranking_prof_total_n": a_mensal.get("ranking_prof_total_n", 0),
                "ranking_serv": a_mensal["ranking_serv"],
                "meios_pagamento": a_mensal["meios_pagamento"], "descontos": a_mensal["descontos"],
                "clientes_top": a_mensal["clientes_top"],
                "cadeiras_utilizacao": a_mensal["cadeiras_utilizacao"],
                "densidade_hora": a_mensal["densidade_hora"],
            },
            "semanal": {
                "kpis": {**a_semanal["kpis"], "periodo_ini": seg.isoformat(), "periodo_fim": dom.isoformat()},
                "meta": meta_sem, "categorias": a_semanal["categorias"],
                "novos_vs_recorr": nvr_sem,
                "por_dow": a_semanal["por_dow"],
                "hora_media": hora_media(a_semanal["hora_abs"], a_semanal["kpis"]["dias_op"]),
                "ranking_prof": a_semanal["ranking_prof"],
                "ranking_prof_total_n": a_semanal.get("ranking_prof_total_n", 0),
                "ranking_serv": a_semanal["ranking_serv"],
                "rentabilidade_hora": a_semanal["rentabilidade_hora"],
                "meios_pagamento": a_semanal["meios_pagamento"],
                "clientes_top": a_semanal["clientes_top"],
                "semana_anterior": semana_anterior,
                "cadeiras_utilizacao": a_semanal["cadeiras_utilizacao"],
                "densidade_hora": a_semanal["densidade_hora"],
            },
            "diario": {
                "kpis": {**a_diario["kpis"], "dia_semana": DOW_NOMES[hoje.weekday()], "data": hoje.isoformat()},
                "meta": meta_dia, "categorias": a_diario["categorias"],
                "hora_abs": a_diario["hora_abs"], "ranking_prof": a_diario["ranking_prof"],
                "ranking_prof_total_n": a_diario.get("ranking_prof_total_n", 0),
                "ranking_serv": a_diario["ranking_serv"],
                "rentabilidade_hora": a_diario["rentabilidade_hora"],
                "meios_pagamento": a_diario["meios_pagamento"],
                "clientes_top": a_diario["clientes_top"],
                "cadeiras_utilizacao": a_diario["cadeiras_utilizacao"],
                "densidade_hora": a_diario["densidade_hora"],
            },
        },
    }

    # ==== INSIGHTS acionaveis por aba ====
    try:
        from insights import gerar_insights
        payload["insights"] = gerar_insights(payload)
        n_total = sum(len(v) for v in payload["insights"].values())
        print(f"[insights] {n_total} recomendacoes geradas nas 5 abas")
    except Exception as e:
        print(f"[insights] erro: {e}")
        payload["insights"] = {}

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[github_refresh] OK · {OUT_JSON}")
    print(f"  Ano R$ {a_anual['kpis']['caixa']:.2f} · Mês R$ {a_mensal['kpis']['caixa']:.2f} · Sem R$ {a_semanal['kpis']['caixa']:.2f} · Hoje R$ {a_diario['kpis']['caixa']:.2f}")


if __name__ == "__main__":
    main()
