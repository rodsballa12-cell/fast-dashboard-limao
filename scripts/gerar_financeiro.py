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
        ("Outros ainda a classificar", 6668.43, 0.0, "17 pessoas físicas (R$ 6.403) + 2 fornecedores diversos (R$ 265)"),
    ]
    esp_total = sum(e[2] for e in esp if e[2] is not None)
    real_total = sum(e[1] for e in esp)

    # ponto de equilibrio
    # CashMe e Pronampe NAO entram: as parcelas sao pagas por pessoa fisica (definido em 29/08).
    FIXO = 41816.32 + 1300.00

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
             "acao": "Abrir o acordo de remuneração dessas duas. Cada ponto percentual de comissão move o ponto de equilíbrio em cerca de R$ 1.800/mês."},
            {"p": 3, "sev": "crit", "titulo": "As regras de comissão não estão no Trinks",
             "detalhe": "O sistema tem o endpoint, mas nenhuma regra cadastrada. O cálculo é manual — a dispersão individual vai de 27,9% a 110,5% sobre o que cada uma produziu.",
             "acao": "Cadastrar as regras no Trinks para o cálculo parar de depender de planilha."},
            {"p": 4, "sev": "crit", "titulo": "Faturamento a 61,6% da meta",
             "detalhe": "R$ 36.955 contra R$ 60.000. Na meta, com a estrutura de custo do modelo, o mês fecharia positivo — o problema é tanto de receita quanto de custo.",
             "acao": "Puxar ocupação: 503 atendimentos em 25 dias com 12 profissionais ativos é baixa densidade."},
            {"p": 5, "sev": "warn", "titulo": "R$ 6.403 pagos a 17 pessoas fora do cadastro",
             "detalhe": "Vinte e oito Pix para pessoas que não constam como profissionais no Trinks. Cinco concentram R$ 4.631: Adriana (R$ 2.103 em 3 pagamentos), Claudio, Andressa, Edilson e Niedja. Se forem equipe, o custo de pessoal sobe de 64% para 81% da receita.",
             "acao": "Identificar essas cinco. É o que falta para o custo de pessoal ficar fechado."},
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
    print("  custo real     :", round(real_total, 2), "| esperado:", round(esp_total, 2))
    print("  resultado real :", round(d["resultado"]["res_real"], 2))
    print("  esperado (mesma receita):", round(d["resultado"]["res_esp_mesma_receita"], 2))
    print("  esperado (na meta)      :", round(d["resultado"]["res_esp_na_meta"], 2))


main()
