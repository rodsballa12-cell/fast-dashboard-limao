# -*- coding: utf-8 -*-
"""Le o painel Excel e gera data/financeiro.json para a aba Financeiro do dashboard.

Roda depois de qualquer atualizacao do painel. O Excel precisa ter sido aberto e
salvo pelo Excel ao menos uma vez (senao as formulas nao tem valor em cache).
"""
import json, os, datetime
import openpyxl

PAINEL = r"C:\Users\rods_\OneDrive\Franquia - FAST\Claude\Painel_Gestao_Financeira_SIIBELLO.xlsx"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "financeiro.json")


def v(ws, cel, default=0.0):
    x = ws[cel].value
    return x if isinstance(x, (int, float)) else default


def main():
    wb = openpyxl.load_workbook(PAINEL, data_only=True)
    P, G, C, K, D, L = (wb["Painel"], wb["Gestão de Capital dos Sócios"], wb["CAPEX"],
                        wb["Cartão_Pessoal"], wb["Reconciliação_Derik"], wb["P&L_Operacional"])
    I = wb["Integridade"]

    caixa_cc = 5060.93
    caixa_bnp = 513965.12

    d = {
        "gerado_em": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "baseline": "2026-08-28",
        "caixa": {
            "conta_corrente": caixa_cc,
            "fundo_bnp": caixa_bnp,
            "total": v(P, "B5"),
            "passivos_reconhecidos": v(P, "B6"),
            "operacional": v(P, "B7"),
            "buffer_minimo": v(P, "B8"),
            "stone_a_receber_d30": 20742.90,
            "stone_reserva_medida": 15070.79,
            "stone_reserva_ate": "2026-08-14",
        },
        "compromissos": {
            "capex_a_pagar": v(C, "D121"),
            "cartao_a_ressarcir": v(K, "B5"),
            "cartao_proxima_fatura": v(K, "B9"),
            "giro_holding": 87750.00,
            "pronampe_saldo": 223853.28,
            "pronampe_parcela": 4663.61,
            "cashme_divida": 1108600.70,
            "cashme_parcela_estimada": 16092.57,
            "obra_derik_saldo": v(D, "E12"),
        },
        "capital": {
            "subscrito": 750000.00,
            "integralizado": v(G, "D9"),
            "a_integralizar": v(G, "E9"),
            "afac": v(G, "F9"),
        },
        "pl": {
            "receita_ago": v(L, "C6"),
            "pessoal_total": v(L, "C18"),
            "comissao": v(L, "C15"),
            "gerente_fixo": v(L, "C16"),
            "vale_transporte": v(L, "C17"),
            "demais_custos": v(L, "C29"),
            "custo_total": v(L, "C33"),
            "resultado": v(L, "C34"),
            "resultado_pos_royalty": v(L, "C36"),
        },
        "break_even": [
            {"cenario": "Comissão real de agosto", "comissao_pct": 0.4444, "mc": 0.4256, "be": 150076.36,
             "nota": "Inclui R$ 4.713,68 pagos a duas profissionais sem produção no mês"},
            {"cenario": "Só quem produziu no mês", "comissao_pct": 0.3169, "mc": 0.5531, "be": 115480.93,
             "nota": "Se aqueles R$ 4.713,68 forem comissão de julho paga com atraso"},
            {"cenario": "Premissa do modelo", "comissao_pct": 0.3200, "mc": 0.5500, "be": 116131.82,
             "nota": "Pack v3 — comissão Escova"},
        ],
        "recebimento": {
            "imediato_pct": 0.2593, "debito_pct": 0.2343, "credito_pct": 0.5063,
            "ciclo_dias_real": 15.4, "ciclo_dias_premissa": 73.7,
            "giro_no_be_real": 75713.90, "giro_no_be_premissa": 362345.12,
            "parcelas_1x_pct": 1.0,
        },
        "integridade": {
            "placar": str(I["E18"].value or ""),
            "pendente": "Obra: R$ 8.277,54 a identificar",
        },
        "decisoes": [
            {"p": 1, "sev": "crit", "titulo": "Royalty devido e não pago",
             "detalhe": "Não há débito de royalty em nenhum extrato até 28/08. O contrato da Escova cobra independentemente de inauguração — o passivo corre sem aparecer.",
             "acao": "Levantar boletos no Sults, inclusive de meses anteriores, e provisionar o piso de R$ 5.000/mês."},
            {"p": 2, "sev": "crit", "titulo": "Comissão: 44,4% ou 31,7%?",
             "detalhe": "Duas profissionais receberam R$ 4.713,68 em agosto sem produção registrada. Se for comissão de julho atrasada, o modelo está calibrado; se for fixo, o ponto de equilíbrio sobe R$ 34,6 mil por mês.",
             "acao": "Abrir o acordo de remuneração dessas duas. É a pergunta de maior valor no P&L."},
            {"p": 3, "sev": "crit", "titulo": "Regras de comissão fora do sistema",
             "detalhe": "O Trinks responde o endpoint de comissões, mas não há nenhuma regra cadastrada. O cálculo é manual — a dispersão individual vai de 27,9% a 110,5% sobre o que cada uma produziu.",
             "acao": "Cadastrar as regras no Trinks para o cálculo parar de depender de planilha."},
            {"p": 4, "sev": "crit", "titulo": "CAPEX consome o caixa livre",
             "detalhe": "Sobram R$ 451.500,55 de CAPEX a pagar contra um caixa de R$ 519 mil que é quase todo dívida da CashMe.",
             "acao": "Repactuar prazo com os fornecedores restantes — é o que compra os meses que a rampa precisa."},
            {"p": 5, "sev": "warn", "titulo": "Giro da Opinião não devolvido",
             "detalhe": "R$ 87.750 com devolução prevista para 07-08/08. O extrato até 28/08 não mostra saída para a Opinião.",
             "acao": "Definir a data e formalizar o contrato de mútuo entre as PJs."},
            {"p": 6, "sev": "warn", "titulo": "Pronampe com duas parcelas vencidas",
             "detalhe": "Parcelas 1/48 (27/07) e 2/48 (27/08) sem registro de reembolso à Opinião.",
             "acao": "Reembolsar e acertar o calendário das 46 restantes."},
            {"p": 7, "sev": "warn", "titulo": "A receita não passa pela conta da PJ",
             "detalhe": "Cai na Stone e fica na Reserva a 100% do CDI. O razão da conta corrente não tem uma única entrada de faturamento — o painel enxerga o capital e não enxerga a operação.",
             "acao": "Baixar o extrato Stone de 15/08 em diante e trazer a Reserva para o painel."},
            {"p": 8, "sev": "ok", "titulo": "O giro necessário é menor do que o modelo diz",
             "detalhe": "Todas as vendas são em 1 parcela. O ciclo real de recebimento é de 15,4 dias contra 73,7 da premissa — o giro no ponto de equilíbrio cai de R$ 362 mil para R$ 76 mil.",
             "acao": "Refazer a projeção de fluxo. A CashMe foi captada em parte para cobrir um giro que não existe nesse tamanho."},
        ],
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    print("gerado:", OUT)
    print("  caixa total      :", d["caixa"]["total"])
    print("  resultado ago    :", d["pl"]["resultado"])
    print("  capital integr.  :", d["capital"]["integralizado"])
    print("  decisões         :", len(d["decisoes"]))


main()
