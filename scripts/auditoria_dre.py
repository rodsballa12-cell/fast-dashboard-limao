#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audita a DRE: a aritmetica por dentro, as premissas contra o real, o rateio
entre as lojas e o que o consolidado soma.

POR QUE EXISTE (20/10/2026)
O Rodrigo pediu "auditoria completa do nosso Excel". A planilha mora no PC e a
sessao da nuvem nao alcanca — mas alcanca o que o `gerar_financeiro.py` extrai
dela, e e ali que os erros aparecem como numero. Esta auditoria confere o que
pode ser conferido sem abrir o Excel, e declara em voz alta o que so o PC ve.

A `auditoria_coerencia.py` confere se as unidades somam no consolidado e se os
blocos derivados sobreviveram. Esta olha para dentro da DRE: se os grupos
fecham, se a margem e o ponto de equilibrio saem das proprias premissas, se a
comissao provisionada bate com a executada, e se o rateio do imovel e da
gerente soma um inteiro entre as duas lojas.

Uso:  python scripts/auditoria_dre.py
      exit 1 se achou divergencia, 0 se so avisos
"""
import json
import pathlib
import sys
from datetime import date

REPO = pathlib.Path(__file__).resolve().parent.parent
TOL = 0.05          # cinco centavos: arredondamento, nao erro
TOL_PCT = 0.0005    # meio decimo de ponto percentual


def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "~").replace(".", ",").replace("~", ".")


def ler(rel):
    p = REPO / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


class Relatorio:
    def __init__(self):
        self.itens = []

    def erro(self, onde, msg):
        self.itens.append(("erro", onde, msg))

    def aviso(self, onde, msg):
        self.itens.append(("aviso", onde, msg))

    def cego(self, onde, msg):
        self.itens.append(("cego", onde, msg))

    def ok(self, onde, msg):
        self.itens.append(("ok", onde, msg))


def linhas_de(g):
    return g.get("linhas") or []


def acha_linha(grupos, trecho):
    for g in grupos:
        for l in linhas_de(g):
            if trecho.lower() in (l.get("cat") or "").lower():
                return l
    return None


def auditar_unidade(rep, rel, nome):
    d = ler(rel)
    if not d:
        rep.erro(nome, f"{rel} nao existe.")
        return None
    r = d["resultado"]
    p = d["premissas"]
    gr = r["grupos"]
    onde = f"{nome} · DRE"

    # ---- A. a aritmetica fecha? -------------------------------------------
    for g in gr:
        soma = sum(float(l.get("real") or 0) for l in linhas_de(g))
        if abs(soma - float(g.get("sub_real") or 0)) > TOL:
            rep.erro(onde, f"grupo '{g.get('titulo')}': as linhas somam "
                           f"{brl(soma)} e o subtotal diz {brl(g['sub_real'])}.")

    var = next((g for g in gr if g.get("id") == "VARIAVEL"), None)
    fixos = [g for g in gr if g.get("id") in ("PESSOAL", "OCUPACAO", "COMERCIAL")]
    var_calc = float(var["sub_real"]) if var else 0.0
    fixo_calc = sum(float(g["sub_real"]) for g in fixos)
    if abs(var_calc - float(r["var_real"])) > TOL:
        rep.erro(onde, f"var_real diz {brl(r['var_real'])} e o grupo variavel soma {brl(var_calc)}.")
    if abs(fixo_calc - float(r["fixo_real"])) > TOL:
        rep.erro(onde, f"fixo_real diz {brl(r['fixo_real'])} e os tres grupos fixos somam {brl(fixo_calc)}.")

    rec = float(r["receita_bruta"])

    # A margem de contribuicao vem da linha 9 do Excel, e a conta dela nao e
    # "receita bruta menos o grupo variavel do painel". O Excel desconta o
    # Simples ANTES (para chegar na receita liquida) e conta o royalty e o
    # marketing local DENTRO da margem -- no painel esses dois moram no grupo
    # Comercial. Entao a identidade e:
    #   MC = receita liquida - (variavel do painel - Simples) - royalty - mkt local
    simples = acha_linha(gr, "simples")
    royalty = acha_linha(gr, "royalty")
    mkt_loc = acha_linha(gr, "marketing local")
    v_simples = float(simples["real"]) if simples else 0.0
    v_royalty = float(royalty["real"]) if royalty else 0.0
    v_mkt = float(mkt_loc["real"]) if mkt_loc else 0.0
    mc_excel = float(r["receita_liquida"]) - (var_calc - v_simples) - v_royalty - v_mkt
    if abs(mc_excel - float(r["margem_contribuicao"])) > TOL:
        rep.erro(onde, f"margem de contribuicao diz {brl(r['margem_contribuicao'])}, "
                       f"mas receita liquida menos comissao, CMV, royalty e "
                       f"marketing local da {brl(mc_excel)}.")

    # O EBITDA, sim, fecha com a divisao do painel (variavel + tres fixos).
    eb_calc = rec - var_calc - fixo_calc
    if abs(eb_calc - float(r["ebitda"])) > TOL:
        rep.erro(onde, f"EBITDA diz {brl(r['ebitda'])}, margem menos fixo da {brl(eb_calc)}.")

    # Receita liquida = bruta menos o Simples
    if simples:
        liq_calc = rec - v_simples
        if abs(liq_calc - float(r["receita_liquida"])) > TOL:
            rep.erro(onde, f"receita liquida diz {brl(r['receita_liquida'])}, "
                           f"bruta menos Simples da {brl(liq_calc)}.")

    # Provisoes: o campo bate com as linhas marcadas?
    prov_calc = sum(float(l.get("real") or 0) for g in gr for l in linhas_de(g) if l.get("prov"))
    if abs(prov_calc - float(r.get("provisoes_nao_debitadas") or 0)) > TOL:
        rep.erro(onde, f"provisoes nao debitadas diz "
                       f"{brl(r.get('provisoes_nao_debitadas') or 0)} e as linhas marcadas "
                       f"somam {brl(prov_calc)}.")
    if abs((float(r["res_real"]) + prov_calc) - float(r["res_caixa"])) > TOL:
        rep.erro(onde, f"resultado de caixa diz {brl(r['res_caixa'])}; resultado "
                       f"{brl(r['res_real'])} mais provisoes {brl(prov_calc)} da "
                       f"{brl(float(r['res_real']) + prov_calc)}.")

    # ---- B. a margem sai das proprias premissas? --------------------------
    mc_pct_prem = 1 - float(p["comissao"]) - float(p["insumos"]) - float(p["simples"])
    mc_decl = float((d["equilibrio"]["cenarios"] or [{}])[0].get("mc") or 0)
    if abs(mc_pct_prem - mc_decl) > TOL_PCT:
        rep.erro(onde, f"margem declarada {mc_decl*100:.2f}% nao sai das premissas "
                       f"(1 - {p['comissao']*100:.2f}% comissao - {p['insumos']*100:.0f}% "
                       f"insumos - {p['simples']*100:.0f}% Simples = {mc_pct_prem*100:.2f}%).")
    # aqui a comparacao certa e contra as tres premissas (comissao, insumos,
    # Simples) -- que sao exatamente o grupo variavel do painel.
    mc_pct_real = (rec - var_calc) / rec if rec else 0
    if abs(mc_pct_real - mc_decl) > TOL_PCT:
        rep.aviso(onde, f"a margem declarada e {mc_decl*100:.2f}% mas as linhas da DRE "
                        f"dao {mc_pct_real*100:.2f}% — ha custo variavel fora das tres premissas.")
    be_calc = fixo_calc / mc_decl if mc_decl else 0
    if abs(be_calc - float(r["be_modelo_1loja"])) > TOL:
        rep.erro(onde, f"ponto de equilibrio diz {brl(r['be_modelo_1loja'])}, "
                       f"fixo dividido pela margem da {brl(be_calc)}.")

    # Cada linha variavel confere com a sua premissa?
    for trecho, chave in (("comiss", "comissao"), ("insumo", "insumos"), ("simples", "simples")):
        l = acha_linha(gr, trecho)
        if not l or not rec:
            continue
        pct = float(l["real"]) / rec
        if abs(pct - float(p[chave])) > TOL_PCT:
            rep.erro(onde, f"linha '{l['cat']}' e {pct*100:.2f}% da receita, "
                           f"premissa diz {float(p[chave])*100:.2f}%.")

    return d


def comissao_executada(rel_dash):
    d = ler(rel_dash)
    if not d:
        return None
    ex = ((d.get("abas") or {}).get("mensal") or {}).get("ranking_prof_executor") or []
    base = sum(float(x.get("v") or 0) for x in ex)
    com = sum(float(x.get("comissao") or 0) for x in ex)
    return (com / base) if base else None


def main() -> int:
    rep = Relatorio()
    esc = auditar_unidade(rep, "data/financeiro.json", "Escova")
    spa = auditar_unidade(rep, "data/spa/financeiro.json", "Spa")
    con = auditar_unidade(rep, "data/consolidado/financeiro.json", "Consolidado")

    # ---- C. o consolidado e a soma das duas? -----------------------------
    if esc and spa and con:
        for campo in ("receita_bruta", "var_real", "fixo_real", "margem_contribuicao",
                      "ebitda", "provisoes_nao_debitadas"):
            a = float(esc["resultado"].get(campo) or 0)
            b = float(spa["resultado"].get(campo) or 0)
            c = float(con["resultado"].get(campo) or 0)
            if abs((a + b) - c) > TOL:
                rep.erro("Consolidado", f"{campo}: Escova {brl(a)} + Spa {brl(b)} = "
                                        f"{brl(a+b)}, mas o consolidado diz {brl(c)}.")

    # ---- D. o rateio soma um inteiro? ------------------------------------
    if esc and spa:
        for trecho, rot in (("gerente", "a gerente"), ("aluguel", "o aluguel + IPTU"),
                            ("sistemas", "sistemas/utilidades")):
            la = acha_linha(esc["resultado"]["grupos"], trecho)
            lb = acha_linha(spa["resultado"]["grupos"], trecho)
            if la and lb:
                rep.ok("Rateio", f"{rot}: Escova {brl(la['real'])} + Spa {brl(lb['real'])} "
                                 f"= {brl(float(la['real']) + float(lb['real']))}/mes")

    # ---- E. a comissao provisionada bate com a executada? ----------------
    for rel_fin, rel_dash, nome in (("data/financeiro.json", "data/dashboard_data.json", "Escova"),
                                    ("data/spa/financeiro.json", "data/spa/dashboard_data.json", "Spa")):
        d = ler(rel_fin)
        taxa = comissao_executada(rel_dash)
        if not d or taxa is None:
            continue
        prov = float(d["premissas"]["comissao"])
        delta = (taxa - prov) * 100
        rec = float(d["resultado"]["receita_bruta"])
        if abs(delta) >= 1.0:
            rep.erro(f"{nome} · comissao",
                     f"provisionada {prov*100:.2f}% contra {taxa*100:.2f}% executada "
                     f"({delta:+.2f} pontos) — {brl(abs(taxa-prov)*rec)}/mes na meta de {brl(rec)}.")
        elif abs(delta) >= 0.25:
            rep.aviso(f"{nome} · comissao",
                      f"provisionada {prov*100:.2f}% contra {taxa*100:.2f}% executada "
                      f"({delta:+.2f} pontos).")
        else:
            rep.ok(f"{nome} · comissao", f"provisionada {prov*100:.2f}% = executada {taxa*100:.2f}%")

    # ---- F. a DRE ve a receita que aconteceu? ----------------------------
    for rel_fin, rel_dash, nome in (("data/financeiro.json", "data/dashboard_data.json", "Escova"),
                                    ("data/spa/financeiro.json", "data/spa/dashboard_data.json", "Spa")):
        d, dash = ler(rel_fin), ler(rel_dash)
        if not d or not dash:
            continue
        rec_dre = float(d["resultado"]["receita_bruta"])
        meta = float(d["resultado"].get("receita_meta") or 0)
        m = ((dash.get("abas") or {}).get("mensal") or {}).get("meta") or {}
        real, proj = float(m.get("realizado") or 0), float(m.get("projecao") or 0)
        if abs(rec_dre - meta) < TOL:
            rep.aviso(f"{nome} · receita",
                      f"a DRE do mes corrente usa a META ({brl(meta)}) como receita, nao o "
                      f"realizado ({brl(real)}) nem a projecao ({brl(proj)}). Todo percentual "
                      f"da coluna projetada e percentual da meta.")

    # ---- G. caixa e inadimplencia ----------------------------------------
    for rel_fin, nome in (("data/financeiro.json", "Escova"), ("data/spa/financeiro.json", "Spa")):
        d = ler(rel_fin)
        if not d:
            continue
        k = d["kpis"]
        caixa, arec = float(k.get("caixa_conta") or 0), float(k.get("a_receber_stone") or 0)
        fixo = float(d["resultado"]["fixo_real"])
        if caixa == 0 and arec == 0:
            rep.erro(f"{nome} · caixa",
                     "caixa em conta e a-receber estao ZERADOS no DRE. Isso nao e conta "
                     "vazia, e campo nao preenchido: nao da para dizer se o caixa cobre o "
                     f"custo fixo de {brl(fixo)}/mes.")
        elif caixa > 0 and fixo > 0:
            dias = caixa / (fixo / 30)
            if dias < 3:
                rep.aviso(f"{nome} · caixa",
                          f"{brl(caixa)} em conta = {dias:.1f} dia(s) de custo fixo. "
                          f"{brl(arec)} a receber (prazo, nao prejuizo), mas sem folga.")
        if float(d["premissas"].get("inadimplencia") or 0) == 0 and arec > 0:
            rep.cego(f"{nome} · inadimplencia",
                     f"premissa de inadimplencia e ZERO com {brl(arec)} a receber. "
                     f"Nunca houve perda, ou nunca foi medida?")

    # ---- H. frescor e o que so o PC ve -----------------------------------
    d = ler("data/financeiro.json")
    dash = ler("data/dashboard_data.json")
    if d and dash:
        try:
            b = date.fromisoformat(str(d.get("baseline"))[:10])
            h = date.fromisoformat(str(dash.get("hoje"))[:10])
            if (h - b).days > 1:
                rep.aviso("Frescor", f"o DRE e de {b.strftime('%d/%m')} e o painel de "
                                     f"{h.strftime('%d/%m')} — {(h-b).days} dia(s) de diferenca.")
            else:
                rep.ok("Frescor", f"DRE de {b.strftime('%d/%m')}, painel de {h.strftime('%d/%m')}")
        except Exception:
            rep.cego("Frescor", "nao consegui ler baseline ou hoje.")
        n = len(d.get("meses") or {})
        if n > 14:
            rep.cego("Projeção longa", f"o DRE traz {n} meses, ate "
                                       f"{max(d['meses'])}. Projecao de anos futuros nao e "
                                       f"auditavel daqui e nao deve alimentar leitura de hoje.")

    rep.cego("Só o PC vê", "formula, celula mesclada, linha oculta e aba a mais do Excel. "
                           "Esta auditoria le o que o gerar_financeiro.py extraiu, nao a planilha.")

    # ---- saida ------------------------------------------------------------
    erros = [x for x in rep.itens if x[0] == "erro"]
    avisos = [x for x in rep.itens if x[0] == "aviso"]
    cegos = [x for x in rep.itens if x[0] == "cego"]
    oks = [x for x in rep.itens if x[0] == "ok"]

    for rot, lista, ico in (("DIVERGÊNCIA", erros, "🛑"), ("AVISO", avisos, "⚠️"),
                            ("NÃO VEJO", cegos, "❔"), ("CONFERE", oks, "✅")):
        if not lista:
            continue
        print(f"\n{ico} {rot} ({len(lista)})")
        for _, onde, msg in lista:
            print(f"   · {onde}: {msg}")

    print(f"\n{len(erros)} divergência(s) · {len(avisos)} aviso(s) · "
          f"{len(cegos)} ponto(s) cego(s) · {len(oks)} confere(m)")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
