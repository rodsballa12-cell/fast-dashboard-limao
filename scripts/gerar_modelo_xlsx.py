# -*- coding: utf-8 -*-
"""Gera o modelo financeiro do FAST Insights em Excel, com fórmulas vivas.

Tudo depende da aba Premissas: mudar uma célula azul recalcula o modelo mensal,
o resumo e os nove cenários.
"""
import pathlib
from openpyxl import Workbook

import cenarios_def as CD
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import LineChart, Reference

SAIDA = pathlib.Path("FAST-Insights-modelo-financeiro.xlsx")

# ---------------------------------------------------------------- estilo
FONTE = "Arial"
AZUL = Font(name=FONTE, size=10, color="0000FF")            # entrada digitada
PRETO = Font(name=FONTE, size=10)                            # fórmula
VERDE = Font(name=FONTE, size=10, color="008000")            # link entre abas
NEGRITO = Font(name=FONTE, size=10, bold=True)
TITULO = Font(name=FONTE, size=14, bold=True, color="1B1A17")
SUB = Font(name=FONTE, size=10, color="6A675E", italic=True)
CABEC = Font(name=FONTE, size=9, bold=True, color="FFFFFF")
SECAO = Font(name=FONTE, size=10, bold=True, color="1F4C88")

F_CABEC = PatternFill("solid", fgColor="1F4C88")
F_SECAO = PatternFill("solid", fgColor="EAEFF7")
F_INPUT = PatternFill("solid", fgColor="FFFFCC")             # preencher aqui
F_TOTAL = PatternFill("solid", fgColor="F1F0EC")
F_ALERTA = PatternFill("solid", fgColor="F7F0E4")

FINA = Side(style="thin", color="D0CEC7")
BORDA = Border(left=FINA, right=FINA, top=FINA, bottom=FINA)

RS = 'R$ #,##0;(R$ #,##0);"–"'
RS2 = 'R$ #,##0.00;(R$ #,##0.00);"–"'
PCT = '0.0%;(0.0%);"–"'
NUM = '#,##0;(#,##0);"–"'
NUM1 = '#,##0.0'

wb = Workbook()


def cab(ws, linha, valores, larguras=None):
    for i, v in enumerate(valores, start=1):
        c = ws.cell(row=linha, column=i, value=v)
        c.font, c.fill, c.border = CABEC, F_CABEC, BORDA
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    if larguras:
        for i, w in enumerate(larguras, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[linha].height = 28


def secao(ws, linha, texto, ate=4):
    c = ws.cell(row=linha, column=1, value=texto)
    c.font, c.fill = SECAO, F_SECAO
    for i in range(2, ate + 1):
        ws.cell(row=linha, column=i).fill = F_SECAO


# ================================================================ LEIA-ME
ws = wb.active
ws.title = "Leia-me"
ws.sheet_view.showGridLines = False
ws.column_dimensions["A"].width = 3
ws.column_dimensions["B"].width = 30
ws.column_dimensions["C"].width = 88

ws["B2"] = "FAST Insights — modelo financeiro"
ws["B2"].font = TITULO
ws["B3"] = "Suporte quantitativo ao business plan · Rodrigo Garcia, franqueado FAST Limão · 08/09/2026"
ws["B3"].font = SUB

linhas = [
    ("", ""),
    ("COMO USAR", ""),
    ("1. Mude só o azul",
     "Toda célula com texto AZUL na aba Premissas é uma entrada que você pode editar. "
     "Células pretas são fórmulas — não digite por cima delas."),
    ("2. Fundo amarelo = decisivo",
     "As entradas com fundo amarelo são as que mais mexem no resultado. Comece por elas."),
    ("3. O resto se ajusta sozinho",
     "Modelo mensal, Resumo e Cenários recalculam a partir das Premissas. "
     "Nenhum número deste arquivo é digitado duas vezes."),
    ("4. Se abrir e vier vazio",
     "Alguns visualizadores não recalculam sozinhos. Abra no Excel, LibreOffice ou "
     "Google Sheets e mande recalcular (no Excel: Ctrl+Alt+F9)."),
    ("", ""),
    ("AS ABAS", ""),
    ("Premissas", "Todas as entradas do modelo, agrupadas por tema, com a fonte de cada número."),
    ("Modelo mensal", "36 meses, linha a linha: lojas, receita, custos, resultado e caixa acumulado."),
    ("Resumo", "Os números de decisão — capital necessário, ponto de equilíbrio, economia unitária — e os dois gráficos."),
    ("Cenários", "Nove cenários calculados ao vivo, inclusive os de participação da franqueadora na receita."),
    ("Descoberta", "Os 34 itens que faltam validar. Marque o status e anote a resposta."),
    ("", ""),
    ("LEGENDA DE CORES", ""),
    ("Azul", "Número digitado — é uma premissa, e você pode mudar."),
    ("Preto", "Fórmula calculada dentro da própria aba."),
    ("Verde", "Fórmula que busca valor em outra aba."),
    ("Fundo amarelo", "Premissa decisiva, ou campo para você preencher."),
    ("", ""),
    ("TRÊS AVISOS HONESTOS", ""),
    ("Projeção, não previsão",
     "Cada linha aqui é uma suposição explícita. As que ainda não foram verificadas estão "
     "na aba Descoberta — seis delas são bloqueantes."),
    ("Antes de impostos, por padrão",
     "A alíquota sobre a receita da empresa de software vem zerada (item N3 da Descoberta). "
     "Preencha-a em Premissas assim que o contador responder: no Simples, algo entre 6% e 16%."),
    ("Adoção já é líquida de churn",
     "A curva de adoção representa lojas ativas, já descontando quem sai. O churn das "
     "Premissas serve só para calcular o LTV."),
]
r = 5
for a, b in linhas:
    if a and not b:
        secao(ws, r, a, ate=3)
    else:
        ws.cell(row=r, column=2, value=a).font = NEGRITO
        c = ws.cell(row=r, column=3, value=b)
        c.font = PRETO
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if a:
            ws.row_dimensions[r].height = 30
    r += 1

for cel, hexcor in (("B20", "0000FF"), ("B21", "000000"), ("B22", "008000")):
    ws[cel].font = Font(name=FONTE, size=10, bold=True, color=hexcor)
ws["B23"].fill = F_INPUT

# ================================================================ PREMISSAS
ps = wb.create_sheet("Premissas")
ps.sheet_view.showGridLines = False
for col, w in zip("ABCDEF", (40, 14, 13, 13, 50, 2)):
    ps.column_dimensions[col].width = w
ps["A1"] = "Premissas"
ps["A1"].font = TITULO
ps["A2"] = ("Edite apenas as células azuis. A célula B7 escolhe o modelo comercial e "
            "reconfigura sete premissas de uma vez.")
ps["A2"].font = SUB
cab(ps, 4, ["Premissa", "Em uso", "Sem homologação", "Com homologação", "Origem / observação"])

L = {}


def prem(linha, rotulo, valor, unidade, obs, fmt=RS, chave=None, destaque=False, formula=None):
    ps.cell(row=linha, column=1, value=rotulo).font = PRETO
    c = ps.cell(row=linha, column=2, value=formula if formula else valor)
    c.font = PRETO if formula else AZUL
    c.number_format, c.border = fmt, BORDA
    if destaque:
        c.fill = F_INPUT
    ps.cell(row=linha, column=3, value=unidade).font = SUB
    o = ps.cell(row=linha, column=5, value=obs)
    o.font, o.alignment = SUB, Alignment(wrap_text=True, vertical="top")
    if chave:
        L[chave] = f"Premissas!$B${linha}"
    return linha


# ---------- o seletor de modelo comercial ----------
secao(ps, 6, "MODELO COMERCIAL — a chave que muda tudo", ate=5)
ps.cell(row=7, column=1, value="Modelo em uso  (1 = COM homologação · 0 = SEM homologação)").font = NEGRITO
c = ps.cell(row=7, column=2, value=1)
c.font, c.number_format, c.border, c.fill = AZUL, NUM, BORDA, F_INPUT
o = ps.cell(row=7, column=5,
            value="1 = homologado obrigatório em toda a rede, com cobrança consolidada pela "
                  "franqueadora. 0 = venda voluntária, loja a loja. Trocar aqui reconfigura "
                  "as sete linhas abaixo de uma vez.")
o.font, o.alignment = Font(name=FONTE, size=10, color="8A5210", italic=True), \
    Alignment(wrap_text=True, vertical="top")
ps.row_dimensions[7].height = 42

MODELO = [
    ("Preço por loja", RS2, "=B24", 299.0, "ticket",
     "Sem homologação vem do mix de planos; com homologação é preço único para a rede toda."),
    ("Teto de adoção", PCT, 0.65, 0.95, "teto",
     "Obrigatório não é venda: os 5% que faltam são lojas em implantação e em transição."),
    ("Mês central da curva", NUM1, 16.0, 12.0, "centro",
     "A franqueadora marca prazo — não há convencimento loja a loja."),
    ("Inclinação da curva", "0.00", 0.32, 0.45, "k",
     "Implantação em bloco, não gota a gota."),
    ("CAC por loja", RS, 400.0, 50.0, "cac",
     "Sem esforço de venda, sobra só o onboarding."),
    ("Cobrança por loja", RS2, 3.0, 0.0, "cobranca",
     "No consolidado é uma fatura só: a taxa por loja desaparece."),
    ("Participação da franqueadora", PCT, 0.0, 0.25, "share",
     "O que a franqueadora cobra para tornar obrigatório e cobrar das lojas por você."),
]
for i, (rot, fmt, vol, obr, chave, obs) in enumerate(MODELO):
    r = 9 + i
    ps.cell(row=r, column=1, value=rot).font = PRETO
    b = ps.cell(row=r, column=2, value=f"=IF($B$7=1,D{r},C{r})")
    b.font, b.number_format, b.border, b.fill = NEGRITO, fmt, BORDA, F_TOTAL
    cv = ps.cell(row=r, column=3, value=vol)
    cv.font = VERDE if isinstance(vol, str) else AZUL
    co = ps.cell(row=r, column=4, value=obr)
    co.font = AZUL
    for cc in (cv, co):
        cc.number_format, cc.border = fmt, BORDA
    co.fill = F_INPUT
    ob = ps.cell(row=r, column=5, value=obs)
    ob.font, ob.alignment = SUB, Alignment(wrap_text=True, vertical="top")
    L[chave] = f"Premissas!$B${r}"
ps.cell(row=8, column=3, value="Sem homologação").font = NEGRITO
ps.cell(row=8, column=4, value="Com homologação").font = NEGRITO

# ---------- planos e mix (só valem no modelo voluntário) ----------
secao(ps, 17, "PLANOS E MIX — usados apenas no modelo SEM homologação", ate=5)
ps.cell(row=18, column=1, value="Plano").font = NEGRITO
ps.cell(row=18, column=2, value="Preço R$/mês").font = NEGRITO
ps.cell(row=18, column=3, value="Mix").font = NEGRITO
for i, (nome, preco, mix) in enumerate(
        [("Essencial", 199, 0.40), ("Gestão", 349, 0.45), ("Crescimento", 549, 0.15)]):
    r = 19 + i
    ps.cell(row=r, column=1, value=nome).font = PRETO
    c = ps.cell(row=r, column=2, value=preco)
    c.font, c.number_format, c.border, c.fill = AZUL, RS, BORDA, F_INPUT
    m = ps.cell(row=r, column=3, value=mix)
    m.font, m.number_format, m.border, m.fill = AZUL, PCT, BORDA, F_INPUT
ps.cell(row=22, column=1, value="Soma do mix (precisa dar 100%)").font = NEGRITO
c = ps.cell(row=22, column=3, value="=SUM(C19:C21)")
c.font, c.number_format, c.fill = PRETO, PCT, F_TOTAL
ps.cell(row=24, column=1, value="Ticket médio do mix").font = NEGRITO
c = ps.cell(row=24, column=2, value="=SUMPRODUCT(B19:B21,C19:C21)")
c.font, c.number_format, c.fill, c.border = PRETO, RS2, F_TOTAL, BORDA
ps.cell(row=24, column=5, value="É este o preço usado quando B7 = 0.").font = SUB

# ---------- custo por loja ----------
secao(ps, 26, "CUSTO POR LOJA", ate=5)
prem(27, "Infraestrutura", 8, "R$/mês", "Servidor, banco e armazenamento rateados. A medir no piloto (item P1).")
prem(28, "Suporte", 34, "R$/mês", "1 pessoa de CS para ~175 lojas. A medir no piloto (item N2).")
prem(29, "Cobrança", None, "R$/mês", "Vem do bloco Modelo comercial (linha 14).",
     fmt=RS2, formula=f"={L['cobranca']}")
prem(30, "API / parceria de dados", 0, "R$/mês",
     "Zero enquanto a cota for do plano da loja. Itens T2 e T4 da Descoberta.", destaque=True)
prem(31, "Custo variável total", None, "R$/mês", "Soma das quatro linhas acima.",
     fmt=RS2, chave="cvar", formula="=SUM(B27:B30)")
ps["B31"].fill = F_TOTAL
prem(32, "Margem de contribuição", None, "R$/mês", "Preço por loja menos custo variável.",
     fmt=RS2, chave="mc", formula=f"={L['ticket']}-B31")
ps["B32"].fill = F_TOTAL
prem(33, "Margem de contribuição %", None, "%", "", fmt=PCT,
     formula=f"=IF({L['ticket']}=0,0,B32/{L['ticket']})")
ps["B33"].fill = F_TOTAL

# ---------- retenção ----------
secao(ps, 35, "RETENÇÃO", ate=5)
prem(36, "Churn mensal", 0.015, "%/mês",
     "Conservador; inclui fechamento de loja. Usado só no LTV — a curva de adoção já é "
     "líquida. No modelo obrigatório o churn real tende a ser menor ainda.",
     fmt=PCT, chave="churn")

# ---------- rede ----------
secao(ps, 38, "REDE E CRONOGRAMA", ate=5)
prem(39, "Lojas na rede hoje", 431, "lojas",
     "Fast Escova 401 + Fast Spa 30 em operação no fim de 2026. Fonte: Times Brasil / "
     "Mapa das Franquias, 09/2026.", fmt=NUM, chave="rede0")
prem(40, "Lojas na rede no mês 36", 600, "lojas",
     "Plano de expansão: +159 lojas em 2026. Fonte: mesma acima.", fmt=NUM, chave="rede36")
prem(41, "Mês em que começam as vendas", 7, "mês",
     "Depois do acordo jurídico e do piloto.", fmt=NUM, chave="inicio")
prem(42, "Atraso na homologação", 0, "meses",
     "Empurra todo o cronograma. Teste 6 para ver o efeito de a franqueadora demorar.",
     fmt=NUM, chave="atraso", destaque=True)

# ---------- painel da rede ----------
secao(ps, 44, "PAINEL DA REDE (FRANQUEADORA)", ate=5)
prem(45, "Mensalidade", 10000, "R$/mês", "Meio da faixa proposta de R$ 8 a 15 mil.",
     chave="rede_mes", destaque=True)
prem(46, "Mês de início", 9, "mês", "Depois da Fase 2, quando o painel da rede existe.",
     fmt=NUM, chave="rede_ini")

# ---------- custo fixo ----------
secao(ps, 48, "CUSTO FIXO POR FASE", ate=5)
prem(49, "Fase 0 — até o mês 2", 5000, "R$/mês", "Jurídico e negociação.", chave="f0")
prem(50, "Fase 1 — meses 3 a 5", 22000, "R$/mês", "Dev sênior parceiro 16k + infra 3k + jurídico 3k.", chave="f1")
prem(51, "Fase 2 — meses 6 a 8", 28000, "R$/mês", "Acrescenta CS meio período.", chave="f2")
prem(52, "Regime — mês 9 em diante", 35000, "R$/mês",
     "Dev 16k + CS 6k + infra e contabilidade 3k + pró-labore 10k. Sem pró-labore: 25.000.",
     chave="freg", destaque=True)

# ---------- investimentos ----------
secao(ps, 54, "INVESTIMENTOS NÃO RECORRENTES", ate=5)
prem(55, "Mês 1", 8000, "R$", "Fechar o acesso, contratos, jurídico inicial.", chave="cap1")
prem(56, "Mês 3", 12000, "R$", "Setup do MVP: infraestrutura, ferramentas, marca.", chave="cap3")
prem(57, "Mês 6", 10000, "R$", "Painel da rede e integração de cobrança.", chave="cap6")

# ---------- impostos ----------
secao(ps, 59, "IMPOSTOS", ate=5)
prem(60, "Impostos sobre a receita", 0.0, "%",
     "ITEM N3 EM ABERTO — no Simples anexo III, algo entre 6% e 16%. Preencher assim que "
     "o contador responder.", fmt=PCT, chave="imposto", destaque=True)
ps["A60"].fill = F_ALERTA

secao(ps, 65, "AUXILIARES — usados pela aba Cenários", ate=5)
prem(66, "Custo variável sem homologação", None, "R$/mês",
     "Infra + suporte + cobrança por loja + API.", fmt=RS2, chave="cvar_sem",
     formula="=B27+B28+C14+B30")
prem(67, "Custo variável com homologação", None, "R$/mês",
     "A cobrança por loja desaparece: é uma fatura só.", fmt=RS2, chave="cvar_com",
     formula="=B27+B28+D14+B30")

ps["A62"] = "Fontes de mercado: Times Brasil, Mapa das Franquias e Portal do Franchising (setembro de 2026)."
ps["A62"].font = SUB
ps["A63"] = ("Cláusulas que sustentam a obrigatoriedade: 7.6, 12.8, 12.11, 2.3 e xlii do contrato "
             "de franquia assinado em 27/01/2026.")
ps["A63"].font = SUB

# ================================================================ MODELO MENSAL
ms = wb.create_sheet("Modelo mensal")
ms.sheet_view.showGridLines = False
ms["A1"] = "Modelo mensal — 36 meses"
ms["A1"].font = TITULO
ms["A2"] = "Todas as colunas são fórmulas que leem a aba Premissas. Custos aparecem como negativos."
ms["A2"].font = SUB

COLS = [
    ("Mês", 7, NUM),
    ("Lojas na rede", 12, NUM),
    ("Lojas pagando", 13, NUM1),
    ("Novas no mês", 12, NUM1),
    ("Receita planos", 15, RS),
    ("Painel da Rede", 14, RS),
    ("Receita total", 15, RS),
    ("Impostos", 13, RS),
    ("Custo variável", 14, RS),
    ("Custo fixo", 13, RS),
    ("Investimento", 13, RS),
    ("Resultado", 15, RS),
    ("Caixa acumulado", 16, RS),
    ("1º mês positivo", 13, NUM),
    ("1º mês caixa > 0", 14, NUM),
]
cab(ms, 4, [c[0] for c in COLS], [c[1] for c in COLS])
ms.freeze_panes = "A5"

P = L
for i in range(36):
    r = 5 + i
    m = i + 1
    ant = r - 1
    ms.cell(row=r, column=1, value=m).number_format = NUM
    ms.cell(row=r, column=1).font = PRETO

    f = {
        2: f"={P['rede0']}+({P['rede36']}-{P['rede0']})*A{r}/36",
        3: (f"=IF(A{r}-{P['atraso']}<{P['inicio']},0,"
            f"{P['teto']}*B{r}/(1+EXP(-{P['k']}*(A{r}-{P['atraso']}-{P['centro']}))))"),
        4: f"=MAX(0,C{r}-C{ant})" if i else f"=C{r}",
        5: f"=C{r}*{P['ticket']}*(1-{P['share']})",
        6: f"=IF(A{r}>={P['rede_ini']}+{P['atraso']},{P['rede_mes']}*(1-{P['share']}),0)",
        7: f"=E{r}+F{r}",
        8: f"=-G{r}*{P['imposto']}",
        9: f"=-(C{r}*{P['cvar']}+D{r}*{P['cac']})",
        10: (f"=-IF(A{r}-{P['atraso']}<=2,{P['f0']},IF(A{r}-{P['atraso']}<=5,{P['f1']},"
             f"IF(A{r}-{P['atraso']}<=8,{P['f2']},{P['freg']})))"),
        11: (f"=-IF(A{r}=1+{P['atraso']},{P['cap1']},IF(A{r}=3+{P['atraso']},{P['cap3']},"
             f"IF(A{r}=6+{P['atraso']},{P['cap6']},0)))"),
        12: f"=G{r}+H{r}+I{r}+J{r}+K{r}",
        13: f"=M{ant}+L{r}" if i else f"=L{r}",
        14: f'=IF(L{r}>0,A{r},9999)',
        15: f'=IF(M{r}>0,A{r},9999)',
    }
    for col, formula in f.items():
        c = ms.cell(row=r, column=col, value=formula)
        c.font = VERDE if col in (2, 3, 5, 6, 8, 9, 10, 11) else PRETO
        c.number_format = COLS[col - 1][2]
        c.border = BORDA
    if m in (12, 24, 36):
        for col in range(1, 16):
            ms.cell(row=r, column=col).fill = F_TOTAL

for col in (14, 15):
    ms.cell(row=4, column=col).font = Font(name=FONTE, size=9, bold=True, color="FFFFFF", italic=True)
ms.cell(row=42, column=14, value="Colunas auxiliares: 9999 = ainda não aconteceu.").font = SUB

# ================================================================ RESUMO
rs = wb.create_sheet("Resumo")
rs.sheet_view.showGridLines = False
for col, w in zip("ABCDEF", (44, 18, 12, 46, 2, 2)):
    rs.column_dimensions[col].width = w
rs["A1"] = "Resumo — os números de decisão"
rs["A1"].font = TITULO
rs["A2"] = "Tudo calculado a partir do Modelo mensal. Nada digitado."
rs["A2"].font = SUB
cab(rs, 4, ["Indicador", "Valor", "Unidade", "Leitura"])

MM = "'Modelo mensal'"


def res(linha, rotulo, formula, unidade, leitura, fmt=RS, destaque=False):
    rs.cell(row=linha, column=1, value=rotulo).font = PRETO
    c = rs.cell(row=linha, column=2, value=formula)
    c.font, c.number_format, c.border = VERDE, fmt, BORDA
    if destaque:
        c.fill, c.font = F_INPUT, Font(name=FONTE, size=10, bold=True, color="008000")
    rs.cell(row=linha, column=3, value=unidade).font = SUB
    t = rs.cell(row=linha, column=4, value=leitura)
    t.font, t.alignment = SUB, Alignment(wrap_text=True, vertical="top")


secao(rs, 6, "CAIXA")
res(7, "Capital necessário", f"=-MIN({MM}!M5:M40)", "R$",
    "O ponto mais fundo do caixa. É o dinheiro que precisa existir antes de começar.", destaque=True)
res(8, "Mês do pico de caixa negativo", f"=INDEX({MM}!A5:A40,MATCH(MIN({MM}!M5:M40),{MM}!M5:M40,0))",
    "mês", "", fmt=NUM)
res(9, "1º mês com resultado positivo", f"=IF(MIN({MM}!N5:N40)=9999,0,MIN({MM}!N5:N40))",
    "mês", "Zero significa que não acontece em 36 meses.", fmt=NUM, destaque=True)
res(10, "Mês em que o caixa volta a zero", f"=IF(MIN({MM}!O5:O40)=9999,0,MIN({MM}!O5:O40))",
    "mês", "Zero significa que não volta em 36 meses.", fmt=NUM, destaque=True)
res(11, "Caixa no mês 36", f"={MM}!M40", "R$", "")

secao(rs, 13, "RESULTADO POR ANO")
rs.cell(row=14, column=1, value="Ano").font = NEGRITO
rs.cell(row=14, column=2, value="Receita (antes de impostos)").font = NEGRITO
rs.cell(row=14, column=3, value="Resultado").font = NEGRITO
rs.cell(row=14, column=4, value="Lojas no fim do ano").font = NEGRITO
for i, (ano, ini, fim) in enumerate([(1, 5, 16), (2, 17, 28), (3, 29, 40)]):
    r = 15 + i
    rs.cell(row=r, column=1, value=f"Ano {ano}").font = PRETO
    for col, formula, fmt in (
            (2, f"=SUM({MM}!G{ini}:G{fim})", RS),
            (3, f"=SUM({MM}!L{ini}:L{fim})", RS),
            (4, f"={MM}!C{fim}", NUM)):
        c = rs.cell(row=r, column=col, value=formula)
        c.font, c.number_format, c.border = VERDE, fmt, BORDA

secao(rs, 19, "PONTO DE EQUILÍBRIO")
res(20, "Lojas necessárias — só os planos", f"=IF({L['mc']}=0,0,{L['freg']}/{L['mc']})",
    "lojas", "Custo fixo em regime dividido pela margem de contribuição.", fmt=NUM1, destaque=True)
res(21, "Lojas necessárias — com o Painel da Rede",
    f"=IF({L['mc']}=0,0,MAX(0,({L['freg']}-{L['rede_mes']})/{L['mc']}))",
    "lojas", "", fmt=NUM1, destaque=True)
res(22, "% da rede de hoje — só os planos", f"=IF({L['rede0']}=0,0,B20/{L['rede0']})", "%", "", fmt=PCT)
res(23, "% da rede de hoje — com o Painel", f"=IF({L['rede0']}=0,0,B21/{L['rede0']})", "%", "", fmt=PCT)

secao(rs, 25, "ECONOMIA UNITÁRIA")
res(26, "Ticket médio", f"={L['ticket']}", "R$/mês", "", fmt=RS2)
res(27, "Custo variável por loja", f"={L['cvar']}", "R$/mês", "", fmt=RS2)
res(28, "Margem de contribuição", f"={L['mc']}", "R$/mês", "", fmt=RS2)
res(29, "Margem de contribuição %", f"={L['mc']}/{L['ticket']}", "%", "", fmt=PCT)
res(30, "Payback do CAC", f"=IF({L['mc']}=0,0,{L['cac']}/{L['mc']})", "meses",
    "Quantos meses uma loja leva para devolver o custo de tê-la conquistado.", fmt=NUM1)
res(31, "LTV", f"=IF({L['churn']}=0,0,{L['mc']}/{L['churn']})", "R$",
    "Margem de contribuição dividida pelo churn mensal.")
res(32, "LTV / CAC", f"=IF({L['cac']}=0,0,B31/{L['cac']})", "x",
    "Acima de 3x já é saudável. Um número muito alto aqui não é sorte: diz que o risco "
    "deste negócio não está em conquistar cliente, está no canal.", fmt='0.0"x"')

rs["A34"] = "Este resumo está antes dos impostos se a alíquota em Premissas estiver zerada (item N3)."
rs["A34"].font = Font(name=FONTE, size=9, italic=True, color="8A5210")

# ---- gráficos
g1 = LineChart()
g1.title = "Caixa acumulado (R$)"
g1.style = 2
g1.height, g1.width = 8.5, 18
g1.y_axis.title = "R$"
g1.x_axis.title = "Mês"
g1.add_data(Reference(ms, min_col=13, min_row=4, max_row=40), titles_from_data=True)
g1.set_categories(Reference(ms, min_col=1, min_row=5, max_row=40))
g1.series[0].graphicalProperties.line.width = 22000
rs.add_chart(g1, "F4")

g2 = LineChart()
g2.title = "Lojas pagando"
g2.style = 2
g2.height, g2.width = 8.5, 18
g2.y_axis.title = "Lojas"
g2.x_axis.title = "Mês"
g2.add_data(Reference(ms, min_col=3, min_row=4, max_row=40), titles_from_data=True)
g2.set_categories(Reference(ms, min_col=1, min_row=5, max_row=40))
g2.series[0].graphicalProperties.line.width = 22000
rs.add_chart(g2, "F22")

# ================================================================ CENÁRIOS
cs = wb.create_sheet("Cenários")
cs.sheet_view.showGridLines = False
cs["A1"] = "Cenários"
cs["A1"].font = TITULO
cs["A2"] = ("Cada cenário recalcula os 36 meses com suas próprias premissas. "
            "Os valores em branco herdam a aba Premissas.")
cs["A2"].font = SUB
cs.column_dimensions["A"].width = 38

LINHA_MOD = CD.LINHA          # parâmetro -> linha do bloco MODELO COMERCIAL
COL_QUAL = {"SEM": "C", "COM": "D"}
GLOBAL = {"atraso": L["atraso"], "rede": L["rede_mes"], "fixo": L["freg"]}
CVAR_REF = {"SEM": L["cvar_sem"], "COM": L["cvar_com"]}

PARAM_ROT = [("Preço por loja", RS2), ("Teto de adoção", PCT), ("Atraso (meses)", NUM),
             ("Participação franqueadora", PCT), ("Painel da Rede", RS),
             ("Custo fixo em regime", RS), ("CAC por loja", RS),
             ("Mês central", NUM1), ("Custo variável", RS2), ("Inclinação", "0.00")]
NP = len(PARAM_ROT)
CEN = CD.CENARIOS

secao(cs, 4, "PREMISSAS DE CADA CENÁRIO", ate=NP + 1)
cab(cs, 5, ["Cenário"] + [r[0] for r in PARAM_ROT],
    [46, 13, 12, 11, 14, 13, 15, 12, 11, 13, 11])


def celula_param(c, nome_par):
    """Link para as Premissas quando o cenário não sobrescreve; número quando sobrescreve."""
    base = CD._base(c["qual"])
    valor, padrao = c[nome_par], base[nome_par]
    if valor != padrao:
        return valor, AZUL
    if nome_par == "cvar":
        return f"={CVAR_REF[c['qual']]}", VERDE
    if nome_par in GLOBAL:
        return f"={GLOBAL[nome_par]}", VERDE
    return f"=Premissas!${COL_QUAL[c['qual']]}${LINHA_MOD[nome_par]}", VERDE


for i, c in enumerate(CEN):
    r = 6 + i
    principal = i < 2
    n = cs.cell(row=r, column=1, value=c["nome"])
    n.font = NEGRITO if principal else PRETO
    for j, nome_par in enumerate(CD.PARAMS):
        val, fonte = celula_param(c, nome_par)
        cel = cs.cell(row=r, column=2 + j, value=val)
        cel.font, cel.number_format, cel.border = fonte, PARAM_ROT[j][1], BORDA
    if principal:
        for col in range(1, NP + 2):
            cs.cell(row=r, column=col).fill = F_TOTAL if i == 0 else F_ALERTA

LIN_RES = 21
CAB_GRADE = 40
GR0 = 42
COL0 = 3
LARG = 7

secao(cs, CAB_GRADE - 1, "GRADE DE CÁLCULO — 36 meses por cenário (pode ocultar estas linhas)", ate=90)
cs.cell(row=CAB_GRADE, column=1, value="Mês").font = NEGRITO
for i, c in enumerate(CEN):
    base = COL0 + i * LARG
    t = cs.cell(row=CAB_GRADE, column=base, value=c["nome"])
    t.font = Font(name=FONTE, size=8, bold=True, color="1F4C88")
    for j, h in enumerate(["", "receita", "custos", "result.", "caixa", "aux+", "auxcx"]):
        if h:
            x = cs.cell(row=CAB_GRADE, column=base + j, value=h)
            x.font = Font(name=FONTE, size=8, color="6A675E")

for i in range(len(CEN)):
    pr = 6 + i
    base = COL0 + i * LARG
    cl, cr, cc = (get_column_letter(base + k) for k in (0, 1, 2))
    cres, ccx, ca1, ca2 = (get_column_letter(base + k) for k in (3, 4, 5, 6))
    tic, tet, atr, sha = f"$B${pr}", f"$C${pr}", f"$D${pr}", f"$E${pr}"
    red, fix, cac, cen, cva, inc = (f"$F${pr}", f"$G${pr}", f"$H${pr}",
                                    f"$I${pr}", f"$J${pr}", f"$K${pr}")
    for k in range(36):
        r = GR0 + k
        ant = r - 1
        if i == 0:
            cs.cell(row=r, column=1, value=k + 1).font = PRETO
        rede_lojas = f"({L['rede0']}+({L['rede36']}-{L['rede0']})*$A{r}/36)"
        cs[f"{cl}{r}"] = (f"=IF($A{r}-{atr}<{L['inicio']},0,{tet}*{rede_lojas}"
                          f"/(1+EXP(-{inc}*($A{r}-{atr}-{cen}))))")
        cs[f"{cr}{r}"] = (f"=({cl}{r}*{tic}+IF($A{r}>={L['rede_ini']}+{atr},{red},0))"
                          f"*(1-{sha})*(1-{L['imposto']})")
        novas = f"MAX(0,{cl}{r}-{cl}{ant})" if k else f"{cl}{r}"
        cs[f"{cc}{r}"] = (
            f"=-({cl}{r}*{cva}+{novas}*{cac}"
            f"+IF($A{r}-{atr}<=2,{L['f0']},IF($A{r}-{atr}<=5,{L['f1']},"
            f"IF($A{r}-{atr}<=8,{L['f2']},{fix})))"
            f"+IF($A{r}=1+{atr},{L['cap1']},IF($A{r}=3+{atr},{L['cap3']},"
            f"IF($A{r}=6+{atr},{L['cap6']},0))))")
        cs[f"{cres}{r}"] = f"={cr}{r}+{cc}{r}"
        cs[f"{ccx}{r}"] = f"={ccx}{ant}+{cres}{r}" if k else f"={cres}{r}"
        cs[f"{ca1}{r}"] = f"=IF({cres}{r}>0,$A{r},9999)"
        cs[f"{ca2}{r}"] = f"=IF({ccx}{r}>0,$A{r},9999)"
        for col, fmt in ((cl, NUM1), (cr, RS), (cc, RS), (cres, RS), (ccx, RS),
                         (ca1, NUM), (ca2, NUM)):
            cel = cs[f"{col}{r}"]
            cel.number_format, cel.font = fmt, Font(name=FONTE, size=8)

secao(cs, LIN_RES - 2, "RESULTADO DE CADA CENÁRIO", ate=7)
cab(cs, LIN_RES - 1, ["Cenário", "1º mês positivo", "Caixa volta a zero", "Capital necessário",
                      "Receita ano 3", "Resultado ano 3", "Lojas no mês 36"],
    [46, 15, 17, 17, 16, 16, 15])
for i, c in enumerate(CEN):
    r = LIN_RES + i
    base = COL0 + i * LARG
    cl = get_column_letter(base)
    cr = get_column_letter(base + 1)
    cres = get_column_letter(base + 3)
    ccx = get_column_letter(base + 4)
    ca1 = get_column_letter(base + 5)
    ca2 = get_column_letter(base + 6)
    ini_g, fim_g = GR0, GR0 + 35
    y3i, y3f = GR0 + 24, GR0 + 35
    n = cs.cell(row=r, column=1, value=c["nome"])
    n.font = NEGRITO if i < 2 else PRETO
    for col, formula, fmt in [
            (2, f'=IF(MIN({ca1}{ini_g}:{ca1}{fim_g})=9999,0,MIN({ca1}{ini_g}:{ca1}{fim_g}))', NUM),
            (3, f'=IF(MIN({ca2}{ini_g}:{ca2}{fim_g})=9999,0,MIN({ca2}{ini_g}:{ca2}{fim_g}))', NUM),
            (4, f"=-MIN({ccx}{ini_g}:{ccx}{fim_g})", RS),
            (5, f"=SUM({cr}{y3i}:{cr}{y3f})", RS),
            (6, f"=SUM({cres}{y3i}:{cres}{y3f})", RS),
            (7, f"={cl}{fim_g}", NUM)]:
        cel = cs.cell(row=r, column=col, value=formula)
        cel.font, cel.number_format, cel.border = PRETO, fmt, BORDA
    if i < 2:
        for col in range(1, 8):
            cs.cell(row=r, column=col).fill = F_TOTAL if i == 0 else F_ALERTA

nota = LIN_RES + len(CEN) + 1
cs[f"A{nota}"] = ("Zero em \"1º mês positivo\" ou \"caixa volta a zero\" significa que não "
                  "acontece dentro dos 36 meses. A receita já está líquida de participação e "
                  "de impostos.")
cs[f"A{nota}"].font = SUB
cs[f"A{nota + 2}"] = (
    "AS DUAS LINHAS EM DESTAQUE SÃO A DECISÃO. Sem homologação: você vende loja a loja, "
    "a R$ 319, e chega a 65% da rede. Com homologação: a franqueadora torna o produto "
    "obrigatório como já fez com Trinks e Sults, cobra das lojas e repassa consolidado — "
    "adesão de 95%, preço único de R$ 299, CAC quase nulo, e 25% da receita fica com ela. "
    "Todas as outras linhas são sensibilidades em torno dessas duas.")
cs[f"A{nota + 2}"].font = Font(name=FONTE, size=9, italic=True, color="8A5210")
cs[f"A{nota + 2}"].alignment = Alignment(wrap_text=True, vertical="top")
cs.row_dimensions[nota + 2].height = 58

# ================================================================ DESCOBERTA
ds = wb.create_sheet("Descoberta")
ds.sheet_view.showGridLines = False
ds["A1"] = "Plano de descoberta — 34 itens"
ds["A1"].font = TITULO
ds["A2"] = "Marque o status e anote a resposta. Os seis bloqueantes vêm primeiro."
ds["A2"].font = SUB
cab(ds, 4, ["Código", "Categoria", "Prioridade", "Onda", "Pergunta", "O que muda",
            "Quem responde", "Status", "Resposta / anotação", "Data"],
    [9, 15, 13, 8, 62, 58, 24, 14, 44, 12])
ds.freeze_panes = "A5"

ITENS = [
    ("J1", "Jurídico", "Bloqueante", 1, "A cláusula 13.13 alcança um software que eu escrevi? Cessão universal e gratuita é exigível ou abusiva num contrato de adesão?", "Tudo. Se alcança, o único caminho é negociar.", "Advogado de franquias"),
    ("J2", "Jurídico", "Bloqueante", 1, "A Lei de Software (9.609/98) muda algo, sendo o autor pessoa física fora de vínculo empregatício?", "Define a força do argumento de titularidade.", "Advogado de franquias"),
    ("J3", "Jurídico", "Bloqueante", 1, "Qual o risco das três exposições atuais — painel público, sync do HubSpot, campanhas — e em que ordem corrigir?", "Define o que fazer nesta semana.", "Advogado de franquias"),
    ("T1", "Trinks", "Bloqueante", 1, "Existe autorização para uso comercial da API? Qual o processo para o contrato específico que os Termos exigem?", "Se não existe caminho, não há produto sobre a API.", "Comercial Trinks"),
    ("T2", "Trinks", "Bloqueante", 1, "A cota de 10.000 requisições/mês é por estabelecimento ou por conta?", "Se for por conta, o custo unitário muda e o modelo é refeito.", "Suporte técnico Trinks"),
    ("T3", "Trinks", "Bloqueante", 1, "Existe programa formal de parceiro ou integrador? Contrato-tipo, requisitos, prazo?", "Define o prazo da Onda 1 e se há atalho.", "Parcerias Trinks"),
    ("J4", "Jurídico", "Estrutural", 2, "Como demonstrar o produto sem entregar o ativo? Existe NDA ou memorando que preserve minha posição?", "Define se a reunião da semana 4 pode acontecer.", "Advogado de franquias"),
    ("J5", "Jurídico", "Estrutural", 2, "Qual estrutura usar: PJ separada, sociedade com a franqueadora, ou licenciamento?", "Define qual das três estruturas é viável.", "Advogado de franquias"),
    ("J6", "Jurídico", "Estrutural", 2, "Sendo franqueado e fornecedor homologado ao mesmo tempo, há conflito a tratar no contrato?", "Define cláusulas do contrato de homologação.", "Advogado de franquias"),
    ("J7", "Jurídico", "Estrutural", 2, "Um produto genérico feito do zero, fora do horário e sem material dos MANUAIS, escapa da 13.13? Que provas de segregação preciso desde já?", "Define se o plano B existe — e as provas começam antes.", "Advogado de franquias"),
    ("T4", "Trinks", "Estrutural", 2, "A parceria envolve taxa, participação na receita, ou é gratuita?", "Entra direto no custo variável por loja.", "Comercial Trinks"),
    ("T5", "Trinks", "Estrutural", 2, "A API tem endpoints incrementais (updated_since, delta, webhooks) ou só paginação completa?", "Define o custo da Fase 3 e a economia de 70% de requisições.", "Documentação e suporte Trinks"),
    ("T7", "Trinks", "Estrutural", 2, "A Trinks tem, ou planeja, produto próprio de BI ou gestão financeira?", "Se sim, o jogo é parceria e o timing fica urgente.", "Comercial Trinks"),
    ("F1", "Franqueadora", "Estrutural", 2, "Existe projeto interno de BI, dados ou painel da rede em andamento?", "Se existe, o jogo é parceria ou venda — não licenciamento.", "Diretoria FE Franchising"),
    ("F2", "Franqueadora", "Estrutural", 2, "Quem decide a homologação de um fornecedor? Processo e prazo típico?", "Define o cronograma real da etapa de homologação.", "Operações FE Franchising"),
    ("F3", "Franqueadora", "Estrutural", 2, "Quais os critérios de homologação — certificações, seguro, capital, contrato-tipo?", "Pode exigir estrutura societária e capital antes do previsto.", "Operações FE Franchising"),
    ("F4", "Franqueadora", "Estrutural", 2, "Existe contrato-tipo de Fornecedor Homologado? Exclusividade, participação, prazo, rescisão?", "Entra direto no modelo — ver cenários de participação.", "Jurídico FE Franchising"),
    ("F5", "Franqueadora", "Estrutural", 2, "Qual o escopo do Sults hoje? Ele já faz, ou vai fazer, parte do que o FAST Insights faz?", "Se houver sobreposição, integrar em vez de competir.", "Operações FE Franchising"),
    ("F8", "Franqueadora", "Estrutural", 2, "Qual o apetite: comprar o ativo, licenciar, entrar como sócia, ou construir?", "Define qual das três estruturas propor primeiro.", "Diretoria FE Franchising"),
    ("M1", "Mercado", "Estrutural", 2, "Qual a primeira métrica que o franqueado olha de manhã? Que pergunta ele não consegue responder hoje?", "Define o que vai no plano Essencial — e o que corta.", "8 a 10 franqueados"),
    ("M2", "Mercado", "Estrutural", 2, "Quanto pagaria? Teste de preço com R$ 199, R$ 349 e R$ 549.", "Valida ou derruba o ticket que sustenta todo o modelo.", "8 a 10 franqueados"),
    ("F6", "Franqueadora", "Refinamento", 3, "A franqueadora coleta dados das lojas hoje? Como e para quê?", "Dimensiona o valor do Painel da Rede e o preço que suporta.", "Operações FE Franchising"),
    ("F7", "Franqueadora", "Refinamento", 3, "O Conselho de Franqueados pode pautar isso? Quando é a próxima reunião?", "É o canal mais barato de validação com a rede.", "Conselho de Franqueados"),
    ("T6", "Trinks", "Refinamento", 3, "Quantos salões no Brasil usam Trinks? Existe base fora da rede FAST?", "Dimensiona o TAM e a viabilidade do plano B.", "Comercial Trinks"),
    ("M3", "Mercado", "Refinamento", 3, "Que ferramentas o franqueado usa além de Trinks e Sults, e quanto gasta?", "Mostra o orçamento disponível e a disposição real de pagar.", "8 a 10 franqueados"),
    ("M4", "Mercado", "Refinamento", 3, "Quantas lojas da rede são multi-unidade, com o mesmo dono?", "Muda o produto e o preço (desconto por grupo).", "Franqueadora ou colegas"),
    ("P2", "Produto", "Estrutural", 3, "Quantas requisições por loja/mês em regime, com ingestão incremental?", "Se estourar a cota, não escala sem contrato especial.", "Você, medindo"),
    ("P3", "Produto", "Estrutural", 3, "Quais adquirentes as lojas usam? Stone é universal? Têm API?", "Define se a conciliação funciona fora da Limão.", "Você + franqueados"),
    ("P4", "Produto", "Estrutural", 3, "Quanto do financeiro dá para automatizar sem Excel? Existe DRE padronizado da rede?", "Se houver modelo da rede, a Fase 2 encolhe muito.", "Você + franqueadora"),
    ("P1", "Produto", "Refinamento", 3, "Custo real de infraestrutura por loja, medido com 5 lojas rodando.", "Modelado em R$ 8. Se for R$ 30, a margem cai para 78%.", "Você, medindo"),
    ("P5", "Produto", "Refinamento", 3, "Qual BSP de WhatsApp usar, com que custo de setup e por conversa?", "Define a viabilidade do plano Crescimento.", "Você, cotando"),
    ("N3", "Números", "Estrutural", 3, "Regime tributário da PJ de software: Simples, Lucro Presumido, alíquota de ISS?", "Pode consumir 6% a 16% da receita — hoje zerado no modelo.", "Contador"),
    ("N1", "Números", "Refinamento", 3, "Preço real da conversa de marketing no WhatsApp, tabela Meta Brasil vigente.", "É repasse, então não afeta margem — mas afeta a proposta.", "Meta / BSP"),
    ("N2", "Números", "Refinamento", 3, "Custo real de suporte por loja, medido no piloto.", "Modelado em R$ 34. É o maior componente do custo variável.", "Você, medindo"),
]
assert len(ITENS) == 34, len(ITENS)

CORES_PRIO = {"Bloqueante": "F7E4E0", "Estrutural": "F7F0E4", "Refinamento": "F1F0EC"}
for i, (cod, cat, prio, onda, perg, muda, quem) in enumerate(ITENS):
    r = 5 + i
    for col, v in enumerate([cod, cat, prio, onda, perg, muda, quem, "Não iniciado", "", ""], start=1):
        c = ds.cell(row=r, column=col, value=v)
        c.font = NEGRITO if col == 1 else PRETO
        c.border = BORDA
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if col == 3:
            c.fill = PatternFill("solid", fgColor=CORES_PRIO[prio])
        if col in (8, 9, 10):
            c.fill = F_INPUT
            c.font = AZUL
        if col == 10:
            c.number_format = "DD/MM/YYYY"
    ds.row_dimensions[r].height = 30

dv = DataValidation(type="list", formula1='"Não iniciado,Em andamento,Respondido,Descartado"',
                    allow_blank=True, showDropDown=False)
ds.add_data_validation(dv)
dv.add(f"H5:H{4 + len(ITENS)}")

r = 6 + len(ITENS)
ds.cell(row=r, column=1, value="Progresso").font = NEGRITO
ds.cell(row=r, column=5, value=f'=COUNTIF(H5:H{4+len(ITENS)},"Respondido")&" de {len(ITENS)} respondidos"').font = PRETO
ds.cell(row=r + 1, column=5,
        value=f'=COUNTIFS(C5:C{4+len(ITENS)},"Bloqueante",H5:H{4+len(ITENS)},"Respondido")'
              f'&" de 6 bloqueantes respondidos"').font = PRETO
ds.cell(row=r + 3, column=1,
        value="Seis itens bloqueantes. Um advogado e três telefonemas — é todo o custo de "
              "descobrir se este projeto existe.").font = SUB

# ================================================================
wb.save(SAIDA)
print("gerado:", SAIDA, SAIDA.stat().st_size, "bytes")
