# -*- coding: utf-8 -*-
"""Definição única dos cenários — usada para GERAR a planilha e para CONFERI-LA.

Os parâmetros são compartilhados de propósito; o que se cruza é a implementação:
o Excel calcula por fórmula, este arquivo calcula em Python. Se os dois baterem,
as fórmulas da planilha estão certas.
"""
import math

# Globais (espelham a aba Premissas)
REDE0, REDE36 = 431.0, 600.0
INICIO = 7
REDE_MES, REDE_INI = 10000.0, 9
F0, F1, F2, FREG = 5000.0, 22000.0, 28000.0, 35000.0
CAPEX = {1: 8000.0, 3: 12000.0, 6: 10000.0}
IMPOSTO = 0.0

# Os dois modelos comerciais, lado a lado (colunas C e D da aba Premissas)
SEM = dict(ticket=319.0, teto=0.65, centro=16.0, k=0.32, cac=400.0, cobranca=3.0, share=0.00)
COM = dict(ticket=299.0, teto=0.95, centro=12.0, k=0.45, cac=50.0, cobranca=0.0, share=0.25)
INFRA, SUPORTE, API = 8.0, 34.0, 0.0
CVAR_SEM = INFRA + SUPORTE + SEM["cobranca"] + API      # 45
CVAR_COM = INFRA + SUPORTE + COM["cobranca"] + API      # 42

# Referências para as fórmulas do Excel: "C" = coluna Voluntário, "D" = Obrigatório.
# Linhas do bloco MODELO COMERCIAL na aba Premissas.
LINHA = {"ticket": 9, "teto": 10, "centro": 11, "k": 12, "cac": 13, "share": 15}


def _base(qual):
    d = dict(SEM if qual == "SEM" else COM)
    d["cvar"] = CVAR_SEM if qual == "SEM" else CVAR_COM
    d["atraso"] = 0
    d["rede"] = REDE_MES
    d["fixo"] = FREG
    return d


def cenario(nome, qual, **over):
    d = _base(qual)
    d.update(over)
    d["nome"], d["qual"] = nome, qual
    return d


CENARIOS = [
    cenario("1 · SEM homologação — venda loja a loja", "SEM"),
    cenario("2 · COM homologação — obrigatório, participação 25%", "COM"),
    cenario("Com homologação · sem participação", "COM", share=0.00),
    cenario("Com homologação · participação 20%", "COM", share=0.20),
    cenario("Com homologação · participação 30%", "COM", share=0.30),
    cenario("Com homologação · participação 40%", "COM", share=0.40),
    cenario("Com homologação · preço R$ 249 · particip. 25%", "COM", ticket=249.0),
    cenario("Com homologação · atraso de 6 meses", "COM", atraso=6),
    cenario("Com homologação · enxuta, sem pró-labore", "COM", fixo=25000.0),
    cenario("Sem homologação · adoção metade da rede", "SEM", teto=0.325),
    cenario("Sem homologação · participação de 35%", "SEM", share=0.35),
    cenario("Sem homologação · pior caso combinado", "SEM", teto=0.325, atraso=6, share=0.35),
]

# Ordem dos parâmetros nas colunas da aba Cenários
PARAMS = ["ticket", "teto", "atraso", "share", "rede", "fixo", "cac", "centro", "cvar", "k"]


def rodar(c, meses=36):
    """Roda um cenário e devolve os indicadores — o par de checagem do Excel."""
    at, teto, centro, k = c["atraso"], c["teto"], c["centro"], c["k"]

    def fixo(m):
        m -= at
        return F0 if m <= 2 else F1 if m <= 5 else F2 if m <= 8 else c["fixo"]

    def capex(m):
        return CAPEX.get(m - at, 0.0)

    def lojas(m):
        mm = m - at
        if mm < INICIO:
            return 0.0
        rede = REDE0 + (REDE36 - REDE0) * m / meses
        return teto * rede / (1 + math.exp(-k * (mm - centro)))

    caixa = pico = 0.0
    be = cz = None
    anos, recs = [0.0] * 3, [0.0] * 3
    for m in range(1, meses + 1):
        n = lojas(m)
        nov = max(0.0, n - (lojas(m - 1) if m > 1 else 0.0))
        rec = (n * c["ticket"] + (c["rede"] if m >= REDE_INI + at else 0.0)) \
            * (1 - c["share"]) * (1 - IMPOSTO)
        res = rec - (n * c["cvar"] + nov * c["cac"]) - fixo(m) - capex(m)
        caixa += res
        pico = min(pico, caixa)
        if be is None and res > 0:
            be = m
        if cz is None and be and caixa > 0:
            cz = m
        anos[(m - 1) // 12] += res
        recs[(m - 1) // 12] += rec
    return dict(be=be or 0, cz=cz or 0, capital=-pico, rec3=recs[2], res3=anos[2],
                lojas36=lojas(meses), anos=anos, recs=recs)


if __name__ == "__main__":
    def br(v):
        return f"{v:,.0f}".replace(",", ".")
    print(f"{'cenário':50} {'1º+':>4} {'cx0':>4} {'capital':>10} "
          f"{'rec ano3':>11} {'res ano3':>11} {'lojas':>6}")
    for c in CENARIOS:
        r = rodar(c)
        print(f"{c['nome']:50} {r['be']:>4} {r['cz']:>4} {br(r['capital']):>10} "
              f"{br(r['rec3']):>11} {br(r['res3']):>11} {r['lojas36']:>6.0f}")
