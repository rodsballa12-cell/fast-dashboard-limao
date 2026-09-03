#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera a mensagem de revisão semanal para a agência de tráfego (Beleza Boost).

Lê data/midias_sociais.json e imprime um texto pronto para colar no WhatsApp,
já com os números da semana, a comparação com a semana anterior e a lista do
que se pede de volta. A formatação usa *asterisco simples*, que é o negrito do
WhatsApp — não usar ** aqui.

A ideia é que a revisão seja sempre a mesma estrutura: o que aconteceu, o que
mudou, o que está pendente e o que se espera da agência. O que muda toda semana
são os números, e esses vêm do painel, não da memória.

Uso:  python scripts/revisao_semanal.py [caminho.json] > revisao.txt
"""
import itertools
import json
import pathlib
import sys
from datetime import date, datetime, timedelta

REPO = pathlib.Path(__file__).resolve().parent.parent
DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def brl(v):
    if v is None:
        return "—"
    return "R$ " + f"{v:,.2f}".replace(",", "~").replace(".", ",").replace("~", ".")


def num(v):
    if v is None:
        return "—"
    return f"{v:,.0f}".replace(",", ".")


def dm(iso):
    """2026-09-02 -> 02/09"""
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m")
    except Exception:
        return iso or "—"


def pc(v, casas=2):
    if v is None:
        return "—"
    return f"{v:.{casas}f}".replace(".", ",") + "%"


def seta(v, menor_e_melhor=False):
    """Delta percentual com sinal e cor."""
    if v is None:
        return "—"
    bom = (v < 0) if menor_e_melhor else (v > 0)
    icone = "🟢" if bom else ("🔴" if abs(v) >= 5 else "⚪")
    sinal = "+" if v > 0 else ""
    return f"{icone} {sinal}{f'{v:.0f}'}%"


def dias_sem_entrega(serie, ini, fim):
    """Dias dentro da janela em que a conta não entregou nada."""
    try:
        a, b = date.fromisoformat(ini), date.fromisoformat(fim)
    except Exception:
        return []
    return [
        d["data"] for d in serie
        if a <= date.fromisoformat(d["data"]) <= b and not (d.get("gasto") or 0)
    ]


def retencao_agregada(caminho=None):
    """Números de retenção do Trinks, só agregados.

    Devolve None se o arquivo não existir ou não tiver os campos — a revisão
    sai sem a seção em vez de quebrar. NUNCA lê top_ltv["top"], que é a lista
    nominal de clientes: esta mensagem é enviada para a agência.
    """
    caminho = caminho or REPO / "data" / "dashboard_data.json"
    try:
        anual = json.loads(caminho.read_text(encoding="utf-8"))["abas"]["anual"]
        t, nvr = anual["top_ltv"], anual["novos_vs_recorr"]
        total, uma_vez = t["total_clientes"], t["uma_vez"]
        voltaram = t["duas_mais"]
        rec, novos = nvr["recorrentes"], nvr["novos"]
        if not (total and voltaram and novos["clientes"]):
            return None
        ltv_recorr = rec["receita"] / rec["clientes"]
        ltv_novo = novos["receita"] / novos["clientes"]
        receita = t["receita_total"]
        return {
            "total": total,
            "receita": receita,
            "uma_vez": uma_vez,
            "uma_vez_pct": uma_vez / total * 100,
            "voltaram": voltaram,
            "visitas_recorr": rec["atend"] / rec["clientes"],
            "receita_recorr": rec["receita"],
            "share_recorr": rec["receita"] / receita * 100 if receita else 0,
            "ltv_recorr": ltv_recorr,
            "ltv_novo": ltv_novo,
            "razao": ltv_recorr / ltv_novo if ltv_novo else 0,
        }
    except Exception:
        return None


def main() -> int:
    caminho = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "data" / "midias_sociais.json"
    d = json.loads(caminho.read_text(encoding="utf-8"))
    m = d["meta_ads"]
    p7 = m["por_periodo"]["7d"]
    p30 = m["por_periodo"]["30d"]
    dl = (d.get("deltas_vs_periodo_anterior") or {}).get("7d", {})
    b = d.get("benchmarks", {})
    L = []
    _n = itertools.count(1)
    sec = lambda t: L.append(f"*{next(_n)}. {t}*")

    L.append("📊 *REVISÃO SEMANAL · FAST ESCOVA LIMÃO*")
    L.append(f"_{dm(p7['inicio'])} a {dm(p7['fim'])} · Meta Ads_")
    L.append("")
    L.append("Oi, pessoal! Segue a revisão da semana.")
    L.append("")

    # ------------------------------------------------------------- números --
    sec("Como foi a semana")
    L.append("")
    L.append(f"• Investimento: {brl(p7['gasto'])}")
    L.append(f"• Conversas no WhatsApp: {num(p7['conversas_msg'])}")
    cpa, meta_cpa = p7.get("cpa_msg"), b.get("cpa_msg_meta")
    if cpa and meta_cpa:
        sit = "🟢 dentro da meta" if cpa <= meta_cpa else "🔴 acima da meta"
        L.append(f"• Custo por conversa: {brl(cpa)} — meta até {brl(meta_cpa)} · {sit}")
    else:
        L.append(f"• Custo por conversa: {brl(cpa)}")
    ctr, meta_ctr = p7.get("ctr_pct"), b.get("ctr_meta")
    if ctr and meta_ctr:
        sit = "🟢" if ctr >= meta_ctr else "🔴"
        L.append(f"• CTR: {pc(ctr)} — meta {pc(meta_ctr, 1)} · {sit}")
    L.append(f"• CPM: {brl(p7.get('cpm'))}")
    L.append(f"• Alcance: {num(p7.get('reach'))} pessoas")

    mortos = dias_sem_entrega(m.get("serie_diaria_30d", []), p7["inicio"], p7["fim"])
    if mortos:
        L.append("")
        L.append(
            f"⚠️ *Atenção:* em {len(mortos)} dos 7 dias dessa janela a conta não "
            f"entregou nada ({', '.join(dm(x) for x in mortos)}). Os números acima "
            f"não comparam com nada enquanto esses dias estiverem dentro da conta."
        )
    L.append("")

    # -------------------------------------------------------------- deltas --
    if any(v is not None for v in dl.values() if not isinstance(v, str)):
        sec("Contra a semana anterior")
        L.append("")
        L.append(f"• Investimento: {seta(dl.get('gasto_pct'))}")
        L.append(f"• Conversas: {seta(dl.get('conversas_msg_pct'))}")
        L.append(f"• Custo por conversa: {seta(dl.get('cpa_msg_pct'), menor_e_melhor=True)}")
        L.append(f"• Alcance: {seta(dl.get('reach_pct'))}")
        if mortos:
            L.append("")
            L.append("_Essa queda é a conta parada, não performance. Só volta a significar alguma coisa na próxima revisão._")
        L.append("")

    # ------------------------------------------------------------ 30 dias ---
    sec("Referência dos últimos 30 dias")
    L.append("")
    L.append(
        f"{brl(p30['gasto'])} · {num(p30['conversas_msg'])} conversas · "
        f"CPA {brl(p30.get('cpa_msg'))} · CTR {pc(p30.get('ctr_pct'))} · "
        f"frequência {str(p30.get('frequency','—')).replace('.', ',')}"
    )
    L.append("")

    # --------------------------------------------------- melhor e pior ------
    # Só campanhas que ainda estão no ar: comparar com uma pausada não gera ação.
    # "cortar"/"matar" continuam aqui de propósito — são campanhas rodando que
    # deveriam parar, e é exatamente isso que a agência precisa ver.
    FORA_DO_AR = {"pausado", "pausada", "encerrado", "encerrada", "inativo", "removido"}
    camp = [
        c for c in m.get("top_campanhas_30d", [])
        if c.get("cpa_msg") and (c.get("status") or "").lower() not in FORA_DO_AR
    ]
    if len(camp) >= 2:
        camp.sort(key=lambda c: c["cpa_msg"])
        sec("Melhor e pior campanha ativa (30 dias, por CPA)")
        L.append("")
        L.append(f"🟢 {camp[0]['nome'].strip()} — {brl(camp[0]['cpa_msg'])} · {num(camp[0].get('conversas_msg'))} conversas")
        L.append(f"🔴 {camp[-1]['nome'].strip()} — {brl(camp[-1]['cpa_msg'])} · {num(camp[-1].get('conversas_msg'))} conversas")
        L.append("")

    # -------------------------------------------------- pontos de atenção ---
    alertas = [a for a in d.get("alertas_topo", []) if a.get("sev") in ("crit", "warn")]
    if alertas:
        sec("Pontos que eu quero entender")
        L.append("")
        for a in alertas[:5]:
            L.append(f"{a.get('icone','•')} {a['titulo']}")
        L.append("")

    # ------------------------------------------------------- pendências -----
    pend = [r for r in d.get("recomendacoes", []) if r.get("sev") == "crit"]
    if pend:
        sec("Pendente da revisão anterior")
        L.append("")
        for r in pend:
            L.append(f"• {r['titulo']} — _{r.get('acao','')}_")
        L.append("")
        L.append("Me confirmem o que já foi feito e o que não foi, com o motivo.")
        L.append("")

    # ----------------------------------------------- retenção (Trinks) ------
    # O que a agência não tem e não consegue ver: o que acontece DEPOIS da
    # conversa. Sem hora marcada não há reserva ligando uma coisa à outra, então
    # esta seção é a única forma de a mídia ser discutida em termos de cliente
    # e receita em vez de custo por mensagem.
    #
    # PII: dashboard_data tem nome e telefone de cliente e esta mensagem vai
    # para fora do salão. Aqui só entram agregados — top_ltv["top"], que é a
    # lista nominal, nunca é tocada.
    ret = retencao_agregada()
    if ret:
        sec("Do outro lado do balcão (Trinks — dado que vocês não têm)")
        L.append("")
        L.append(f"• {num(ret['total'])} clientes no ano · {brl(ret['receita'])} de receita")
        L.append(f"• {num(ret['uma_vez'])} vieram uma vez só ({pc(ret['uma_vez_pct'], 0)})")
        L.append(f"• {num(ret['voltaram'])} voltaram — e fazem {str(round(ret['visitas_recorr'], 1)).replace('.', ',')} visitas cada")
        L.append(f"• Quem volta gera {brl(ret['receita_recorr'])} ({pc(ret['share_recorr'], 0)} da receita)")
        L.append(f"• Um cliente que volta vale {brl(ret['ltv_recorr'])} contra {brl(ret['ltv_novo'])} de quem vem uma vez — {str(round(ret['razao'], 1)).replace('.', ',')}x")
        L.append("")
        L.append(
            f"Ou seja: {pc(ret['share_recorr'], 0)} da receita vem de quem volta, e "
            f"100% da verba vai para quem ainda não veio. E como o salão é sem hora "
            f"marcada, não existe reserva segurando ninguém entre uma visita e a outra."
        )
        L.append("")
        L.append("*O que eu quero de vocês sobre isso:*")
        L.append(
            f"• Subir a base de clientes do Trinks como público personalizado e rodar "
            f"uma campanha de retorno. Essas pessoas já conhecem o salão — deve sair "
            f"bem abaixo dos {brl(p30.get('cpa_msg'))} de uma conversa nova."
        )
        L.append(
            f"• Fazer o lookalike a partir de quem VOLTA ({num(ret['voltaram'])} clientes), "
            f"não de todo mundo que já veio. Assim a Meta aprende a achar quem vira "
            f"recorrente, e não quem aparece uma vez e some."
        )
        L.append("")

    # ------------------------------------------------- recomendações Meta ---
    rm = (d.get("meta_ads", {}).get("recomendacoes_meta") or {}).get("itens", [])
    if rm:
        sec("O painel de Recomendações da Meta")
        L.append("")
        L.append(f"Tem {len(rm)} itens abertos lá. Agrupados por tipo:")
        # A Meta repete o mesmo tipo para grupos de ad sets diferentes: listar item
        # a item gera linhas idênticas. Agrupa-se por tipo e ordena-se pelo
        # opportunity_score da Meta, onde MAIOR = mais oportunidade.
        grupos: dict[str, dict] = {}
        for it in rm:
            g = grupos.setdefault(it["tipo"], {"n": 0, "score": 0, "ganho": "", "alvo": ""})
            g["n"] += 1
            if (it.get("prioridade_meta") or 0) >= g["score"]:
                g["score"] = it.get("prioridade_meta") or 0
                g["ganho"] = it.get("ganho_estimado_meta") or "—"
                g["alvo"] = (it.get("alvo") or "").strip()
        for tipo, g in sorted(grupos.items(), key=lambda kv: -kv[1]["score"])[:4]:
            onde = f"{g['n']} grupos de ad sets" if g["n"] > 1 else g["alvo"][:90]
            L.append(f"• *{tipo}* ({onde})")
            L.append(f"  ↳ estimativa da Meta: {g['ganho']}")
        L.append("")
        prior = next((i for i in rm if i["tipo"] == "FRAGMENTATION" and "VAGA" in (i.get("alvo") or "")), None)
        if prior:
            L.append(f"O que eu quero aceitar primeiro é a fragmentação dos ad sets de vaga — {prior.get('ganho_estimado_meta','')}, e é um clique.")
            L.append("")
        L.append("Quais valem aceitar e quais não? Quero a opinião de vocês, não é pra aceitar tudo no automático.")
        L.append("")

    # ------------------------------------------------------- o que peço -----
    # 3 dias corridos, mas nunca caindo em sábado ou domingo — cobrar resposta
    # de agência para o fim de semana só garante que ela não venha.
    alvo_dia = date.today() + timedelta(days=3)
    while alvo_dia.weekday() >= 5:
        alvo_dia += timedelta(days=1)
    prazo = f"{DIAS[alvo_dia.weekday()]} ({alvo_dia.strftime('%d/%m')})"
    sec(f"O que eu preciso de vocês até {prazo}")
    L.append("")
    L.append("1. *A leitura de vocês sobre a semana.* Concordam com o que eu apontei ou estão vendo outra coisa nos números?")
    L.append("")
    L.append("2. *O que vocês recomendam mudar* — e o porquê de cada item. Prefiro uma mudança bem justificada a cinco no chute.")
    L.append("")
    L.append("3. *Um teste para a semana que vem.* Criativo, público, posicionamento ou oferta: qual vocês querem rodar e o que esperam de resultado?")
    L.append("")
    L.append("4. *Onde vocês acham que estamos deixando dinheiro na mesa.* Alguma campanha, público ou horário que a gente ainda não explorou?")
    L.append("")
    L.append("5. *O que vocês precisam de mim* — foto, vídeo, informação de preço, decisão de verba. Não quero descobrir na revisão seguinte que travou esperando alguma coisa minha.")
    L.append("")
    L.append("Abraço!")

    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
