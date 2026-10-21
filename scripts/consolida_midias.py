#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Consolida as mídias de Escova + Spa em data/consolidado/midias_sociais.json.

Regra: número de consolidado nunca é digitado — sai daqui. Soma o que soma
(gasto, impressões, cliques, conversas, reach), recalcula o que é razão
(frequência, CTR, CPM, CPC, CPA) e entrega, além do total, a leitura POR LOJA:

  · meta_ads.por_unidade   — gasto/conversas/CPA de cada loja em cada janela, e o
                             CPA de SERVIÇO separado do de VAGA (conversa de vaga
                             custa R$ 1-2 e não é cliente);
  · alertas_por_loja       — os alertas de topo de cada loja + o alarme de entrega;
  · _frescor               — de quando é o dado de cada loja.

Preserva as chaves que não são de Meta Ads (instagram, google_business, ...).

Uso:  python3 scripts/consolida_midias.py
"""
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
ESC = REPO / "data" / "midias_sociais.json"
SPA = REPO / "data" / "spa" / "midias_sociais.json"
DST = REPO / "data" / "consolidado" / "midias_sociais.json"

JANELAS = ["hoje", "7d", "mtd", "30d", "90d"]
LABELS = {"hoje": None, "7d": "Ultimos 7 dias", "mtd": "Mes corrente", "30d": "Últimos 30 dias", "90d": "Ultimos 90 dias"}
SOMAR = ["gasto", "impressoes", "cliques", "link_clicks", "post_engagement", "conversas_msg", "reach"]


def r2(x):
    return round(x, 2)


def somar_periodo(k, a, b):
    o = {c: (a.get(c) or 0) + (b.get(c) or 0) for c in SOMAR}
    g, im, cl, lk, cv, rc = o["gasto"], o["impressoes"], o["cliques"], o["link_clicks"], o["conversas_msg"], o["reach"]
    o["gasto"] = r2(g)
    o.update(
        label=a.get("label") if k == "hoje" else LABELS[k],
        inicio=a.get("inicio"), fim=a.get("fim"),
        frequency=round(im / rc, 4) if rc else 0.0,
        ctr_pct=r2(cl / im * 100) if im else 0.0,
        link_ctr_pct=r2(lk / im * 100) if im else 0.0,
        cpm=r2(g / im * 1000) if im else 0.0,
        cpc=r2(g / cl) if cl else 0.0,
        cpc_link=r2(g / lk) if lk else 0.0,
        cpa_msg=r2(g / cv) if cv else None,
    )
    return o


def razao(gasto, conv):
    return r2(gasto / conv) if conv else None


def recalcula_vagas(m):
    """Os números de `vagas_30d` saem das campanhas '[VAGA ...]' da própria janela 30d.

    O bloco era digitado à mão e envelheceu: no Spa a janela parou em 29/09 e dava
    303 conversas de vaga num mês com 176 no total, o que zerava o CPA de serviço
    do card. Os textos (situação, lacuna de medição) continuam sendo de pessoa.
    """
    p30 = (m.get("por_periodo") or {}).get("30d") or {}
    camp = [c for c in (m.get("top_campanhas_30d") or []) if "VAGA" in (c.get("nome") or "").upper()]
    vg = m.get("vagas_30d")
    if not p30 or not isinstance(vg, dict):
        return False
    g = r2(sum(c.get("gasto") or 0 for c in camp))
    cv = sum(c.get("conversas_msg") or 0 for c in camp)
    vg.update(janela=f"{p30['inicio']} a {p30['fim']}", gasto_total=g, conversas=cv, cpa_msg=razao(g, cv),
              campanhas=len(camp), share_da_verba_pct=r2(g / p30["gasto"] * 100) if p30.get("gasto") else 0.0,
              _origem="calculado de top_campanhas_30d (nome com VAGA) por scripts/consolida_midias.py")
    return True


def por_loja(m):
    """Janelas da loja + serviço × vaga (a vaga só existe em 30d)."""
    pp = m.get("por_periodo") or {}
    out = {k: {"gasto": (pp.get(k) or {}).get("gasto"), "conversas": (pp.get(k) or {}).get("conversas_msg"),
               "cpa": (pp.get(k) or {}).get("cpa_msg")} for k in JANELAS}
    p30, vg = pp.get("30d") or {}, m.get("vagas_30d") or {}
    if p30 and vg:
        sg = r2((p30.get("gasto") or 0) - (vg.get("gasto_total") or 0))
        sc = (p30.get("conversas_msg") or 0) - (vg.get("conversas") or 0)
        out["30d_servico"] = {"gasto": sg, "conversas": sc, "cpa": razao(sg, sc)}
        out["30d_vaga"] = {"gasto": vg.get("gasto_total"), "conversas": vg.get("conversas"), "cpa": vg.get("cpa_msg")}
    return out


def alarme(caminho):
    try:
        import alerta_entrega
        nivel, titulo, detalhe = alerta_entrega.avaliar(caminho)
        return {"nivel": nivel, "titulo": titulo, "detalhe": detalhe}
    except Exception as e:  # nunca derruba a consolidação
        return {"nivel": "indef", "titulo": "Alarme não avaliado", "detalhe": str(e)}


def main():
    E = json.loads(ESC.read_text(encoding="utf-8"))
    S = json.loads(SPA.read_text(encoding="utf-8"))
    C = json.loads(DST.read_text(encoding="utf-8")) if DST.exists() else {}
    em, sm = E["meta_ads"], S["meta_ads"]
    for caminho, dados, m in ((ESC, E, em), (SPA, S, sm)):
        if recalcula_vagas(m):
            caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    pp = {k: somar_periodo(k, em["por_periodo"][k], sm["por_periodo"][k]) for k in JANELAS}
    for k in JANELAS:
        pp[k]["atualizado_em"] = max(em["por_periodo"][k].get("atualizado_em") or "", sm["por_periodo"][k].get("atualizado_em") or "") or None
    cm = C.setdefault("meta_ads", {})
    cm.update(ad_account_id="consolidado", ad_account_nome="Escova + SPA", por_periodo=pp)

    # série diária somada (30 pontos, mesmo calendário das duas)
    se = {x["data"]: x for x in em["serie_diaria_30d"]}
    ss = {x["data"]: x for x in sm["serie_diaria_30d"]}
    serie = []
    for d in sorted(set(se) | set(ss)):
        a, b = se.get(d) or {}, ss.get(d) or {}
        g = r2((a.get("gasto") or 0) + (b.get("gasto") or 0)); cv = (a.get("conversas_msg") or 0) + (b.get("conversas_msg") or 0)
        cl = (a.get("cliques") or 0) + (b.get("cliques") or 0)
        serie.append(dict(data=d, gasto=g, impressoes=(a.get("impressoes") or 0) + (b.get("impressoes") or 0), cliques=cl, clicks=cl,
                          reach=(a.get("reach") or 0) + (b.get("reach") or 0), conversas_msg=cv, cpa_msg=razao(g, cv)))
    cm["serie_diaria_30d"] = serie

    # vagas somadas (duas lojas recrutam) — a orientação de "escalar/pausar" olha o CPA de serviço
    ve, vs = em.get("vagas_30d") or {}, sm.get("vagas_30d") or {}
    if ve or vs:
        g = r2((ve.get("gasto_total") or 0) + (vs.get("gasto_total") or 0)); cv = (ve.get("conversas") or 0) + (vs.get("conversas") or 0)
        cm["vagas_30d"] = dict(janela=pp["30d"]["inicio"] + " a " + pp["30d"]["fim"], gasto_total=g, conversas=cv, cpa_msg=razao(g, cv),
                               share_da_verba_pct=r2(g / pp["30d"]["gasto"] * 100) if pp["30d"]["gasto"] else 0.0,
                               campanhas=(ve.get("campanhas") or 0) + (vs.get("campanhas") or 0))

    cm["por_unidade"] = {"escova": por_loja(em), "spa": por_loja(sm)}
    cm["nota"] = "Soma direta dos dois Ad Accounts (Escova + Spa). Reach é aproximado (soma sem deduplicar). Gerado por scripts/consolida_midias.py."

    # Google Business: soma Escova + SPA (ambos conectados desde 15/10/2026).
    # Antes dessa data o consolidado herdava so Escova; hoje subcontaria views/
    # acoes/reviews. Fallback preserva um lado se o outro perder a conexao.
    e_gb = E.get("google_business") or {}
    s_gb = S.get("google_business") or {}
    if e_gb.get("conectado") and s_gb.get("conectado"):
        def _n(x): return x or 0
        e_k, s_k = e_gb.get("kpis_30d") or {}, s_gb.get("kpis_30d") or {}
        views = int(_n(e_k.get("views_total")) + _n(s_k.get("views_total")))
        acoes = int(_n(e_k.get("actions_total")) + _n(s_k.get("actions_total")))
        cons_kpis = {
            "views_total":        views,
            "views_maps":         int(_n(e_k.get("views_maps"))     + _n(s_k.get("views_maps"))),
            "views_search":       int(_n(e_k.get("views_search"))   + _n(s_k.get("views_search"))),
            "actions_total":      acoes,
            "actions_phone":      int(_n(e_k.get("actions_phone"))    + _n(s_k.get("actions_phone"))),
            "actions_directions": int(_n(e_k.get("actions_directions")) + _n(s_k.get("actions_directions"))),
            "actions_website":    int(_n(e_k.get("actions_website"))  + _n(s_k.get("actions_website"))),
            "actions_messages":   int(_n(e_k.get("actions_messages")) + _n(s_k.get("actions_messages"))),
            "taxa_conversao_pct": round(acoes / views * 100, 1) if views else 0,
        }
        # Rating: media ponderada por review count (nao media simples — a loja
        # com mais reviews pesa mais na nota consolidada).
        e_r, s_r = e_gb.get("rating") or {}, s_gb.get("rating") or {}
        e_rev, s_rev = int(_n(e_r.get("reviews_total"))), int(_n(s_r.get("reviews_total")))
        tot_rev = e_rev + s_rev
        media = ((_n(e_r.get("estrelas_media")) * e_rev + _n(s_r.get("estrelas_media")) * s_rev) / tot_rev) if tot_rev else 0
        cons_rating = {"reviews_total": tot_rev, "estrelas_media": round(media, 1)}
        # Serie diaria: soma por data (dias so em um lado entram com o outro = 0).
        serie_map = {}
        for d in (e_gb.get("serie_diaria_30d") or []):
            serie_map[d["data"]] = {k: int(_n(d.get(k))) for k in d if k != "data"}
        for d in (s_gb.get("serie_diaria_30d") or []):
            dst = serie_map.setdefault(d["data"], {})
            for k, v in d.items():
                if k == "data": continue
                dst[k] = int(_n(dst.get(k)) + _n(v))
        cons_serie = [{"data": dt, **vals} for dt, vals in sorted(serie_map.items())]
        C["google_business"] = {
            "nome": "Fast Escova + Fast Spa Limão",
            "conectado": True,
            "conectado_em": max(e_gb.get("conectado_em") or "", s_gb.get("conectado_em") or ""),
            "dados_ate": min(e_gb.get("dados_ate") or "9999", s_gb.get("dados_ate") or "9999"),
            "kpis_30d": cons_kpis,
            "rating": cons_rating,
            "serie_diaria_30d": cons_serie,
            "detalhes_por_unidade": {
                "escova": {"nome": e_gb.get("nome"), "views_30d": e_k.get("views_total"), "reviews": e_r.get("reviews_total"), "estrelas": e_r.get("estrelas_media")},
                "spa":    {"nome": s_gb.get("nome"), "views_30d": s_k.get("views_total"), "reviews": s_r.get("reviews_total"), "estrelas": s_r.get("estrelas_media")},
            },
            "_fonte_refresh": "consolidado · scripts/consolida_midias.py (views/acoes somados, estrelas ponderadas por review count)",
        }
    elif e_gb.get("conectado") or s_gb.get("conectado"):
        # Um lado so: usa esse lado (preserva comportamento pre-ativacao do SPA).
        C["google_business"] = e_gb if e_gb.get("conectado") else s_gb

    def top(alertas):
        ordem = {"crit": 0, "warn": 1, "info": 2}
        return sorted(alertas or [], key=lambda a: ordem.get(a.get("sev"), 3))[:3]
    C["alertas_por_loja"] = {
        "escova": {"alarme_entrega": alarme(ESC), "alertas": top(E.get("alertas_topo"))},
        "spa": {"alarme_entrega": alarme(SPA), "alertas": top(S.get("alertas_topo"))},
    }
    C["_frescor"] = {"escova": E.get("gerado_em"), "spa": S.get("gerado_em"),
                     "fonte_escova": E.get("fonte"), "fonte_spa": S.get("fonte")}
    C["gerado_em"] = max(E.get("gerado_em") or "", S.get("gerado_em") or "")
    C["fonte"] = "consolidado (escova + spa) · scripts/consolida_midias.py"
    DST.write_text(json.dumps(C, ensure_ascii=False, indent=2), encoding="utf-8")
    p = pp["30d"]
    print(f"[consolida_midias] 30d R$ {p['gasto']:,.2f} · {p['conversas_msg']} conversas · CPA {p['cpa_msg']} · gerado_em {C['gerado_em']}")


if __name__ == "__main__":
    main()
