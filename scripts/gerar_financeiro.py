# -*- coding: utf-8 -*-
"""Le o painel Excel e gera data/financeiro.json para a aba Financeiro do dashboard.

Rodar depois de qualquer atualizacao do painel. O Excel precisa ter sido aberto e
salvo pelo Excel antes, senao as formulas nao tem valor em cache.

Por decisao do Rodrigo (29/08): NAO expor o montante aplicado no fundo, nem o
capital integralizado, nem o quadro de compromissos.
"""
import json, os, datetime, re, unicodedata
import openpyxl

PAINEL = r"C:\Users\rods_\OneDrive\Franquia - FAST\Claude\Painel_Gestao_Financeira_SIIBELLO.xlsx"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "financeiro.json")

META_MES = 60000.00
# premissas do modelo (aba Premissas do painel)
PREM = dict(comissao=0.32, insumos=0.06, aluguel=18000.00, gerente=6500.00,
            midia=2500.00, beleza_boost=1900.00, sistemas=400.00,
            royalty_min=2500.00, mkt_local=1000.00)


def v(ws, cel, default=0.0):
    x = ws[cel].value
    return x if isinstance(x, (int, float)) else default


def _norm(x):
    """Rotulo comparavel: sem acento, sem pontuacao, minusculo."""
    t = unicodedata.normalize("NFKD", str(x or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def ler_pl(ws, col=3):
    """Le o P&L por ROTULO, nao por celula fixa.

    Toda vez que uma categoria nova entra no painel as linhas andam. Ler por
    endereco ja quebrou o KPI de resultado uma vez (lia C34, virou cabecalho).
    """
    m = {}
    for r in range(1, ws.max_row + 1):
        rot, val = ws.cell(r, 1).value, ws.cell(r, col).value
        if rot and isinstance(val, (int, float)):
            m.setdefault(_norm(rot), val)
    return m


def custo(m, rotulo):
    """Custo de agosto pelo rotulo, como valor positivo. Estoura se sumir."""
    k = _norm(rotulo)
    if k not in m:
        raise KeyError("linha ausente no P&L do Excel: %r — o painel mudou de estrutura" % rotulo)
    return -m[k]


def main():
    wb = openpyxl.load_workbook(PAINEL, data_only=True)
    L = wb["P&L_Operacional"]
    I = wb["Integridade"]

    M = ler_pl(L)
    rec = M[_norm("Receita faturada (R$)")]
    comissao = custo(M, "Comissão sobre produção — VARIÁVEL")
    gerente = custo(M, "Gerente — fixo mensal")
    clt_rec = custo(M, "Folha CLT — recepção (2 pessoas)")
    clt_lim = custo(M, "Folha CLT — limpeza")
    vt = custo(M, "Vale-transporte da equipe")
    aluguel = custo(M, "Aluguel + IPTU")
    marketing = custo(M, "Marketing (mídia, Beleza Boost, impressos, audiovisual)")
    insumos = custo(M, "Produtos e insumos")
    utilidades = custo(M, "Utilidades, telecom e consumo")
    seguro = custo(M, "Seguro do imóvel")
    franqueadora = custo(M, "Franqueadora, sistemas e taxas")
    a_classificar = custo(M, "Outros ainda a classificar")
    # resultado NAO e lido de celula fixa: as linhas do P&L mudam quando entra
    # uma categoria nova. E calculado abaixo, a partir das proprias linhas da DRE.

    # ---- DRE executiva: custos agrupados por natureza ----
    # esperado = premissas do modelo aplicadas a receita REALIZADA
    SIMPLES, INSUMOS_PCT = 0.07, PREM["insumos"]

    grupos = [
        ("VARIAVEL", "Custos variáveis — acompanham a venda", [
            ("Comissão sobre produção", comissao, PREM["comissao"] * rec, "31,7% da receita · premissa 32%"),
            ("Produtos e insumos (CMV)", insumos, INSUMOS_PCT * rec, "6% da receita na premissa"),
            ("Impostos sobre venda — Simples", SIMPLES * rec, SIMPLES * rec,
             "7% da receita · provisionado por competência, ainda não debitado", True),
        ]),
        ("PESSOAL", "Pessoal fixo — independe do faturamento", [
            ("Gerente", gerente, PREM["gerente"], "R$ 6.500/mês"),
            ("Folha CLT — recepção (2 pessoas)", clt_rec, 0.0, "não estava no modelo"),
            ("Folha CLT — limpeza", clt_lim, 0.0, "não estava no modelo"),
            ("Vale-transporte", vt, 0.0, "não estava no modelo"),
        ]),
        ("OCUPACAO", "Ocupação — o imóvel das duas lojas", [
            ("Aluguel + IPTU", aluguel, PREM["aluguel"], "R$ 18.000/mês na premissa · 2 lojas, 1 faturando"),
            ("Utilidades, telecom e consumo", utilidades, None, "sem premissa no modelo"),
            ("Seguro do imóvel", seguro, None, "sem premissa no modelo"),
        ]),
        ("COMERCIAL", "Comercial e franquia", [
            ("Marketing", marketing, PREM["midia"] + PREM["beleza_boost"], "inclui R$ 750 da gravação da inauguração"),
            ("Franqueadora, sistemas e taxas", franqueadora, PREM["sistemas"], "Trinks + Sults"),
            ("Royalty + marketing local", PREM["royalty_min"] + PREM["mkt_local"],
             PREM["royalty_min"] + PREM["mkt_local"],
             "mínimo contratual · provisionado por competência, ainda não debitado", True),
        ]),
        ("ABERTO", "Ainda sem classificação", [
            ("Outros a classificar", a_classificar, 0.0, "13 pessoas de menor valor + R$ 265 de diversos"),
        ]),
    ]

    def soma(g, i):
        return sum((l[i] or 0.0) for l in g[2])

    G = [{"id": g[0], "titulo": g[1],
          "linhas": [{"cat": l[0], "real": l[1], "esp": l[2], "nota": l[3],
                      "prov": len(l) > 4 and l[4]} for l in g[2]],
          "sub_real": soma(g, 1), "sub_esp": soma(g, 2)} for g in grupos]
    gi = {g["id"]: g for g in G}

    var_real, var_esp = gi["VARIAVEL"]["sub_real"], gi["VARIAVEL"]["sub_esp"]
    mc_real, mc_esp = rec - var_real, rec - var_esp
    fixo_real = sum(gi[k]["sub_real"] for k in ("PESSOAL", "OCUPACAO", "COMERCIAL", "ABERTO"))
    fixo_esp = sum(gi[k]["sub_esp"] for k in ("PESSOAL", "OCUPACAO", "COMERCIAL", "ABERTO"))
    real_total, esp_total = var_real + fixo_real, var_esp + fixo_esp

    # a DRE e por competencia: as provisoes entram no realizado.
    # o caixa e a memoria de calculo — o que a conta corrente de fato sentiu.
    prov = sum(l["real"] for g in G for l in g["linhas"] if l["prov"])
    resultado = rec - real_total          # competencia
    caixa_real = resultado + prov         # caixa

    # na meta, com a estrutura de custo do modelo
    mc_meta = 1 - PREM["comissao"] - INSUMOS_PCT - SIMPLES
    fixo_modelo = PREM["aluguel"] + PREM["gerente"] + PREM["midia"] + PREM["beleza_boost"]         + PREM["sistemas"] + PREM["royalty_min"] + PREM["mkt_local"]

    # formas de pagamento medidas em agosto (extracao local, 139 transacoes)
    FORMAS = [
        {"forma": "PIX e dinheiro", "valor": 9585.00, "prazo": "no mesmo dia", "taxa": 0.0064,
         "evidencia": "45 lançamentos na Stone, tarifa média de 0,65%"},
        {"forma": "Débito", "valor": 8660.10, "prazo": "dia seguinte", "taxa": None,
         "evidencia": "liquidação diária"},
        {"forma": "Crédito", "valor": 18711.00, "prazo": "dia seguinte", "taxa": None,
         "evidencia": "21 'Recebíveis de Cartão' em 14 dos 22 dias do período, sempre pela manhã"},
    ]

    # ponto de equilibrio
    # CashMe e Pronampe NAO entram: as parcelas sao pagas por pessoa fisica (definido em 29/08).
    FIXO = 41816.32 + 1300.00
    com_pct = comissao / rec

    d = {
        "gerado_em": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "baseline": "2026-08-28",
        "kpis": {
            "caixa_conta": 5060.93,
            "a_receber_stone": 20742.90,
            "resultado_mes": resultado,
            "resultado_mes_caixa": caixa_real,
            "receita_mes": rec,
            "meta_mes": META_MES,
        },
        "resultado": {
            "receita_real": rec, "receita_meta": META_MES,
            "grupos": G,
            "var_real": var_real, "var_esp": var_esp,
            "mc_real": mc_real, "mc_esp": mc_esp,
            "fixo_real": fixo_real, "fixo_esp": fixo_esp,
            "custo_real": real_total, "custo_esp": esp_total,
            "res_real": resultado,
            "res_caixa": caixa_real,
            "res_esp_mesma_receita": rec - esp_total,
            "res_esp_na_meta": META_MES * mc_meta - fixo_modelo,
            "provisoes_nao_debitadas": prov,
            "be_modelo_1loja": fixo_modelo / mc_meta,
        },
        "premissas": {"comissao": PREM["comissao"], "insumos": INSUMOS_PCT, "simples": SIMPLES},
        "equilibrio": {
            "fatura_hoje": rec,
            "custo_fixo_mes": FIXO,
            "cenarios": [
                {"nome": "Com a comissão de hoje", "comissao": com_pct, "mc": 1 - com_pct - INSUMOS_PCT - SIMPLES},
                {"nome": "Se a comissão subir para 40%", "comissao": 0.40, "mc": 1 - 0.40 - INSUMOS_PCT - SIMPLES},
            ],
        },
        "recebimento": {
            "medido_ate": "2026-08-14",
            "linhas": [dict(l, pct=l["valor"] / sum(x["valor"] for x in FORMAS)) for l in FORMAS],
            "total_formas": sum(l["valor"] for l in FORMAS),
            "prova": "O primeiro recebível de cartão caiu em 24/07 — um dia depois de a loja abrir. Se fosse D+30 não haveria nada para liquidar.",
            "parcelado_pct": 0.0,
            "ressalva": "O extrato da Stone traz 21 lançamentos de cartão contra 225 transações no Trinks. A cadência diária está provada; o valor total não — falta o extrato de 15/08 em diante.",
        },
        "integridade": {"placar": str(I["E18"].value or "")},
        "decisoes": [
            {"p": 1, "sev": "crit", "titulo": "Royalty devido e não pago",
             "detalhe": "Não há débito de royalty em nenhum extrato até 28/08. O contrato da Escova cobra independentemente de inauguração — o passivo corre sem aparecer.",
             "acao": "Levantar boletos no Sults, inclusive de meses anteriores, e provisionar o piso de R$ 5.000/mês."},
            {"p": 2, "sev": "crit", "titulo": "Nenhum encargo de folha aparece no razão",
             "detalhe": "São três funcionárias CLT — duas na recepção e uma na limpeza — e não existe um único pagamento de FGTS, INSS, DAS ou eSocial em nenhum mês. Só o líquido sai da conta. Com encargos e provisões de 13º e férias, a folha CLT custa cerca de R$ 8.170/mês, não R$ 6.409.",
             "acao": "Conferir com o contador onde os encargos estão sendo pagos. Se não estiverem, há passivo trabalhista e fiscal correndo."},
            {"p": 3, "sev": "crit", "titulo": "As regras de comissão não estão no Trinks",
             "detalhe": "O sistema tem o endpoint, mas nenhuma regra cadastrada. O cálculo é manual — a dispersão individual vai de 27,9% a 110,5% sobre o que cada uma produziu.",
             "acao": "Cadastrar as regras no Trinks para o cálculo parar de depender de planilha."},
            {"p": 4, "sev": "crit", "titulo": "Faturamento a 61,6% da meta",
             "detalhe": "R$ 36.955 contra R$ 60.000. Na meta, com a estrutura de custo do modelo, o mês fecharia positivo — o problema é tanto de receita quanto de custo.",
             "acao": "Puxar ocupação: 503 atendimentos em 25 dias com 12 profissionais ativos é baixa densidade."},
            {"p": 5, "sev": "ok", "titulo": "A comissão está dentro da premissa",
             "detalhe": "Separando a folha CLT das recepcionistas, a comissão de agosto é 31,7% da receita — contra os 32% do modelo. O que parecia desvio era salário classificado como comissão.",
             "acao": "Cadastrar as regras de comissão no Trinks para o cálculo parar de depender de leitura de extrato."},
            {"p": 6, "sev": "warn", "titulo": "Pronampe: R$ 190.000 entraram, mas quem paga é PF",
             "detalhe": "Os R$ 190.000 caíram na conta da empresa em 23/04, vindos da Opinião. Se as 48 parcelas são pagas por pessoa física, a empresa não tem essa dívida — o valor é aporte, não empréstimo.",
             "acao": "Classificar a entrada com o contador: mútuo do sócio, AFAC ou capital. Hoje o painel mostra R$ 223.853 de passivo que a empresa não paga."},
            {"p": 7, "sev": "warn", "titulo": "A receita não passa pela conta da PJ",
             "detalhe": "Cai na Stone e fica na Reserva. O razão da conta corrente não tem uma única entrada de faturamento — o painel enxerga o capital e não enxerga a operação.",
             "acao": "Baixar o extrato Stone de 15/08 em diante."},
            {"p": 8, "sev": "ok", "titulo": "O dinheiro entra rápido — o modelo estava errado",
             "detalhe": "O modelo assume 70% da receita em crédito parcelado em 6x, imobilizando capital de giro. A realidade: nenhuma venda parcelada e o cartão liquidando no dia seguinte.",
             "acao": "Refazer a projeção de fluxo. A necessidade de giro é uma fração do que foi dimensionado — e a CashMe foi captada em parte para cobrir isso."},
        ],
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    print("gerado:", OUT)
    print("  receita        :", rec, "| meta:", META_MES)
    print("  margem contrib :", round(mc_real, 2), "(", round(100*mc_real/rec, 1), "%) | esp:", round(100*mc_esp/rec, 1), "%")
    print("  CONFERE colunas: var", round(var_esp - var_real, 2), "| fixo", round(fixo_esp - fixo_real, 2),
          "| soma", round((var_esp - var_real) + (fixo_esp - fixo_real), 2),
          "== variacao do resultado", round(resultado - (rec - esp_total), 2))
    print("  custo fixo     :", round(fixo_real, 2), "| esperado:", round(fixo_esp, 2))
    print("  custo total    :", round(real_total, 2), "| esperado:", round(esp_total, 2))
    print("  provisoes nao debitadas:", round(prov, 2))
    print("  break-even 1 loja (modelo):", round(d["resultado"]["be_modelo_1loja"], 2))
    print("  resultado (competencia):", round(resultado, 2), "| caixa:", round(caixa_real, 2))
    print("  esperado (mesma receita):", round(d["resultado"]["res_esp_mesma_receita"], 2))
    print("  esperado (na meta)      :", round(d["resultado"]["res_esp_na_meta"], 2))


main()
