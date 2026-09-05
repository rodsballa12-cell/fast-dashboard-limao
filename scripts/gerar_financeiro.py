# -*- coding: utf-8 -*-
"""Lê a aba DRE do painel Excel (bloco FAST ESCOVA) e gera data/financeiro.json
com TODOS os meses do plano de 5 anos.

Estrutura da aba DRE do Rodrigo:
  - Linha 4: cabeçalho com datetime de cada mês (2026-05 até 2031-04)
  - Linha 7: título "🟦 DRE FAST ESCOVA"
  - Linhas 8-22: linhas da DRE Fast Escova
  - Linhas 25-40: DRE Fast Spa (ignoramos aqui)
  - Linhas 43-46: consolidado
  - Linhas 49-57: resumo anual

Setembro projetado hoje: receita R$ 52.992 · EBITDA -R$ 5.901.

O Excel mantém o projetado no mês corrente até Rodrigo começar a atualizar
com o realizado (a cada 15 dias).
"""
import json, os, datetime, re, unicodedata, sys
import openpyxl

PAINEL = r"C:\Users\rods_\OneDrive\Franquia - FAST\Claude\Painel_Gestao_Financeira_SIIBELLO.xlsx"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "financeiro.json")

META_MES = 60000.00

# Carrega config pra puxar salário da gerente (separa do pessoal_clt consolidado do Excel)
def _load_cfg():
    cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "config.json")
    try:
        with open(cfg_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
CFG = _load_cfg()
SALARIO_GERENTE = float(((CFG.get("pessoal_clt") or {}).get("salario_gerente_com_encargos")) or 6500)

# Linhas da DRE FAST ESCOVA (bloco 8-22)
# rot_key: (linha, sinal_positivo?) — se True mantém sinal, se False inverte
LINHAS_ESCOVA = {
    # ROW: (chave interna, descrição)
    8:  ("receita_bruta",        "(+) Receita Bruta"),
    9:  ("impostos",             "(-) Impostos (Simples 7%)"),
    10: ("inadimplencia",        "(-) Inadimplência 2%"),
    11: ("receita_liquida",      "(=) Receita Líquida"),
    12: ("comissoes",            "(-) Comissões (32%)"),
    13: ("royalty",              "(-) Royalty (max 2500 ou 7%)"),
    14: ("cmv",                  "(-) CMV/insumos 12%"),
    15: ("marketing_local",      "(-) Marketing local mínimo"),
    16: ("margem_contribuicao",  "(=) Margem Contribuição"),
    17: ("aluguel_iptu",         "(-) Aluguel + IPTU (rateio 45,5%)"),
    18: ("trinks_sults",         "(-) Trinks/Sults"),
    19: ("pessoal_clt",          "(-) Pessoal CLT"),
    20: ("beleza_boost",         "(-) Beleza Boost gestão"),
    21: ("midia",                "(-) Mídia"),
    22: ("ebitda",                "(=) EBITDA"),
}

MES_NUM = {
    "jan":1, "janeiro":1, "fev":2, "fevereiro":2, "mar":3, "marco":3, "março":3,
    "abr":4, "abril":4, "mai":5, "maio":5, "jun":6, "junho":6,
    "jul":7, "julho":7, "ago":8, "agosto":8, "set":9, "setembro":9,
    "out":10, "outubro":10, "nov":11, "novembro":11, "dez":12, "dezembro":12,
}


def detectar_meses(ws):
    """Varre linha 4 (cabeçalho de meses) procurando datetime."""
    achados = {}
    for c in range(2, ws.max_column + 1):
        v = ws.cell(4, c).value
        if isinstance(v, (datetime.datetime, datetime.date)):
            achados[c] = (v.year, v.month)
    return achados


def num(x):
    """Extrai float ou 0.0."""
    return float(x) if isinstance(x, (int, float)) else 0.0


def monta_mes(ws, col, ano, mes):
    """Constrói o dict de um mês lendo as 15 linhas do bloco FAST ESCOVA."""
    v = {chave: num(ws.cell(row, col).value)
         for row, (chave, _) in LINHAS_ESCOVA.items()}

    receita_bruta   = v["receita_bruta"]
    receita_liquida = v["receita_liquida"]
    ebitda          = v["ebitda"]

    # Valores em módulo (positivos) pra facilitar leitura
    impostos   = abs(v["impostos"])
    inad       = abs(v["inadimplencia"])
    comissoes  = abs(v["comissoes"])
    royalty    = abs(v["royalty"])
    cmv        = abs(v["cmv"])
    mkt_local  = abs(v["marketing_local"])
    aluguel    = abs(v["aluguel_iptu"])
    trinks     = abs(v["trinks_sults"])
    pessoal    = abs(v["pessoal_clt"])
    beleza_bst = abs(v["beleza_boost"])
    midia      = abs(v["midia"])

    # Grupos que a UI do painel espera (mesma estrutura de antes, adaptada)
    def _row(cat, real, esp=None, nota="", prov=False, extra=None):
        d = {"cat": cat, "real": real, "esp": esp if esp is not None else real,
             "nota": nota, "prov": prov}
        if extra: d.update(extra)
        return d

    rec = receita_bruta
    grupos = [
        {"id": "VARIAVEL", "titulo": "Custos variáveis — acompanham a venda",
         "linhas": [
             _row("Comissão sobre produção", comissoes, comissoes,
                  "32% da receita (premissa do modelo)", False,
                  {"esp_pct": 0.32, "real_delta_pct": comissoes/max(rec,1)}),
             _row("Produtos e insumos (CMV)", cmv, cmv,
                  "12% da receita (Fast Escova)", False,
                  {"esp_pct": 0.12, "real_delta_pct": cmv/max(rec,1)}),
             _row("Impostos sobre venda — Simples", impostos, impostos,
                  "7% da receita · provisionado por competência", True,
                  {"esp_pct": 0.07, "real_pct": 0.07}),
             _row("Inadimplência 2%", inad, inad,
                  "2% da receita bruta", False),
         ]},
        {"id": "PESSOAL", "titulo": "Pessoal fixo — CLT",
         "linhas": [
             _row("Gerente (CLT com encargos)", SALARIO_GERENTE, SALARIO_GERENTE,
                  "salário + INSS + FGTS + férias/13º proporcional"),
             _row("Recepção + limpeza + encargos", max(pessoal - SALARIO_GERENTE, 0),
                  max(pessoal - SALARIO_GERENTE, 0),
                  "total pessoal do Excel menos gerente"),
         ]},
        {"id": "OCUPACAO", "titulo": "Ocupação — rateio 45,5% do imóvel",
         "linhas": [
             _row("Aluguel + IPTU", aluguel, aluguel,
                  "45,5% do rateio das 2 lojas"),
             _row("Trinks + Sults (sistemas)", trinks, trinks,
                  "45,5% rateio"),
         ]},
        {"id": "COMERCIAL", "titulo": "Comercial e franquia",
         "linhas": [
             _row("Mídia paga", midia, midia,
                  "45,5% rateio · varia por fase"),
             _row("Beleza Boost (gestão)", beleza_bst, beleza_bst,
                  "100% Fast Escova"),
             _row("Marketing local mínimo", mkt_local, mkt_local,
                  "mínimo contratual"),
             _row("Royalty", royalty, royalty,
                  "máx entre R$ 2.500 e 7% da receita · provisionado", True),
         ]},
    ]

    def soma(g, key):
        return sum((l[key] or 0.0) for l in g["linhas"])

    for g in grupos:
        g["sub_real"] = soma(g, "real")
        g["sub_esp"] = soma(g, "esp")
    gi = {g["id"]: g for g in grupos}

    var_real = gi["VARIAVEL"]["sub_real"]
    fixo_real = sum(gi[k]["sub_real"] for k in ("PESSOAL", "OCUPACAO", "COMERCIAL"))
    real_total = var_real + fixo_real
    prov = sum(l["real"] for g in grupos for l in g["linhas"] if l["prov"])

    return {
        "ano": ano, "mes": mes, "chave": f"{ano}-{mes:02d}",
        "receita_bruta": receita_bruta,
        "receita_liquida": receita_liquida,
        "receita_real": receita_bruta,
        "receita_meta": META_MES,
        "ebitda": ebitda,
        "margem_contribuicao": v["margem_contribuicao"],
        "grupos": grupos,
        "var_real": var_real, "var_esp": var_real,
        "fixo_real": fixo_real, "fixo_esp": fixo_real,
        "custo_real": real_total, "custo_esp": real_total,
        "res_real": ebitda,
        "res_caixa": ebitda + prov,
        "provisoes_nao_debitadas": prov,
    }


def main():
    if not os.path.exists(PAINEL):
        print(f"❌ Painel não encontrado: {PAINEL}"); sys.exit(1)
    wb = openpyxl.load_workbook(PAINEL, data_only=True)
    if "DRE" not in wb.sheetnames:
        print(f"❌ Aba 'DRE' não existe. Disponíveis: {wb.sheetnames}"); sys.exit(1)
    ws = wb["DRE"]

    cols_meses = detectar_meses(ws)
    if not cols_meses:
        print("❌ Não achei cabeçalhos de mês na linha 4"); sys.exit(1)

    print(f"[dre] {len(cols_meses)} meses detectados de {min(cols_meses.values())} a {max(cols_meses.values())}")

    meses = {}
    for col, (ano, mes) in cols_meses.items():
        m = monta_mes(ws, col, ano, mes)
        meses[m["chave"]] = m

    # Log resumo
    print("\n[dre] Resumo por mês (só Fast Escova):")
    print(f"  {'MÊS':<10} {'RECEITA':>12} {'CUSTOS':>12} {'EBITDA':>12}")
    for k in sorted(meses):
        m = meses[k]
        if m["receita_bruta"] > 0 or m["custo_real"] > 0:
            print(f"  {k:<10} {m['receita_bruta']:>12,.2f} {m['custo_real']:>12,.2f} {m['res_real']:>12,.2f}")

    # Determinar mês principal
    hoje = datetime.date.today()
    chave_hoje = f"{hoje.year}-{hoje.month:02d}"
    principal = meses.get(chave_hoje)
    if not principal or principal["receita_bruta"] == 0:
        # Fallback: último mês fechado com dados
        candidatos = sorted([k for k in meses if meses[k]["receita_bruta"] > 0 and k <= chave_hoje])
        if candidatos:
            principal = meses[candidatos[-1]]
        else:
            principal = meses.get(chave_hoje) or next(iter(meses.values()))

    mes_fechado_chave = None
    for k in sorted(meses, reverse=True):
        if k < chave_hoje and meses[k]["receita_bruta"] > 0:
            mes_fechado_chave = k; break

    # Equilíbrio: usa dados do PRÓPRIO mês principal (não hardcoded)
    rec_p = principal["receita_bruta"]
    fixo_p = principal["fixo_real"]
    var_pct_p = principal["var_real"] / max(rec_p, 1)
    mc_pct_p = 1 - var_pct_p
    be_mes = fixo_p / max(mc_pct_p, 0.01)

    d = {
        "gerado_em": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "baseline": hoje.isoformat(),
        "custos_ate": hoje.isoformat(),
        "mes_corrente_chave": chave_hoje if chave_hoje in meses else None,
        "mes_principal_chave": principal["chave"],
        "mes_fechado_chave": mes_fechado_chave,
        "loja": "FAST ESCOVA LIMÃO",
        "kpis": {
            "caixa_conta": 5060.93,   # TODO: puxar do extrato
            "a_receber_stone": 20742.90,
            "resultado_mes": principal["res_real"],
            "resultado_mes_caixa": principal["res_caixa"],
            "receita_mes": principal["receita_bruta"],
            "meta_mes": META_MES,
        },
        "meses": meses,
        "resultado": {
            **principal,
            "res_esp_mesma_receita": principal["res_real"],  # projetado = real no Excel
            "res_esp_na_meta": None,  # o Excel já tem os cenários projetados
            "be_modelo_1loja": be_mes,
            "mc_real": principal["margem_contribuicao"],
            "mc_esp": principal["margem_contribuicao"],
        },
        "premissas": {
            "comissao": 0.32, "insumos": 0.12, "simples": 0.07, "inadimplencia": 0.02,
        },
        "equilibrio": {
            "fatura_hoje": rec_p,
            "custo_fixo_mes": fixo_p,
            "cenarios": [
                {"nome": "Projetado do Excel", "comissao": 0.32, "mc": mc_pct_p},
                {"nome": "Se comissão subir para 40%", "comissao": 0.40,
                 "mc": 1 - 0.40 - 0.12 - 0.07 - 0.02},
            ],
        },
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)

    print(f"\n✓ gerado: {OUT}")
    print(f"  {len(meses)} meses · mês principal: {principal['chave']} (R$ {principal['receita_bruta']:,.2f})")
    if mes_fechado_chave:
        print(f"  Último fechado com receita: {mes_fechado_chave}")


if __name__ == "__main__":
    main()
