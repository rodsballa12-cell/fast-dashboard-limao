"""Gera data/spa/midias_sociais.json com o que já temos de real da SPA
(Meta Ad Account + IG + FB do config) e métricas zeradas — loja abre
25/09/2026, ainda sem gasto/campanha/seguidor histórico.

Substituição: quando gerente Marketing FAST rodar o Supermetrics MCP
apontando pros IDs SPA, o payload é reescrito com métricas reais.
Este script deixa de ser necessário nesse momento.
"""

import json, os
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "data", "config.json")
DST_DIR = os.path.join(ROOT, "data", "spa")
DST = os.path.join(DST_DIR, "midias_sociais.json")

BRT = timezone(timedelta(hours=-3))


def _periodo_zerado(label):
    return {
        "label": label,
        "gasto": 0.0,
        "impressoes": 0,
        "clicks": 0,
        "conversas_msg": 0,
        "cpa_msg": None,
        "cpm": 0.0,
        "ctr_pct": 0.0,
        "frequency": 0.0,
        "reach": 0,
        "alerta": None,
    }


def main():
    with open(CONFIG) as f:
        cfg = json.load(f)
    spa = cfg["unidades"]["spa"]["midia_ids"]

    now = datetime.now(BRT).isoformat(timespec="seconds")
    d_inauguracao = cfg["unidades"]["spa"]["data_inauguracao"]

    payload = {
        "gerado_em": now,
        "fonte": "Placeholder pré-abertura · Meta trio já provisionado, aguardando primeiras campanhas SPA",
        "_pre_abertura": True,
        "_data_inauguracao": d_inauguracao,
        "janelas": {"hoje": None, "7d": None, "mtd": None, "30d": None, "90d": None},
        "kpi_estrela": {
            "explicacao": "CPA por conversa iniciada · aguardando primeira campanha SPA (0 anúncios rodando).",
        },
        "instagram": {
            "handle": spa.get("ig_handle") or "fastspa.limao",
            "ig_user_id": spa.get("ig_user_id"),
            "url": f"https://www.instagram.com/{spa.get('ig_handle') or 'fastspa.limao'}/",
            "followers": 0,
            "posts_total": 0,
            "posts_na_janela": 0,
            "organico_30d": {
                "novos_seguidores": 0,
                "novos_seguidores_dia_medio": 0,
                "profile_views": 0,
                "profile_views_dia_medio": 0,
                "profile_reposts": 0,
                "profile_replies": 0,
                "nota_profile_views": "IG API só devolve views a partir do primeiro insight coletado.",
            },
            "organico_7d": {
                "novos_seguidores": 0,
                "profile_views": 0,
                "reach": 0,
            },
            "serie_diaria_30d": [],
            "top_posts_30d": [],
            "ultimo_post": {
                "data": None,
                "dias_sem_postar": None,
                "alerta": "Aguardando primeiro insight sync (~24h após primeiro post publicado).",
            },
        },
        "meta_ads": {
            "ad_account_id": spa.get("meta_ad_account_id"),
            "ad_account_nome": spa.get("meta_ad_account_nome") or "FS - LIMÃO",
            "por_periodo": {
                "hoje": _periodo_zerado("Hoje"),
                "7d":   _periodo_zerado("Últimos 7 dias"),
                "mtd":  _periodo_zerado("Mês corrente"),
                "30d":  _periodo_zerado("Últimos 30 dias"),
                "90d":  _periodo_zerado("Últimos 90 dias"),
            },
            "serie_diaria_30d": [],
            "por_objetivo_30d": [],
            "anuncios_30d": [],
            "ad_sets_30d": [],
            "top_campanhas_30d": [],
            "verba_setembro": 0,
            "nota_reach": "SPA ainda não iniciou campanhas — reach medido a partir do primeiro anúncio.",
        },
        "facebook_page": {
            "nome": spa.get("facebook_page_nome") or "Fast Spa Limão",
            "page_id": spa.get("facebook_page_id"),
            "conectado": bool(spa.get("facebook_page_id")),
            "seguidores": 0,
            "posts_30d": 0,
        },
        "google_business": {
            "nome": spa.get("google_business_nome") or "Fast SPA Limão",
            "location_id": spa.get("google_business_location_id"),
            "conectado": bool(spa.get("google_business_location_id")),
            "endereco": spa.get("google_business_endereco"),
            "categorias": spa.get("google_business_categorias") or [],
            "kpis_30d": {"actions_phone": 0, "actions_directions": 0, "views_total": 0},
            "rating": {"estrelas_media": 0, "reviews_total": 0},
            "serie_diaria_30d": [],
            "mensagem": None if spa.get("google_business_location_id") else "Business Profile pendente de criação — brief entregue ao gerente Marketing (ver data/spa/BRIEF_MARKETING.md).",
        },
        "google_ads": {"conectado": False, "mensagem": "SPA sem Google Ads planejado no lançamento."},
        "hubspot": {"portal_id": spa.get("hubspot_portal_id"), "contatos": 0},
        "whatsapp_cloud_api": {
            "conectado": bool(spa.get("whatsapp_phone_number_id")),
            "display_number": spa.get("whatsapp_display_number"),
            "display_name": spa.get("whatsapp_display_name"),
            "waba_id": spa.get("whatsapp_business_account_id"),
            "phone_number_id": spa.get("whatsapp_phone_number_id"),
            "mensagem": None if spa.get("whatsapp_phone_number_id") else f"Número {spa.get('whatsapp_display_number', '')} registrado no portfolio Fast Spa 2026 · WABA a ser criada pelo gerente Marketing (ver brief).",
        },
        "benchmarks": {"cpa_msg_meta": 25, "ctr_meta": 1.5, "cpm_meta": 20},
        "direcionamentos_estrategicos": [
            {
                "titulo": "🚀 Pré-abertura · warm-up dos canais",
                "prioridade": "P1",
                "texto": f"SPA inaugura em {d_inauguracao.split('-')[::-1] and '/'.join(d_inauguracao.split('-')[::-1])}. Meta trio (Ad Account + IG + FB) já conectado. Começar aquecimento: 3-5 posts orgânicos IG/FB por semana + campanha de reconhecimento (baixo custo, alcance amplo do bairro) 15 dias antes da abertura.",
            },
        ],
        "recomendacoes": [
            {
                "sev": "warn",
                "titulo": "Templates WhatsApp precisam ser aprovados",
                "texto": "aniversario_fast_v1 e reativacao_fast_v1 rodam na Escova (WABA perdida) — precisam ser reaprovados nas 2 novas WABAs (Escova recriação + SPA). Sem template aprovado, disparo automático fica off na abertura.",
            },
            {
                "sev": "info",
                "titulo": "Google Business Profile antes da abertura",
                "texto": "Fluxo de verificação (cartão postal ou vídeo) leva 5-14 dias. Criar já pra Business Profile estar aprovado antes de 25/09 — 1 mês antes é o ideal.",
            },
        ],
        "insights_narrativa": [
            f"SPA em pré-abertura (D-{max(0, (datetime.fromisoformat(d_inauguracao).date() - datetime.now().date()).days)} até 25/09).",
            "Meta Ad Account provisionado sob portfolio Fast Spa 2026 (mesmo admin da Escova). Nenhuma campanha rodando ainda.",
            "IG @fastspa.limao e página Facebook Fast Spa Limão criadas, seguidores começando do zero.",
        ],
        "alertas_topo": [],
        "deltas_vs_periodo_anterior": {},
        "funil_conversao": {
            "gasto": 0, "impressoes": 0, "clicks": 0,
            "conversas_msg": 0, "novos_clientes_trinks": 0,
            "cpa_msg": None, "cac_real": None,
            "mensagem": "Funil ativa quando primeira campanha SPA rodar + Trinks SPA subir (estabelecimentoId pendente).",
        },
    }

    os.makedirs(DST_DIR, exist_ok=True)
    with open(DST, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"[build_spa_midias] gerado {DST}")
    print(f"  Meta Ad Account: {spa.get('meta_ad_account_id')} ({spa.get('meta_ad_account_nome')})")
    print(f"  IG: @{spa.get('ig_handle')} · user_id {spa.get('ig_user_id')}")
    print(f"  FB: {spa.get('facebook_page_nome')} · page_id {spa.get('facebook_page_id')}")
    print(f"  WA: {spa.get('whatsapp_display_number')} · WABA {spa.get('whatsapp_business_account_id') or 'pendente'}")
    print(f"  GBP: {spa.get('google_business_nome')} · location_id {spa.get('google_business_location_id') or 'pendente'}")


if __name__ == "__main__":
    main()
