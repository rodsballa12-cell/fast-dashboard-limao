#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modelo financeiro do FAST Insights — 36 meses, com cenários.

Existe para que as premissas do business plan (docs/produtizacao/06) sejam
reprodutíveis: mude um número no bloco PREMISSAS e rode de novo em vez de
recalcular tabela à mão.

    python scripts/modelo_negocio.py            # projeção mês a mês + cenários
    python scripts/modelo_negocio.py --mensal   # só a tabela mensal

Toda saída é markdown, pronta para colar no documento.
"""
from __future__ import annotations

import math
import sys

# ----------------------------- PREMISSAS -----------------------------
# Mix 40% Essencial (199) + 45% Gestão (349) + 15% Crescimento (549).
TICKET = 319.0          # receita média por loja/mês
CVAR = 45.0             # infra 8 + suporte 34 + cobrança 3
CAC = 400.0             # onboarding + rateio de eventos da rede
REDE_MENSAL = 10000.0   # Painel da Rede, a partir do mês 9
TETO_ADOCAO = 0.65      # fração da rede que chega a pagar
REDE_INI, REDE_FIM = 431, 600   # lojas da rede no mês 0 e no mês 36
MESES = 36

# Custo fixo por fase (mês -> R$/mês). Ver seção 10 do business plan.
FIXO_FASES = [(2, 5000.0), (5, 22000.0), (8, 28000.0)]
FIXO_REGIME = 35000.0

# Investimentos não recorrentes: {mês: valor}
CAPEX = {1: 8000.0, 3: 12000.0, 6: 10000.0}


def _fixo(m: int, regime: float, atraso: int) -> float:
    m -= atraso
    for ate, valor in FIXO_FASES:
        if m <= ate:
            return valor
    return regime


def _capex(m: int, atraso: int) -> float:
    return CAPEX.get(m - atraso, 0.0)


def _rede(m: int) -> float:
    return REDE_INI + (REDE_FIM - REDE_INI) * m / MESES


def _lojas(m: int, teto: float, atraso: int, inicio: int = 7) -> float:
    """Curva logística de adoção, centrada no mês 16."""
    mm = m - atraso
    if mm < inicio:
        return 0.0
    return teto * _rede(m) / (1 + math.exp(-0.32 * (mm - 16)))


def rodar(ticket=TICKET, cvar=CVAR, cac=CAC, rede=REDE_MENSAL,
          teto=TETO_ADOCAO, atraso=0, share=0.0, fixo_regime=FIXO_REGIME):
    """Devolve (linhas, resumo). `share` = fatia da receita cedida à franqueadora."""
    linhas, caixa, pico = [], 0.0, 0.0
    be = cx_pos = None
    for m in range(1, MESES + 1):
        n = _lojas(m, teto, atraso)
        novas = max(0.0, n - (_lojas(m - 1, teto, atraso) if m > 1 else 0.0))
        rec_lojas = n * ticket
        rec_rede = rede if m >= 9 + atraso else 0.0
        receita = (rec_lojas + rec_rede) * (1 - share)
        custo_var = n * cvar + novas * cac
        fixo, capex = _fixo(m, fixo_regime, atraso), _capex(m, atraso)
        res = receita - custo_var - fixo - capex
        caixa += res
        pico = min(pico, caixa)
        if be is None and res > 0:
            be = m
        if cx_pos is None and be and caixa > 0:
            cx_pos = m
        linhas.append(dict(mes=m, lojas=n, rec_lojas=rec_lojas * (1 - share),
                           rec_rede=rec_rede * (1 - share), receita=receita,
                           custo_var=custo_var, fixo=fixo, capex=capex,
                           res=res, caixa=caixa))
    anos = [(sum(l["receita"] for l in linhas[a:a + 12]),
             sum(l["res"] for l in linhas[a:a + 12])) for a in (0, 12, 24)]
    return linhas, dict(be=be, caixa_zero=cx_pos, capital=-pico, anos=anos,
                        lojas_fim=linhas[-1]["lojas"])


def brl(v: float) -> str:
    return f"{v:,.0f}".replace(",", ".")


def tabela_mensal(linhas):
    print("| Mês | Lojas | Receita lojas | Painel Rede | Receita total | "
          "Custo var. | Custo fixo | Investim. | Resultado | Caixa acum. |")
    print("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for l in linhas:
        print(f"| {l['mes']} | {l['lojas']:,.0f} | {brl(l['rec_lojas'])} | "
              f"{brl(l['rec_rede'])} | {brl(l['receita'])} | {brl(l['custo_var'])} | "
              f"{brl(l['fixo'])} | {brl(l['capex'])} | {brl(l['res'])} | {brl(l['caixa'])} |")


CENARIOS = [
    ("Base", {}),
    ("Adoção metade (33% da rede)", dict(teto=0.325)),
    ("Homologação atrasa 6 meses", dict(atraso=6)),
    ("Preço 20% menor", dict(ticket=255.0)),
    ("Sem o Painel da Rede", dict(rede=0.0)),
    ("Participação de 20% à franqueadora", dict(share=0.20)),
    ("Participação de 35%", dict(share=0.35)),
    ("Participação de 50%", dict(share=0.50)),
    ("Pior caso combinado", dict(teto=0.325, share=0.35, atraso=6)),
    ("Enxuta: sem pró-labore", dict(fixo_regime=25000.0)),
]


def main() -> int:
    linhas, r = rodar()
    if "--mensal" in sys.argv:
        tabela_mensal(linhas)
        return 0

    tabela_mensal(linhas)
    mc = TICKET - CVAR
    print(f"\n**Margem de contribuição por loja:** R$ {mc:,.0f} "
          f"({mc / TICKET:.0%}) · **payback do CAC:** {CAC / mc:.1f} mês")
    for churn in (0.010, 0.015, 0.020):
        print(f"- churn {churn:.1%}/mês → LTV R$ {brl(mc / churn)} · "
              f"LTV/CAC {mc / churn / CAC:.0f}x")

    print("\n| Cenário | 1º mês positivo | Caixa zera | Capital necessário | "
          "Receita ano 3 | Resultado ano 3 |")
    print("|---|---:|---:|---:|---:|---:|")
    for nome, kw in CENARIOS:
        _, s = rodar(**kw)
        be = f"M{s['be']}" if s["be"] else "nunca"
        cz = f"M{s['caixa_zero']}" if s["caixa_zero"] else "não volta"
        print(f"| {nome} | {be} | {cz} | R$ {brl(s['capital'])} | "
              f"R$ {brl(s['anos'][2][0])} | R$ {brl(s['anos'][2][1])} |")

    print("\n> Projeção **antes** dos impostos da empresa de software "
          "(item N3 do plano de descoberta).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
