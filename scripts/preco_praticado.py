#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Separa desconto de verdade de pacote sendo consumido.

POR QUE ESTE SCRIPT EXISTE (18/10/2026)
O card "Preco praticado vs tabela" compara a TABELA da franqueadora com o
preco CADASTRADO no Trinks. Ele nunca olha quanto saiu de verdade. Sao tres
precos e o painel so via dois — e o terceiro muda tudo.

Em 18/09 o painel acusou "36 servicos fora da tabela". O achado foi
redecidido em 11/10 e em 16/10 ganhou dono: a gerente da loja. Um mes
cobrando de alguem um numero que media outra coisa.

O que estava acontecendo: quando a cliente compra "4 MAOS + 2 PES" por
R$ 306, o dinheiro entra como PACOTE. Depois, cada sessao resgatada entra no
ranking de servico valendo ZERO — ela ja foi paga. O preco medio da MAO cai
para R$ 35,19 e o painel le isso como desconto de 34%.

A prova e aritmetica. Quantas sessoes teriam que ter entrado a zero para o
medio fechar?

  FAST ESCOVA LISA   9,0        MAOS    28,0
  PES               17,9        RENOVE-SE EM 45 (Spa)  18,0

Numeros inteiros. Desconto no balcao nunca da numero redondo. E cada um bate
com os pacotes vendidos: 8x "4 MAOS + 2 PES" dao direito a 32 maos e 16 pes;
28 maos foram usadas. Nenhuma sessao foi dada — todas estavam pagas.

Com o dinheiro do pacote de volta na conta: Escova R$ 74,55 por sessao, Spa
R$ 149,61 contra tabela de R$ 149 no servico que e 63% do movimento dele.
Exato.

O QUE SOBRA DE VERDADE e cadastro, nao atendimento: quatro servicos da
Escova sao cobrados ACIMA do que esta cadastrado (a FAST MASK sai a R$ 81,38
com cadastro de R$ 39,50, e o painel gritava "desconto de 55,6%, o maior da
casa"). E um unico desvio real: DESIGN SOBRANCELHAS a R$ 57,29 contra R$ 60
— R$ 65 em 17 dias.

Uso:  python scripts/preco_praticado.py [--dry-run]
"""
import json
import pathlib
import sys
from datetime import datetime, timezone, timedelta

REPO = pathlib.Path(__file__).resolve().parent.parent
BRT = timezone(timedelta(hours=-3))

# Acima disto a diferenca deixa de ser arredondamento e passa a ser desvio.
TOL_PCT = 3.0
# Quantas sessoes a zero bastam para chamar de resgate. Uma pode ser cortesia
# ou erro de lancamento; duas ja e padrao.
MIN_ZEROS = 2.0
# Quao perto de um numero inteiro o resultado tem que cair para a hipotese do
# resgate se sustentar. Desconto no balcao espalha; resgate fecha redondo.
TOL_INTEIRO = 0.30

JANELA = "mensal"
UNIDADES = {
    "escova": "data/dashboard_data.json",
    "spa": "data/spa/dashboard_data.json",
    # O consolidado tambem: o catalogo dele e a juniao dos dois (112 servicos)
    # e o ranking vem somado. Os nomes nao se cruzam entre as lojas — escova,
    # unhas e make de um lado; massagem, limpeza de pele e terapia do outro —
    # entao a classificacao por servico continua valendo. O numero por sessao,
    # ai sim, e media de dois negocios: a ressalva vai gravada no bloco.
    "consolidado": "data/consolidado/dashboard_data.json",
}


def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "~").replace(".", ",").replace("~", ".")


def norm(s):
    tr = str.maketrans("ÁÃÀÂÉÊÍÓÕÔÚÜÇ", "AAAAEEIOOOUUC")
    return " ".join((s or "").upper().translate(tr).replace("-", " ").split())


def ler(rel):
    p = REPO / rel
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def apurar(dash):
    cs = dash.get("catalogo_servicos") or {}
    aba = (dash.get("abas") or {}).get(JANELA) or {}
    rank = aba.get("ranking_serv") or []
    cat = aba.get("categorias") or {}
    if not cs.get("n_total") or not rank:
        return None, "sem catalogo de servicos ou sem ranking no periodo"

    tab = {norm(x.get("servico")): x for x in (cs.get("desvio_tabela") or [])}
    pac_v = float((cat.get("pacotes") or {}).get("v") or 0)
    serv_v = float((cat.get("servicos") or {}).get("v") or 0)
    serv_n = int((cat.get("servicos") or {}).get("n") or 0)

    itens, zeros_tot, mesa_tot, n_cadastro, n_desvio, n_sem_tabela = [], 0.0, 0.0, 0, 0, 0
    for x in rank:
        nq = int(x.get("n") or 0)
        v = float(x.get("v") or 0)
        if nq <= 0:
            continue
        cobrado = v / nq
        t = tab.get(norm(x.get("nome")))
        if not t:
            n_sem_tabela += 1
            itens.append({
                "servico": x.get("nome"), "n": nq, "cobrado_medio": round(cobrado, 2),
                "tabela": None, "cadastrado": None, "classe": "sem_tabela",
                "leitura": "Não está no catálogo com preço — não dá para comparar.",
            })
            continue

        tabela = float(t.get("tabela") or 0)
        cadast = float(t.get("praticado") or 0)
        pagas = (v / cadast) if cadast else None
        zeros = (nq - pagas) if pagas is not None else None
        perto_inteiro = (zeros is not None
                         and abs(zeros - round(zeros)) <= TOL_INTEIRO)

        item = {
            "servico": x.get("nome"), "n": nq,
            "tabela": round(tabela, 2), "cadastrado": round(cadast, 2),
            "cobrado_medio": round(cobrado, 2),
            "sessoes_a_zero_estimadas": (round(zeros, 1) if zeros is not None else None),
            "deixado_na_mesa": 0.0,
        }

        if zeros is not None and zeros >= MIN_ZEROS and perto_inteiro and pac_v > 0:
            # As sessoes que foram pagas sairam no preco cadastrado, redondo.
            n_pagas = round(pagas)
            item.update({
                "classe": "resgate_de_pacote",
                "cobrado_nas_pagas": round(cadast, 2),
                "desvio_real_pct": round((cadast / tabela - 1) * 100, 1) if tabela else None,
                "leitura": (f"{round(zeros)} de {nq} sessões entraram a zero — já pagas em "
                            f"pacote. As {n_pagas} cobradas saíram a {brl(cadast)}, o preço "
                            f"da casa. Não é desconto."),
            })
            zeros_tot += round(zeros)
        elif zeros is not None and zeros <= -1 and perto_inteiro:
            n_cadastro += 1
            item.update({
                "classe": "cadastro_desatualizado",
                "desvio_real_pct": round((cobrado / tabela - 1) * 100, 1) if tabela else None,
                "leitura": (f"Cobrado a {brl(cobrado)} com cadastro de {brl(cadast)} — "
                            f"o cadastro no Trinks está velho, não o atendimento. "
                            f"Contra a tabela de {brl(tabela)}: "
                            f"{(cobrado / tabela - 1) * 100:+.1f}%."),
            })
        else:
            pct = ((cobrado / tabela - 1) * 100) if tabela else None
            if pct is not None and abs(pct) >= TOL_PCT:
                n_desvio += 1
                mesa = max((tabela - cobrado) * nq, 0.0)
                mesa_tot += mesa
                item.update({
                    "classe": "desvio_real", "desvio_real_pct": round(pct, 1),
                    "deixado_na_mesa": round(mesa, 2),
                    "leitura": (f"Cobrado a {brl(cobrado)} contra tabela de {brl(tabela)} "
                                f"({pct:+.1f}%) em {nq} sessões, e nenhum pacote explica. "
                                f"Deixado na mesa: {brl(mesa)}."),
                })
            else:
                item.update({
                    "classe": "aderente",
                    "desvio_real_pct": round(pct, 1) if pct is not None else None,
                    "leitura": f"Cobrado a {brl(cobrado)} — na tabela.",
                })
        itens.append(item)

    # AS ACOES, JA PRONTAS.
    # O card antigo (e o meu primeiro) mostrava 14 servicos e deixava o leitor
    # deduzir o que fazer. Quem decide precisa de duas coisas: o que arrumar e
    # quanto vale. A lista sai daqui montada, com "de → para" onde couber.
    acoes = []
    for i in itens:
        if i["classe"] == "cadastro_desatualizado":
            # Dois casos bem diferentes dentro da mesma classe.
            # (a) cadastro abaixo da tabela e cobrando a tabela → e so acertar
            #     o cadastro, o atendimento esta certo.
            # (b) cobrando ACIMA da tabela da franqueadora → nao da para
            #     "atualizar para R$ 59" quando o cadastro JA e R$ 59. Ou o
            #     preco subiu e ninguem registrou, ou o servico esta sendo
            #     confundido com outro. No Spa a LIBERACAO MIOFASCIAL (tabela
            #     R$ 59) sai a R$ 89, e existe uma TERAPIA LIBERACAO MIOFASCIAL
            #     de R$ 179. Isso e conferir, nao atualizar.
            acima_da_tabela = (i["cobrado_medio"] or 0) > (i["tabela"] or 0) * 1.03
            if acima_da_tabela and abs((i["cadastrado"] or 0) - (i["tabela"] or 0)) < 0.01:
                acoes.append({
                    "tipo": "conferir", "servico": i["servico"],
                    "de": i["tabela"], "para": i["cobrado_medio"],
                    "o_que_fazer": (f"Conferir: sai a {brl(i['cobrado_medio'])} com "
                                    f"tabela de {brl(i['tabela'])}"),
                    "por_que": ("o preço subiu e ninguém registrou, ou está sendo "
                                "lançado no serviço errado"),
                    "vale": 0.0,
                })
            else:
                acoes.append({
                    "tipo": "cadastro", "servico": i["servico"],
                    "de": i["cadastrado"], "para": i["tabela"],
                    "o_que_fazer": (f"Atualizar no Trinks: {brl(i['cadastrado'])} → "
                                    f"{brl(i['tabela'])}"),
                    "por_que": (f"você já cobra {brl(i['cobrado_medio'])}; o cadastro é "
                                f"que está atrás"),
                    "vale": 0.0,
                })
        elif i["classe"] == "desvio_real":
            acoes.append({
                "tipo": "desconto", "servico": i["servico"],
                "de": i["cobrado_medio"], "para": i["tabela"],
                "o_que_fazer": (f"Cobrar {brl(i['tabela'])} — está saindo a "
                                f"{brl(i['cobrado_medio'])}"),
                "por_que": f"{i['n']} sessões, e nenhum pacote explica",
                "vale": i["deixado_na_mesa"],
            })
    acoes.sort(key=lambda a: (-a["vale"], a["tipo"]))

    receita_periodo = serv_v + pac_v
    return {
        "gerado_em": datetime.now(BRT).isoformat(timespec="seconds"),
        "janela": JANELA,
        "acoes": acoes,
        "deixado_na_mesa_pct": (round(mesa_tot / receita_periodo * 100, 2)
                                if receita_periodo else None),
        "metodo": ("Cruza a tabela da franqueadora, o preço cadastrado no Trinks e "
                   "o que REALMENTE saiu (receita ÷ sessões). Quando o médio só "
                   "fecha com um número inteiro de sessões a zero e a loja vendeu "
                   "pacote no período, é resgate — a cliente já pagou — e não "
                   "desconto. É inferência aritmética: o painel não enxerga "
                   "transação a transação."),
        "sessoes": serv_n,
        "receita_servico": round(serv_v, 2),
        "receita_pacote": round(pac_v, 2),
        "por_sessao_sem_pacote": round(serv_v / serv_n, 2) if serv_n else None,
        "por_sessao_com_pacote": round((serv_v + pac_v) / serv_n, 2) if serv_n else None,
        "resgate_sessoes_estimadas": int(zeros_tot),
        "resgate_pct_das_sessoes": round(zeros_tot / serv_n * 100, 1) if serv_n else None,
        "deixado_na_mesa_real": round(mesa_tot, 2),
        "n_cadastro_desatualizado": n_cadastro,
        "n_desvio_real": n_desvio,
        "n_sem_tabela": n_sem_tabela,
        "itens": itens,
    }, None


def main() -> int:
    dry = "--dry-run" in sys.argv
    feitos = 0
    for u, rel in UNIDADES.items():
        dash = ler(rel)
        if not dash:
            print(f"❔ {u}: payload ausente — pulando.")
            continue
        ap, motivo = apurar(dash)
        if not ap:
            print(f"❔ {u}: {motivo}")
            continue
        if u == "consolidado":
            ap["ressalva"] = ("O valor por sessão aqui é média de dois negócios: "
                              "a Escova gira perto de R$ 75 e o Spa de R$ 150. "
                              "Leia por loja antes de decidir preço.")
        dash.setdefault("catalogo_servicos", {})["preco_realizado"] = ap
        if not dry:
            (REPO / rel).write_text(
                json.dumps(dash, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        feitos += 1

        print(f"📐 {u.upper()} · {ap['sessoes']} sessões · "
              f"{brl(ap['por_sessao_com_pacote'])}/sessão com o pacote de volta")
        print(f"   resgate: {ap['resgate_sessoes_estimadas']} sessões "
              f"({ap['resgate_pct_das_sessoes']}%) já pagas em pacote")
        print(f"   cadastro velho: {ap['n_cadastro_desatualizado']} serviço(s) · "
              f"desvio real: {ap['n_desvio_real']} · "
              f"deixado na mesa {brl(ap['deixado_na_mesa_real'])}")
        for i in ap["itens"]:
            if i["classe"] in ("resgate_de_pacote", "cadastro_desatualizado", "desvio_real"):
                print(f"     [{i['classe']:<22}] {i['servico'][:34]}")
    return 0 if feitos else 2


if __name__ == "__main__":
    sys.exit(main())
