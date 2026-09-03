#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Detecta parada de entrega na conta de anúncios.

Existe por causa de 27 a 31/08/2026: a conta parou de entregar por 4 dias com
todas as campanhas ENABLED, e ninguém percebeu. A descoberta veio por acaso,
cinco dias depois, num refresh de rotina. Custou ~R$ 480 de entrega, ~77
conversas e o reaprendizado de 10 campanhas.

A rotina de mídias já roda 2x/dia e já passa por cima do número que denunciaria
isso — ela só não olhava. Este script olha.

Lê a série diária de data/midias_sociais.json e compara o último dia COMPLETO
com a mediana dos dias que entregaram antes dele. O dia corrente é ignorado de
propósito: às 08h da manhã todo dia parece uma parada.

Saída:
  exit 0 = entrega normal
  exit 1 = alerta (imprime a mensagem pronta para notificação)
  exit 2 = não deu para avaliar (dado velho ou série curta)

Uso:  python scripts/alerta_entrega.py [caminho.json]
"""
import json
import pathlib
import statistics
import sys
from datetime import date, datetime, timedelta

REPO = pathlib.Path(__file__).resolve().parent.parent

# Abaixo disto o dia é considerado colapso, não oscilação. A série de agosto
# variou entre R$ 76 e R$ 130 (mediana ~R$ 97), ou seja ±35% em dia normal;
# 40% da mediana fica fora dessa faixa com folga.
PISO_PCT = 0.40
JANELA_BASE = 14        # dias com entrega usados para a mediana
IDADE_MAX_H = 30        # painel mais velho que isto não serve para julgar hoje


def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "~").replace(".", ",").replace("~", ".")


def dm(d):
    return d.strftime("%d/%m")


def avaliar(caminho):
    """Devolve (nivel, titulo, detalhe). nivel: 'ok' | 'alerta' | 'critico' | 'indef'."""
    d = json.loads(pathlib.Path(caminho).read_text(encoding="utf-8"))
    serie = d.get("meta_ads", {}).get("serie_diaria_30d") or []
    if len(serie) < 8:
        return "indef", "Série curta demais", f"{len(serie)} pontos — não dá para avaliar."

    ger = d.get("gerado_em")
    try:
        gerado = datetime.fromisoformat(ger)
        idade_h = (datetime.now(gerado.tzinfo) - gerado).total_seconds() / 3600
    except Exception:
        return "indef", "gerado_em inválido", f"Não consegui ler {ger!r}."
    if idade_h > IDADE_MAX_H:
        return ("indef", "Painel congelado",
                f"O painel tem {idade_h:.0f}h. Não dá para afirmar nada sobre a entrega "
                f"de hoje com dado desse tempo — o problema pode ser a coleta, não a conta.")

    hoje = gerado.date()
    pontos = [(date.fromisoformat(p["data"]), p.get("gasto") or 0.0) for p in serie]
    pontos.sort()

    # O dia corrente está em curso: às 08h ele sempre pareceria uma parada.
    completos = [(dt, g) for dt, g in pontos if dt < hoje]
    if not completos:
        return "indef", "Sem dia completo", "A série não tem nenhum dia anterior a hoje."

    ultimo_dt, ultimo_g = completos[-1]
    if (hoje - ultimo_dt).days > 2:
        return ("indef", "Série desatualizada",
                f"O último dia completo da série é {dm(ultimo_dt)}, e hoje é {dm(hoje)}.")

    anteriores = completos[:-1][-JANELA_BASE * 2:]
    entregaram = [g for _, g in anteriores if g > 0]
    if len(entregaram) < 5:
        return ("indef", "Base insuficiente",
                f"Só {len(entregaram)} dias com entrega antes de {dm(ultimo_dt)}.")
    mediana = statistics.median(entregaram[-JANELA_BASE:])

    # Quantos dias completos seguidos terminando no último estão zerados
    zerados = []
    for dt, g in reversed(completos):
        if g > 0:
            break
        zerados.append(dt)
    zerados.reverse()

    if len(zerados) >= 2:
        perda = mediana * len(zerados)
        return ("critico", f"Conta parada há {len(zerados)} dias",
                f"{dm(zerados[0])} a {dm(zerados[-1])} sem entrega nenhuma. No ritmo "
                f"normal ({brl(mediana)}/dia) isso já são {brl(perda)} que não "
                f"entraram. Conferir limite de gastos da conta e meio de pagamento AGORA.")
    if len(zerados) == 1:
        return ("critico", f"Zero entrega em {dm(ultimo_dt)}",
                f"A conta não gastou nada ontem, contra {brl(mediana)}/dia de mediana. "
                f"Se repetir hoje, são dois dias. Conferir limite de gastos e pagamento.")
    if ultimo_g < mediana * PISO_PCT:
        queda = (1 - ultimo_g / mediana) * 100
        return ("alerta", f"Entrega despencou em {dm(ultimo_dt)}",
                f"{brl(ultimo_g)} contra mediana de {brl(mediana)}/dia — queda de "
                f"{queda:.0f}%. Foi assim que começou a parada de 27/08, que virou "
                f"4 dias zerados. Vale olhar hoje, não semana que vem.")

    return ("ok", f"Entrega normal em {dm(ultimo_dt)}",
            f"{brl(ultimo_g)} contra mediana de {brl(mediana)}/dia.")


def main() -> int:
    caminho = sys.argv[1] if len(sys.argv) > 1 else REPO / "data" / "midias_sociais.json"
    try:
        nivel, titulo, detalhe = avaliar(caminho)
    except Exception as e:
        print(f"⚠️  Não consegui avaliar a entrega: {e}")
        return 2

    icone = {"critico": "🛑", "alerta": "⚠️", "ok": "✅", "indef": "❔"}[nivel]
    print(f"{icone} {titulo}")
    print(f"   {detalhe}")
    return {"critico": 1, "alerta": 1, "ok": 0, "indef": 2}[nivel]


if __name__ == "__main__":
    sys.exit(main())
