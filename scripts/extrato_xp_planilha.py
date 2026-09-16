# -*- coding: utf-8 -*-
"""Gera a planilha de lançamentos classificados a partir do extrato da XP.

Companheiro do `extrato_xp.py`: aquele classifica e imprime, este entrega um
.xlsx para o Rodrigo colar no Painel_Gestao_Financeira_SIIBELLO.xlsx.

O rateio de cada grupo fica numa célula só, na aba Parâmetros: mudar 45,5%
para outro número recalcula o resumo inteiro, sem tocar em 330 linhas.

ATENÇÃO AO ENTREGAR: o openpyxl grava fórmula sem valor em cache. O Excel
calcula ao abrir, mas qualquer coisa que leia o cache vê None. O LibreOffice
do ambiente de nuvem não recalcula (16/09/2026: estourou 180s num arquivo de
três células), por isso a aba Resumo traz uma linha CONFERÊNCIA com os mesmos
totais calculados em Python — se o Excel abrir e divergir, a fórmula está errada.

Uso:
    python3 scripts/extrato_xp_planilha.py <extrato.csv> <saida.xlsx>
"""
import json, sys
from pathlib import Path
from collections import OrderedDict
sys.path.insert(0, str(Path(__file__).resolve().parent))
from extrato_xp import ler, classificar, nomes_equipe, parte
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(2)
CSV, OUT = sys.argv[1], sys.argv[2]

linhas = ler(Path(CSV))
eq = nomes_equipe()
for x in linhas:
    g, s = classificar(x['desc'], x['valor'], eq)
    x['grupo'], x['linha'], x['parte'] = g, s, parte(x['desc'])
linhas.sort(key=lambda x: (x['data'], x['desc']))
meses = sorted({x['data'][:7] for x in linhas})

# grupos na ordem do DRE + rateio padrão (editável na aba Parâmetros)
GRUPOS = OrderedDict([
    ('COMISSAO',        ('Comissão sobre produção',              1.000, 'Equipe da Escova · 100% da unidade')),
    ('CMV',             ('Produtos e insumos',                   1.000, 'Insumo consumido na Escova')),
    ('PESSOAL_FIXO',    ('Pessoal fixo (gerente, recepção, VT)', 1.000, 'Folha da Escova')),
    ('OCUPACAO',        ('Ocupação (aluguel, energia, água)',    0.455, 'Imóvel dividido com o Spa')),
    ('COMERCIAL',       ('Comercial (mídia, agência)',           0.455, 'Verba dividida entre as duas contas')),
    ('FRANQUIA',        ('Royalty e sistemas da rede',           1.000, 'Cobrado sobre a receita da Escova')),
    ('CAPEX',           ('Obra, mobiliário e abertura',          0.000, 'Investimento, não despesa — fora do DRE')),
    ('NAO_OPERACIONAL', ('Sócios e conta investimento',          0.000, 'Capital, não operação')),
    ('A_CLASSIFICAR',   ('Transferências SIIBELLO (holding)',    0.000, 'Intragrupo — confirmar com o Rodrigo')),
    ('OUTROS',          ('Não classificado',                     0.000, 'Rodrigo precisa dizer o que é')),
])

ARIAL   = 'Arial'
AZUL    = Font(name=ARIAL, size=10, color='0000FF')
PRETO   = Font(name=ARIAL, size=10)
NEG     = Font(name=ARIAL, size=10, bold=True)
TIT     = Font(name=ARIAL, size=13, bold=True)
CAB     = Font(name=ARIAL, size=10, bold=True, color='FFFFFF')
FILL_CAB= PatternFill('solid', fgColor='1F3864')
FILL_AM = PatternFill('solid', fgColor='FFFF00')
FILL_CZ = PatternFill('solid', fgColor='F2F2F2')
MOEDA   = '#,##0.00;(#,##0.00);-'
PCT     = '0.0%'
fina    = Side(style='thin', color='BFBFBF')
BORDA   = Border(bottom=fina)

wb = Workbook()

# ---------------------------------------------------------------- Leia-me
ws = wb.active; ws.title = 'Leia-me'
ws.column_dimensions['A'].width = 100
txt = [
    ('Extrato XP classificado · 18/06/2026 a 16/09/2026', TIT),
    ('', PRETO),
    ('Para que serve', NEG),
    ('Colar no Painel_Gestao_Financeira_SIIBELLO.xlsx, aba DRE, bloco FAST ESCOVA.', PRETO),
    ('Os 330 lançamentos da conta XP, classificados nos mesmos grupos do DRE.', PRETO),
    ('', PRETO),
    ('O que editar (células em AMARELO, na aba Parâmetros)', NEG),
    ('· O rateio de cada grupo. O padrão de 45,5% vem do rateio do imóvel já usado no DRE.', PRETO),
    ('· As premissas do DRE, para a aba "Premissa x Real" comparar contra o realizado.', PRETO),
    ('Tudo o mais é fórmula. Se você mudar um rateio, o resumo inteiro recalcula.', PRETO),
    ('', PRETO),
    ('Três separações que mudam a leitura', NEG),
    ('1. APORTE NÃO É RECEITA. Transferência entre sócios e para conta investimento soma', PRETO),
    ('   R$ 1,2 milhão no trimestre — trinta vezes o movimento da loja. Rateio 0%.', PRETO),
    ('2. CAPEX NÃO É CUSTO. Obra, mobiliário e uniforme somam R$ 318 mil, quase tudo Spa. Rateio 0%.', PRETO),
    ('3. RECEITA NÃO SAI DAQUI. A XP é conta de PAGAMENTO: o dinheiro de venda chega em lotes', PRETO),
    ('   que não batem com dia nenhum de caixa. Receita continua vindo do Trinks.', PRETO),
    ('', PRETO),
    ('O que ficou sem classificar', NEG),
    ('64 lançamentos, R$ 16.650, quase todos PIX a pessoas físicas em julho (R$ 400 a R$ 1.600).', PRETO),
    ('Parecem obra e serviço de abertura, mas não foram chutados. Estão na aba Lançamentos', PRETO),
    ('com grupo OUTROS — classifique e o resumo se ajusta sozinho.', PRETO),
    ('', PRETO),
    ('Gerado por scripts/extrato_xp.py · o CSV bruto não foi para o repositório,', PRETO),
    ('porque traz movimentação pessoal entre os sócios.', PRETO),
]
for i, (t, f) in enumerate(txt, start=1):
    c = ws.cell(row=i, column=1, value=t); c.font = f; c.alignment = Alignment(wrap_text=False)

# ------------------------------------------------------------ Parâmetros
wp = wb.create_sheet('Parâmetros')
wp.column_dimensions['A'].width = 20
wp.column_dimensions['B'].width = 38
wp.column_dimensions['C'].width = 12
wp.column_dimensions['D'].width = 46
wp['A1'] = 'Parâmetros'; wp['A1'].font = TIT
wp['A2'] = 'Células amarelas: editáveis. O resto do arquivo lê daqui.'; wp['A2'].font = PRETO
for j, h in enumerate(['GRUPO', 'Linha do DRE', '% Escova', 'Por que esse rateio'], start=1):
    c = wp.cell(row=4, column=j, value=h); c.font = CAB; c.fill = FILL_CAB
for i, (g, (nome, rat, porque)) in enumerate(GRUPOS.items(), start=5):
    wp.cell(row=i, column=1, value=g).font = PRETO
    wp.cell(row=i, column=2, value=nome).font = PRETO
    c = wp.cell(row=i, column=3, value=rat); c.font = AZUL; c.fill = FILL_AM; c.number_format = PCT
    wp.cell(row=i, column=4, value=porque).font = PRETO
LIN_G0, LIN_G1 = 5, 4 + len(GRUPOS)

r = LIN_G1 + 2
wp.cell(row=r, column=1, value='Premissas do DRE (para comparar)').font = NEG
prem = [('Comissão sobre produção', 0.3744, 'nota do DRE: taxa efetiva ponderada · Trinks BackOffice'),
        ('Produtos e insumos (CMV)', 0.12, '12% da receita · padrão Fast Escova'),
        ('Impostos Simples', 0.07, 'provisionado por competência'),
        ('Inadimplência', 0.0, 'não se aplica — sem inadimplência (Rodrigo, 16/09)'),
        ('Custo fixo mensal', 30807.52, 'financeiro.json · equilibrio.custo_fixo_mes'),
        ('Receita 23/07 a 31/08 (Trinks)', 47522.10, 'produção já fechada e já paga em comissão')]
for k, (nome, v, nota) in enumerate(prem):
    rr = r + 1 + k
    wp.cell(row=rr, column=2, value=nome).font = PRETO
    c = wp.cell(row=rr, column=3, value=v); c.font = AZUL; c.fill = FILL_AM
    c.number_format = PCT if v < 1 else MOEDA
    wp.cell(row=rr, column=4, value=nota).font = PRETO
P_COM, P_CMV, P_SIMP, P_INAD, P_FIXO, P_RECEITA = [f'Parâmetros!$C${r+1+k}' for k in range(6)]

# ----------------------------------------------------------- Lançamentos
wl = wb.create_sheet('Lançamentos')
cabs = ['Data', 'Descrição', 'Contraparte', 'Valor (conta)', 'GRUPO', 'Linha', 'Mês', '% Escova', 'Valor Escova']
larg = [11, 62, 40, 15, 17, 34, 9, 10, 15]
for j, (h, w) in enumerate(zip(cabs, larg), start=1):
    c = wl.cell(row=1, column=j, value=h); c.font = CAB; c.fill = FILL_CAB
    wl.column_dimensions[get_column_letter(j)].width = w
wl.freeze_panes = 'A2'
for i, x in enumerate(linhas, start=2):
    wl.cell(row=i, column=1, value=x['data']).font = PRETO
    wl.cell(row=i, column=2, value=x['desc']).font = PRETO
    wl.cell(row=i, column=3, value=x['parte']).font = PRETO
    c = wl.cell(row=i, column=4, value=round(x['valor'], 2)); c.font = AZUL; c.number_format = MOEDA
    wl.cell(row=i, column=5, value=x['grupo']).font = PRETO
    wl.cell(row=i, column=6, value=x['linha']).font = PRETO
    wl.cell(row=i, column=7, value=x['data'][:7]).font = PRETO
    c = wl.cell(row=i, column=8,
        value=f'=IFERROR(INDEX(Parâmetros!$C${LIN_G0}:$C${LIN_G1},MATCH(E{i},Parâmetros!$A${LIN_G0}:$A${LIN_G1},0)),0)')
    c.font = PRETO; c.number_format = PCT
    c = wl.cell(row=i, column=9, value=f'=D{i}*H{i}'); c.font = PRETO; c.number_format = MOEDA
N = len(linhas) + 1

# --------------------------------------------------------------- Resumo
ws2 = wb.create_sheet('Resumo por mês')
ws2.column_dimensions['A'].width = 20
ws2.column_dimensions['B'].width = 40
for j in range(len(meses) + 1):
    ws2.column_dimensions[get_column_letter(3 + j)].width = 14
ws2['A1'] = 'Custo da Escova por mês · já rateado'; ws2['A1'].font = TIT
ws2['A2'] = 'Soma a coluna "Valor Escova" da aba Lançamentos. Muda o rateio, muda aqui.'; ws2['A2'].font = PRETO
for j, h in enumerate(['GRUPO', 'Linha do DRE'] + meses + ['TOTAL'], start=1):
    c = ws2.cell(row=4, column=j, value=h); c.font = CAB; c.fill = FILL_CAB
    c.alignment = Alignment(horizontal='center')
lin = 5
for g, (nome, _, _) in GRUPOS.items():
    ws2.cell(row=lin, column=1, value=g).font = PRETO
    ws2.cell(row=lin, column=2, value=nome).font = PRETO
    for k, m in enumerate(meses):
        c = ws2.cell(row=lin, column=3 + k,
            value=f"=SUMIFS(Lançamentos!$I$2:$I${N},Lançamentos!$E$2:$E${N},$A{lin},Lançamentos!$G$2:$G${N},{get_column_letter(3+k)}$4)")
        c.font = PRETO; c.number_format = MOEDA
    c = ws2.cell(row=lin, column=3 + len(meses),
        value=f"=SUM(C{lin}:{get_column_letter(2+len(meses))}{lin})")
    c.font = NEG; c.number_format = MOEDA
    for j in range(1, 4 + len(meses)):
        ws2.cell(row=lin, column=j).border = BORDA
    lin += 1
L0, L1 = 5, lin - 1
LOP0, LOP1 = 5, 10   # COMISSAO..FRANQUIA
ws2.cell(row=lin + 1, column=2, value='CUSTO OPERACIONAL DA ESCOVA').font = NEG
for k in range(len(meses) + 1):
    col = get_column_letter(3 + k)
    c = ws2.cell(row=lin + 1, column=3 + k, value=f'=SUM({col}{LOP0}:{col}{LOP1})')
    c.font = NEG; c.fill = FILL_CZ; c.number_format = MOEDA

# ------------------------------------------------------- Premissa x Real
ws3 = wb.create_sheet('Premissa x Real')
for col, w in zip('ABCDE', [44, 16, 16, 16, 52]):
    ws3.column_dimensions[col].width = w
ws3['A1'] = 'Premissa do DRE contra o que o banco pagou'; ws3['A1'].font = TIT
ws3['A2'] = 'Comissão é paga com defasagem: o lote de 15/09 cobre produção até ~31/08.'; ws3['A2'].font = PRETO
for j, h in enumerate(['', 'Premissa', 'Realizado', 'Diferença', 'Observação'], start=1):
    c = ws3.cell(row=4, column=j, value=h); c.font = CAB; c.fill = FILL_CAB
IC = LOP0  # linha da COMISSAO no Resumo
TOT = get_column_letter(3 + len(meses))
ws3['A5'] = 'Comissão paga (R$)'; ws3['A5'].font = PRETO
ws3['B5'] = f"={P_COM}*{P_RECEITA}"; ws3['B5'].number_format = MOEDA; ws3['B5'].font = PRETO
ws3['C5'] = f"=-'Resumo por mês'!{TOT}{IC}"; ws3['C5'].number_format = MOEDA; ws3['C5'].font = PRETO
ws3['D5'] = '=C5-B5'; ws3['D5'].number_format = MOEDA; ws3['D5'].font = NEG
ws3['E5'] = 'Premissa = 37,44% da produção fechada'; ws3['E5'].font = PRETO
ws3['A6'] = 'Comissão sobre a produção (%)'; ws3['A6'].font = PRETO
ws3['B6'] = f"={P_COM}"; ws3['B6'].number_format = PCT; ws3['B6'].font = PRETO
ws3['C6'] = f"=IF({P_RECEITA}=0,0,C5/{P_RECEITA})"; ws3['C6'].number_format = PCT; ws3['C6'].font = PRETO
ws3['D6'] = '=C6-B6'; ws3['D6'].number_format = PCT; ws3['D6'].font = NEG
ws3['E6'] = 'Cada ponto vale ~R$ 600/mês na meta de 60k'; ws3['E6'].font = PRETO

ws3['A8'] = 'Margem de contribuição'; ws3['A8'].font = NEG
ws3['B8'] = f"=1-B6-{P_CMV}-{P_SIMP}-{P_INAD}"; ws3['B8'].number_format = PCT; ws3['B8'].font = PRETO
ws3['C8'] = f"=1-C6-{P_CMV}-{P_SIMP}-{P_INAD}"; ws3['C8'].number_format = PCT; ws3['C8'].font = PRETO
ws3['D8'] = '=C8-B8'; ws3['D8'].number_format = PCT; ws3['D8'].font = NEG
ws3['E8'] = '1 − comissão − CMV − Simples − inadimplência'; ws3['E8'].font = PRETO

ws3['A9'] = 'Faturamento de equilíbrio'; ws3['A9'].font = NEG
ws3['B9'] = f"=IF(B8<=0,\"\",{P_FIXO}/B8)"; ws3['B9'].number_format = MOEDA; ws3['B9'].font = PRETO
ws3['C9'] = f"=IF(C8<=0,\"\",{P_FIXO}/C8)"; ws3['C9'].number_format = MOEDA; ws3['C9'].font = PRETO
ws3['D9'] = '=IF(OR(B9="",C9=""),"",C9-B9)'; ws3['D9'].number_format = MOEDA; ws3['D9'].font = NEG
ws3['E9'] = 'Custo fixo ÷ margem de contribuição'; ws3['E9'].font = PRETO

ws3['A10'] = 'Resultado batendo a meta de R$ 60.000'; ws3['A10'].font = NEG
ws3['B10'] = f"=60000*B8-{P_FIXO}"; ws3['B10'].number_format = MOEDA; ws3['B10'].font = PRETO
ws3['C10'] = f"=60000*C8-{P_FIXO}"; ws3['C10'].number_format = MOEDA; ws3['C10'].font = PRETO
ws3['D10'] = '=C10-B10'; ws3['D10'].number_format = MOEDA; ws3['D10'].font = NEG
ws3['E10'] = 'Negativo nas duas leituras: a meta não é meta de equilíbrio'; ws3['E10'].font = PRETO

ws3['A12'] = 'Custos que o DRE ainda não tem'; ws3['A12'].font = NEG
ws3['A13'] = 'Energia, água, gás, telefone, seguro e vale-transporte'; ws3['A13'].font = PRETO
ws3['C13'] = f"=-('Resumo por mês'!{TOT}8)/{len(meses)}"; ws3['C13'].number_format = MOEDA; ws3['C13'].font = PRETO
ws3['E13'] = f'Média mensal do grupo OCUPAÇÃO já rateado, sobre {len(meses)} meses'; ws3['E13'].font = PRETO

# ------------------------------------------------- bloco de conferência
# Valores calculados em Python sobre os MESMOS lançamentos. Ficam aqui como
# número fixo, de propósito: se o Excel recalcular e der outra coisa, alguma
# fórmula está errada. É a única checagem possível deste lado — o LibreOffice
# do ambiente onde isto foi gerado não conseguiu recalcular a planilha, e um
# arquivo do openpyxl nasce sem valor em cache (o Excel calcula ao abrir).
rat = {g: v[1] for g, v in GRUPOS.items()}
lc = lin + 3
ws2.cell(row=lc, column=1, value='CONFERÊNCIA').font = NEG
ws2.cell(row=lc, column=2,
         value='Números fixos, calculados fora do Excel. As linhas acima devem bater com estes.').font = PRETO
for k, m in enumerate(meses):
    c = ws2.cell(row=lc, column=3 + k,
        value=round(sum(x['valor'] * rat[x['grupo']] for x in linhas
                        if x['data'][:7] == m and x['grupo'] in
                        ('COMISSAO', 'CMV', 'PESSOAL_FIXO', 'OCUPACAO', 'COMERCIAL', 'FRANQUIA')), 2))
    c.font = AZUL; c.number_format = MOEDA
c = ws2.cell(row=lc, column=3 + len(meses),
    value=round(sum(x['valor'] * rat[x['grupo']] for x in linhas if x['grupo'] in
                    ('COMISSAO', 'CMV', 'PESSOAL_FIXO', 'OCUPACAO', 'COMERCIAL', 'FRANQUIA')), 2))
c.font = AZUL; c.number_format = MOEDA
ws2.cell(row=lc + 1, column=2,
         value='Se mudar o rateio na aba Parâmetros, a linha de cima muda e esta NÃO — é esperado.').font = PRETO

wb.save(OUT)
print('gravado:', OUT, '|', len(linhas), 'lançamentos |', len(meses), 'meses')
