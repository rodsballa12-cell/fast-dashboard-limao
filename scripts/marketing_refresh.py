r"""Orquestrador do módulo de marketing.

Roda os coletores (Google Meu Negócio + Meta) e, opcionalmente, o gerador de
conteúdo. Grava tudo em data/marketing_data.json preservando o que foi escrito
à mão (calendário e campanhas nunca são sobrescritos por um coletor).

Uso:
  python scripts/marketing_refresh.py                # só coleta métricas
  python scripts/marketing_refresh.py --conteudo     # coleta + gera pauta com Claude
  python scripts/marketing_refresh.py --conteudo --dias 14

Nenhuma etapa derruba as outras: se o Google falhar, o Instagram ainda atualiza.
"""
from __future__ import annotations

import argparse
import sys

import marketing_gmn
import marketing_meta
from marketing_common import carregar, hoje, registrar_erro, salvar


def sincronizar_calendario(dados: dict) -> None:
    """Marca como publicado o item do calendário que já saiu de fato no Instagram.

    O casamento é por data + canal: o coletor da Meta traz o que realmente foi ao
    ar, e o calendário é o plano. Quando os dois batem, o plano vira histórico.
    """
    publicados = {
        (p.get("quando", "")[:10], p.get("canal"))
        for p in (dados.get("meta", {}) or {}).get("publicacoes", [])
    }
    for item in dados.get("calendario", []):
        chave = (item.get("data", ""), item.get("canal"))
        if chave in publicados and item.get("status") != "publicado":
            item["status"] = "publicado"


def resumo(dados: dict) -> dict:
    """KPIs do topo da aba — calculados aqui para a UI não recalcular."""
    cal = dados.get("calendario", [])
    gmn = dados.get("gmn", {}) or {}
    mt = dados.get("meta", {}) or {}
    ig = mt.get("instagram", {}) or {}
    ravl = gmn.get("resumo_avaliacoes", {}) or {}
    hj = hoje().isoformat()

    return {
        "posts_agendados": sum(1 for c in cal if c.get("status") in ("aprovado", "agendado")),
        "posts_pendentes": sum(1 for c in cal if c.get("status") in ("ideia", "rascunho")),
        "posts_atrasados": sum(
            1 for c in cal
            if c.get("status") in ("aprovado", "agendado") and c.get("data", "9999") < hj
        ),
        "seguidores_ig": ig.get("seguidores", 0),
        "alcance_ig_28d": (ig.get("insights", {}) or {}).get("reach", 0),
        "nota_google": ravl.get("nota_media", 0),
        "avaliacoes_total": ravl.get("total", 0),
        "avaliacoes_sem_resposta": ravl.get("sem_resposta", 0),
        "impressoes_google_30d": (gmn.get("insights", {}) or {}).get("impressoes", 0),
        "rotas_google_30d": (gmn.get("insights", {}) or {}).get("rotas", 0),
        "sugestoes_pendentes": len(dados.get("conteudo_sugerido", [])),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Refresh do módulo de marketing")
    ap.add_argument("--conteudo", action="store_true",
                    help="gera pauta e respostas com Claude (exige ANTHROPIC_API_KEY)")
    ap.add_argument("--dias", type=int, default=7, help="horizonte da pauta (default 7)")
    args = ap.parse_args()

    dados = carregar()
    dados["erros"] = []  # erros são do ciclo atual, não acumulam entre execuções

    for nome, coletor in (("gmn", marketing_gmn.coletar), ("meta", marketing_meta.coletar)):
        try:
            coletor(dados)
        except Exception as e:  # coletor já trata o esperado; isto é a rede de segurança
            registrar_erro(dados, nome, e)

    if args.conteudo:
        try:
            import marketing_content

            marketing_content.executar(dados, dias=args.dias)
        except Exception as e:
            registrar_erro(dados, "claude", e)

    sincronizar_calendario(dados)
    dados["resumo"] = resumo(dados)
    salvar(dados)

    r = dados["resumo"]
    print(
        f"Marketing atualizado · Google: {'ok' if dados['gmn'].get('conectado') else 'off'} "
        f"(nota {r['nota_google']}, {r['avaliacoes_sem_resposta']} sem resposta) · "
        f"Meta: {'ok' if dados['meta'].get('conectado') else 'off'} "
        f"({r['seguidores_ig']} seguidores) · "
        f"{r['posts_pendentes']} pautas pendentes"
    )
    for e in dados.get("erros", []):
        print(f"  ! {e['fonte']}: {e['msg']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
