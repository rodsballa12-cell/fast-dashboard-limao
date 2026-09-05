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
CLIENTES_CACHE = REPO_ROOT / "data" / "clientes_detalhes.json"
PROF_CACHE = REPO_ROOT / "data" / "profissionais_cache.json"
CLIENTES_LISTA_CACHE = REPO_ROOT / "data" / "clientes_lista_cache.json"
SERV_CACHE = REPO_ROOT / "data" / "servicos_cache.json"
AGEND_DET_CACHE = REPO_ROOT / "data" / "agend_detail_cache.json"

# TTLs de cache (economia de API)
TTL_PROF_HORAS = 24 * 7   # profs quase nunca mudam
TTL_CLI_LISTA_HORAS = 24  # lista básica de clientes (só id/nome/tel) — 1×/dia suficiente
TTL_CATALOGO_HORAS = 24 * 7  # serviços/produtos catálogo mudam raro
TTL_AGEND_DET_HORAS = 72     # detalhe cancelado (quem/quando) não muda após 3d

# TIMEZONE: todo o pipeline opera em Brasília (UTC-3, sem DST desde 2019).
# Container do GitHub Actions roda em UTC, então nunca usar date.today() ou
# datetime.now() sem timezone — sempre datetime.now(BRT).
BRT = timezone(timedelta(hours=-3))


def parse_trinks_dt(s):
    """Parse defensivo de dataHoraInicio do Trinks.

    Hoje Trinks retorna ISO naive tipo "2026-08-22T17:32:00" (BRT local).
    Se um dia mudar pra vir com 'Z' ou '+00:00' (UTC), converte pra BRT antes
    de devolver — protege .date(), .hour, comparações etc contra shift de 3h
    silencioso. Aceita None e retorna None.
    """
    if not s:
        return None
    dt = datetime.fromisoformat(s.replace("Z", "+00:00")) if isinstance(s, str) else s
    if dt.tzinfo is not None:
        # veio com timezone → converte pra BRT e joga fora o tzinfo
        # (código atual assume naive-BRT em todas as comparações)
        dt = dt.astimezone(BRT).replace(tzinfo=None)
    return dt

# Config da loja (cadeiras físicas, horas de operação, mapping serviço→cadeira)
try:
    _cfg = json.loads(CONFIG_JSON.read_text(encoding="utf-8"))
except Exception:
    _cfg = {}
CADEIRAS_FIS = _cfg.get("cadeiras") or {"cabelo": 5, "maquiagem": 3, "unhas": 8}
HORAS_OPERACAO_DIA = _cfg.get("horas_operacao_dia", 12)
# Jornada de operação por dow (0=seg .. 6=dom). Default: 12h seg-sáb, 0 dom.
_horas_dow_cfg = _cfg.get("horas_operacao_por_dow") or {}
HORAS_POR_DOW = {i: float(_horas_dow_cfg.get(str(i), HORAS_OPERACAO_DIA if i < 6 else 0)) for i in range(7)}
# Data em que a loja passou (ou passará) a operar aos domingos. Se None ou futuro, dom = fechado.
_dom_ini_str = _cfg.get("data_inicio_domingo")
DATA_INICIO_DOM = date.fromisoformat(_dom_ini_str) if _dom_ini_str else None
CADEIRA_KEYWORDS = _cfg.get("cadeira_por_servico_keywords") or {}

# === METAS DA FRANQUEADORA (fixas, por categoria) ===
# Franqueadora define meta MENSAL por recepcionista pra 3 categorias específicas.
# Multiplicamos por N recepcionistas pra chegar no total da loja. O resto do
# META_MENSAL (60k) vai pra "serviços gerais" (escova + demais serviços que não
# são Fast Retoque). "Fast Retoque" é serviço com meta SEPARADA (não vai no bolo).
_metas_fr = _cfg.get("metas_franqueadora") or {}
N_RECEPCIONISTAS = int(_metas_fr.get("recepcionistas") or 1)
_por_rec = _metas_fr.get("por_recepcionista_mensal") or {}
METAS_CATEGORIA_MENSAL = {k: float(v) * N_RECEPCIONISTAS for k, v in _por_rec.items()}
# servicos_gerais = META_MENSAL - (pacotes + fast_retoque + produtos)
_subtotal_franq = sum(METAS_CATEGORIA_MENSAL.values())
FAST_RETOQUE_KEYWORDS = [k.upper() for k in (_metas_fr.get("fast_retoque_keywords") or ["RETOQUE"])]


def is_fast_retoque(nome_servico: str) -> bool:
    if not nome_servico: return False
    n = nome_servico.upper()
    return any(kw in n for kw in FAST_RETOQUE_KEYWORDS)


def opera_no_dia(d: date) -> bool:
    """True se a loja opera nesse dia (considera início do domingo)."""
    if d.weekday() != 6:
        return HORAS_POR_DOW[d.weekday()] > 0
    return DATA_INICIO_DOM is not None and d >= DATA_INICIO_DOM and HORAS_POR_DOW[6] > 0


def dias_operacionais_no_mes(ano: int, mes: int) -> int:
    ultimo = monthrange(ano, mes)[1]
    return sum(1 for d in range(1, ultimo + 1) if opera_no_dia(date(ano, mes, d)))


def classificar_cadeira(nome_serv):
    """Retorna 'cabelo' | 'maquiagem' | 'unhas' | 'outro' pelo nome do serviço."""
    if not nome_serv: return "outro"
    n = nome_serv.upper()
    for tipo, kws in CADEIRA_KEYWORDS.items():
        for kw in kws:
            if kw.upper() in n:
                return tipo
    return "outro"


class QuotaExhaustedError(RuntimeError):
    """Cota mensal Trinks esgotada. Retry inútil até virar mês — degrada com graça."""
    pass


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
                # 429 pode ser rate-limit por segundo (backoff resolve) OU cota mensal
                # esgotada (backoff não resolve, só desperdiça GH minutes). Duas tentativas
                # rápidas — se ainda 429, propaga QuotaExhaustedError pro caller decidir.
                if i >= 1:
                    raise QuotaExhaustedError(f"429 persistente em {path} — provavelmente cota mensal esgotada")
                delay = 10 * (i + 1)
                print(f"[trinks] {path} 429 rate-limit · aguarda {delay}s (tentativa {i+1}/2)")
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
    ag = [a for a in agend if a.get("dataHoraInicio") and ini <= parse_trinks_dt(a["dataHoraInicio"]).date() <= fim]
    fin = [a for a in ag if (a.get("status") or {}).get("nome") == "Finalizado"]
    canc = [a for a in ag if (a.get("status") or {}).get("nome") == "Cancelado"]
    em_at = [a for a in ag if (a.get("status") or {}).get("nome") == "Em atendimento"]

    tr = [t for t in transac if t.get("dataHora") and ini <= parse_trinks_dt(t["dataHora"]).date() <= fim]

    # KPIs base
    receita_serv = sum(float(a.get("valor") or 0) for a in fin)
    dias_com_op = len({parse_trinks_dt(a["dataHoraInicio"]).date() for a in fin})
    unicos = len({(a.get("cliente") or {}).get("id") for a in fin if (a.get("cliente") or {}).get("id")})
    # clientes-dia = ticket médio do Trinks (1 cliente em 1 dia = 1 visita)
    # mesmo cliente com N serviços no mesmo dia conta como 1; se voltar noutro dia, +1
    cliente_dia = {((a.get("cliente") or {}).get("id"),
                    parse_trinks_dt(a["dataHoraInicio"]).date())
                   for a in fin if (a.get("cliente") or {}).get("id")}
    n_cliente_dia = len(cliente_dia)

    # Categorias + caixa via transações
    caixa = 0.0
    pac_v = pac_n = 0
    prod_v = prod_n = 0
    serv_v = serv_n = 0
    # Fast Retoque: subset de serviços com meta específica da franqueadora.
    # Continua contando dentro de serv_v (pra compat) mas também separado.
    fast_retoque_v = 0.0; fast_retoque_n = 0
    descontos = 0.0
    trocos = 0.0
    mp_c = Counter(); mp_v = defaultdict(float)
    # PARCELAS por meio: {(meio, parcelas): {"n": count, "v": valor_total}}
    parcelas_agg = defaultdict(lambda: {"n": 0, "v": 0.0})
    # CATEGORIA nativa Trinks vinda de transacao.servicos[].categoria
    categoria_native = defaultdict(lambda: {"n": 0, "v": 0.0})
    hora_c = defaultdict(int); hora_v = defaultdict(float)

    for t in tr:
        for fp in (t.get("formasPagamentos") or []):
            v = float(fp.get("valor") or 0)
            caixa += v
            nome = fp.get("nome") or "outros"
            mp_c[nome] += 1; mp_v[nome] += v
            # Parcelas: 1 = à vista, >1 = parcelado (relevante pra cash-flow cartão)
            parc = int(fp.get("parcelas") or 1)
            parcelas_agg[(nome, parc)]["n"] += 1
            parcelas_agg[(nome, parc)]["v"] += v
        for p in (t.get("pacotes") or []):
            q = int(p.get("quantidade") or 1)
            pac_v += float(p.get("valorUnitario") or 0) * q
            pac_n += q
        for p in (t.get("produtos") or []):
            q = int(p.get("quantidade") or 1)
            prod_v += float(p.get("valorUnitario") or 0) * q
            prod_n += q
        for s in (t.get("servicos") or []):
            preco_s = float(s.get("preco") or 0)
            nome_s = s.get("nome") or ""
            serv_v += preco_s
            serv_n += 1
            if is_fast_retoque(nome_s):
                fast_retoque_v += preco_s
                fast_retoque_n += 1
            # Categoria nativa Trinks (quando presente)
            cat = s.get("categoria") or ""
            if isinstance(cat, dict): cat = cat.get("nome") or ""
            cat = (cat or "sem categoria").strip().title()
            categoria_native[cat]["n"] += 1
            categoria_native[cat]["v"] += float(s.get("preco") or 0)
        descontos += float(t.get("descontos") or 0)
        trocos += float(t.get("troco") or 0)
        dt = parse_trinks_dt(t["dataHora"])
        hora_c[dt.hour] += 1
        hora_v[dt.hour] += float(t.get("totalPagar") or 0)

    # Formatar parcelas pro payload
    parcelas_list = sorted(
        [{"meio": meio, "parcelas": p, "n": v["n"], "v": brl_round(v["v"])}
         for (meio, p), v in parcelas_agg.items()],
        key=lambda x: (-x["v"], x["meio"], x["parcelas"])
    )
    # Categoria nativa formatada e ordenada por receita
    categoria_native_list = sorted(
        [{"nome": k, "n": v["n"], "v": brl_round(v["v"]),
          "pct_receita": round(v["v"] / max(caixa, 1) * 100, 1)}
         for k, v in categoria_native.items()],
        key=lambda x: -x["v"]
    )

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

    # === PROFISSIONAL EXECUTOR (idProfissionalQueRealizouServico) ===
    # Vem da TRANSAÇÃO (não do agendamento). Compara com o prof da comanda pra detectar
    # divergências: comanda no nome de A, executado por B → verificar se é troca legítima
    # de escala ou anomalia de setup. Também dá o ranking REAL de execução por serviço.
    exec_agg = defaultdict(lambda: {"n": 0, "v": 0.0})
    exec_por_serv_receita = defaultdict(float)  # {(id_exec, nome_serv): valor}
    # Map id_prof → nome. Primeiro do agend (rápido); IDs órfãos ficam como "ID XXX"
    prof_id_nome = getattr(analisar, "_prof_id_nome_cache", None) or {}
    for a in fin:
        pid = (a.get("profissional") or {}).get("id")
        pnome = (a.get("profissional") or {}).get("nome") or ""
        if pid: prof_id_nome[pid] = pnome.strip().title()
    for tx in tr:
        for s in (tx.get("servicos") or []):
            exec_id = s.get("idProfissionalQueRealizouServico")
            if not exec_id: continue
            nome_exec = prof_id_nome.get(exec_id)
            if not nome_exec:
                # Prof desligado (ID não retorna em /v1/profissionais).
                # Marcador claro em vez de "ID 723073" cru.
                nome_exec = f"Prof desligado #{exec_id}"
            v = float(s.get("preco") or 0)
            exec_agg[nome_exec]["n"] += 1
            exec_agg[nome_exec]["v"] += v
            exec_por_serv_receita[(nome_exec, s.get("nome") or "sem")] += v
    ranking_prof_executor = sorted(
        [{"nome": k, "n_serv": v["n"], "v": brl_round(v["v"]),
          "ticket_medio_serv": brl_round(v["v"] / max(v["n"], 1))}
         for k, v in exec_agg.items()],
        key=lambda x: -x["v"]
    )

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

    # Capacidade DOW-aware: soma horas reais de cada dia operado no período
    # (dom = 6h vs seg-sáb = 12h). Antes usava 12h flat → distorcia domingo pra baixo.
    #
    # A janela é limitada aos dias que REALMENTE existiram como operação:
    #  - não conta dia futuro: na aba mensal, dia 2 do mês somava os 30 dias do mês
    #    inteiro e a utilização aparecia como 0,3% em vez de ~5%;
    #  - não conta dia anterior à abertura: a aba anual somava jan–jun, quando o
    #    salão nem existia, e mostrava 1,1% de utilização — o equivalente a 104h
    #    por cadeira por dia operado, que é impossível.
    # A data de abertura sai do próprio dado (primeiro atendimento registrado),
    # sem constante cravada.
    _hoje = datetime.now(BRT).date()
    _primeiro_atend = min(
        (parse_trinks_dt(a["dataHoraInicio"]).date()
         for a in agend if a.get("dataHoraInicio")),
        default=None,
    )
    _ini_cap = max(ini, _primeiro_atend) if _primeiro_atend else ini
    _fim_cap = min(fim, _hoje)
    horas_operacao_periodo = 0.0
    _cur = _ini_cap
    while _cur <= _fim_cap:
        if opera_no_dia(_cur):
            horas_operacao_periodo += HORAS_POR_DOW[_cur.weekday()]
        _cur += timedelta(days=1)

    cadeiras_detalhe = {}
    for tipo, n_cad in CADEIRAS_FIS.items():
        cap_h = n_cad * horas_operacao_periodo
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
            inicio = parse_trinks_dt(dt)
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
    # Média por hora (dividido por dias operados no período)
    dias_ref = max(dias_com_op, 1)
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
        dt = parse_trinks_dt(a["dataHoraInicio"])
        by_dow[DOW_NOMES[dt.weekday()]]["n"] += 1
        by_dow[DOW_NOMES[dt.weekday()]]["v"] += float(a.get("valor") or 0)
    dow_list = [{"nome": n, "n": by_dow[n]["n"], "v": brl_round(by_dow[n]["v"])} for n in DOW_NOMES]

    by_day = defaultdict(lambda: {"n": 0, "v": 0.0})
    for a in fin:
        dt = parse_trinks_dt(a["dataHoraInicio"])
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
            "fast_retoque": {"v": brl_round(fast_retoque_v), "n": fast_retoque_n, "pct": round(fast_retoque_v / max(caixa, 1) * 100, 1)},
            "servicos_gerais": {"v": brl_round(serv_v - fast_retoque_v), "n": max(serv_n - fast_retoque_n, 0),
                                "pct": round(max(serv_v - fast_retoque_v, 0) / max(caixa, 1) * 100, 1)},
        },
        "meios_pagamento": meios,
        "hora_abs": hora_abs,
        "por_dow": dow_list,
        "por_dia_mes": dia_list,
        "ranking_prof": ranking_prof,
        "ranking_prof_total_n": ranking_prof_total_n,
        "ranking_prof_executor": ranking_prof_executor,
        "ranking_serv": ranking_serv,
        "rentabilidade_hora": rent_hora,
        "clientes_top": top_cli,
        "descontos": brl_round(descontos),
        "trocos": brl_round(trocos),
        "parcelas": parcelas_list,
        "categoria_native": categoria_native_list,
    }


def marcar_dias_atipicos(historico_dias, min_amostras=3, lim_alto=2.0, lim_baixo=0.45):
    """Marca dias fora do padrão do PRÓPRIO dia da semana.

    A referência de cada dia é a mediana dos outros dias na mesma posição da
    semana, não a mediana geral. Testei com a mediana geral primeiro e ela
    acusou 01, 08, 15, 22 e 29/08 como anômalos — que são simplesmente todos
    os sábados de agosto. Sábado vale 41,9% do faturamento da semana e terça
    4,3%: contra a média geral, todo sábado é outlier e nenhuma terça nunca é.

    Devolve {data: {ratio, tipo, mediana_dow}} só para os dias marcados.
    """
    from statistics import median
    por_dow = defaultdict(list)
    for iso, bloco in historico_dias.items():
        caixa = (bloco.get("kpis") or {}).get("caixa") or 0
        if caixa > 0:
            por_dow[date.fromisoformat(iso).weekday()].append(caixa)

    marcados = {}
    for iso, bloco in historico_dias.items():
        caixa = (bloco.get("kpis") or {}).get("caixa") or 0
        if caixa <= 0:
            continue
        amostras = por_dow[date.fromisoformat(iso).weekday()]
        if len(amostras) < min_amostras:
            continue                      # poucos dados: não dá para dizer o que é normal
        med = median(amostras)
        if not med:
            continue
        ratio = caixa / med
        if ratio >= lim_alto or ratio <= lim_baixo:
            marcados[iso] = {
                "ratio": round(ratio, 2),
                "tipo": "alto" if ratio >= lim_alto else "baixo",
                "mediana_dow": brl_round(med),
                "caixa": brl_round(caixa),
            }
    return marcados


def peso_janela(ini: date, fim: date, peso_dow):
    """Fatia do faturamento de uma semana que os dias desta janela representam.

    peso_dow é indexado por weekday() e soma 1. Uma janela de sáb+dom+seg
    carrega muito mais expectativa de caixa que uma de ter+qua+qui, e comparar
    as duas pelo total bruto mede o calendário, não o negócio.
    """
    total, dias = 0.0, []
    cur = ini
    while cur <= fim:
        total += peso_dow.get(cur.weekday(), 0) or 0
        dias.append(DOW_NOMES[cur.weekday()])
        cur += timedelta(days=1)
    return total, dias


def calc_meta(caixa, meta, dias_real, dias_total):
    """KPIs de meta do período, com a meta proporcional aos dias já corridos.

    'pct' compara o realizado com a meta do período INTEIRO. No dia 3 de 30 ele
    sempre dá ~3%, o que não diz nada: claro que 3 dias não pagam 30. Por isso
    existe 'meta_ate_hoje' — a fatia da meta que caberia aos dias já corridos,
    na mesma competência. É contra ela que dá para saber se o mês está indo bem.

    Setembro/2026 no dia 3: R$ 1.949 contra os R$ 6.000 esperados até aqui =
    32,5%, e não os 3,2% que a leitura contra a meta cheia sugere.

    A mesma função serve mês, semana e ano, então a régua é a mesma nas três.
    """
    pct = caixa / max(meta, 1) * 100
    falta = meta - caixa
    dias_rest = max(dias_total - dias_real, 0)
    necessario = falta / max(dias_rest, 1) if dias_rest else 0
    ritmo = caixa / max(dias_real, 1)
    proj = ritmo * dias_total

    # Meta proporcional. Sem dias corridos ou sem dias totais não há fatia a
    # cobrar, e devolver 0 aqui produziria "realizado infinitamente acima".
    if dias_real > 0 and dias_total > 0:
        meta_ate_hoje = meta * dias_real / dias_total
        pct_ate_hoje = round(caixa / meta_ate_hoje * 100, 1) if meta_ate_hoje > 0 else None
        saldo_ate_hoje = brl_round(caixa - meta_ate_hoje)
    else:
        meta_ate_hoje = pct_ate_hoje = saldo_ate_hoje = None

    return {
        "meta": meta, "realizado": brl_round(caixa), "pct": round(pct, 1),
        "falta": brl_round(falta), "dias_realizados": dias_real, "dias_total": dias_total,
        "dias_restantes": dias_rest, "necessario_dia": brl_round(necessario),
        "ritmo_dia": brl_round(ritmo), "projecao": brl_round(proj),
        "projecao_pct": round(proj / max(meta, 1) * 100, 1),
        "meta_ate_hoje": brl_round(meta_ate_hoje) if meta_ate_hoje is not None else None,
        "pct_ate_hoje": pct_ate_hoje,
        "saldo_ate_hoje": saldo_ate_hoje,
    }


def top_ltv(agend, ini: date, fim: date, limite=15):
    ltv = defaultdict(lambda: {"n": 0, "v": 0.0, "nome": ""})
    for a in agend:
        if (a.get("status") or {}).get("nome") != "Finalizado": continue
        dt = parse_trinks_dt(a["dataHoraInicio"]).date() if a.get("dataHoraInicio") else None
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


def novos_vs_recorr(fin_mes, cadastro_map, ini_mes: date, criterio: str = "cadastro_vs_periodo"):
    """
    Classifica clientes como novos vs recorrentes.

    criterio='cadastro_vs_periodo' (padrão para MES/SEMANA):
        novo = cliente cadastrado dentro do período
        recorrente = cliente cadastrado antes do período (já era cliente)

    criterio='visitas_no_periodo' (recomendado para ANO ou períodos > 90 dias):
        novo = cliente com apenas 1 atendimento no período (não retornou)
        recorrente = cliente com 2+ atendimentos no período (retornou)
        Motivo: se o período é grande OU cobre toda a operação da loja,
        a data de cadastro sempre cai dentro dele → todos viram "novos" e
        recorrentes = 0. A retenção real vira invisível.
    """
    if criterio == "visitas_no_periodo":
        # Conta atendimentos por cliente no período
        atend_por_cid = {}
        for a in fin_mes:
            cid = (a.get("cliente") or {}).get("id")
            if cid is None: continue
            atend_por_cid[cid] = atend_por_cid.get(cid, 0) + 1
        novos_ids = {cid for cid, n in atend_por_cid.items() if n == 1}
        rec_ids = {cid for cid, n in atend_por_cid.items() if n >= 2}
    else:
        # Critério padrão (cadastro vs período) — bom para janelas curtas
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
    # BRT global no módulo (ver definição no topo)
    hoje = datetime.now(BRT).date()
    ini_ano = date(hoje.year, 1, 1)
    fim_ano = date(hoje.year, 12, 31)
    ini_mes = date(hoje.year, hoje.month, 1)
    fim_mes = date(hoje.year, hoje.month, monthrange(hoje.year, hoje.month)[1])
    seg = hoje - timedelta(days=hoje.weekday())
    dom = seg + timedelta(days=6)

    print(f"[github_refresh] Períodos: ano={ini_ano}..{fim_ano} · mês={ini_mes}..{fim_mes} · sem={seg}..{dom} · hoje={hoje}")
    # (chamada única de /v1/consumo movida pro fim do run — economiza 1 req)

    _api_count = {"n": 0}  # contador local pra reportar consumo do run

    def _cache_valido(path, ttl_horas):
        """True se cache existe e é mais novo que TTL."""
        if not path.exists(): return False
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            gerado = datetime.fromisoformat(data.get("gerado_em", "").replace("Z", "+00:00"))
            if gerado.tzinfo is None: gerado = gerado.replace(tzinfo=BRT)
            idade = (datetime.now(BRT) - gerado).total_seconds() / 3600
            return idade < ttl_horas
        except Exception: return False

    def _load_cache(path):
        return json.loads(path.read_text(encoding="utf-8")).get("payload") or []

    def _save_cache(path, payload):
        path.write_text(json.dumps({
            "gerado_em": datetime.now(BRT).isoformat(timespec="seconds"),
            "payload": payload,
        }, ensure_ascii=False), encoding="utf-8")

    # === AGENDAMENTOS ===
    # Ano inteiro só aos domingos (refresh semanal do histórico). Nos outros
    # dias, puxa só o MÊS CORRENTE fresh e mescla com o cache do ano.
    # Economia: 5-7 req/run × 6 dias/semana × 8 runs/dia = ~250 req/semana.
    # Se cache não existe (primeira execução), força pull do ano.
    AGEND_ANO_CACHE = REPO_ROOT / "data" / "agendamentos_ano_cache.json"
    eh_domingo = hoje.weekday() == 6
    cache_existe = AGEND_ANO_CACHE.exists()
    if eh_domingo or not cache_existe:
        motivo = "domingo · refresh semanal" if eh_domingo else "cache miss"
        print(f"[fetch] agendamentos ANO ({motivo})...")
        agend_ano = list(t.paginate("/v1/agendamentos", {"dataInicio": ini_ano.isoformat(), "dataFim": fim_ano.isoformat()}))
        AGEND_ANO_CACHE.write_text(json.dumps({
            "gerado_em": datetime.now(BRT).isoformat(timespec="seconds"),
            "payload": agend_ano,
        }, ensure_ascii=False), encoding="utf-8")
        print(f"  {len(agend_ano)} agendamentos · cache atualizado")
    else:
        cache_data = json.loads(AGEND_ANO_CACHE.read_text(encoding="utf-8"))
        agend_ano = cache_data.get("payload") or []
        cache_ger = cache_data.get("gerado_em", "?")[:10]
        print(f"[fetch] agendamentos ANO (cache local · último domingo {cache_ger})")

    # Sempre puxa o MÊS CORRENTE fresh — cancelamentos, "em atendimento agora",
    # atendimentos novos entram aqui e sobrescrevem o range mensal do cache.
    print("[fetch] agendamentos MÊS corrente (fresh)...")
    agend_mes = list(t.paginate("/v1/agendamentos", {"dataInicio": ini_mes.isoformat(), "dataFim": fim_mes.isoformat()}))
    print(f"  {len(agend_mes)} agendamentos do mês")

    # Merge: cache ano SEM mês corrente + mês corrente fresh
    ini_mes_iso = ini_mes.isoformat()
    fim_mes_iso = fim_mes.isoformat()
    agend = [a for a in agend_ano
             if a.get("dataHoraInicio")
             and not (ini_mes_iso <= a["dataHoraInicio"][:10] <= fim_mes_iso)]
    agend.extend(agend_mes)
    print(f"[fetch] agendamentos merged: {len(agend)} total")

    # === TRANSAÇÕES · mesma estratégia dos agendamentos ===
    TRANSAC_ANO_CACHE = REPO_ROOT / "data" / "transacoes_ano_cache.json"
    cache_tx_existe = TRANSAC_ANO_CACHE.exists()
    if eh_domingo or not cache_tx_existe:
        motivo = "domingo · refresh semanal" if eh_domingo else "cache miss"
        print(f"[fetch] transacoes ANO ({motivo})...")
        transac_ano = list(t.paginate("/v1/transacoes", {"dataInicio": ini_ano.isoformat(), "dataFim": fim_ano.isoformat()}))
        TRANSAC_ANO_CACHE.write_text(json.dumps({
            "gerado_em": datetime.now(BRT).isoformat(timespec="seconds"),
            "payload": transac_ano,
        }, ensure_ascii=False), encoding="utf-8")
        print(f"  {len(transac_ano)} transações · cache atualizado")
    else:
        cache_tx = json.loads(TRANSAC_ANO_CACHE.read_text(encoding="utf-8"))
        transac_ano = cache_tx.get("payload") or []
        cache_ger = cache_tx.get("gerado_em", "?")[:10]
        print(f"[fetch] transacoes ANO (cache local · último domingo {cache_ger})")

    print("[fetch] transacoes MÊS corrente (fresh)...")
    transac_mes = list(t.paginate("/v1/transacoes", {"dataInicio": ini_mes.isoformat(), "dataFim": fim_mes.isoformat()}))
    print(f"  {len(transac_mes)} transações do mês")

    # Merge: cache ano SEM mês corrente + mês corrente fresh
    transac = [x for x in transac_ano
               if x.get("dataHora")
               and not (ini_mes_iso <= x["dataHora"][:10] <= fim_mes_iso)]
    transac.extend(transac_mes)
    print(f"[fetch] transacoes merged: {len(transac)} total")

    # === CLIENTES LISTA · cache 12h (base muda pouco durante o dia) ===
    if _cache_valido(CLIENTES_LISTA_CACHE, TTL_CLI_LISTA_HORAS):
        clientes = _load_cache(CLIENTES_LISTA_CACHE)
        print(f"[fetch] clientes: {len(clientes)} (cache local · <{TTL_CLI_LISTA_HORAS}h)")
    else:
        print("[fetch] clientes...")
        clientes = list(t.paginate("/v1/clientes"))
        print(f"  {len(clientes)} clientes")
        _save_cache(CLIENTES_LISTA_CACHE, clientes)

    # === PROFISSIONAIS · cache 7 dias (mudança rara) ===
    # Formato do cache v2: {"prof_map": {id: nome}, "prof_meta": {id: {...}}}.
    # prof_map indexa por AMBOS `id` e `idProfissional` (chaves diferentes que o Trinks
    # devolve: `id` no cadastro, `idProfissional` no vínculo com estabelecimento) —
    # resolve o bug do executor aparecer como "Prof desligado" quando idProfissional
    # do serviço não bate com `id` do cadastro.
    prof_map_global = {}
    prof_meta_global = {}
    cache_ok = False
    if _cache_valido(PROF_CACHE, TTL_PROF_HORAS):
        payload_cache = _load_cache(PROF_CACHE)
        if isinstance(payload_cache, dict) and "prof_map" in payload_cache:
            prof_map_global = {int(k): v for k, v in payload_cache["prof_map"].items()}
            prof_meta_global = {int(k): v for k, v in (payload_cache.get("prof_meta") or {}).items()}
            cache_ok = True
            print(f"[fetch] profissionais: {len(prof_meta_global)} cadastros · {len(prof_map_global)} chaves (cache v2 · <{TTL_PROF_HORAS}h)")
    if not cache_ok:
        print("[fetch] profissionais (v2 · id + idProfissional + metadata)...")
        for ativo_flag in ("true", "false"):
            try:
                prof_lista = list(t.paginate("/v1/profissionais", {"ativo": ativo_flag}))
                for p in prof_lista:
                    pid = p.get("id")
                    id_prof_vinc = p.get("idProfissional")  # chave usada em servicos[].idProfissionalQueRealizouServico
                    nome = (p.get("nome") or "").strip().title()
                    if not nome:
                        continue
                    # Indexa por AMBAS as chaves apontando pro mesmo nome
                    if pid: prof_map_global[pid] = nome
                    if id_prof_vinc and id_prof_vinc != pid:
                        prof_map_global[id_prof_vinc] = nome
                    # Metadata rica pro ranking/insights (função, status, agenda, apelido)
                    if pid:
                        prof_meta_global[pid] = {
                            "nome": nome,
                            "apelido": (p.get("apelido") or "").strip(),
                            "funcao": (p.get("funcao") or "").strip() if isinstance(p.get("funcao"), str) else ((p.get("funcao") or {}).get("nome") or "").strip(),
                            "status": p.get("status") or ("ativo" if ativo_flag == "true" else "inativo"),
                            "possui_agenda": bool(p.get("possuiAgenda")),
                            "id_profissional": id_prof_vinc,
                            "genero": (p.get("genero") or "").strip()[:1].upper(),
                        }
            except Exception as e:
                print(f"  [warn] /v1/profissionais ativo={ativo_flag} falhou: {e}")
        _save_cache(PROF_CACHE, {"prof_map": prof_map_global, "prof_meta": prof_meta_global})
        print(f"  {len(prof_meta_global)} cadastros · {len(prof_map_global)} chaves indexadas (id + idProfissional)")
    analisar._prof_id_nome_cache = prof_map_global

    # === CATÁLOGO SERVIÇOS · /v1/servicos (cache 7d) ===
    # Preço-tabela oficial (source of truth) pra comparar contra preço mediano praticado.
    # Detecta descontos sistemáticos ou serviços cobrados acima da tabela.
    servicos_catalogo = []
    if _cache_valido(SERV_CACHE, TTL_CATALOGO_HORAS):
        servicos_catalogo = _load_cache(SERV_CACHE)
        print(f"[fetch] servicos catalogo: {len(servicos_catalogo)} (cache · <{TTL_CATALOGO_HORAS}h)")
    else:
        print("[fetch] servicos catalogo...")
        try:
            servicos_catalogo = list(t.paginate("/v1/servicos"))
            _save_cache(SERV_CACHE, servicos_catalogo)
            print(f"  {len(servicos_catalogo)} serviços no catálogo")
        except Exception as e:
            print(f"  [warn] /v1/servicos falhou: {e}")

    tabela_precos = {}
    for s in servicos_catalogo:
        nome = (s.get("nome") or "").strip()
        preco = float(s.get("preco") or s.get("valor") or 0)
        if nome and preco > 0:
            tabela_precos[nome] = {"preco": preco, "duracao": s.get("duracaoEmMinutos") or 0,
                                    "categoria": (s.get("categoria") or {}).get("nome") if isinstance(s.get("categoria"), dict) else s.get("categoria")}

    # === COMISSÕES · /v1/profissionais/comissoes ===
    # Endpoint existe (200 OK) mas está sem cadastro no Trinks hoje (totalRecords=0).
    # Código pronto pra ler quando comissão for cadastrada no Trinks — evita novo deploy.
    comissoes_data = {"habilitado": False, "n_regras": 0, "regras": [], "obs": ""}
    try:
        cm_resp = t.get("/v1/profissionais/comissoes", {"pageSize": 200})
        regras = cm_resp.get("data") if isinstance(cm_resp, dict) else []
        if regras:
            comissoes_data["habilitado"] = True
            comissoes_data["n_regras"] = len(regras)
            for r in regras:
                pid = r.get("idProfissional") or r.get("id")
                nome_prof = prof_map_global.get(pid) or (prof_meta_global.get(pid) or {}).get("nome") or f"ID {pid}"
                comissoes_data["regras"].append({
                    "profissional_id": pid,
                    "profissional": nome_prof,
                    "servico": (r.get("servico") or {}).get("nome") if isinstance(r.get("servico"), dict) else r.get("servico"),
                    "percentual": r.get("percentual") or r.get("valorPercentual"),
                    "valor_fixo": r.get("valorFixo"),
                    "tipo": r.get("tipo") or r.get("tipoComissao"),
                })
            print(f"[comissoes] {len(regras)} regras cadastradas no Trinks")
        else:
            comissoes_data["obs"] = "endpoint OK mas sem regras cadastradas no Trinks"
            print("[comissoes] endpoint OK · totalRecords=0 (cadastrar no Trinks pra ativar)")
    except Exception as e:
        comissoes_data["obs"] = f"falha ao ler: {type(e).__name__}"
        print(f"[comissoes] falha (não-fatal): {e}")

    # === ENRIQUECIMENTO: buscar clienteDetalhes via /v1/clientes/{id} (com cache) ===
    # A rota lista traz o básico, mas /v1/clientes/{id} traz dataNascimento, endereço,
    # comoNosConheceu, gênero, cpf, email, etc. Cachear em data/clientes_detalhes.json
    # pra não queimar cota a cada refresh.
    detalhes_cache = {}
    if CLIENTES_CACHE.exists():
        try:
            detalhes_cache = json.loads(CLIENTES_CACHE.read_text(encoding="utf-8"))
        except Exception:
            detalhes_cache = {}
    # ⚡ DEFESA DE COTA: só enriquecer IDs que realmente têm visita registrada.
    # Base cadastrada tem MUITO cliente inativo (walk-in que passou uma vez e nunca
    # mais). Detalhar todos queima cota sem retorno. Só quem visitou aparece nas
    # análises → só quem visitou merece detalhe rico.
    ids_com_visita = {str((a.get("cliente") or {}).get("id"))
                      for a in agend if (a.get("cliente") or {}).get("id")}
    ids_hoje = {str(c.get("id")) for c in clientes if c.get("id")} & ids_com_visita
    ids_ja_cacheados = set(detalhes_cache.keys())
    ids_novos = list(ids_hoje - ids_ja_cacheados)
    # Cache miss → buscar. Limite defensivo (evita queimar cota se ID list explode)
    MAX_FETCH_POR_RUN = 50  # antes 200 — reduzido pra proteger cota mensal (10k/mês)
    if len(ids_novos) > MAX_FETCH_POR_RUN:
        print(f"[detalhes] {len(ids_novos)} clientes novos c/ visita; limitando a {MAX_FETCH_POR_RUN} nesta run")
        ids_novos = ids_novos[:MAX_FETCH_POR_RUN]
    if ids_novos:
        print(f"[detalhes] buscando {len(ids_novos)} clientes novos via /v1/clientes/{{id}}")
        for i, cid in enumerate(ids_novos, 1):
            try:
                det = t.get(f"/v1/clientes/{cid}")
                if isinstance(det, dict):
                    detalhes_cache[cid] = det
                if i % 25 == 0:
                    print(f"  {i}/{len(ids_novos)}...")
            except Exception as e:
                print(f"  [detalhes] {cid} falhou: {e}")
        # Persistir cache
        CLIENTES_CACHE.write_text(json.dumps(detalhes_cache, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[detalhes] cache atualizado · total {len(detalhes_cache)} clientes")
    cad_map = {}
    aniv_map = {}         # {id: (mm, dd, nome)}
    tel_map = {}          # {id: "+55 11 9XXXX-XXXX"}
    canal_map = {}        # {id: comoNosConheceu} · Instagram/WhatsApp/indicação
    genero_map = {}       # {id: F|M|Outro}
    bairro_map = {}       # {id: bairro}
    obs_map = {}          # {id: observacoes} · alergias, preferências
    email_map = {}
    for c in clientes:
        cid = c.get("id")
        if not cid: continue
        if c.get("dataCadastro"):
            try: cad_map[cid] = parse_trinks_dt(c["dataCadastro"])
            except Exception: pass
        # Telefone (formato: {"ddi":"55","ddd":"11","telefone":"XXX"})
        tels = c.get("telefones") or []
        if tels and isinstance(tels[0], dict):
            t0 = tels[0]
            ddi = t0.get("ddi") or "55"; ddd = t0.get("ddd") or ""; num = t0.get("telefone") or ""
            if num:
                # Formato brasileiro padrão
                if len(num) == 9: num_fmt = f"{num[:5]}-{num[5:]}"
                elif len(num) == 8: num_fmt = f"{num[:4]}-{num[4:]}"
                else: num_fmt = num
                tel_map[cid] = f"+{ddi} ({ddd}) {num_fmt}"
        # Detalhes ricos (do cache)
        det = detalhes_cache.get(str(cid)) or {}
        # dataNascimento — pode estar no top-level ou nos detalhes
        dn_str = c.get("dataNascimento") or det.get("dataNascimento")
        if dn_str:
            try:
                dn = parse_trinks_dt(dn_str)
                aniv_map[cid] = (dn.month, dn.day, c.get("nome") or det.get("nome") or "")
            except Exception: pass
        # comoNosConheceu — canal de aquisição.
        # O Trinks devolve um objeto {"id": 941, "descricao": "Instagram"}. O código
        # antigo lia canal.get("nome"), chave que não existe nessa rota: o resultado
        # era None para TODO cliente, e o painel mostrava "cobertura 0%" com 328
        # clientes sem dado — quando na verdade ~69% da base tem o canal preenchido.
        # Por isso o funil caía nos cenários de ROAS chutados em vez de usar a
        # atribuição real. Aceita 'descricao' e 'nome' para não quebrar se a rota mudar.
        canal = det.get("comoNosConheceu")
        if canal:
            if isinstance(canal, str):
                nome_canal = canal
            elif isinstance(canal, dict):
                nome_canal = canal.get("descricao") or canal.get("nome") or ""
            else:
                nome_canal = ""
            nome_canal = nome_canal.strip().title()
            if nome_canal:
                canal_map[cid] = nome_canal
        # gênero / sexo
        g = det.get("genero") or det.get("sexo")
        if g:
            g_str = str(g).strip().upper()[:1]
            genero_map[cid] = g_str if g_str in "FM" else "O"
        # endereço → bairro
        end = det.get("endereco") or {}
        if isinstance(end, dict):
            bairro = end.get("bairro") or ""
            if bairro: bairro_map[cid] = bairro.strip().title()
        # observações
        obs = det.get("observacoes")
        if obs and str(obs).strip():
            obs_map[cid] = str(obs).strip()[:200]
        # email
        em = c.get("email") or det.get("email")
        if em: email_map[cid] = em

    # Análises por período
    a_anual = analisar(agend, transac, ini_ano, fim_ano)
    a_mensal = analisar(agend, transac, ini_mes, fim_mes)
    a_semanal = analisar(agend, transac, seg, dom)
    a_diario = analisar(agend, transac, hoje, hoje)

    # === HISTÓRICO NAVEGÁVEL: semanas e dias ===
    # Permite que o dashboard permita navegar ◀ ▶ entre períodos passados.
    historico_semanas = {}
    d = ini_ano - timedelta(days=ini_ano.weekday())  # segunda da semana de ini_ano
    while d <= hoje:
        d_dom = d + timedelta(days=6)
        ini_sem = max(d, ini_ano)
        fim_sem = min(d_dom, hoje)
        a = analisar(agend, transac, ini_sem, fim_sem)
        if a["kpis"]["atend_fin"] > 0 or a["kpis"]["atend_total"] > 0:
            iso_year, iso_week, _ = d.isocalendar()
            kw = f"{iso_year}-W{iso_week:02d}"
            historico_semanas[kw] = {
                "periodo_ini": ini_sem.isoformat(),
                "periodo_fim": fim_sem.isoformat(),
                "kpis": a["kpis"],
                "categorias": a.get("categorias", {}),
                "novos_vs_recorr": novos_vs_recorr(
                    [x for x in agend if (x.get("status") or {}).get("nome") == "Finalizado"
                     and x.get("dataHoraInicio")
                     and ini_sem <= parse_trinks_dt(x["dataHoraInicio"]).date() <= fim_sem],
                    cad_map, ini_sem),
            }
        d += timedelta(days=7)

    # Últimos 60 dias com atendimentos
    historico_dias = {}
    for i in range(60):
        dd = hoje - timedelta(days=i)
        if dd < ini_ano: break
        a = analisar(agend, transac, dd, dd)
        if a["kpis"]["atend_fin"] > 0 or a["kpis"]["atend_total"] > 0:
            historico_dias[dd.isoformat()] = {
                "kpis": a["kpis"],
                "categorias": a.get("categorias", {}),
            }

    fin_mes = [a for a in agend if (a.get("status") or {}).get("nome") == "Finalizado"
               and a.get("dataHoraInicio")
               and ini_mes <= parse_trinks_dt(a["dataHoraInicio"]).date() <= fim_mes]
    nvr_mes = novos_vs_recorr(fin_mes, cad_map, ini_mes)

    # novos_vs_recorr também pra semanal e anual
    fin_sem = [a for a in agend if (a.get("status") or {}).get("nome") == "Finalizado"
               and a.get("dataHoraInicio") and seg <= parse_trinks_dt(a["dataHoraInicio"]).date() <= dom]
    nvr_sem = novos_vs_recorr(fin_sem, cad_map, seg)
    fin_ano = [a for a in agend if (a.get("status") or {}).get("nome") == "Finalizado"
               and a.get("dataHoraInicio") and ini_ano <= parse_trinks_dt(a["dataHoraInicio"]).date() <= fim_ano]
    # Para o ano usamos 'visitas_no_periodo': novo = 1 atend, recorrente = 2+
    # (a lógica 'cadastro_vs_periodo' zera os recorrentes quando a loja abriu
    # dentro do período — todos os clientes ficam classificados como novos)
    nvr_ano = novos_vs_recorr(fin_ano, cad_map, ini_ano, criterio="visitas_no_periodo")

    ltv_ano = top_ltv(agend, ini_ano, fim_ano)

    # === Semana anterior — MESMA JANELA (apples-to-apples) ===
    # Se hoje é quarta (3 dias na semana atual: seg-ter-qua), comparar com
    # seg-ter-qua da semana passada — não com a semana inteira anterior.
    seg_ant = seg - timedelta(days=7)
    dias_semana_atu = (hoje - seg).days  # 0=seg, 1=ter, ..., 6=dom
    fim_janela_sem_ant = seg_ant + timedelta(days=dias_semana_atu)
    a_sem_ant = analisar(agend, transac, seg_ant, fim_janela_sem_ant)
    dom_ant_full = seg_ant + timedelta(days=6)
    semana_anterior = {
        "periodo_ini": seg_ant.isoformat(),
        "periodo_fim": fim_janela_sem_ant.isoformat(),
        "janela_dias": dias_semana_atu + 1,
        "sem_completa_fim": dom_ant_full.isoformat(),
        "caixa": a_sem_ant["kpis"]["caixa"], "atend_fin": a_sem_ant["kpis"]["atend_fin"],
        "n_trans": a_sem_ant["kpis"]["n_trans"], "ticket_trans": a_sem_ant["kpis"]["ticket_trans"],
        "ticket_medio": a_sem_ant["kpis"]["ticket_medio"],
        "cliente_dia": a_sem_ant["kpis"]["cliente_dia"],
        "dias_op": a_sem_ant["kpis"]["dias_op"],
    }

    # === Mês anterior — MESMA JANELA de dias (comparação direta) ===
    # Setembro 01-03 vs Agosto 01-03 — mesmos dias corridos, apples-to-apples.
    # É a comparação mais literal: "aos mesmos dias do mês passado, como
    # estávamos?". Sem média, sem projeção — só o número que existiu.
    if hoje.month == 1:
        ini_mes_ant = date(hoje.year - 1, 12, 1)
    else:
        ini_mes_ant = date(hoje.year, hoje.month - 1, 1)
    ult_dia_mes_ant = monthrange(ini_mes_ant.year, ini_mes_ant.month)[1]
    fim_janela_ant = date(ini_mes_ant.year, ini_mes_ant.month, min(hoje.day, ult_dia_mes_ant))
    a_mes_ant = analisar(agend, transac, ini_mes_ant, fim_janela_ant)
    mes_anterior_kpis = {
        "periodo_ini": ini_mes_ant.isoformat(),
        "periodo_fim": fim_janela_ant.isoformat(),
        "janela_dias": hoje.day,
        "caixa": a_mes_ant["kpis"]["caixa"], "atend_fin": a_mes_ant["kpis"]["atend_fin"],
        "cliente_dia": a_mes_ant["kpis"]["cliente_dia"], "ticket_medio": a_mes_ant["kpis"]["ticket_medio"],
        "dias_op": a_mes_ant["kpis"]["dias_op"],
    }

    # === Mesmo DOW semana passada — MESMA HORA-JANELA (apples-to-apples) ===
    # Comparar hoje-13h (parcial) com quinta-passada-inteira (fechada) distorce.
    # Fix: filtrar transações/agendamentos do dia_ant até a hora atual, pra
    # ambos os lados representarem "o mesmo pedaço do dia".
    hoje_ant = hoje - timedelta(days=7)
    agora_dt = datetime.now(BRT)
    hora_num = agora_dt.hour + agora_dt.minute / 60.0
    def _no_dia_ate_hora(dt_str, dia_alvo, hora_lim):
        dt = parse_trinks_dt(dt_str)
        if not dt or dt.date() != dia_alvo: return False
        return (dt.hour + dt.minute/60.0) <= hora_lim
    agend_dia_ant_parcial = [a for a in agend
                              if a.get("dataHoraInicio")
                              and _no_dia_ate_hora(a["dataHoraInicio"], hoje_ant, hora_num)]
    transac_dia_ant_parcial = [t for t in transac
                                if t.get("dataHora")
                                and _no_dia_ate_hora(t["dataHora"], hoje_ant, hora_num)]
    a_dia_ant = analisar(agend_dia_ant_parcial, transac_dia_ant_parcial, hoje_ant, hoje_ant)
    dia_anterior_kpis = {
        "data": hoje_ant.isoformat(),
        "hora_max": round(hora_num, 2),
        "caixa": a_dia_ant["kpis"]["caixa"], "atend_fin": a_dia_ant["kpis"]["atend_fin"],
        "cliente_dia": a_dia_ant["kpis"]["cliente_dia"], "ticket_medio": a_dia_ant["kpis"]["ticket_medio"],
        "dias_op": a_dia_ant["kpis"]["dias_op"] or 1,  # se hora atual muito cedo, evita div/0
    }

    def _delta_pct(atual, ant):
        if not ant or ant == 0:
            return None
        return round((atual - ant) / ant * 100, 1)

    def _delta_pct_perdia(atual, ant, dias_atu, dias_ant):
        """Delta normalizado por dias COM movimento. Exposto como leitura
        secundária — ver o comentário do laço abaixo para por que não é o
        número principal."""
        if not dias_atu or not dias_ant or not ant: return None
        return _delta_pct(atual / dias_atu, ant / dias_ant)

    # Injeta deltas nos KPIs de cada aba.
    #
    # O delta principal é BRUTO, não normalizado por dia. As três referências
    # acima já são janelas de calendário alinhadas por construção — 01 a hoje
    # contra 01 ao mesmo dia do mês passado, N dias de semana contra os mesmos
    # N, o dia de hoje até a hora atual contra o mesmo DOW até a mesma hora.
    # Estando a janela igual dos dois lados, dividir por dias_op corrige uma
    # distorção que não existe e cria outra: dias_op conta dias COM movimento,
    # então um dia em que a loja abriu e não veio ninguém simplesmente sai da
    # conta e infla a média do lado que o teve.
    #
    # Caso real de 03/09/2026: agosto 01-03 teve movimento em 2 dos 3 dias
    # (02/08 ficou zerado). O per-dia comparava R$ 786 contra R$ 3.228 e
    # mostrava -75,7%; a queda real da mesma janela é -63,5%. O card dizia
    # "vs 01-03/mês passado" e entregava outro número.
    for aba, ant in [(a_mensal, mes_anterior_kpis), (a_semanal, semana_anterior),
                     (a_diario, dia_anterior_kpis)]:
        k = aba["kpis"]
        dias_atu = k.get("dias_op", 1)
        dias_ant = ant.get("dias_op", 1)
        k["caixa_delta_pct"] = _delta_pct(k.get("caixa", 0), ant.get("caixa", 0))
        k["atend_delta_pct"] = _delta_pct(k.get("atend_fin", 0), ant.get("atend_fin", 0))
        k["cliente_dia_delta_pct"] = _delta_pct(k.get("cliente_dia", 0), ant.get("cliente_dia", 0))
        # Secundários: a mesma comparação por dia com movimento, para quando a
        # pergunta for "nos dias em que abriu, rendeu mais ou menos?"
        k["caixa_delta_perdia_pct"] = _delta_pct_perdia(k.get("caixa", 0), ant.get("caixa", 0), dias_atu, dias_ant)
        k["atend_delta_perdia_pct"] = _delta_pct_perdia(k.get("atend_fin", 0), ant.get("atend_fin", 0), dias_atu, dias_ant)
        k["cliente_dia_delta_perdia_pct"] = _delta_pct_perdia(k.get("cliente_dia", 0), ant.get("cliente_dia", 0), dias_atu, dias_ant)
        k["dias_com_movimento"] = {"atual": dias_atu, "anterior": dias_ant}
        k["ticket_delta_pct"] = _delta_pct(k.get("ticket_medio", 0), ant.get("ticket_medio", 0))
        # Delta bruto também exposto pra UI mostrar quando as duas janelas SÃO comparáveis
        k["caixa_delta_bruto_pct"] = _delta_pct(k.get("caixa", 0), ant.get("caixa", 0))
        k["periodo_ant_ref"] = ant

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
            dt = parse_trinks_dt(a["dataHoraInicio"]).date()
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
                "telefone": tel_map.get(cid, ""),
            })
    churn_candidatos.sort(key=lambda x: -x["ltv"])
    churn = {
        "n_alerta": len(churn_candidatos),
        "ltv_em_risco": brl_round(sum(c["ltv"] for c in churn_candidatos)),
        "top": churn_candidatos[:20],
    }

    # === Série diária de clientes NOVOS (para o funil respeitar a competência) ===
    # O funil do painel cruza gasto de mídia com clientes novos do Trinks. Enquanto
    # o número de novos era só o do mês fechado, o funil ficava travado em agosto
    # e não acompanhava a janela escolhida (Hoje / 7d / mês / 90d).
    #
    # "Novo" aqui é primeira visita de todas, não "cadastrado no período": é essa
    # a pessoa que a mídia pode ter trazido. Quem já tinha vindo antes e voltou é
    # retorno, mesmo que o cadastro seja recente. Como o fetch cobre o ano inteiro
    # desde 01/01, a primeira visita é confiável — a loja começou a operar em julho.
    primeira_visita = {cid: min(datas) for cid, datas in cli_visitas.items() if datas}
    novos_por_dia = defaultdict(lambda: {"novos": 0, "atend": 0, "receita": 0.0})
    for cid, d0 in primeira_visita.items():
        novos_por_dia[d0]["novos"] += 1
    for a in agend:
        if (a.get("status") or {}).get("nome") != "Finalizado": continue
        cid = (a.get("cliente") or {}).get("id")
        if cid is None: continue
        try:
            dt = parse_trinks_dt(a["dataHoraInicio"]).date()
        except Exception:
            continue
        # Só o atendimento do próprio dia de estreia conta como receita de novo
        if primeira_visita.get(cid) != dt: continue
        novos_por_dia[dt]["atend"] += 1
        novos_por_dia[dt]["receita"] += float(a.get("valor") or 0)
    # `receita` é só a visita de estreia — o que a janela de mídia produziu de
    # caixa imediato. `receita_ltv` é tudo que essa safra já gastou até hoje,
    # incluindo os retornos: é o retorno real da aquisição, e cresce depois que
    # a janela fecha. Os dois juntos mostram o piso e o acumulado do ROAS.
    for cid, d0 in primeira_visita.items():
        novos_por_dia[d0]["ltv"] = novos_por_dia[d0].get("ltv", 0.0) + cli_valor.get(cid, 0.0)
    serie_novos_dia = [
        {"data": d.isoformat(), "novos": v["novos"], "atend": v["atend"],
         "receita": brl_round(v["receita"]), "receita_ltv": brl_round(v.get("ltv", 0.0))}
        for d, v in sorted(novos_por_dia.items())
        if (hoje - d).days <= 180
    ]

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
                "telefone": tel_map.get(cid, ""),
            })
    aniversariantes.sort(key=lambda x: (x["dias"], -x["ltv"]))

    # === Segmentação (canal aquisição / gênero / bairro) — só de clientes ativos no ano ===
    ativos_ids = {cid for cid in cli_visitas.keys()}
    ativos_receita = defaultdict(float)  # {id: receita_ano}
    for a in fin_ano:
        cid = (a.get("cliente") or {}).get("id")
        if cid and cid in ativos_ids:
            ativos_receita[cid] += float(a.get("valor") or 0)

    def _agrupa_seg(mapa, ativos, receitas):
        agg = defaultdict(lambda: {"n": 0, "receita": 0.0})
        sem_dado = {"n": 0, "receita": 0.0}
        for cid in ativos:
            valor = receitas.get(cid, 0)
            chave = mapa.get(cid)
            if chave:
                agg[chave]["n"] += 1
                agg[chave]["receita"] += valor
            else:
                sem_dado["n"] += 1
                sem_dado["receita"] += valor
        total_r = sum(v["receita"] for v in agg.values()) + sem_dado["receita"] or 1
        result = sorted(
            [{"nome": k, "n_clientes": v["n"], "receita": brl_round(v["receita"]),
              "pct_receita": round(v["receita"] / total_r * 100, 1),
              "ticket_medio_cliente": brl_round(v["receita"] / max(v["n"], 1))}
             for k, v in agg.items()],
            key=lambda x: -x["receita"]
        )
        return {
            "cobertura_pct": round((sum(v["n"] for v in agg.values()) / max(len(ativos), 1)) * 100, 1),
            "sem_dado": {"n": sem_dado["n"], "receita": brl_round(sem_dado["receita"])},
            "top": result,
        }

    seg_canal = _agrupa_seg(canal_map, ativos_ids, ativos_receita)
    seg_genero = _agrupa_seg(genero_map, ativos_ids, ativos_receita)
    seg_bairro = _agrupa_seg(bairro_map, ativos_ids, ativos_receita)

    # Clientes com observações (VIP alert)
    obs_alertas = []
    for cid, obs in obs_map.items():
        if cid in ativos_ids:
            obs_alertas.append({
                "cliente": (cli_nome.get(cid) or "").title(),
                "obs": obs,
                "n_visitas": len(cli_visitas.get(cid, [])),
                "ltv": brl_round(cli_valor.get(cid, 0)),
                "telefone": tel_map.get(cid, ""),
            })
    obs_alertas.sort(key=lambda x: -x["ltv"])

    # === SNAPSHOT da base pra aba Clientes (CRM) ===
    # Estado da base: total, ativos (janelas), dormentes, novos recentes, LTV/ticket médio
    total_base = len(ativos_ids)
    ultima_visita_por_id = {cid: max(v) for cid, v in cli_visitas.items() if v}
    def _janela(dias):
        limite = hoje - timedelta(days=dias)
        return sum(1 for cid, uv in ultima_visita_por_id.items() if uv >= limite)
    ativos_30d = _janela(30)
    ativos_60d = _janela(60)
    ativos_90d = _janela(90)
    dormentes_60d = total_base - ativos_60d  # não vem há 60+ dias
    novos_30d_ids = {cid for cid, dc in cad_map.items() if dc.date() >= hoje - timedelta(days=30)}
    ltv_por_id = {cid: cli_valor.get(cid, 0) for cid in ativos_ids}
    ltv_medio = sum(ltv_por_id.values()) / max(total_base, 1)
    # cli_visitas guarda linhas de atendimento (múltiplos serviços/dia contam separado).
    # Ticket médio "por visita" = cliente-dia único, alinhado com o resto do painel.
    total_atend = sum(len(v) for v in cli_visitas.values())
    total_visitas = sum(len(set(v)) for v in cli_visitas.values())  # cliente-dia único
    ticket_medio_visita = sum(ltv_por_id.values()) / max(total_visitas, 1)
    freq_media = total_visitas / max(total_base, 1)
    n_uma_vez = sum(1 for v in cli_visitas.values() if len(v) == 1)
    n_recorrentes = total_base - n_uma_vez

    clientes_snapshot = {
        "total_base": total_base,
        "ativos_30d": ativos_30d,
        "ativos_60d": ativos_60d,
        "ativos_90d": ativos_90d,
        "dormentes_60d": dormentes_60d,
        "novos_30d": len(novos_30d_ids),
        "n_uma_vez": n_uma_vez,
        "n_recorrentes": n_recorrentes,
        "pct_recorrentes": round(n_recorrentes / max(total_base, 1) * 100, 1),
        "ltv_medio": brl_round(ltv_medio),
        "ticket_medio_visita": brl_round(ticket_medio_visita),
        "freq_media_visitas": round(freq_media, 2),
        "n_alerta_churn": len(churn_candidatos),
        "n_aniv_14d": len(aniversariantes),
        "n_obs_vip": len(obs_alertas),
    }

    # === Observações por agendamento (finalizados) — VIP notes agregadas ===
    # Cliente com obs de estabelecimento em ≥1 atendimento vira alerta de contexto.
    obs_por_cliente_agend = defaultdict(list)  # {cid: [obs_est/obs_cli, ...]}
    for a in fin_ano:
        cid = (a.get("cliente") or {}).get("id")
        if not cid: continue
        oe = (a.get("observacoesDoEstabelecimento") or "").strip()
        if oe: obs_por_cliente_agend[cid].append(("est", oe))
        oc = (a.get("observacoesDoCliente") or "").strip()
        if oc: obs_por_cliente_agend[cid].append(("cli", oc))
    obs_agend_alertas = []
    for cid, obss in obs_por_cliente_agend.items():
        nome = (cli_nome.get(cid) or "").title() or "cliente sem nome"
        # dedup textos iguais
        vistos = set(); unicas = []
        for tipo, txt in obss:
            k = (tipo, txt.lower()[:80])
            if k in vistos: continue
            vistos.add(k); unicas.append((tipo, txt))
        obs_agend_alertas.append({
            "cliente": nome,
            "n_observacoes": len(unicas),
            "n_visitas": len(cli_visitas.get(cid, [])),
            "ltv": brl_round(cli_valor.get(cid, 0)),
            "telefone": tel_map.get(cid, ""),
            "observacoes": [{"tipo": t, "texto": x} for t, x in unicas[:5]],
        })
    obs_agend_alertas.sort(key=lambda x: (-x["n_visitas"], -x["ltv"]))

    # === QUALIDADE de cadastro (cobertura de campos no Trinks) ===
    clientes_cadastro = {
        "total": total_base,
        "cobertura": {
            "telefone": round(sum(1 for cid in ativos_ids if tel_map.get(cid)) / max(total_base, 1) * 100, 1),
            "email": round(sum(1 for cid in ativos_ids if email_map.get(cid)) / max(total_base, 1) * 100, 1),
            "data_nasc": round(sum(1 for cid in ativos_ids if cid in aniv_map) / max(total_base, 1) * 100, 1),
            "genero": round(sum(1 for cid in ativos_ids if genero_map.get(cid)) / max(total_base, 1) * 100, 1),
            "canal_aquisicao": round(sum(1 for cid in ativos_ids if canal_map.get(cid)) / max(total_base, 1) * 100, 1),
            "bairro": round(sum(1 for cid in ativos_ids if bairro_map.get(cid)) / max(total_base, 1) * 100, 1),
        }
    }

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
    # Fonte: histórico anual acumulado. Peso ponderado por horas de operação de cada dow
    # (dom = 6h, outros = 12h por padrão), pra domingo ser proporcionalmente estimado.
    dow_hist_v = {i: 0.0 for i in range(7)}
    dow_hist_n = {i: 0 for i in range(7)}
    for a in fin_ano:
        try:
            dt = parse_trinks_dt(a["dataHoraInicio"]).date()
            dow_hist_v[dt.weekday()] += float(a.get("valor") or 0)
        except Exception: pass
    dias_vistos = {parse_trinks_dt(a["dataHoraInicio"]).date() for a in fin_ano if a.get("dataHoraInicio")}
    for d in dias_vistos:
        dow_hist_n[d.weekday()] += 1

    # Caixa médio de 1 dia daquele dow. Precisa >=3 amostras pra usar histórico.
    caixa_medio_dow = {}
    for i in range(7):
        if HORAS_POR_DOW[i] == 0:
            caixa_medio_dow[i] = 0
            continue
        # Domingo só entra se a data de início já passou (senão não tem sentido histórico)
        if i == 6 and (not DATA_INICIO_DOM or hoje < DATA_INICIO_DOM):
            caixa_medio_dow[i] = 0  # marca sem dado (fallback abaixo)
            continue
        if dow_hist_n[i] >= 3:
            caixa_medio_dow[i] = dow_hist_v[i] / dow_hist_n[i]
        else:
            caixa_medio_dow[i] = 0

    # Fallback pra dow sem histórico: usa média do caixa/hora × horas do próprio dow.
    # Assim domingo (6h) recebe estimativa proporcional em vez de 0 quando começa a operar.
    dias_com_dado = [i for i in range(7) if caixa_medio_dow[i] > 0 and HORAS_POR_DOW[i] > 0]
    if dias_com_dado:
        caixa_hora_medio = sum(caixa_medio_dow[i] / HORAS_POR_DOW[i] for i in dias_com_dado) / len(dias_com_dado)
        for i in range(7):
            if caixa_medio_dow[i] == 0 and HORAS_POR_DOW[i] > 0:
                # Só estima se o dow vai operar no mês corrente
                if i == 6 and (not DATA_INICIO_DOM or (DATA_INICIO_DOM.year, DATA_INICIO_DOM.month) > (hoje.year, hoje.month)):
                    continue  # dom ainda não começou nesse mês
                caixa_medio_dow[i] = caixa_hora_medio * HORAS_POR_DOW[i]

    total = sum(caixa_medio_dow.values())
    if total > 0:
        peso_dow = {i: caixa_medio_dow[i] / total for i in range(7)}
    else:
        # nenhum dado: uniforme entre dias que operam
        n_op = sum(1 for i in range(7) if HORAS_POR_DOW[i] > 0)
        peso_dow = {i: (1/n_op if HORAS_POR_DOW[i] > 0 else 0) for i in range(7)}

    # === Qualidade da base de comparação de cada aba ===
    # Roda aqui, e não junto dos deltas, porque depende do peso_dow acima.
    #
    # "01 a hoje contra 01 ao mesmo dia do mês passado" parece a comparação
    # mais justa que existe, e é — de calendário. De negócio não é: em 2026,
    # 01/09 caiu numa terça e 01/08 num sábado. A janela de setembro pega
    # ter+qua+qui (25,1% do faturamento de uma semana) e a de agosto pega
    # sáb+dom+seg (56,7%). O card mostrava -63,5% de caixa; corrigida a
    # composição, a queda é de 17,5%. O resto era o calendário.
    dias_atipicos = marcar_dias_atipicos(historico_dias)
    for aba, ant, ini_atu in ((a_mensal, mes_anterior_kpis, ini_mes),
                              (a_semanal, semana_anterior, seg),
                              (a_diario, dia_anterior_kpis, hoje)):
        k = aba["kpis"]
        try:
            ini_ant = date.fromisoformat(ant.get("periodo_ini") or ant["data"])
            fim_ant = date.fromisoformat(ant.get("periodo_fim") or ant["data"])
        except Exception:
            continue
        p_atu, comp_atu = peso_janela(ini_atu, hoje, peso_dow)
        p_ant, comp_ant = peso_janela(ini_ant, fim_ant, peso_dow)
        razao = (p_ant / p_atu) if p_atu else None

        ajustado = None
        if p_atu and p_ant and ant.get("caixa"):
            ajustado = round(((k.get("caixa", 0) / p_atu) / (ant["caixa"] / p_ant) - 1) * 100, 1)

        na_base = {iso: info for iso, info in dias_atipicos.items()
                   if ini_ant <= date.fromisoformat(iso) <= fim_ant}
        # 15% de folga: abaixo disso a diferença de composição não move a
        # leitura o suficiente para valer um aviso na tela.
        comparavel = razao is not None and abs(razao - 1) <= 0.15

        k["base_comparacao"] = {
            "composicao_atual": comp_atu,
            "composicao_anterior": comp_ant,
            "peso_semana_atual_pct": round(p_atu * 100, 1),
            "peso_semana_anterior_pct": round(p_ant * 100, 1),
            "razao_peso": round(razao, 2) if razao else None,
            "comparavel": comparavel,
            "caixa_delta_ajustado_pct": ajustado,
            "dias_atipicos_na_base": na_base,
        }

    # === PESO SEMANA-DO-MÊS: capta semana forte (pós-pagamento) vs fraca (final do mês) ===
    def sem_do_mes(d: date) -> int:
        return (d.day - 1) // 7 + 1  # 1..5

    sem_v_per_mes = defaultdict(lambda: defaultdict(float))  # {(y,m): {sem_num: caixa}}
    for a in fin_ano:
        try:
            dt = parse_trinks_dt(a["dataHoraInicio"]).date()
            sem_v_per_mes[(dt.year, dt.month)][sem_do_mes(dt)] += float(a.get("valor") or 0)
        except Exception: pass
    today_ym = (hoje.year, hoje.month)
    meses_fechados = [ym for ym in sem_v_per_mes if ym < today_ym and sum(sem_v_per_mes[ym].values()) > 0]
    if len(meses_fechados) >= 2:
        fracoes_sem = defaultdict(list)
        for ym in meses_fechados:
            tot = sum(sem_v_per_mes[ym].values())
            for sem_n, v in sem_v_per_mes[ym].items():
                fracoes_sem[sem_n].append(v / tot)
        peso_sem_mes = {sem_n: sum(f) / len(f) for sem_n, f in fracoes_sem.items()}
        # Normaliza
        tot_pesos = sum(peso_sem_mes.values()) or 1
        peso_sem_mes = {k: v / tot_pesos for k, v in peso_sem_mes.items()}
        fonte_sem_mes = f"histórico ({len(meses_fechados)} meses fechados)"
    else:
        peso_sem_mes = {i: 1.0 for i in range(1, 6)}  # uniforme = passa direto
        fonte_sem_mes = f"uniforme (aguarda ≥2 meses fechados · atual: {len(meses_fechados)})"

    # === PESO MÊS-DO-ANO: para 2027 em diante, com histórico de 2026 ===
    # (dez/jul costumam ser mais fortes em beleza)
    mes_v_hist_ano = defaultdict(lambda: defaultdict(float))  # {ano: {mes: caixa}}
    for a in fin_ano:
        try:
            dt = parse_trinks_dt(a["dataHoraInicio"]).date()
            mes_v_hist_ano[dt.year][dt.month] += float(a.get("valor") or 0)
        except Exception: pass
    anos_fechados = [y for y, meses in mes_v_hist_ano.items()
                     if y < hoje.year and len(meses) >= 10]  # exigir pelo menos 10 meses do ano
    if anos_fechados:
        fracoes_mes = defaultdict(list)
        for y in anos_fechados:
            tot_ano = sum(mes_v_hist_ano[y].values())
            for m, v in mes_v_hist_ano[y].items():
                fracoes_mes[m].append(v / tot_ano)
        peso_mes_ano = {m: sum(f) / len(f) for m, f in fracoes_mes.items()}
        for m in range(1, 13):
            peso_mes_ano.setdefault(m, sum(peso_mes_ano.values()) / max(len(peso_mes_ano), 1))
        tot_pm = sum(peso_mes_ano.values()) or 1
        peso_mes_ano = {m: v / tot_pm for m, v in peso_mes_ano.items()}
        fonte_mes_ano = f"histórico ({len(anos_fechados)} anos fechados)"
    else:
        peso_mes_ano = {m: 1/12 for m in range(1, 13)}
        fonte_mes_ano = "uniforme (aguarda ≥1 ano fechado · framework pronto pra 2027)"

    # === META POR DATA no mês corrente ===
    # Capacidade base de cada data = caixa_medio_dow × peso_semana_do_mes (aplicado a cada dia real).
    # Depois escala uniformemente pra bater META_MENSAL. Assim cada dia individual do mês recebe uma
    # meta específica que respeita 3 fatores: dia da semana, posição no mês, e horas de operação.
    capacidade_por_data = {}
    n_dias_dow_mes = {i: 0 for i in range(7)}
    for d_num in range(1, monthrange(hoje.year, hoje.month)[1] + 1):
        dt = date(hoje.year, hoje.month, d_num)
        if not opera_no_dia(dt):
            capacidade_por_data[dt] = 0.0
            continue
        dow = dt.weekday()
        sm = sem_do_mes(dt)
        # peso normalizado por número típico de semanas no mês (4-5) — evita concentração espúria
        peso_sem = peso_sem_mes.get(sm, 1.0)
        capacidade_por_data[dt] = caixa_medio_dow[dow] * peso_sem
        n_dias_dow_mes[dow] += 1

    total_cap = sum(capacidade_por_data.values())
    scale_factor = (META_MENSAL / total_cap) if total_cap > 0 else 1.0
    meta_por_data = {dt: round(cap * scale_factor, 2) for dt, cap in capacidade_por_data.items()}

    # Meta média por DOW (pra card sazonalidade / retrocompat)
    dow_meta_soma = {i: 0.0 for i in range(7)}
    for dt, m in meta_por_data.items():
        if m > 0: dow_meta_soma[dt.weekday()] += m
    meta_dia_por_dow = {i: round(dow_meta_soma[i] / n_dias_dow_mes[i], 2) if n_dias_dow_mes[i] > 0 else 0.0 for i in range(7)}

    # Semanas-do-mês agregadas (pra expor no payload)
    sem_mes_agg = defaultdict(lambda: {"n_dias": 0, "meta_total": 0.0, "datas": []})
    for dt, m in meta_por_data.items():
        if m > 0:
            sm = sem_do_mes(dt)
            sem_mes_agg[sm]["n_dias"] += 1
            sem_mes_agg[sm]["meta_total"] += m
            sem_mes_agg[sm]["datas"].append(dt.isoformat())
    sem_mes_meta = [
        {
            "sem_do_mes": sm,
            "n_dias": v["n_dias"],
            "meta_total": brl_round(v["meta_total"]),
            "peso_pct": round(peso_sem_mes.get(sm, 0) * 100, 1),
            "datas": v["datas"],
        }
        for sm, v in sorted(sem_mes_agg.items())
    ]

    # Curva horária esperada (pct do caixa do dia acumulado até hora H)
    # Fonte: hora_abs anual dividido por total. Usamos como pace guide intraday.
    hora_v_hist = Counter()
    for tr in transac:
        if not tr.get("dataHora"): continue
        try:
            dt = parse_trinks_dt(tr["dataHora"])
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
    # Dias operacionais do mês real (respeita início do domingo)
    dias_op_mes_real = dias_operacionais_no_mes(hoje.year, hoje.month)
    meta_mensal = calc_meta(a_mensal["kpis"]["caixa"], META_MENSAL, a_mensal["kpis"]["dias_op"], dias_op_mes_real)

    # Meta do DIA: valor específico da data (respeita dow + peso da semana-do-mês).
    meta_dia_valor = meta_por_data.get(hoje, 0.0) if opera_no_dia(hoje) else 0.0
    meta_dia = calc_meta(a_diario["kpis"]["caixa"], meta_dia_valor, 1, 1)

    # === PACE INTRADAY: combina curva horária + hora atual ===
    # "Às 15h você já deveria ter feito X% da meta do dia".
    # A curva horária foi calculada acima com base no histórico anual (pct acum do caixa por hora).
    # Aqui interpolamos pra hora atual pra dar leitura em tempo real.
    agora = datetime.now(BRT)
    hora_atual = agora.hour + agora.minute / 60.0
    caixa_hoje = a_diario["kpis"].get("caixa", 0)
    # pct esperado até agora, interpolando linearmente entre horas cheias
    pct_esperado_agora = 0.0
    if opera_no_dia(hoje) and meta_dia_valor > 0 and curva_horaria:
        # curva_horaria vai de 8h a 21h com pct_acum ao final de cada hora
        # Ex: {"h": 15, "pct_acum": 45.0} = ao FIM das 15h, 45% do caixa acumulado
        # Antes de 8h: 0%. Após 21h: 100%. Entre h e h+1: interpolação linear.
        if hora_atual <= curva_horaria[0]["h"]:
            pct_esperado_agora = 0.0
        elif hora_atual >= curva_horaria[-1]["h"] + 1:
            pct_esperado_agora = 100.0
        else:
            for i, ponto in enumerate(curva_horaria):
                pct_fim_hora = ponto["pct_acum"]
                pct_ini_hora = curva_horaria[i-1]["pct_acum"] if i > 0 else 0.0
                if hora_atual < ponto["h"] + 1:
                    frac = hora_atual - ponto["h"]
                    if frac < 0: frac = 0
                    pct_esperado_agora = pct_ini_hora + (pct_fim_hora - pct_ini_hora) * frac
                    break
    meta_esperada_agora = meta_dia_valor * pct_esperado_agora / 100 if meta_dia_valor > 0 else 0
    pace_delta = caixa_hoje - meta_esperada_agora
    pace_ratio = (caixa_hoje / meta_esperada_agora * 100) if meta_esperada_agora > 0 else (100.0 if caixa_hoje == 0 else 0)
    # Projeção do fim do dia: caixa_atual / pct_esperado_agora = projeção linear
    projecao_dia = (caixa_hoje / pct_esperado_agora * 100) if pct_esperado_agora > 5 else 0
    a_diario["kpis"]["pace_intraday"] = {
        "hora_atual_str": agora.strftime("%H:%M"),
        "hora_atual_num": round(hora_atual, 2),
        "pct_esperado_agora": round(pct_esperado_agora, 1),
        "meta_dia": brl_round(meta_dia_valor),
        "meta_esperada_agora": brl_round(meta_esperada_agora),
        "realizado_agora": brl_round(caixa_hoje),
        "pace_delta": brl_round(pace_delta),
        "pace_ratio_pct": round(pace_ratio, 1),
        "projecao_dia": brl_round(projecao_dia),
        "opera_hoje": opera_no_dia(hoje),
    }

    # Meta da SEMANA: soma das metas ESPECÍFICAS por data dos dias da semana atual.
    # Se semana cruzar fronteira de mês, os dias fora do mês corrente ficam sem meta ainda —
    # meta reflete a fatia do mês corrente. Fallback: divisão flat se meta_por_data vazio.
    dias_op_sem_real = sum(1 for i in range(7) if opera_no_dia(seg + timedelta(days=i)))
    meta_sem_valor = 0.0
    for i in range(7):
        d = seg + timedelta(days=i)
        if opera_no_dia(d):
            meta_sem_valor += meta_por_data.get(d, 0.0)
    if meta_sem_valor == 0:
        meta_sem_valor = round(META_MENSAL / max(dias_op_mes_real, 1) * dias_op_sem_real, 2)
    meta_sem = calc_meta(a_semanal["kpis"]["caixa"], round(meta_sem_valor, 2),
                         a_semanal["kpis"]["dias_op"], dias_op_sem_real)

    # META ANO: com histórico de meses fechados (2027+), usa peso_mes_ano pra ponderar
    # o restante do ano. Sem histórico: mantém extrapolação META_MENSAL × meses_rest.
    real_pre_atual = sum(m["caixa"] for k, m in meses.items() if k < f"{hoje.year}-{hoje.month:02d}")
    meses_rest = 12 - hoje.month + 1  # inclui mês atual
    if fonte_mes_ano.startswith("histórico"):
        # META_ANUAL_TOTAL = META_MENSAL × 12 (equivalente ao target anual). Distribui pelo peso_mes.
        meta_anual_alvo = META_MENSAL * 12
        meta_dos_meses_rest = sum(meta_anual_alvo * peso_mes_ano.get(m, 1/12) for m in range(hoje.month, 13))
        meta_ano_valor = round(real_pre_atual + meta_dos_meses_rest, 2)
    else:
        meta_ano_valor = round(real_pre_atual + META_MENSAL * meses_rest, 2)

    # dias operacionais reais desde abertura da loja (23/07/26) até 31/12/26
    # · exclui domingos antes de DATA_INICIO_DOM; inclui a partir daí
    def _dias_op(ini_d: date, fim_d: date) -> int:
        n, d = 0, ini_d
        while d <= fim_d:
            if opera_no_dia(d): n += 1
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
    _inject_ticket_meta(a_semanal["kpis"], meta_sem, a_semanal["kpis"]["dias_op"], dias_op_sem_real)
    _inject_ticket_meta(a_mensal["kpis"], meta_mensal, a_mensal["kpis"]["dias_op"], dias_op_mes_real)
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
                    dt_full = parse_trinks_dt(tr["dataHora"])
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
        stone_data = processar_stone_csv(STONE_CSV, trinks_tx, hoje=hoje)  # hoje em BRT
        print(f"[stone] {'OK · ' + str(stone_data['total_lancamentos']) + ' lancamentos' if stone_data else 'sem CSV · aba vazia'}")
        # Enriquece aplicacao_reserva com meta + rendimento previsto do config
        _res_cfg = _cfg.get("reserva_stone") or {}
        if stone_data and _res_cfg and stone_data.get("aplicacao_reserva"):
            ar = stone_data["aplicacao_reserva"]
            meta = float(_res_cfg.get("meta_objetivo") or 0)
            rend30 = float(_res_cfg.get("rendimento_previsto_30d") or 0)
            saldo = float(ar.get("saldo_aplicado") or 0)
            ar["meta_objetivo"] = meta
            ar["pct_atingimento_meta"] = round(saldo / meta * 100, 2) if meta > 0 else 0
            ar["falta_para_meta"] = brl_round(max(meta - saldo, 0))
            ar["rendimento_previsto_30d"] = rend30
            ar["produto"] = _res_cfg.get("produto", "CDB Stone")
            ar["resgate"] = _res_cfg.get("resgate", "imediato")
            ar["ultima_conferencia_app"] = _res_cfg.get("ultima_conferencia_app", "")
            # Projeção: quantos meses pra bater meta no ritmo atual
            aportes_ultimos_10 = sum(m.get("aporte", 0) for m in (ar.get("ultimos_movs") or []))
            aporte_medio_dia = aportes_ultimos_10 / max(len(ar.get("ultimos_movs") or []), 1)
            aporte_medio_mes = aporte_medio_dia * 26  # 26 dias operacionais
            meses_ate_meta = round(max(meta - saldo, 0) / aporte_medio_mes, 1) if aporte_medio_mes > 0 else None
            ar["ritmo_aporte_mensal_est"] = brl_round(aporte_medio_mes)
            ar["meses_ate_meta_est"] = meses_ate_meta
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

            # Observações do agendamento (contexto do cancelamento)
            obs_cli = (a.get("observacoesDoCliente") or "").strip()
            obs_est = (a.get("observacoesDoEstabelecimento") or "").strip()
            canc_com_valor.append({
                "id": a.get("id"),
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
                "obs_cliente": obs_cli[:200] if obs_cli else "",
                "obs_estabelecimento": obs_est[:200] if obs_est else "",
            })
    canc_com_valor.sort(key=lambda x: x["data"], reverse=True)

    # === FORENSE de cancelados suspeitos · /v1/agendamentos/{id} ===
    # Só busca detalhe pros de risco != ok (crítico/atenção/revisar) → limita custo.
    # Cache 72h por ID (histórico não muda depois do fato).
    agend_det_cache = {}
    if AGEND_DET_CACHE.exists():
        try: agend_det_cache = json.loads(AGEND_DET_CACHE.read_text(encoding="utf-8"))
        except Exception: agend_det_cache = {}
    agora_iso = datetime.now(BRT).isoformat()
    canc_top_risco = [x for x in canc_com_valor if x["risco"] in ("critico", "atencao", "revisar")][:40]
    n_fetched = 0
    for item in canc_top_risco:
        aid = item.get("id")
        if not aid: continue
        cached = agend_det_cache.get(str(aid))
        cache_ok = False
        if cached:
            try:
                gerado = datetime.fromisoformat(cached.get("_gerado_em","").replace("Z","+00:00"))
                if gerado.tzinfo is None: gerado = gerado.replace(tzinfo=BRT)
                if (datetime.now(BRT) - gerado).total_seconds()/3600 < TTL_AGEND_DET_HORAS:
                    cache_ok = True
            except Exception: pass
        if not cache_ok:
            try:
                det = t.get(f"/v1/agendamentos/{aid}")
                if isinstance(det, dict):
                    det["_gerado_em"] = agora_iso
                    agend_det_cache[str(aid)] = det
                    cached = det
                    n_fetched += 1
            except Exception as e:
                print(f"  [agend/{aid}] {e}")
                cached = None
        if cached:
            hist = cached.get("historicoStatus") or cached.get("historico") or []
            criado_por = cached.get("criadoPor") or cached.get("usuarioCriacao") or (cached.get("criadoPorUsuario") or {}).get("nome")
            cancelado_em = None
            cancelado_por = None
            for h in (hist if isinstance(hist, list) else []):
                st = ((h.get("status") or {}).get("nome") if isinstance(h.get("status"), dict) else h.get("status")) or ""
                if "cancel" in st.lower():
                    cancelado_em = h.get("dataHora") or h.get("data")
                    cancelado_por = h.get("usuario") or (h.get("usuarioAcao") or {}).get("nome")
                    break
            item["criado_por"] = criado_por
            item["cancelado_em"] = cancelado_em
            item["cancelado_por"] = cancelado_por
    if n_fetched:
        AGEND_DET_CACHE.write_text(json.dumps(agend_det_cache, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[agend detail] {n_fetched} buscas novas · cache {len(agend_det_cache)} IDs")

    # === DESVIO da tabela (preço praticado vs oficial do catálogo) ===
    desvio_tabela = []
    for nome, info in tabela_precos.items():
        praticado = preco_mediano_geral.get(nome)
        if not praticado: continue
        tabela = info["preco"]
        if tabela <= 0: continue
        diff = praticado - tabela
        pct = diff / tabela * 100
        # Só reporta desvios ≥ 3% (evita ruído de arredondamento)
        if abs(pct) < 3: continue
        desvio_tabela.append({
            "servico": nome,
            "tabela": round(tabela, 2),
            "praticado": round(praticado, 2),
            "diff": round(diff, 2),
            "pct": round(pct, 1),
            "sinal": "desconto" if diff < 0 else "premium",
        })
    desvio_tabela.sort(key=lambda x: -abs(x["pct"]))

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
        # BRT com offset explícito (-03:00) — JS new Date() interpreta correto
        "gerado_em": datetime.now(BRT).isoformat(timespec="seconds"),
        "hoje": hoje.isoformat(),
        "meta_mensal_valor": META_MENSAL,
        "dias_op_mes": dias_op_mes_real,
        "dias_atipicos": dias_atipicos,
        "sazonalidade": {
            "peso_dow": {DOW_NOMES[i]: round(peso_dow[i]*100, 1) for i in range(7)},
            "meta_dia_por_dow": {DOW_NOMES[i]: meta_dia_por_dow[i] for i in range(7)},
            "n_dias_dow_mes": {DOW_NOMES[i]: n_dias_dow_mes[i] for i in range(7)},
            "horas_por_dow": {DOW_NOMES[i]: HORAS_POR_DOW[i] for i in range(7)},
            "curva_horaria": curva_horaria,
            "amostra_dias_ano": len(dias_vistos),
            "data_inicio_domingo": _dom_ini_str,
            "domingo_ativo_no_mes": n_dias_dow_mes[6] > 0,
            "peso_sem_do_mes": {str(k): round(v*100, 1) for k, v in peso_sem_mes.items()},
            "sem_mes_meta": sem_mes_meta,
            "fonte_sem_mes": fonte_sem_mes,
            "peso_mes_ano": {m: round(peso_mes_ano.get(m, 0)*100, 1) for m in range(1, 13)},
            "fonte_mes_ano": fonte_mes_ano,
            "meta_por_data": {dt.isoformat(): m for dt, m in meta_por_data.items() if m > 0},
        },
        "cota_api": cota_final,
        "metas_franqueadora": {
            "recepcionistas": N_RECEPCIONISTAS,
            "por_recepcionista_mensal": _por_rec,
            "meta_mensal_total": META_MENSAL,
            "categorias_mensal": {
                "pacotes": METAS_CATEGORIA_MENSAL.get("pacotes", 0),
                "fast_retoque": METAS_CATEGORIA_MENSAL.get("fast_retoque", 0),
                "produtos": METAS_CATEGORIA_MENSAL.get("produtos", 0),
                "servicos_gerais": max(META_MENSAL - _subtotal_franq, 0),
            },
            "subtotal_franqueadora": _subtotal_franq,
        },
        "comissoes": comissoes_data,
        "prof_meta": {str(k): v for k, v in prof_meta_global.items()},
        "catalogo_servicos": {
            "n_total": len(tabela_precos),
            "desvio_tabela": desvio_tabela[:30],
            "n_com_desvio": len(desvio_tabela),
        },
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
        "historico": {
            "semanas": historico_semanas,
            "dias": historico_dias,
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
                "ranking_prof_executor": a_anual.get("ranking_prof_executor", []),
                "ranking_serv": a_anual["ranking_serv"],
                "meios_pagamento": a_anual["meios_pagamento"], "descontos": a_anual["descontos"],
                "clientes_top": a_anual["clientes_top"],
                "cadeiras_utilizacao": a_anual["cadeiras_utilizacao"],
                "densidade_hora": a_anual["densidade_hora"],
                "parcelas": a_anual.get("parcelas", []),
                "categoria_native": a_anual.get("categoria_native", []),
                "churn_early": churn,
                "serie_novos_dia": serie_novos_dia,
                "cross_sell": cross_sell_data,
                "aniversariantes": aniversariantes,
                "seg_canal": seg_canal,
                "seg_genero": seg_genero,
                "seg_bairro": seg_bairro,
                "obs_alertas": obs_alertas[:30],
                "obs_agend_alertas": obs_agend_alertas[:30],
                "clientes_snapshot": clientes_snapshot,
                "clientes_cadastro": clientes_cadastro,
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
    # Limpa status de cota esgotada quando refresh volta a funcionar
    status_path = REPO_ROOT / "data" / "quota_status.json"
    if status_path.exists():
        status_path.unlink()
        print("[quota] status esgotada removido (cota voltou a funcionar)")
    print(f"[github_refresh] OK · {OUT_JSON}")
    print(f"  Ano R$ {a_anual['kpis']['caixa']:.2f} · Mês R$ {a_mensal['kpis']['caixa']:.2f} · Sem R$ {a_semanal['kpis']['caixa']:.2f} · Hoje R$ {a_diario['kpis']['caixa']:.2f}")


if __name__ == "__main__":
    try:
        main()
    except QuotaExhaustedError as e:
        # Cota Trinks mensal esgotada. Não sobrescreve dashboard_data.json —
        # preserva os últimos dados válidos. Escreve status pro frontend mostrar
        # banner. Sai com sucesso (não polui GH Actions com falhas repetidas
        # até o reset da cota no dia 1º do mês).
        print(f"\n⚠️  COTA TRINKS ESGOTADA: {e}")
        print("   → Dashboard preservado com últimos dados válidos.")
        print(f"   → Refreshes vão retomar automaticamente quando cota resetar (dia 1º).")
        status_path = REPO_ROOT / "data" / "quota_status.json"
        status_path.write_text(json.dumps({
            "cota_esgotada": True,
            "detectado_em": datetime.now(BRT).isoformat(timespec="seconds"),
            "mensagem": "Cota mensal Trinks (10k req) esgotada. Dados congelados. Reset automático no dia 1º do mês.",
            "erro": str(e),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        sys.exit(0)
