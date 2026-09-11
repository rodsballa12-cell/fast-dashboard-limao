# -*- coding: utf-8 -*-
"""Lê a aba DRE do painel Excel (blocos FAST ESCOVA e FAST SPA) e gera
data/financeiro.json (Escova) + data/spa/financeiro.json (SPA) +
data/consolidado/financeiro.json (soma).

Estrutura da aba DRE do Rodrigo:
  - Linha 4: cabeçalho com datetime de cada mês (2026-05 até 2031-04)
  - Bloco FAST ESCOVA · linhas 8-22 (título em 7)
  - Bloco FAST SPA · linhas 25-40 (título ~24)
  - Consolidado ~ linhas 43-46 (calculamos aqui em vez de ler)

Cada bloco tem as mesmas 15 linhas de DRE (receita_bruta até EBITDA). O
script detecta o início de cada bloco pelo marcador "FAST ESCOVA"/"FAST SPA"
em coluna A/B, então tolera pequenos deslocamentos no layout.

Setembro projetado Escova: receita ~R$ 52.992 · EBITDA ~-R$ 5.901.
SPA abre 25/09/2026 — projeções vêm do próprio Excel.
"""
import json, os, datetime, re, unicodedata, sys
import openpyxl

PAINEL = r"C:\Users\rods_\OneDrive\Franquia - FAST\Claude\Painel_Gestao_Financeira_SIIBELLO.xlsx"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_ESCOVA = os.path.join(ROOT, "data", "financeiro.json")
OUT_SPA = os.path.join(ROOT, "data", "spa", "financeiro.json")
OUT_CONS = os.path.join(ROOT, "data", "consolidado", "financeiro.json")

META_MES_ESCOVA = 60000.00
META_MES_SPA = 60000.00  # ajustar se franqueadora definir outro

# Carrega config pra puxar salário da gerente (separa do pessoal_clt consolidado do Excel)
def _load_cfg():
    cfg_path = os.path.join(ROOT, "data", "config.json")
    try:
        with open(cfg_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
CFG = _load_cfg()
SALARIO_GERENTE = float(((CFG.get("pessoal_clt") or {}).get("salario_gerente_com_encargos")) or 6500)


def _load_comissoes(dashboard_path):
    """Carrega regras de comissão do Trinks BackOffice + calcula taxa efetiva
    ponderada usando o mix de categorias da unidade (dashboard_data.json próprio)."""
    cpath = os.path.join(ROOT, "data", "comissoes.json")
    try:
        with open(cpath, encoding="utf-8") as f: cfg = json.load(f)
    except Exception:
        return 0.32
    try:
        with open(dashboard_path, encoding="utf-8") as f: dash = json.load(f)
    except Exception:
        return cfg.get("regra_padrao_pct") or 0.32
    cats = (dash.get("abas", {}).get("anual", {}).get("categoria_native") or [])
    if not cats:
        return cfg.get("regra_padrao_pct") or 0.32
    def _norm(s): return (s or "").lower().strip()
    mapa = {_norm(k): v for k, v in (cfg.get("por_categoria") or {}).items()}
    default = cfg.get("regra_padrao_pct") or 0.32
    total_rec = sum(c.get("v", 0) for c in cats)
    total_com = sum(c.get("v", 0) * mapa.get(_norm(c.get("nome")), default) for c in cats)
    if total_rec <= 0: return default
    return total_com / total_rec


# Mapa relativo ao TÍTULO do bloco:
# offset 0 = linha do título; +1..+15 = linhas de dados
# (bate com Escova: título 7, dados 8-22)
LINHAS_RELATIVAS = {
    1:  ("receita_bruta",        "(+) Receita Bruta"),
    2:  ("impostos",             "(-) Impostos (Simples 7%)"),
    3:  ("inadimplencia",        "(-) Inadimplência 2%"),
    4:  ("receita_liquida",      "(=) Receita Líquida"),
    5:  ("comissoes",            "(-) Comissões"),
    6:  ("royalty",              "(-) Royalty (max 2500 ou 7%)"),
    7:  ("cmv",                  "(-) CMV/insumos 12%"),
    8:  ("marketing_local",      "(-) Marketing local mínimo"),
    9:  ("margem_contribuicao",  "(=) Margem Contribuição"),
    10: ("aluguel_iptu",         "(-) Aluguel + IPTU (rateio)"),
    11: ("trinks_sults",         "(-) Trinks/Sults"),
    12: ("pessoal_clt",          "(-) Pessoal CLT"),
    13: ("beleza_boost",         "(-) Beleza Boost gestão"),
    14: ("midia",                "(-) Mídia"),
    15: ("ebitda",               "(=) EBITDA"),
}

MES_NUM = {
    "jan":1, "janeiro":1, "fev":2, "fevereiro":2, "mar":3, "marco":3, "março":3,
    "abr":4, "abril":4, "mai":5, "maio":5, "jun":6, "junho":6,
    "jul":7, "julho":7, "ago":8, "agosto":8, "set":9, "setembro":9,
    "out":10, "outubro":10, "nov":11, "novembro":11, "dez":12, "dezembro":12,
}


def _norm_txt(s):
    if not s: return ""
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().strip()


def detectar_meses(ws):
    """Varre linha 4 (cabeçalho de meses) procurando datetime."""
    achados = {}
    for c in range(2, ws.max_column + 1):
        v = ws.cell(4, c).value
        if isinstance(v, (datetime.datetime, datetime.date)):
            achados[c] = (v.year, v.month)
    return achados


def detectar_titulo_bloco(ws, texto_alvo):
    """Procura o marcador do bloco (ex 'FAST ESCOVA' ou 'FAST SPA') nas
    primeiras colunas. Retorna a linha do título ou None."""
    alvo = _norm_txt(texto_alvo)
    # scan linhas 1-60 e colunas 1-3
    for row in range(1, 60):
        for col in range(1, 4):
            v = _norm_txt(ws.cell(row, col).value)
            if v and alvo in v and "spa" not in v.replace(alvo, "") if "escova" in alvo else alvo in v:
                # ajusta: para 'fast spa' pega match direto
                if alvo == "fast spa" and "fast spa" in v:
                    return row
                if alvo == "fast escova" and "fast escova" in v:
                    return row
    return None


def num(x):
    return float(x) if isinstance(x, (int, float)) else 0.0


def monta_mes(ws, col, ano, mes, linha_titulo, meta_mes, comissao_pct, loja_label):
    """Constrói o dict de um mês lendo as 15 linhas do bloco a partir do título."""
    v = {chave: num(ws.cell(linha_titulo + off, col).value)
         for off, (chave, _) in LINHAS_RELATIVAS.items()}

    receita_bruta   = v["receita_bruta"]
    receita_liquida = v["receita_liquida"]
    impostos   = abs(v["impostos"])
    inad       = abs(v["inadimplencia"])
    comissoes_excel = abs(v["comissoes"])
    comissoes  = receita_bruta * comissao_pct
    delta_comissao = comissoes - comissoes_excel
    ebitda     = v["ebitda"] - delta_comissao
    royalty    = abs(v["royalty"])
    cmv        = abs(v["cmv"])
    mkt_local  = abs(v["marketing_local"])
    aluguel    = abs(v["aluguel_iptu"])
    trinks     = abs(v["trinks_sults"])
    pessoal    = abs(v["pessoal_clt"])
    beleza_bst = abs(v["beleza_boost"])
    midia      = abs(v["midia"])

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
                  f"{comissao_pct*100:.1f}% da receita (taxa efetiva ponderada · Trinks BackOffice)", False,
                  {"esp_pct": round(comissao_pct, 4), "real_delta_pct": comissoes/max(rec,1)}),
             _row("Produtos e insumos (CMV)", cmv, cmv,
                  f"12% da receita ({loja_label})", False,
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
        {"id": "OCUPACAO", "titulo": "Ocupação — rateio do imóvel",
         "linhas": [
             _row("Aluguel + IPTU", aluguel, aluguel,
                  "rateio 2 lojas"),
             _row("Trinks + Sults (sistemas)", trinks, trinks,
                  "rateio 2 lojas"),
         ]},
        {"id": "COMERCIAL", "titulo": "Comercial e franquia",
         "linhas": [
             _row("Mídia paga", midia, midia,
                  "rateio · varia por fase"),
             _row("Beleza Boost (gestão)", beleza_bst, beleza_bst,
                  f"100% {loja_label}"),
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
        "receita_meta": meta_mes,
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


def _consolidar_mes(m_esc, m_spa):
    """Soma dois meses. Se um dos lados for None (bloco vazio no Excel), usa o outro."""
    def val(a, b, key): return (a[key] if a else 0) + (b[key] if b else 0)
    ref = m_esc or m_spa
    grupos_c = []
    for i, g_ref in enumerate(ref["grupos"]):
        g_esc = m_esc["grupos"][i] if m_esc else None
        g_spa = m_spa["grupos"][i] if m_spa else None
        linhas_c = []
        for j, l_ref in enumerate(g_ref["linhas"]):
            l_esc = g_esc["linhas"][j] if g_esc else None
            l_spa = g_spa["linhas"][j] if g_spa else None
            l = {
                "cat": l_ref["cat"],
                "real": (l_esc["real"] if l_esc else 0) + (l_spa["real"] if l_spa else 0),
                "esp":  (l_esc["esp"]  if l_esc else 0) + (l_spa["esp"]  if l_spa else 0),
                "nota": l_ref.get("nota",""),
                "prov": l_ref.get("prov", False),
            }
            for k in ("esp_pct","real_pct","real_delta_pct"):
                if k in l_ref: l[k] = l_ref[k]
            linhas_c.append(l)
        grupos_c.append({
            "id": g_ref["id"], "titulo": g_ref["titulo"], "linhas": linhas_c,
            "sub_real": sum(l["real"] for l in linhas_c),
            "sub_esp":  sum(l["esp"]  for l in linhas_c),
        })
    ebitda_c = val(m_esc, m_spa, "ebitda")
    prov_c = val(m_esc, m_spa, "provisoes_nao_debitadas")
    return {
        "ano": ref["ano"], "mes": ref["mes"], "chave": ref["chave"],
        "receita_bruta":   val(m_esc, m_spa, "receita_bruta"),
        "receita_liquida": val(m_esc, m_spa, "receita_liquida"),
        "receita_real":    val(m_esc, m_spa, "receita_real"),
        "receita_meta":    val(m_esc, m_spa, "receita_meta"),
        "ebitda": ebitda_c,
        "margem_contribuicao": val(m_esc, m_spa, "margem_contribuicao"),
        "grupos": grupos_c,
        "var_real":  val(m_esc, m_spa, "var_real"),
        "var_esp":   val(m_esc, m_spa, "var_esp"),
        "fixo_real": val(m_esc, m_spa, "fixo_real"),
        "fixo_esp":  val(m_esc, m_spa, "fixo_esp"),
        "custo_real":val(m_esc, m_spa, "custo_real"),
        "custo_esp": val(m_esc, m_spa, "custo_esp"),
        "res_real":  ebitda_c,
        "res_caixa": ebitda_c + prov_c,
        "provisoes_nao_debitadas": prov_c,
    }


def _empacotar(meses, loja_label, meta_mes, caixa_conta=0.0, a_receber_stone=0.0):
    hoje = datetime.date.today()
    chave_hoje = f"{hoje.year}-{hoje.month:02d}"
    principal = meses.get(chave_hoje)
    if not principal or principal["receita_bruta"] == 0:
        candidatos = sorted([k for k in meses if meses[k]["receita_bruta"] > 0 and k <= chave_hoje])
        if candidatos:
            principal = meses[candidatos[-1]]
        else:
            principal = meses.get(chave_hoje) or next(iter(meses.values()))

    mes_fechado_chave = None
    for k in sorted(meses, reverse=True):
        if k < chave_hoje and meses[k]["receita_bruta"] > 0:
            mes_fechado_chave = k; break

    rec_p = principal["receita_bruta"]
    fixo_p = principal["fixo_real"]
    var_pct_p = principal["var_real"] / max(rec_p, 1)
    mc_pct_p = 1 - var_pct_p
    be_mes = fixo_p / max(mc_pct_p, 0.01)

    return {
        "gerado_em": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "baseline": hoje.isoformat(),
        "custos_ate": hoje.isoformat(),
        "mes_corrente_chave": chave_hoje if chave_hoje in meses else None,
        "mes_principal_chave": principal["chave"],
        "mes_fechado_chave": mes_fechado_chave,
        "loja": loja_label,
        "kpis": {
            "caixa_conta": caixa_conta,
            "a_receber_stone": a_receber_stone,
            "resultado_mes": principal["res_real"],
            "resultado_mes_caixa": principal["res_caixa"],
            "receita_mes": principal["receita_bruta"],
            "meta_mes": meta_mes,
        },
        "meses": meses,
        "resultado": {
            **principal,
            "res_esp_mesma_receita": principal["res_real"],
            "res_esp_na_meta": None,
            "be_modelo_1loja": be_mes,
            "mc_real": principal["margem_contribuicao"],
            "mc_esp": principal["margem_contribuicao"],
        },
        "premissas": {
            "comissao": None, "insumos": 0.12, "simples": 0.07, "inadimplencia": 0.02,
        },
        "equilibrio": {
            "fatura_hoje": rec_p,
            "custo_fixo_mes": fixo_p,
            "cenarios": [
                {"nome": "Projetado do Excel", "comissao": None, "mc": mc_pct_p},
                {"nome": "Se comissão subir para 40%", "comissao": 0.40,
                 "mc": 1 - 0.40 - 0.12 - 0.07 - 0.02},
            ],
        },
    }


def _detectar_titulo(ws, chaves_norm):
    """Retorna linha onde qualquer chave em chaves_norm aparece em coluna A-C."""
    for row in range(1, 80):
        for col in range(1, 4):
            v = _norm_txt(ws.cell(row, col).value)
            if not v: continue
            for k in chaves_norm:
                if k in v: return row
    return None


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

    # Detecta início dos blocos
    linha_titulo_escova = _detectar_titulo(ws, ["fast escova", "escova"]) or 7
    linha_titulo_spa    = _detectar_titulo(ws, ["fast spa", "spa"]) or 24
    # Garante que SPA venha depois de Escova
    if linha_titulo_spa <= linha_titulo_escova:
        # scan após Escova
        for row in range(linha_titulo_escova + 16, 80):
            for col in range(1, 4):
                v = _norm_txt(ws.cell(row, col).value)
                if v and "spa" in v: linha_titulo_spa = row; break
            if linha_titulo_spa > linha_titulo_escova: break
    print(f"[dre] título Escova linha {linha_titulo_escova} · SPA linha {linha_titulo_spa}")

    # Comissão ponderada — cada unidade tem seu dashboard_data.json
    dash_escova = os.path.join(ROOT, "data", "dashboard_data.json")
    dash_spa    = os.path.join(ROOT, "data", "spa", "dashboard_data.json")
    com_escova = _load_comissoes(dash_escova)
    com_spa    = _load_comissoes(dash_spa)
    print(f"[dre] comissão Escova {com_escova*100:.2f}% · SPA {com_spa*100:.2f}%")

    # Escova
    meses_escova = {}
    for col, (ano, mes) in cols_meses.items():
        m = monta_mes(ws, col, ano, mes, linha_titulo_escova, META_MES_ESCOVA, com_escova, "Fast Escova")
        meses_escova[m["chave"]] = m

    # SPA
    meses_spa = {}
    for col, (ano, mes) in cols_meses.items():
        m = monta_mes(ws, col, ano, mes, linha_titulo_spa, META_MES_SPA, com_spa, "Fast SPA")
        meses_spa[m["chave"]] = m

    # Consolidado
    meses_cons = {k: _consolidar_mes(meses_escova.get(k), meses_spa.get(k))
                  for k in sorted(set(meses_escova) | set(meses_spa))}

    def _print_resumo(nome, meses):
        print(f"\n[{nome}] Resumo por mês:")
        print(f"  {'MÊS':<10} {'RECEITA':>12} {'CUSTOS':>12} {'EBITDA':>12}")
        for k in sorted(meses):
            m = meses[k]
            if m["receita_bruta"] > 0 or m["custo_real"] > 0:
                print(f"  {k:<10} {m['receita_bruta']:>12,.2f} {m['custo_real']:>12,.2f} {m['res_real']:>12,.2f}")

    _print_resumo("escova", meses_escova)
    _print_resumo("spa",    meses_spa)
    _print_resumo("consol", meses_cons)

    # Empacotar e salvar
    d_escova = _empacotar(meses_escova, "FAST ESCOVA LIMÃO", META_MES_ESCOVA,
                          caixa_conta=5060.93, a_receber_stone=20742.90)
    d_escova["premissas"]["comissao"] = round(com_escova, 4)
    d_escova["equilibrio"]["cenarios"][0]["comissao"] = round(com_escova, 4)

    d_spa = _empacotar(meses_spa, "FAST SPA LIMÃO", META_MES_SPA)
    d_spa["premissas"]["comissao"] = round(com_spa, 4)
    d_spa["equilibrio"]["cenarios"][0]["comissao"] = round(com_spa, 4)
    d_spa["_pre_abertura"] = True
    d_spa["_data_inauguracao"] = ((CFG.get("unidades") or {}).get("spa") or {}).get("data_inauguracao")
    d_spa["_fonte_receita"] = "Projeção Excel (Rodrigo) — Trinks estabelecimentoId ainda não existe."

    d_cons = _empacotar(meses_cons, "FAST LIMÃO CONSOLIDADO", META_MES_ESCOVA + META_MES_SPA,
                        caixa_conta=d_escova["kpis"]["caixa_conta"],
                        a_receber_stone=d_escova["kpis"]["a_receber_stone"])
    d_cons["premissas"]["comissao"] = round((com_escova + com_spa)/2, 4)
    d_cons["equilibrio"]["cenarios"][0]["comissao"] = round((com_escova + com_spa)/2, 4)

    for path, payload, tag in [
        (OUT_ESCOVA, d_escova, "escova"),
        (OUT_SPA,    d_spa,    "spa"),
        (OUT_CONS,   d_cons,   "consolidado"),
    ]:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
        p = payload["resultado"]
        print(f"\n✓ [{tag}] gerado: {path}")
        print(f"    {len(payload['meses'])} meses · principal: {p['chave']} (R$ {p['receita_bruta']:,.2f})")


if __name__ == "__main__":
    main()
