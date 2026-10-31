#!/usr/bin/env python3
"""Auditoria profunda do consolidado: cada bloco, cada campo, cada periodo.

Rodrigo (31/10/2026): "valores e ranking nao bate, faca uma auditoria de
tudo". Este script vai alem do `auditoria_coerencia.py` (que confere
unidades + consolidado em kpis.* mas poupa a maior parte dos blocos):
confere TODOS os blocos de kpis, categorias, rankings, meses, hora_media,
rentabilidade_hora, meios_pagamento, categoria_native, por_dia_mes.

Para cada bloco:
- Soma numericos leaf-a-leaf de Escova + SPA
- Compara com o Consolidado
- Lista divergencias com valor absoluto e percentual

Para rankings (list of dicts com nome/n/v):
- Confere que cada nome aparece 1x
- Confere que v e n somam
- Confere que _unidade esta setada

Para por_dia_mes (array por dia):
- Confere soma por dia

Saida: lista estruturada de ACHADOS por bloco, severidade e detalhe.
"""
import json
import os
import re
from pathlib import Path
from collections import defaultdict

RAIZ = Path(__file__).resolve().parent.parent

TOL = 0.05  # dinheiro em reais; 5 centavos tolerancia
TOL_INT = 0  # inteiro: tolerancia zero
MAX_LISTAR = 20  # limita listagem por bloco pra nao estourar log

# Campos que NAO somam (medias/percentuais) — mesma lista do
# consolida_dashboard.NAO_SOMAR + alguns extras pra auditoria.
# Dois jeitos de bater: prefixo (comeca com) OU sufixo _pct.
_DERIVADO_PREFIXOS = re.compile(
    r"^(ticket_|rs_hora|pct|utilizacao|cobertura|delta|rating|"
    r"estrelas|ltv_medio|freq_|rendimento|taxa_pix|taxa_antec|"
    r"media_dia|taxa_canc|taxa_efetiva|min_medio|"
    r"pix_tarifa|conf_)",
    re.I,
)
_DERIVADO_SUFIXOS = re.compile(r"(_pct|_atingimento|_delta|^media$)", re.I)

def _eh_derivado(campo):
    return bool(_DERIVADO_PREFIXOS.search(campo) or _DERIVADO_SUFIXOS.search(campo))

# Dias de operacao: no consolidado e o MAIOR dos calendarios, nao a soma
# (documentado em consolida_dashboard.corrigir_meses_consolidado). Audit
# nao pode acusar como erro.
_NAO_SOMA_EM_MESES = {"dias_op", "meta", "meta_origem", "clientes_novos",
                      "clientes_recorrentes", "taxa_canc"}

# Mesma regra em kpis (dias_op) + derivados calculados por consolida_
# dashboard em `_ticket_meta` (visitas_projetadas, visitas_restantes,
# ticket_meta_*) que vem com valor PROPRIO do consolidado (nao soma).
_NAO_SOMA_EM_KPIS = {"dias_op", "visitas_projetadas", "visitas_restantes",
                     "ticket_meta_deficit_caixa", "ticket_meta_supera_caixa",
                     "ticket_gap_por_atend"}


def carregar(path):
    p = RAIZ / path
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def eh_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def difere(a, b, tol=TOL):
    if a is None or b is None:
        return False
    return abs(a - b) > tol


def auditar_kpis(e, s, c, aba, acha):
    """Para kpis de uma aba, confere soma campo a campo."""
    ke = (e.get("abas") or {}).get(aba, {}).get("kpis") or {}
    ks = (s.get("abas") or {}).get(aba, {}).get("kpis") or {}
    kc = (c.get("abas") or {}).get(aba, {}).get("kpis") or {}
    campos = sorted(set(ke) | set(ks) | set(kc))
    for campo in campos:
        a, b, cv = ke.get(campo), ks.get(campo), kc.get(campo)
        if not all(eh_num(x) for x in (a, b, cv)):
            continue
        if _eh_derivado(campo):
            continue
        if campo in _NAO_SOMA_EM_KPIS:
            continue
        soma = a + b
        if difere(soma, cv):
            acha.append(("erro", "kpis", aba,
                f"{campo}: esc={a} + spa={b} = {round(soma,2)} · cons={cv} "
                f"(delta {round(cv-soma,2)})"))


def auditar_categorias(e, s, c, aba, acha):
    """categorias.{servicos,produtos,pacotes,...}.v e n."""
    pe = (e.get("abas") or {}).get(aba, {}).get("categorias") or {}
    ps = (s.get("abas") or {}).get(aba, {}).get("categorias") or {}
    pc = (c.get("abas") or {}).get(aba, {}).get("categorias") or {}
    for cat in sorted(set(pe) | set(ps) | set(pc)):
        ve, vs, vc = pe.get(cat) or {}, ps.get(cat) or {}, pc.get(cat) or {}
        if not isinstance(vc, dict):
            continue
        for campo in ("v", "n"):
            a, b, cv = ve.get(campo), vs.get(campo), vc.get(campo)
            if not all(eh_num(x) for x in (a, b, cv)):
                continue
            soma = a + b
            if difere(soma, cv):
                acha.append(("erro", "categorias", aba,
                    f"{cat}.{campo}: esc={a}+spa={b}={round(soma,2)} · "
                    f"cons={cv} (delta {round(cv-soma,2)})"))


def _por_nome(lst, key="nome"):
    out = {}
    for x in (lst or []):
        if isinstance(x, dict):
            k = x.get(key) or "?"
            out[k] = x
    return out


def auditar_ranking(e, s, c, aba, bloco, acha, kname="nome"):
    """Rankings (lista de dicts por nome). Confere soma de v e n por nome."""
    le = (e.get("abas") or {}).get(aba, {}).get(bloco) or []
    ls = (s.get("abas") or {}).get(aba, {}).get(bloco) or []
    lc = (c.get("abas") or {}).get(aba, {}).get(bloco) or []
    if not lc:
        return

    # Duplicatas no consolidado
    nomes_cons = [x.get(kname) for x in lc if isinstance(x, dict)]
    dup = [n for n in set(nomes_cons) if nomes_cons.count(n) > 1]
    if dup:
        acha.append(("erro", bloco, aba,
            f"duplicatas no consolidado: {dup[:5]}"))

    de, ds, dc = _por_nome(le, kname), _por_nome(ls, kname), _por_nome(lc, kname)

    # Nomes que estao em uma unidade mas sumiram do consolidado
    sumidos = (set(de) | set(ds)) - set(dc)
    if sumidos:
        acha.append(("erro", bloco, aba,
            f"sumidos do consolidado: {list(sumidos)[:5]}"))

    # Nomes no consolidado que nao existem em nenhuma unidade
    inventados = set(dc) - set(de) - set(ds)
    if inventados:
        acha.append(("erro", bloco, aba,
            f"no consolidado mas nao esta em escova nem spa: {list(inventados)[:5]}"))

    # Soma de v e n por nome
    for nome in sorted(set(dc)):
        itc = dc[nome]
        ite = de.get(nome) or {}
        its = ds.get(nome) or {}
        for campo in ("v", "n", "ltv", "receita"):
            a, b, cv = ite.get(campo), its.get(campo), itc.get(campo)
            if not all(eh_num(x) for x in (a, b, cv)):
                # Se so um lado tem valor numerico, aceita como soma do unico
                ab_only = eh_num(a) or eh_num(b)
                if ab_only and eh_num(cv):
                    soma = (a or 0) + (b or 0)
                    if difere(soma, cv):
                        acha.append(("erro", bloco, aba,
                            f"{nome}.{campo}: esc={a}+spa={b}={round(soma,2)} · "
                            f"cons={cv}"))
                continue
            soma = a + b
            if difere(soma, cv):
                acha.append(("erro", bloco, aba,
                    f"{nome}.{campo}: esc={a}+spa={b}={round(soma,2)} · "
                    f"cons={cv} (delta {round(cv-soma,2)})"))
        # _unidade correta?
        tem_esc = nome in de
        tem_spa = nome in ds
        esperado = ("ambas" if tem_esc and tem_spa
                    else ("escova" if tem_esc else "spa"))
        if itc.get("_unidade") and itc.get("_unidade") != esperado:
            acha.append(("warn", bloco, aba,
                f"{nome}._unidade={itc.get('_unidade')} · esperado={esperado}"))


def auditar_meses(e, s, c, acha):
    """abas.anual.meses[YYYY-MM]: cada mes somado."""
    pe = ((e.get("abas") or {}).get("anual") or {}).get("meses") or {}
    ps = ((s.get("abas") or {}).get("anual") or {}).get("meses") or {}
    pc = ((c.get("abas") or {}).get("anual") or {}).get("meses") or {}
    for ym in sorted(set(pe) | set(ps) | set(pc)):
        ve, vs, vc = pe.get(ym) or {}, ps.get(ym) or {}, pc.get(ym) or {}
        if not isinstance(vc, dict):
            continue
        for campo in sorted(set(ve) | set(vs) | set(vc)):
            a, b, cv = ve.get(campo), vs.get(campo), vc.get(campo)
            if not all(eh_num(x) for x in (a, b, cv)):
                continue
            if _eh_derivado(campo):
                continue
            if campo in _NAO_SOMA_EM_MESES:
                continue
            soma = a + b
            if difere(soma, cv, tol=0.1):
                acha.append(("erro", "meses", "anual",
                    f"{ym}.{campo}: esc={a}+spa={b}={round(soma,2)} · "
                    f"cons={cv} (delta {round(cv-soma,2)})"))


def auditar_por_dia_mes(e, s, c, aba, acha):
    pe = (e.get("abas") or {}).get(aba, {}).get("por_dia_mes") or []
    ps = (s.get("abas") or {}).get(aba, {}).get("por_dia_mes") or []
    pc = (c.get("abas") or {}).get(aba, {}).get("por_dia_mes") or []
    if not pc: return
    por_dia = defaultdict(lambda: {"esc": {"v":0,"n":0}, "spa": {"v":0,"n":0}})
    for x in pe:
        if isinstance(x, dict) and "d" in x:
            por_dia[x["d"]]["esc"]["v"] += float(x.get("v") or 0)
            por_dia[x["d"]]["esc"]["n"] += int(x.get("n") or 0)
    for x in ps:
        if isinstance(x, dict) and "d" in x:
            por_dia[x["d"]]["spa"]["v"] += float(x.get("v") or 0)
            por_dia[x["d"]]["spa"]["n"] += int(x.get("n") or 0)
    cons_map = {x["d"]: x for x in pc if isinstance(x, dict) and "d" in x}
    for d, lados in sorted(por_dia.items()):
        soma_v = lados["esc"]["v"] + lados["spa"]["v"]
        soma_n = lados["esc"]["n"] + lados["spa"]["n"]
        c_item = cons_map.get(d) or {}
        cv = c_item.get("v")
        cn = c_item.get("n")
        if eh_num(cv) and difere(soma_v, cv):
            acha.append(("erro", "por_dia_mes", aba,
                f"d={d}.v: esc={lados['esc']['v']}+spa={lados['spa']['v']}="
                f"{round(soma_v,2)} · cons={cv}"))
        if eh_num(cn) and (soma_n - cn) != 0:
            acha.append(("erro", "por_dia_mes", aba,
                f"d={d}.n: esc={lados['esc']['n']}+spa={lados['spa']['n']}="
                f"{soma_n} · cons={cn}"))


def auditar_hora_media(e, s, c, aba, acha):
    pe = (e.get("abas") or {}).get(aba, {}).get("hora_media") or []
    ps = (s.get("abas") or {}).get(aba, {}).get("hora_media") or []
    pc = (c.get("abas") or {}).get(aba, {}).get("hora_media") or []
    if not pc: return
    por_h = {}
    for x in pe:
        if isinstance(x, dict) and "h" in x:
            por_h.setdefault(x["h"], {"esc":0,"spa":0})["esc"] = x.get("n_total") or 0
    for x in ps:
        if isinstance(x, dict) and "h" in x:
            por_h.setdefault(x["h"], {"esc":0,"spa":0})["spa"] = x.get("n_total") or 0
    cons_map = {x["h"]: x for x in pc if isinstance(x, dict) and "h" in x}
    for h, lados in sorted(por_h.items()):
        soma_n = lados["esc"] + lados["spa"]
        cv = (cons_map.get(h) or {}).get("n_total")
        if eh_num(cv) and (soma_n - cv) != 0:
            acha.append(("erro", "hora_media", aba,
                f"h={h}.n_total: esc={lados['esc']}+spa={lados['spa']}={soma_n} · cons={cv}"))
        # 'media' deve ser recalculada no consolidado (n_total / dias_op cons)
        # — nao somada. Testa se foi somada (bug).
        me, ms = (
            next((x.get("media") for x in pe if x.get("h")==h), None),
            next((x.get("media") for x in ps if x.get("h")==h), None),
        )
        mc = (cons_map.get(h) or {}).get("media")
        if eh_num(me) and eh_num(ms) and eh_num(mc):
            soma_me = me + ms
            if abs(mc - soma_me) < 0.05 and abs(mc - max(me, ms)) > 0.1:
                acha.append(("erro", "hora_media", aba,
                    f"h={h}.media={mc} parece ser soma (esc={me}+spa={ms})"))


def auditar_meios(e, s, c, aba, acha):
    """meios_pagamento: cada bandeira deve aparecer uma vez e somar v."""
    auditar_ranking(e, s, c, aba, "meios_pagamento", acha, kname="nome")


def rodar():
    e = carregar("data/dashboard_data.json")
    s = carregar("data/spa/dashboard_data.json")
    c = carregar("data/consolidado/dashboard_data.json")
    if not e or not s or not c:
        print("[erro] Faltam payloads descriptografados. Rode scripts/cofre.py abrir.")
        return 2

    acha = []
    print(f"[gerado_em] esc={e.get('gerado_em')} spa={s.get('gerado_em')} cons={c.get('gerado_em')}")

    for aba in ("diario", "semanal", "mensal", "anual"):
        auditar_kpis(e, s, c, aba, acha)
        auditar_categorias(e, s, c, aba, acha)
        auditar_por_dia_mes(e, s, c, aba, acha)
        auditar_hora_media(e, s, c, aba, acha)
        auditar_meios(e, s, c, aba, acha)
        for bloco in ("ranking_prof", "ranking_prof_executor", "ranking_serv",
                      "ranking_produtos", "ranking_pacotes", "rentabilidade_hora",
                      "upsell_pacotes", "upsell_produtos", "clientes_top",
                      "aniversariantes", "categoria_native"):
            auditar_ranking(e, s, c, aba, bloco, acha,
                            kname="cliente" if bloco == "aniversariantes" else "nome")

    auditar_meses(e, s, c, acha)

    # Top ltv/cross_sell/churn_early
    for bloco in ("top_ltv", "cross_sell", "churn_early"):
        for sub in ("top",):
            # these are nested: abas.anual.{bloco}.{sub} ou kpis
            pass

    # Agrupamento final
    por_bloco = defaultdict(list)
    for sev, bloco, aba, msg in acha:
        por_bloco[(sev, bloco)].append((aba, msg))

    print("\n" + "="*78)
    print(" AUDITORIA PROFUNDA DO CONSOLIDADO")
    print("="*78)

    erros_count = sum(1 for x in acha if x[0] == "erro")
    warns_count = sum(1 for x in acha if x[0] == "warn")
    print(f"\nTotal: {erros_count} erros, {warns_count} avisos")

    for (sev, bloco), itens in sorted(por_bloco.items(),
                                       key=lambda x: (x[0][0] != "erro", x[0][1])):
        marker = "XX" if sev == "erro" else "!!"
        print(f"\n{marker} [{sev.upper()}] {bloco} ({len(itens)} item/s)")
        for aba, msg in itens[:MAX_LISTAR]:
            print(f"   · {aba}: {msg}")
        if len(itens) > MAX_LISTAR:
            print(f"   · ... +{len(itens) - MAX_LISTAR} outros")

    return 1 if erros_count else 0


if __name__ == "__main__":
    import sys
    sys.exit(rodar())
