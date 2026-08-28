r"""Gerador de conteúdo com Claude, ancorado nos dados reais do Trinks.

Duas saídas:
  1. Pauta de posts para os próximos dias — cada ideia justificada por um número
     real do painel (serviço campeão, horário ocioso, meta do mês, ticket médio).
  2. Rascunhos de resposta para avaliações do Google ainda sem réplica.

Nada é publicado automaticamente: tudo entra como sugestão para aprovação na aba
Marketing. Publicar é ação explícita (marketing_publicar.py).

Env var necessária: ANTHROPIC_API_KEY
"""
from __future__ import annotations

import json
import sys
from datetime import timedelta

from marketing_common import agora_iso, carregar, carregar_dashboard, env, hoje, registrar_erro, salvar

MODELO = "claude-opus-5"
BETA_FALLBACK = "server-side-fallback-2026-07-01"

SISTEMA = """Você é o gestor de marketing da FAST Escova Limão, franquia de beleza \
express em São Paulo (bairro do Limão). Serviços rápidos: escova, chapinha, hidratação, \
manicure/pedicure. Público: mulheres da região, entre 25 e 55 anos, que valorizam \
rapidez, preço justo e resultado imediato.

Regras de escrita:
- Português do Brasil, tom próximo e direto — nada de linguagem corporativa.
- Sem promessas de resultado que a loja não controla; sem preço inventado.
- Emojis com parcimônia (no máximo 2 por post).
- Toda pauta precisa se apoiar num número real fornecido nos dados.
- Legenda de Instagram: até 500 caracteres. Post do Google: até 700 caracteres.
"""

SCHEMA_POSTS = {
    "type": "object",
    "properties": {
        "posts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "canal": {"type": "string", "enum": ["instagram", "facebook", "gmn"]},
                    "data": {"type": "string", "description": "AAAA-MM-DD"},
                    "tipo": {"type": "string", "enum": ["feed", "reels", "story", "post_google"]},
                    "titulo": {"type": "string"},
                    "legenda": {"type": "string"},
                    "hashtags": {"type": "array", "items": {"type": "string"}},
                    "cta": {"type": "string"},
                    "porque": {
                        "type": "string",
                        "description": "O dado real que justifica esta pauta",
                    },
                },
                "required": ["canal", "data", "tipo", "titulo", "legenda", "hashtags", "cta", "porque"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["posts"],
    "additionalProperties": False,
}

SCHEMA_RESPOSTAS = {
    "type": "object",
    "properties": {
        "respostas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "autor": {"type": "string"},
                    "nota": {"type": "integer"},
                    "resposta": {"type": "string"},
                },
                "required": ["id", "autor", "nota", "resposta"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["respostas"],
    "additionalProperties": False,
}


def _cliente():
    import anthropic  # import tardio: o refresh roda sem a lib se não houver chave

    return anthropic.Anthropic()


def _chamar(client, prompt: str, schema: dict) -> dict:
    """Uma chamada com saída estruturada. Tenta o fallback server-side; se o beta
    não estiver liberado na conta, repete na rota padrão."""
    import anthropic

    comum = dict(
        model=MODELO,
        max_tokens=16000,
        system=SISTEMA,
        thinking={"type": "adaptive"},
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": prompt}],
    )
    try:
        resp = client.beta.messages.create(
            **comum, betas=[BETA_FALLBACK], fallbacks="default"
        )
    except anthropic.BadRequestError:
        resp = client.messages.create(**comum)

    if getattr(resp, "stop_reason", None) == "refusal":
        detalhe = getattr(resp, "stop_details", None)
        raise RuntimeError(f"Pedido recusado pelo modelo: {getattr(detalhe, 'category', '?')}")

    texto = next((b.text for b in resp.content if b.type == "text"), "")
    if not texto:
        raise RuntimeError("Resposta sem bloco de texto")
    return json.loads(texto)


def _contexto(dash: dict, mkt: dict) -> str:
    """Resumo compacto dos números que importam para a pauta."""
    m = (dash.get("abas", {}) or {}).get("mensal", {}) or {}
    kpis = m.get("kpis", {}) or {}
    meta = m.get("meta", {}) or {}
    serv = (m.get("ranking_serv") or [])[:6]
    rent = (m.get("rentabilidade_hora") or [])[:5]
    horas = m.get("hora_media") or []
    nvr = m.get("novos_vs_recorr", {}) or {}

    ociosas = sorted(horas, key=lambda h: h.get("media", 0))[:4]
    gmn = mkt.get("gmn", {}) or {}
    resumo_gmn = gmn.get("resumo_avaliacoes", {}) or {}
    ig = (mkt.get("meta", {}) or {}).get("instagram", {}) or {}
    ultimas = [p.get("legenda", "")[:120] for p in (mkt.get("meta", {}) or {}).get("publicacoes", [])[:6]]

    linhas = [
        f"DATA DE HOJE: {hoje().isoformat()}",
        "",
        "DESEMPENHO DO MÊS (Trinks, dados reais):",
        f"- Caixa: R$ {kpis.get('caixa', 0):,.2f} · meta R$ {meta.get('meta', 0):,.0f} "
        f"({meta.get('pct', 0)}% atingido, faltam R$ {meta.get('falta', 0):,.0f} "
        f"em {meta.get('dias_restantes', 0)} dias úteis)",
        f"- Ticket médio: R$ {kpis.get('ticket_trans', 0):,.2f} · "
        f"{kpis.get('atend_fin', 0)} atendimentos · {kpis.get('clientes_unicos', 0)} clientes únicos",
        f"- Taxa de cancelamento: {kpis.get('taxa_canc', 0)}%",
        f"- Clientes novos: {(nvr.get('novos') or {}).get('clientes', 0)} · "
        f"recorrentes: {(nvr.get('recorrentes') or {}).get('clientes', 0)}",
        "",
        "SERVIÇOS MAIS VENDIDOS:",
    ]
    linhas += [f"- {s['nome']}: {s['n']} vendas, R$ {s['v']:,.2f}" for s in serv]
    linhas += ["", "MAIOR RECEITA POR HORA (serviços que valem empurrar):"]
    linhas += [f"- {s['nome']}: R$ {s.get('rs_hora', 0):,.0f}/h, ticket R$ {s.get('ticket', 0):,.2f}"
               for s in rent]
    linhas += ["", "HORÁRIOS MAIS OCIOSOS (média de atendimentos por dia):"]
    linhas += [f"- {h['h']}h: {h.get('media', 0)} atendimentos/dia" for h in ociosas]

    if resumo_gmn:
        linhas += [
            "",
            f"GOOGLE MEU NEGÓCIO: nota {resumo_gmn.get('nota_media')} · "
            f"{resumo_gmn.get('total')} avaliações · {resumo_gmn.get('sem_resposta')} sem resposta",
        ]
    if ig.get("seguidores"):
        linhas += [f"INSTAGRAM: @{ig.get('usuario')} · {ig.get('seguidores')} seguidores · "
                   f"alcance 28d: {(ig.get('insights') or {}).get('reach', 'n/d')}"]
    if ultimas:
        linhas += ["", "ÚLTIMAS LEGENDAS PUBLICADAS (não repetir o ângulo):"]
        linhas += [f"- {t}" for t in ultimas]
    return "\n".join(linhas)


def gerar_pauta(dados: dict, dias: int = 7, por_dia: int = 1) -> list[dict]:
    dash = carregar_dashboard()
    ctx = _contexto(dash, dados)
    fim = hoje() + timedelta(days=dias)
    prompt = f"""{ctx}

Monte a pauta de conteúdo de {hoje().isoformat()} até {fim.isoformat()} \
({dias} dias), com cerca de {por_dia} publicação por dia.

Distribua entre Instagram (a maioria), Facebook e Google Meu Negócio. Varie os \
ângulos: prova social, serviço campeão, horário ocioso com convite explícito, \
bastidores da equipe, educativo rápido. Se falta muito para a meta do mês, \
priorize pautas de conversão em vez de institucional.

O campo "porque" deve citar o número concreto que motivou a pauta."""

    client = _cliente()
    out = _chamar(client, prompt, SCHEMA_POSTS)
    posts = out.get("posts", [])
    for i, p in enumerate(posts):
        p["id"] = f"sug-{hoje().isoformat()}-{i + 1}"
        p["status"] = "ideia"
        p["origem"] = "claude"
        p["gerado_em"] = agora_iso()
    return posts


def gerar_respostas(dados: dict, limite: int = 10) -> list[dict]:
    pendentes = [
        a for a in (dados.get("gmn", {}) or {}).get("avaliacoes", []) if not a.get("respondida")
    ][:limite]
    if not pendentes:
        return []

    bloco = json.dumps(
        [{"id": a["id"], "autor": a["autor"], "nota": a["nota"], "texto": a["texto"]}
         for a in pendentes],
        ensure_ascii=False,
        indent=2,
    )
    prompt = f"""Avaliações do Google ainda sem resposta:

{bloco}

Escreva a resposta pública de cada uma. Regras:
- Máximo 350 caracteres por resposta.
- Cite algo específico do que a pessoa escreveu — nada de resposta genérica.
- Use o primeiro nome de quem avaliou.
- Nota 1-3: reconheça o problema sem se defender, e convide para resolver pelo \
telefone da loja. Não ofereça desconto nem reembolso.
- Nota 4-5: agradeça e convide para voltar, mencionando um serviço que faça sentido.
- Assine como "Equipe FAST Limão"."""

    client = _cliente()
    out = _chamar(client, prompt, SCHEMA_RESPOSTAS)
    respostas = out.get("respostas", [])
    for r in respostas:
        r["status"] = "rascunho"
        r["gerado_em"] = agora_iso()
    return respostas


def executar(dados: dict, dias: int = 7) -> dict:
    """Preenche conteudo_sugerido e respostas_avaliacoes. Falha não derruba o refresh."""
    if not env("ANTHROPIC_API_KEY"):
        dados["conteudo_sugerido"] = dados.get("conteudo_sugerido", [])
        dados["motivo_conteudo"] = "ANTHROPIC_API_KEY não configurada"
        return dados

    try:
        dados["conteudo_sugerido"] = gerar_pauta(dados, dias=dias)
        dados.pop("motivo_conteudo", None)
    except Exception as e:  # inclui erros da API — não pode derrubar o refresh
        registrar_erro(dados, "claude/pauta", e)
        dados["motivo_conteudo"] = str(e)[:200]

    try:
        dados["respostas_avaliacoes"] = gerar_respostas(dados)
    except Exception as e:
        registrar_erro(dados, "claude/respostas", e)
    return dados


def main() -> int:
    dados = carregar()
    executar(dados)
    salvar(dados)
    print(f"Pauta: {len(dados.get('conteudo_sugerido', []))} sugestões · "
          f"Respostas: {len(dados.get('respostas_avaliacoes', []))} rascunhos")
    if dados.get("motivo_conteudo"):
        print(f"Aviso: {dados['motivo_conteudo']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
