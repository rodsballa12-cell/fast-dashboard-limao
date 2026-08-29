# -*- coding: utf-8 -*-
"""Le o painel Excel e gera data/financeiro.json para a aba Financeiro do dashboard.

Rodar depois de qualquer atualizacao do painel. O Excel precisa ter sido aberto e
salvo pelo Excel antes, senao as formulas nao tem valor em cache.

Por decisao do Rodrigo (29/08): NAO expor o montante aplicado no fundo, nem o
capital integralizado, nem o quadro de compromissos.
"""
import json, os, datetime
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


def main():
    wb = openpyxl.load_workbook(PAINEL, data_only=True)
    L = wb["P&L_Operacional"]
    I = wb["Integridade"]

    rec = v(L, "C6")
    comissao = -v(L, "C15")
    gerente = -v(L, "C16")
    vt = -v(L, "C17")
    demais = -v(L, "C29")
    custo_total = -v(L, "C33")
    resultado = v(L, "C34")
    royalty = 3500.00

    # esperado: premissas do modelo aplicadas a receita realizada
    esp = [
        ("Comissão sobre produção", comissao, PREM["comissao"] * rec, "32% da receita — premissa Pack v3"),
        ("Gerente — fixo", gerente, PREM["gerente"], "R$ 6.500/mês"),
        ("Vale-transporte", vt, 0.0, "não estava previsto no modelo"),
        ("Aluguel + IPTU", 19886.18, PREM["aluguel"], "R$ 18.000/mês na premissa"),
        ("Marketing", 1900.00, PREM["midia"] + PREM["beleza_boost"], "mídia R$ 2.500 + Beleza Boost R$ 1.900"),
        ("Produtos e insumos", 2138.91, PREM["insumos"] * rec, "6% da receita"),
        ("Franqueadora e sistemas", 460.39, PREM["sistemas"], "Trinks + Sults"),
        ("Royalty + marketing local", 0.0, PREM["royalty_min"] + PREM["mkt_local"], "mínimo contratual — ainda não debitado"),
        ("Utilidades, telecom e consumo", 2851.01, None, "sem premissa no modelo"),
        ("Seguro do imóvel", 594.98, None, "sem premissa no modelo"),
        ("Outros ainda a classificar", 8394.93, 0.0, "não deveria existir"),
    ]
    esp_total = sum(e[2] for e in esp if e[2] is not None)
    real_total = sum(e[1] for e in esp)

    # ponto de equilibrio
    FIXO = 41816.32 + 1300.00 + 4663.61 + 16092.57

    d = {
        "gerado_em": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "baseline": "2026-08-28",
        "kpis": {
            "caixa_conta": 5060.93,
            "a_receber_stone": 20742.90,
            "resultado_mes": resultado - royalty,
            "receita_mes": rec,
            "meta_mes": META_MES,
        },
        "resultado": {
            "receita_real": rec, "receita_meta": META_MES,
            "linhas": [{"cat": c, "real": r, "esp": e, "nota": n} for c, r, e, n in esp],
            "custo_real": real_total, "custo_esp": esp_total,
            "res_real": rec - real_total,
            "res_esp_mesma_receita": rec - esp_total,
            "res_esp_na_meta": META_MES - (PREM["comissao"] * META_MES + PREM["insumos"] * META_MES
                                           + PREM["aluguel"] + PREM["gerente"] + PREM["midia"]
                                           + PREM["beleza_boost"] + PREM["sistemas"]
                                           + PREM["royalty_min"] + PREM["mkt_local"]),
        },
        "equilibrio": {
            "fatura_hoje": rec,
            "custo_fixo_mes": FIXO,
            "cenarios": [
                {"nome": "Com a comissão de hoje", "comissao": 0.4444, "mc": 1 - 0.4444 - 0.06 - 0.07},
                {"nome": "Se a comissão voltar a 32%", "comissao": 0.32, "mc": 1 - 0.32 - 0.06 - 0.07},
            ],
        },
        "recebimento": {
            "medido_ate": "2026-08-14",
            "linhas": [
                {"forma": "PIX e dinheiro", "pct": 0.2593, "prazo": "no mesmo dia", "taxa": 0.0064,
                 "evidencia": "45 lançamentos na Stone, tarifa média de 0,65%"},
                {"forma": "Débito", "pct": 0.2343, "prazo": "dia seguinte", "taxa": None,
                 "evidencia": "liquidação diária"},
                {"forma": "Crédito", "pct": 0.5063, "prazo": "dia seguinte", "taxa": None,
                 "evidencia": "21 'Recebíveis de Cartão' em 14 dos 22 dias do período, sempre pela manhã"},
            ],
            "prova": "O primeiro recebível de cartão caiu em 24/07 — um dia depois de a loja abrir. Se fosse D+30 não haveria nada para liquidar.",
            "parcelado_pct": 0.0,
            "ressalva": "O extrato da Stone traz 21 lançamentos de cartão contra 225 transações no Trinks. A cadência diária está provada; o valor total não — falta o extrato de 15/08 em diante.",
        },
        "integridade": {"placar": str(I["E18"].value or "")},
        "decisoes": [
            {"p": 1, "sev": "crit", "titulo": "Royalty devido e não pago",
             "detalhe": "Não há débito de royalty em nenhum extrato até 28/08. O contrato da Escova cobra independentemente de inauguração — o passivo corre sem aparecer.",
             "acao": "Levantar boletos no Sults, inclusive de meses anteriores, e provisionar o piso de R$ 5.000/mês."},
            {"p": 2, "sev": "crit", "titulo": "A comissão está 12,4 pontos acima da premissa",
             "detalhe": "Foram pagos 44,4% da receita contra os 32% do modelo — R$ 4.600 a mais só em agosto. Parte pode ser comissão de julho paga com atraso: duas profissionais receberam R$ 4.713,68 sem produção no mês.",
             "acao": "Abrir o acordo de remuneração dessas duas. Cada ponto percentual vale ~R$ 370/mês na receita de hoje e ~R$ 1.500/mês na meta."},
            {"p": 3, "sev": "crit", "titulo": "As regras de comissão não estão no Trinks",
             "detalhe": "O sistema tem o endpoint, mas nenhuma regra cadastrada. O cálculo é manual — a dispersão individual vai de 27,9% a 110,5% sobre o que cada uma produziu.",
             "acao": "Cadastrar as regras no Trinks para o cálculo parar de depender de planilha."},
            {"p": 4, "sev": "crit", "titulo": "Faturamento a 61,6% da meta",
             "detalhe": "R$ 36.955 contra R$ 60.000. Na meta, com a estrutura de custo do modelo, o mês fecharia positivo — o problema é tanto de receita quanto de custo.",
             "acao": "Puxar ocupação: 503 atendimentos em 25 dias com 12 profissionais ativos é baixa densidade."},
            {"p": 5, "sev": "warn", "titulo": "R$ 8.395 de custo sem classificação",
             "detalhe": "Enquanto esses lançamentos não forem abertos, o custo real de agosto é pelo menos o que está aqui — pode ser maior.",
             "acao": "Pente fino nos lançamentos de agosto sem categoria."},
            {"p": 6, "sev": "warn", "titulo": "A receita não passa pela conta da PJ",
             "detalhe": "Cai na Stone e fica na Reserva. O razão da conta corrente não tem uma única entrada de faturamento — o painel enxerga o capital e não enxerga a operação.",
             "acao": "Baixar o extrato Stone de 15/08 em diante."},
            {"p": 7, "sev": "ok", "titulo": "O dinheiro entra rápido — o modelo estava errado",
             "detalhe": "O modelo assume 70% da receita em crédito parcelado em 6x, imobilizando capital de giro. A realidade: nenhuma venda parcelada e o cartão liquidando no dia seguinte.",
             "acao": "Refazer a projeção de fluxo. A necessidade de giro é uma fração do que foi dimensionado — e a CashMe foi captada em parte para cobrir isso."},
        ],
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    print("gerado:", OUT)
    print("  receita        :", rec, "| meta:", META_MES)
    print("  custo real     :", round(real_total, 2), "| esperado:", round(esp_total, 2))
    print("  resultado real :", round(d["resultado"]["res_real"], 2))
    print("  esperado (mesma receita):", round(d["resultado"]["res_esp_mesma_receita"], 2))
    print("  esperado (na meta)      :", round(d["resultado"]["res_esp_na_meta"], 2))


main()
