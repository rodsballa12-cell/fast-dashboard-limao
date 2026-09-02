#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida data/midias_sociais.json antes de commitar.

Existe porque esse arquivo é regenerado por uma Routine (sessão do Claude
consultando o Supermetrics), não por um script determinístico — então nada
garante que a estrutura continue a mesma. O index.html acessa vários campos
sem guarda: se um sumir ou virar null, renderMidias() lança e a aba Mídias
fica em branco, sem erro visível pro usuário.

Uso:  python scripts/validar_midias.py [caminho.json]
Sai com 0 se está tudo certo, 1 se não. Imprime todos os problemas de uma vez.
"""
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
PERIODOS = ["hoje", "7d", "30d", "mtd", "90d"]

# Campos que o index.html lê direto (p.ctr_pct.toFixed, p.frequency.toFixed...).
# Um null aqui quebra a renderização da aba inteira.
CAMPOS_PERIODO = [
    "label", "inicio", "fim", "gasto", "impressoes", "cliques", "link_clicks",
    "post_engagement", "conversas_msg", "reach", "frequency", "ctr_pct",
    "link_ctr_pct", "cpm", "cpc", "cpc_link",
]
NAO_NULO_PERIODO = ["gasto", "impressoes", "cliques", "reach", "frequency", "ctr_pct"]

TOPO = [
    "gerado_em", "fonte", "kpi_estrela", "instagram", "meta_ads", "facebook_page",
    "deltas_vs_periodo_anterior", "alertas_topo", "funil_conversao", "google_ads",
    "hubspot", "whatsapp_cloud_api", "benchmarks", "direcionamentos_estrategicos",
    "recomendacoes", "insights_narrativa",
]
META = [
    "ad_account_id", "ad_account_nome", "por_periodo", "serie_diaria_30d",
    "por_objetivo_30d", "anuncios_30d", "ad_sets_30d", "top_campanhas_30d",
    "geografia_30d", "foco_geografico", "demografia_30d", "placement_30d",
]
BENCH = ["cpa_msg_meta", "ctr_meta", "cpm_meta", "frequency_alerta"]


def main() -> int:
    caminho = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "data" / "midias_sociais.json"
    erros: list[str] = []
    avisos: list[str] = []

    try:
        d = json.loads(caminho.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ JSON inválido: {e}")
        return 1

    for k in TOPO:
        if k not in d:
            erros.append(f"falta a chave de topo '{k}'")

    m = d.get("meta_ads", {})
    for k in META:
        if k not in m:
            erros.append(f"falta meta_ads.{k}")

    # --- períodos -----------------------------------------------------------
    pp = m.get("por_periodo", {})
    for per in PERIODOS:
        p = pp.get(per)
        if not isinstance(p, dict):
            erros.append(f"falta meta_ads.por_periodo['{per}'] (o export CSV do painel usa '30d')")
            continue
        for c in CAMPOS_PERIODO:
            if c not in p:
                erros.append(f"por_periodo['{per}'] sem campo '{c}'")
            elif c in NAO_NULO_PERIODO and p[c] is None:
                erros.append(f"por_periodo['{per}'].{c} é null — o painel chama .toFixed() nele")

    # --- séries -------------------------------------------------------------
    for rotulo, serie in (
        ("meta_ads.serie_diaria_30d", m.get("serie_diaria_30d")),
        ("instagram.serie_diaria_30d", d.get("instagram", {}).get("serie_diaria_30d")),
    ):
        if not isinstance(serie, list):
            erros.append(f"{rotulo} não é lista")
        elif len(serie) != 30:
            erros.append(f"{rotulo} tem {len(serie)} pontos, esperado 30")

    # --- Instagram ----------------------------------------------------------
    ig = d.get("instagram", {})
    for k in ("handle", "followers", "posts_total", "organico_30d", "organico_7d", "top_posts_30d"):
        if k not in ig:
            erros.append(f"falta instagram.{k}")
    o30 = ig.get("organico_30d", {})
    for k in ("novos_seguidores", "novos_seguidores_dia_medio", "profile_views", "profile_views_dia_medio"):
        if o30.get(k) is None:
            erros.append(f"instagram.organico_30d.{k} ausente ou null")

    # --- Facebook Page ------------------------------------------------------
    fb = d.get("facebook_page", {})
    if fb.get("conectado"):
        f30 = fb.get("organico_30d", {})
        for k in ("page_visits", "page_post_engagements", "total_video_views", "video_views_organicos"):
            if f30.get(k) is None:
                erros.append(f"facebook_page.organico_30d.{k} ausente ou null")

    for k in BENCH:
        if d.get("benchmarks", {}).get(k) is None:
            erros.append(f"benchmarks.{k} ausente ou null")

    # --- reconciliação: os recortes de 30d têm que fechar com o total -------
    total = (pp.get("30d") or {}).get("gasto")
    if isinstance(total, (int, float)) and total > 0:
        recortes = {
            "por_objetivo_30d": m.get("por_objetivo_30d"),
            "top_campanhas_30d": m.get("top_campanhas_30d"),
            "anuncios_30d": m.get("anuncios_30d"),
            "ad_sets_30d": m.get("ad_sets_30d"),
        }
        for nome, linhas in recortes.items():
            if not isinstance(linhas, list) or not linhas:
                continue
            soma = sum(x.get("gasto") or 0 for x in linhas)
            if abs(soma - total) > 0.05:
                erros.append(
                    f"{nome} soma R$ {soma:,.2f}, mas por_periodo['30d'].gasto é "
                    f"R$ {total:,.2f} (diferença R$ {abs(soma - total):,.2f})"
                )
        serie = m.get("serie_diaria_30d") or []
        if serie:
            soma = sum(x.get("gasto") or 0 for x in serie)
            if abs(soma - total) > 0.05:
                erros.append(
                    f"serie_diaria_30d soma R$ {soma:,.2f}, mas por_periodo['30d'].gasto "
                    f"é R$ {total:,.2f}"
                )

    # --- frescor ------------------------------------------------------------
    ger = d.get("gerado_em")
    if ger:
        try:
            from datetime import datetime, timezone
            dt = datetime.fromisoformat(ger)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            horas = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
            if horas > 26:
                avisos.append(f"gerado_em tem {horas:.0f}h — o arquivo não foi realmente regenerado?")
            elif horas < -1:
                erros.append(f"gerado_em está {abs(horas):.0f}h no futuro")
        except Exception:
            erros.append(f"gerado_em não é uma data ISO válida: {ger!r}")

    for a in avisos:
        print(f"⚠️  {a}")
    if erros:
        print(f"\n❌ {len(erros)} problema(s) em {caminho.name}:")
        for e in erros:
            print(f"   · {e}")
        return 1
    print(f"✅ {caminho.name} OK · gasto 30d R$ {total:,.2f} · gerado_em {ger}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
