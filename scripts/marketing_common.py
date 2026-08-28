r"""Utilitários compartilhados do módulo de marketing.

Centraliza paths, leitura/escrita do marketing_data.json e helpers de ambiente.
Nenhum coletor deve escrever o JSON direto — todos passam por aqui.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MKT_JSON = REPO_ROOT / "data" / "marketing_data.json"
DASH_JSON = REPO_ROOT / "data" / "dashboard_data.json"

CANAIS = ["instagram", "facebook", "gmn"]
STATUS = ["ideia", "rascunho", "aprovado", "agendado", "publicado"]


def agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def hoje() -> date:
    return datetime.now(timezone.utc).date()


def env(nome: str, default: str | None = None) -> str | None:
    """Lê env var tratando string vazia como ausente (secret não configurado no Actions)."""
    v = os.environ.get(nome, "")
    v = v.strip()
    return v if v else default


def tem_credenciais(*nomes: str) -> bool:
    return all(env(n) for n in nomes)


def slug(texto: str, limite: int = 40) -> str:
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return (t or "item")[:limite]


def esqueleto() -> dict:
    """Estrutura vazia — usada quando o JSON ainda não existe."""
    return {
        "gerado_em": agora_iso(),
        "config": {
            "nome_negocio": "FAST Escova Limão",
            "meta_posts_semana": 4,
            "meta_avaliacoes_mes": 15,
            "nota_alvo": 4.8,
        },
        "calendario": [],
        "campanhas": [],
        "gmn": {"conectado": False, "perfil": {}, "insights": {}, "avaliacoes": [], "posts": []},
        "meta": {"conectado": False, "instagram": {}, "facebook": {}, "publicacoes": []},
        "conteudo_sugerido": [],
        "erros": [],
    }


def carregar() -> dict:
    if not MKT_JSON.exists():
        return esqueleto()
    try:
        dados = json.loads(MKT_JSON.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return esqueleto()
    # merge defensivo: garante chaves novas em arquivos antigos
    base = esqueleto()
    for k, v in base.items():
        dados.setdefault(k, v)
    return dados


def salvar(dados: dict) -> None:
    dados["gerado_em"] = agora_iso()
    MKT_JSON.parent.mkdir(parents=True, exist_ok=True)
    MKT_JSON.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def carregar_dashboard() -> dict:
    """Dados operacionais do Trinks — usados como insumo para conteúdo."""
    if not DASH_JSON.exists():
        return {}
    try:
        return json.loads(DASH_JSON.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def registrar_erro(dados: dict, fonte: str, msg: str) -> None:
    """Erros são acumulados no JSON (a UI mostra) — coletor nunca derruba o refresh."""
    dados.setdefault("erros", []).append(
        {"fonte": fonte, "msg": str(msg)[:400], "quando": agora_iso()}
    )
    dados["erros"] = dados["erros"][-20:]


def janela(dias: int) -> tuple[date, date]:
    fim = hoje()
    return fim - timedelta(days=dias), fim
