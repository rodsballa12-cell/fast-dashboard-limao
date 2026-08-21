r"""Publicação — a única parte do módulo que escreve para fora.

Tudo aqui é ação explícita e exige --confirmar. Sem a flag o script apenas mostra
o que faria (dry-run), para você conferir o texto antes de ir ao ar.

Uso:
  # ver o que seria publicado
  python scripts/marketing_publicar.py --aprovados
  # publicar de fato
  python scripts/marketing_publicar.py --aprovados --confirmar

  # responder uma avaliação do Google
  python scripts/marketing_publicar.py --responder <review_id> --confirmar
  # responder todas as que já têm rascunho aprovado
  python scripts/marketing_publicar.py --responder-todas --confirmar
"""
from __future__ import annotations

import argparse
import sys

import marketing_gmn
import marketing_meta
from marketing_common import agora_iso, carregar, hoje, registrar_erro, salvar


def _pendentes(dados: dict) -> list[dict]:
    """Itens do calendário aprovados cuja data já chegou."""
    hj = hoje().isoformat()
    return [
        c for c in dados.get("calendario", [])
        if c.get("status") in ("aprovado", "agendado") and c.get("data", "9999") <= hj
    ]


def publicar_item(item: dict, dados: dict, confirmar: bool) -> str:
    canal = item.get("canal")
    texto = item.get("legenda") or item.get("titulo", "")
    tags = " ".join(item.get("hashtags", []) or [])
    corpo = f"{texto}\n\n{tags}".strip()

    if not confirmar:
        return f"[dry-run] {canal} · {item.get('data')} · {corpo[:90]}…"

    if canal == "instagram":
        if not item.get("midia"):
            raise RuntimeError("Instagram exige uma imagem (campo 'midia' com URL pública)")
        m = marketing_meta.Meta()
        r = m.ig_publicar(corpo, item["midia"])
        item["url_publicado"] = r.get("id", "")
    elif canal == "facebook":
        m = marketing_meta.Meta()
        r = m.fb_publicar(corpo, item.get("link", ""))
        item["url_publicado"] = r.get("id", "")
    elif canal == "gmn":
        g = marketing_gmn.GMN()
        account, location = g.resolver_location()
        r = g.publicar_post(account, location, corpo, item.get("midia", ""), item.get("link", ""))
        item["url_publicado"] = r.get("name", "")
    else:
        raise RuntimeError(f"Canal desconhecido: {canal}")

    item["status"] = "publicado"
    item["publicado_em"] = agora_iso()
    return f"publicado em {canal}: {item.get('titulo', '')[:60]}"


def responder(dados: dict, review_id: str | None, todas: bool, confirmar: bool) -> list[str]:
    rascunhos = dados.get("respostas_avaliacoes", [])
    alvos = [r for r in rascunhos if todas or r.get("id") == review_id]
    if not alvos:
        return ["Nenhum rascunho de resposta encontrado para esse filtro"]

    linhas = []
    if not confirmar:
        return [f"[dry-run] responder {r['autor']} ({r['nota']}★): {r['resposta'][:90]}…"
                for r in alvos]

    g = marketing_gmn.GMN()
    account, location = g.resolver_location()
    for r in alvos:
        try:
            g.responder_avaliacao(account, location, r["id"], r["resposta"])
            r["status"] = "publicada"
            r["publicada_em"] = agora_iso()
            for a in dados.get("gmn", {}).get("avaliacoes", []):
                if a.get("id") == r["id"]:
                    a["respondida"] = True
                    a["resposta"] = r["resposta"]
            linhas.append(f"respondida: {r['autor']} ({r['nota']}★)")
        except Exception as e:
            registrar_erro(dados, "gmn/responder", e)
            linhas.append(f"FALHOU {r['autor']}: {str(e)[:120]}")
    return linhas


def main() -> int:
    ap = argparse.ArgumentParser(description="Publica conteúdo aprovado nas redes")
    ap.add_argument("--aprovados", action="store_true", help="publica itens aprovados e vencidos")
    ap.add_argument("--id", help="publica um item específico do calendário pelo id")
    ap.add_argument("--responder", metavar="REVIEW_ID", help="responde uma avaliação do Google")
    ap.add_argument("--responder-todas", action="store_true", help="responde todos os rascunhos")
    ap.add_argument("--confirmar", action="store_true",
                    help="executa de fato — sem esta flag é só simulação")
    args = ap.parse_args()

    dados = carregar()
    saida: list[str] = []

    if args.id:
        alvos = [c for c in dados.get("calendario", []) if c.get("id") == args.id]
        if not alvos:
            print(f"Item {args.id} não encontrado no calendário", file=sys.stderr)
            return 1
    elif args.aprovados:
        alvos = _pendentes(dados)
    else:
        alvos = []

    for item in alvos:
        try:
            saida.append(publicar_item(item, dados, args.confirmar))
        except Exception as e:
            registrar_erro(dados, "publicar", e)
            saida.append(f"FALHOU {item.get('titulo', '')[:40]}: {str(e)[:120]}")

    if args.responder or args.responder_todas:
        saida += responder(dados, args.responder, args.responder_todas, args.confirmar)

    if args.confirmar:
        salvar(dados)

    if not saida:
        saida = ["Nada a publicar. Use --aprovados, --id ou --responder."]
    print("\n".join(saida))
    if not args.confirmar and alvos:
        print("\nSimulação. Repita com --confirmar para publicar de verdade.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
