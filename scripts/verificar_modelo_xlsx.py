# -*- coding: utf-8 -*-
"""Avalia de verdade as fórmulas do .xlsx e confere contra o modelo em Python."""
import re, formulas

xl = formulas.ExcelModel().loads("FAST-Insights-modelo-financeiro.xlsx").finish()
sol = xl.calculate()

C = {}
for k, v in sol.items():
    m = re.match(r"^'\[.*?\](.+?)'!([A-Z]+\d+)$", k)
    if not m:
        continue
    try:
        val = v.value[0, 0]
    except Exception:
        val = getattr(v, "value", v)
    C[(m.group(1).upper(), m.group(2))] = val

ERRO = re.compile(r"#(REF|NAME|VALUE|DIV/0|N/A|NUM|NULL)")
erros = [(a, b, x) for (a, b), x in C.items() if ERRO.search(str(x))]
print(f"CÉLULAS COM ERRO: {len(erros)}")
for a, b, x in erros[:12]:
    print("   ", a, b, "=", x)

def v(aba, cel):
    x = C.get((aba.upper(), cel), "ausente")
    try:
        return float(x)
    except Exception:
        return x

def chk(rot, obtido, esperado, tol=1.0):
    try:
        ok = abs(float(obtido) - esperado) <= tol
    except Exception:
        ok = False
    print(f"  {'OK ' if ok else 'ERRO'} {rot:38} {obtido!s:>16}   esperado {esperado:,.2f}".replace(",", "."))
    return ok

print("\nPREMISSAS E RESUMO")
todos = [
    chk("ticket médio", v("Premissas", "B12"), 319.0, 0.01),
    chk("custo variável", v("Premissas", "B19"), 45.0, 0.01),
    chk("margem de contribuição", v("Premissas", "B20"), 274.0, 0.01),
    chk("caixa no mês 36", v("Modelo mensal", "M40"), 953229, 2),
    chk("capital necessário", v("Resumo", "B7"), 267088, 2),
    chk("mês do pico", v("Resumo", "B8"), 14, 0),
    chk("1º mês positivo", v("Resumo", "B9"), 15, 0),
    chk("mês em que o caixa zera", v("Resumo", "B10"), 23, 0),
    chk("receita ano 1", v("Resumo", "B15"), 112990, 2),
    chk("resultado ano 1", v("Resumo", "C15"), -254871, 2),
    chk("receita ano 2", v("Resumo", "B16"), 968140, 2),
    chk("resultado ano 2", v("Resumo", "C16"), 324852, 2),
    chk("receita ano 3", v("Resumo", "B17"), 1526137, 2),
    chk("resultado ano 3", v("Resumo", "C17"), 883248, 2),
    chk("ponto de equilíbrio (lojas)", v("Resumo", "B20"), 127.74, 0.05),
    chk("ponto de equilíbrio com painel", v("Resumo", "B21"), 91.24, 0.05),
    chk("payback do CAC", v("Resumo", "B30"), 1.46, 0.02),
    chk("LTV / CAC", v("Resumo", "B32"), 45.67, 0.05),
]

ESPERADO = [
    ("Base",                  15, 23, 267088, 1526137,  883248, 389),
    ("Adoção metade",         19, 35, 327402,  823069,  291624, 195),
    ("Atraso 6 meses",        21, 29, 292811, 1417651,  752896, 386),
    ("Preço 20% menor",       17, 27, 302405, 1244028,  601139, 389),
    ("Sem Painel da Rede",    17, 26, 335658, 1406137,  763248, 389),
    ("Participação 20%",      17, 28, 318259, 1220910,  578021, 389),
    ("Participação 35%",      19, 35, 377326,  991989,  349100, 389),
    ("Participação 50%",      23,  0, 474338,  763069,  120180, 389),
    ("Pior caso combinado",   33,  0, 500221,  499736,  -42641, 193),
    ("Enxuta",                13, 21, 214871, 1526137, 1003248, 389),
]
print("\nCENÁRIOS")
for i, (nome, be, cz, cap, r3, res3, lj) in enumerate(ESPERADO):
    r = 20 + i
    got = [v("Cenários", f"{c}{r}") for c in "BCDEFG"]
    esp = [be, cz, cap, r3, res3, lj]
    ok = all(abs(float(g) - e) <= max(2, abs(e) * 0.001) for g, e in zip(got, esp))
    todos.append(ok)
    marca = "OK " if ok else "ERRO"
    fmt = lambda x: f"{float(x):,.0f}".replace(",", ".")
    print(f"  {marca} {nome:22} 1º+ {fmt(got[0]):>3} | caixa0 {fmt(got[1]):>3} | "
          f"capital {fmt(got[2]):>9} | rec3 {fmt(got[3]):>10} | res3 {fmt(got[4]):>9} | lojas {fmt(got[5]):>4}")

print(f"\nRESULTADO: {sum(todos)}/{len(todos)} conferências corretas · {len(erros)} células com erro")
