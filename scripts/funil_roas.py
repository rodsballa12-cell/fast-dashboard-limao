#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monta o ROAS de cada loja a partir do que foi MEDIDO no balcao.

POR QUE ESTE SCRIPT EXISTE (08/10/2026)
O Rodrigo perguntou qual era o ROAS da midia do Spa e a resposta foi: nao
existe. Nao existe de dois jeitos distintos, e os dois sao consertaveis.

1. A conta do Spa nao tem objetivo de venda nem evento de valor — so
   ENGAGEMENT, LINK_CLICKS e AWARENESS. A Meta nao calcula ROAS numa conta
   assim, e nunca vai: um spa de porta de rua nao tem checkout.
2. O bloco `funil_conversao` do Spa ainda dizia "ativa quando a primeira
   campanha rodar + Trinks SPA subir (estabelecimentoId pendente)". A
   campanha rodou em 13/09 e o Trinks do Spa esta no ar desde a abertura.
   O bloco nunca foi religado, entao o painel nao tinha de onde tirar o
   numero — e o Rodrigo ficou semanas sem ver se a verba voltava.

O ROAS desta empresa nao e metrica de plataforma: e a pergunta "como nos
conheceu" feita na recepcao, cruzada com a receita do Trinks. Era assim que
o 4,72x da Escova tinha sido calculado a mao, para agosto. A mao envelhece:
em 08/10 aquele numero ainda era de agosto. Este script faz a mesma conta
todo dia, nas duas lojas.

O QUE ELE NUNCA FAZ
Nao sobrescreve campo escrito por pessoa. `roas_estimado`, `cenarios_roas` e
`atribuicao_medida` sao gravados apenas quando ESTAO AUSENTES — foi assim que
o Spa ganhou o card sem que a leitura curada de agosto da Escova fosse
apagada. O bloco `apuracao_automatica`, sim, e reescrito todo dia: ele e
nosso, carimbado com a hora, e fica ao lado do curado para quem quiser
comparar.

SEMANTICA DO `share_pct` — a parte facil de errar
No bloco curado da Escova, `share_pct` e a fatia de CLIENTES que responderam
aquele canal, nao a fatia de receita (79 de 191 = 41,4%). O index.html conta
com isso: ele multiplica a receita da janela escolhida por esse share. Fatia
por receita daria outro numero e quebraria o card em silencio. Aqui se usa
contagem de cliente, como o original.

Uso:  python scripts/funil_roas.py [--dry-run]
"""
import json
import pathlib
import sys
from datetime import date, datetime, timezone, timedelta

REPO = pathlib.Path(__file__).resolve().parent.parent
BRT = timezone(timedelta(hours=-3))

# Canais que sao Meta paga OU organica — o campo do Trinks nao separa as duas,
# e dizer que separa seria inventar. A ressalva viaja junto com o numero.
META = ("instagram", "facebook")
# "Digital amplo" existe para dar o outro extremo do cenario, igual ao bloco
# curado da Escova fazia.
DIGITAL = META + ("internet", "aplicativo", "outras redes sociais", "whatsapp")

UNIDADES = {
    "escova": ("data/dashboard_data.json", "data/midias_sociais.json"),
    "spa": ("data/spa/dashboard_data.json", "data/spa/midias_sociais.json"),
}


def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "~").replace(".", ",").replace("~", ".")


def ler(rel):
    p = REPO / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def apurar(unidade, dash, mid):
    """Devolve o bloco de apuracao, ou (None, motivo) quando falta dado.

    A data de hoje vem do campo `hoje` do payload, nao do relogio da
    maquina: o container roda em UTC e as 21h de Sao Paulo ja e o dia
    seguinte lá. O PROTOCOLO.md manda derivar a data do dado.
    """
    anual = ((dash or {}).get("abas") or {}).get("anual") or {}
    sc = anual.get("seg_canal") or {}
    top = sc.get("top") or []
    kp = anual.get("kpis") or {}
    receita = kp.get("receita_serv")
    if not top or not receita:
        return None, "sem seg_canal ou sem receita de servico no payload anual"

    pp = ((mid or {}).get("meta_ads") or {}).get("por_periodo") or {}
    gasto = (pp.get("90d") or {}).get("gasto")
    if not gasto:
        return None, "sem gasto de midia na janela 90d"

    respondentes = sum(int(x.get("n_clientes") or 0) for x in top)
    if respondentes == 0:
        return None, "nenhum cliente respondeu de onde veio"

    sem = sc.get("sem_dado") or {}
    receita_respondida = round(sum(float(x.get("receita") or 0) for x in top), 2)

    mix = []
    for x in top:
        n = int(x.get("n_clientes") or 0)
        mix.append({
            "canal": x.get("nome"),
            "n": n,
            "share_pct": round(n / respondentes * 100, 1),
            "receita_medida": round(float(x.get("receita") or 0), 2),
        })

    def share(nomes):
        n = sum(m["n"] for m in mix if (m["canal"] or "").strip().lower() in nomes)
        return n, round(n / respondentes * 100, 2)

    n_meta, pct_meta = share(set(META))
    n_dig, pct_dig = share(set(DIGITAL))
    rec_meta_medida = round(sum(m["receita_medida"] for m in mix
                                if (m["canal"] or "").strip().lower() in set(META)), 2)

    # A JANELA. A pergunta do balcao e feita uma vez, no cadastro, entao
    # `seg_canal` e sempre "desde a abertura". O gasto de midia disponivel no
    # payload vai so ate 90 dias. Enquanto a loja for mais nova que isso as
    # duas janelas coincidem; quando passar, o texto tem que dizer que o ROAS
    # esta dividindo receita de sempre por verba de 90 dias — que e otimista.
    inaug = ((dash or {}).get("unidade_config") or {}).get("data_inauguracao")
    hoje_dado = (dash or {}).get("hoje")
    try:
        hoje_d = date.fromisoformat(str(hoje_dado)[:10])
    except Exception:
        return None, "payload sem campo `hoje` legível — nao chuto a data"
    dias_loja = None
    if inaug:
        try:
            dias_loja = (hoje_d - date.fromisoformat(inaug)).days
        except Exception:
            dias_loja = None
    janela_casa = dias_loja is not None and dias_loja <= 90

    def roas(rec):
        return round(rec / gasto, 2) if gasto else None

    rec_extrap = round(receita * pct_meta / 100, 2)
    rec_teto = round(rec_meta_medida + float(sem.get("receita") or 0), 2)

    cenarios = [
        {"cenario": f"Piso — só o que foi medido ({n_meta} cliente(s) de {respondentes})",
         "receita_atribuida": rec_meta_medida, "roas": roas(rec_meta_medida)},
        {"cenario": f"📊 Instagram + Facebook ({pct_meta:.2f}% de quem respondeu)",
         "receita_atribuida": rec_extrap, "roas": roas(rec_extrap), "recomendado": True},
    ]
    if round(pct_dig, 2) > round(pct_meta, 2):
        cenarios.append(
            {"cenario": f"Digital amplo ({pct_dig:.2f}%)",
             "receita_atribuida": round(receita * pct_dig / 100, 2),
             "roas": roas(round(receita * pct_dig / 100, 2))})
    cenarios += [
        {"cenario": f"Teto absurdo — os {sem.get('n', 0)} sem resposta todos da Meta",
         "receita_atribuida": rec_teto, "roas": roas(rec_teto)},
    ]

    cobertura = sc.get("cobertura_pct")
    confianca = ("Alta" if (cobertura or 0) >= 70 else
                 "Media" if (cobertura or 0) >= 55 else "Baixa")

    return {
        "gerado_em": datetime.now(BRT).isoformat(timespec="seconds"),
        "janela": (f"desde a abertura ({inaug} a {hoje_d.isoformat()}"
                   f" · {kp.get('dias_op')} dias operados)" if janela_casa else
                   f"receita desde a abertura contra verba dos últimos 90 dias"
                   f" — a loja tem {dias_loja} dias, então o ROAS está otimista"),
        "metodo": ("Receita de serviço do Trinks × fatia de clientes que disseram "
                   "Instagram/Facebook em \"como nos conheceu\", dividido pela verba "
                   "de mídia. Não é ROAS da Meta: a Meta não tem evento de valor "
                   "nesta conta."),
        "investimento": round(float(gasto), 2),
        "receita_servico_total": round(float(receita), 2),
        "atribuicao": {
            "cobertura_pct": cobertura,
            "respondentes": respondentes,
            "receita_respondida": receita_respondida,
            "sem_resposta_clientes": sem.get("n"),
            "sem_resposta_receita": sem.get("receita"),
        },
        "meta_share_respondentes_pct": pct_meta,
        "receita_atribuida_medida": rec_meta_medida,
        "receita_atribuida_extrapolada": rec_extrap,
        "roas_medido": roas(rec_meta_medida),
        "roas_extrapolado": roas(rec_extrap),
        "confianca": confianca,
        "cenarios": cenarios,
        "ressalvas": [
            "\"Instagram\" no Trinks não separa pago de orgânico — parte da "
            "receita atribuída pode ter vindo do perfil, não do anúncio.",
            f"{sem.get('n', 0)} cliente(s) não disseram de onde vieram, "
            f"carregando {brl(float(sem.get('receita') or 0))}. O cenário "
            f"recomendado espalha esses no mesmo mix de quem respondeu.",
            "A verba inclui campanha de vaga e post impulsionado, que nunca "
            "tentaram trazer cliente. Veja `meta_ads.vagas_30d` e "
            "`top_campanhas_30d` para separar.",
        ],
    }, None


def aplicar(mid, ap, topo):
    """Grava sem pisar em campo escrito por pessoa. Devolve o que mudou."""
    fc = mid.setdefault("funil_conversao", {})
    mudou = ["apuracao_automatica"]
    fc["apuracao_automatica"] = ap

    # Os contadores do topo do bloco. No Spa eles estavam em zero desde antes
    # da abertura, ao lado de uma `mensagem` dizendo "ativa quando a primeira
    # campanha rodar" — a campanha rodou em 13/09. Zero com cara de dado e o
    # erro que esta casa mais repete, entao eles passam a sair da mesma janela
    # do ROAS, e o que nao da para medir fica null com o motivo do lado.
    # ...mas so num bloco que E um esboco. A Escova tem um funil curado com
    # `etapas` de agosto e `periodo: "Agosto/2026"`; enfiar contadores de 90
    # dias ali deixaria duas janelas diferentes no mesmo bloco, que e
    # justamente como se le um numero errado sem perceber.
    if not fc.get("etapas"):
        fc.update(topo)
        if fc.get("mensagem"):
            fc.pop("mensagem")
            mudou.append("mensagem (removida — estava desatualizada)")
        mudou.append("contadores do topo")

    if not fc.get("roas_estimado"):
        fc["roas_estimado"] = {
            "valor": ap["roas_extrapolado"],
            "calculo": (f"{ap['meta_share_respondentes_pct']:.2f}% dos "
                        f"{ap['atribuicao']['respondentes']} clientes que responderam "
                        f"\"como nos conheceu\" disseram Instagram ou Facebook. "
                        f"Aplicado à receita de serviço de "
                        f"{brl(ap['receita_servico_total'])}: "
                        f"{brl(ap['receita_atribuida_extrapolada'])} ÷ "
                        f"{brl(ap['investimento'])} investido = "
                        f"{ap['roas_extrapolado']}x."),
            "confianca": (f"{ap['confianca']} — cobertura de "
                          f"{ap['atribuicao']['cobertura_pct']}% das fichas. "
                          + ap["ressalvas"][0]),
            "_fonte": "scripts/funil_roas.py (automático)",
        }
        mudou.append("roas_estimado")

    if not fc.get("cenarios_roas"):
        fc["cenarios_roas"] = [dict(c) for c in ap["cenarios"]]
        mudou.append("cenarios_roas")

    if not (fc.get("atribuicao_medida") or {}).get("mix"):
        a = ap["atribuicao"]
        fc["atribuicao_medida"] = {
            "fonte": "Trinks · campo comoNosConheceu, todos os clientes desde a abertura",
            "coorte": (a["respondentes"] or 0) + (a["sem_resposta_clientes"] or 0),
            "responderam": a["respondentes"],
            "cobertura_pct": a["cobertura_pct"],
            "resumo": (f"{a['respondentes']} de "
                       f"{(a['respondentes'] or 0) + (a['sem_resposta_clientes'] or 0)} "
                       f"clientes informaram o canal na recepção; "
                       f"{ap['meta_share_respondentes_pct']:.2f}% vieram de "
                       f"Instagram/Facebook."),
            "mix": [{"canal": m["canal"], "n": m["n"], "share_pct": m["share_pct"]}
                    for m in (ap.get("_mix") or [])],
            "_fonte": "scripts/funil_roas.py (automático)",
        }
        mudou.append("atribuicao_medida")

    return mudou


def main() -> int:
    dry = "--dry-run" in sys.argv
    resultados = {}

    for u, (p_dash, p_mid) in UNIDADES.items():
        dash, mid = ler(p_dash), ler(p_mid)
        if not dash or not mid:
            print(f"❔ {u}: payload ausente — pulando.")
            continue
        ap, motivo = apurar(u, dash, mid)
        if not ap:
            print(f"❔ {u}: {motivo}")
            continue

        # O mix vai separado para o aplicar() poder montar atribuicao_medida.
        anual = dash["abas"]["anual"]["seg_canal"]
        resp = sum(int(x.get("n_clientes") or 0) for x in anual["top"])
        ap["_mix"] = [{"canal": x.get("nome"), "n": int(x.get("n_clientes") or 0),
                       "share_pct": round(int(x.get("n_clientes") or 0) / resp * 100, 1)}
                      for x in anual["top"]]

        j90 = ((mid.get("meta_ads") or {}).get("por_periodo") or {}).get("90d") or {}
        nvr = (dash["abas"]["anual"].get("novos_vs_recorr") or {}).get("novos") or {}
        conv = j90.get("conversas_msg") or 0
        topo = {
            "janela_contadores": ap["janela"],
            "gasto": round(float(j90.get("gasto") or 0), 2),
            "impressoes": j90.get("impressoes") or 0,
            "clicks": j90.get("cliques") or j90.get("clicks") or 0,
            "conversas_msg": conv,
            "novos_clientes_trinks": nvr.get("clientes") or 0,
            "cpa_msg": (round(float(j90.get("gasto") or 0) / conv, 2) if conv else None),
            "cac_real": None,
            "nota_cac": ("Não existe CAC real: nem todo cliente novo veio de "
                         "mídia e o salão não tem agendamento online que ligue "
                         "o anúncio à visita. O que existe é o custo por "
                         "conversa, acima, e o ROAS atribuído no balcão."),
        }
        mudou = aplicar(mid, ap, topo)
        ap.pop("_mix", None)
        resultados[u] = ap

        print(f"📣 {u.upper()} · {ap['janela']}")
        print(f"   verba {brl(ap['investimento'])} · receita de serviço "
              f"{brl(ap['receita_servico_total'])} · cobertura "
              f"{ap['atribuicao']['cobertura_pct']}%")
        print(f"   Meta = {ap['meta_share_respondentes_pct']:.2f}% de quem respondeu "
              f"→ ROAS medido {ap['roas_medido']}x · extrapolado "
              f"{ap['roas_extrapolado']}x ({ap['confianca'].lower()} confiança)")
        print(f"   gravado: {', '.join(mudou)}")

        if not dry:
            (REPO / p_mid).write_text(
                json.dumps(mid, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if len(resultados) == 2:
        a, b = resultados["escova"], resultados["spa"]
        if a["roas_extrapolado"] and b["roas_extrapolado"]:
            vezes = a["roas_extrapolado"] / b["roas_extrapolado"]
            print(f"\n⚖️  Escova {a['roas_extrapolado']}x contra Spa "
                  f"{b['roas_extrapolado']}x — {vezes:.0f}x de diferença.")
        if not dry:
            consolidar(a, b)

    return 0 if resultados else 2


def consolidar(a, b):
    """ROAS da holding: soma receita atribuida, soma verba, divide uma vez.

    Nao e a media dos dois ROAS — isso daria peso igual a uma loja que gastou
    R$ 8.597 e a outra que gastou R$ 2.509. E o numero sai com a diferenca
    escrita do lado, porque 3,94x e 0,33x somados dao um 3,13x que nao
    descreve nenhuma das duas lojas. `docs/aprendizados/media-de-dois-
    negocios.md` e sobre exatamente este tipo de linha.
    """
    rel = "data/consolidado/midias_sociais.json"
    mid = ler(rel)
    if not mid:
        print("❔ consolidado ausente — pulando.")
        return

    rec = round(a["receita_atribuida_extrapolada"] + b["receita_atribuida_extrapolada"], 2)
    verba = round(a["investimento"] + b["investimento"], 2)
    valor = round(rec / verba, 2) if verba else None

    fc = mid.setdefault("funil_conversao", {})
    fc["apuracao_automatica"] = {
        "gerado_em": datetime.now(BRT).isoformat(timespec="seconds"),
        "janela": "desde a abertura de cada loja",
        "metodo": a["metodo"],
        "investimento": verba,
        "receita_atribuida_extrapolada": rec,
        "roas_extrapolado": valor,
        "por_unidade": {"escova": a["roas_extrapolado"], "spa": b["roas_extrapolado"]},
        "ressalvas": [
            f"Este {valor}x não descreve nenhuma das duas lojas: a Escova está "
            f"em {a['roas_extrapolado']}x e o Spa em {b['roas_extrapolado']}x. "
            f"Leia por unidade antes de decidir verba.",
        ] + a["ressalvas"][:1],
    }
    fc["roas_estimado"] = {
        "valor": valor,
        "calculo": (f"{brl(rec)} de receita atribuída à Meta nas duas lojas ÷ "
                    f"{brl(verba)} de verba = {valor}x."),
        "confianca": (f"Escova {a['roas_extrapolado']}x (cobertura "
                      f"{a['atribuicao']['cobertura_pct']}%) e Spa "
                      f"{b['roas_extrapolado']}x (cobertura "
                      f"{b['atribuicao']['cobertura_pct']}%). A soma esconde a "
                      f"diferença — decida por loja."),
        "_fonte": "scripts/funil_roas.py (automático)",
    }
    (REPO / rel).write_text(
        json.dumps(mid, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"🎯 CONSOLIDADO · {valor}x · {brl(rec)} ÷ {brl(verba)} "
          f"(Escova {a['roas_extrapolado']}x · Spa {b['roas_extrapolado']}x)")


if __name__ == "__main__":
    sys.exit(main())
