#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monta a fila diária de WhatsApp — aniversário e reativação.

Substitui o fluxo antigo de aprovação por issue. Motivo: entre 24/08 e 04/09
foram criados 9 issues de aniversário e 7 nunca foram respondidos. O gate de
aprovação não estava protegendo ninguém — estava sendo o lugar onde o processo
morria. Automatizar sem trava seria o outro extremo, então as travas foram para
o código, onde rodam sozinhas.

Travas aplicadas, nesta ordem:
  1. kill switch      — disparo_wa.ativo = false desliga tudo
  2. campanha ligada  — cada campanha tem seu próprio on/off
  3. opt-out          — telefone na lista nunca recebe, de nada
  4. telefone válido  — E.164 com DDI/DDD plausível
  5. cooldown global  — ninguém recebe 2 mensagens dentro de N dias
  6. cooldown da campanha — aniversário 1x/ano, reativação a cada N dias
  7. teto diário      — protege a qualidade do número na Meta

A janela de horário é responsabilidade do dispatcher, não daqui: a fila pode
ser montada a qualquer hora; o que não pode é ENVIAR fora do horário.

Uso:  python scripts/campanhas_wa.py            # monta data/wa_fila.json
      python scripts/campanhas_wa.py --resumo   # só imprime, não grava
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DASH = REPO / "data" / "dashboard_data.json"
CONFIG = REPO / "data" / "config.json"
HIST = REPO / "data" / "wa_historico.json"
FILA = REPO / "data" / "wa_fila.json"
BRT = timezone(timedelta(hours=-3))

PADRAO = {
    "ativo": False,                    # kill switch — precisa ser ligado de propósito
    "teto_diario": 20,
    "cooldown_global_dias": 14,
    "janela_envio": {"inicio": 9, "fim": 20},
    "opt_out": [],
    "campanhas": {
        "aniversario": {
            "ativo": True,
            "cooldown_dias": 300,      # ~1x por ano
            "teto_diario": 10,
            "template": "aniversario_fast_v1",
            "lingua": "pt_BR",
        },
        "reativacao": {
            "ativo": True,
            "cooldown_dias": 45,
            "teto_diario": 5,          # gotejamento: a recepção precisa dar conta de responder
            "min_visitas": 3,
            "min_dias_sem_vir": 14,
            "max_dias_sem_vir": 120,
            "template": "reativacao_fast_v1",
            "lingua": "pt_BR",
        },
    },
}


def _merge(base: dict, novo: dict) -> dict:
    """Merge raso-recursivo: config do usuário sobrescreve o padrão."""
    out = dict(base)
    for k, v in (novo or {}).items():
        out[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def e164(telefone: str) -> str | None:
    """+55 (11) 99123-0296 → 5511991230296. None se não der para confiar."""
    if not telefone:
        return None
    d = re.sub(r"\D", "", telefone)
    if not d.startswith("55"):
        d = "55" + d
    # 55 + DDD(2) + numero(8 ou 9)
    if not (12 <= len(d) <= 13):
        return None
    return d


def chave(tel_e164: str) -> str:
    """Identificador estável e não reversível, porque o repositório é público.

    O histórico precisa saber "esta pessoa já recebeu?" — não precisa saber
    quem ela é. Guardar o hash resolve o dedup sem publicar mais telefone do
    que o que já existe nos outros arquivos.
    """
    return hashlib.sha256(tel_e164.encode()).hexdigest()[:16]


def carregar_hist() -> dict:
    if not HIST.exists():
        return {"envios": []}
    try:
        return json.loads(HIST.read_text(encoding="utf-8"))
    except Exception:
        return {"envios": []}


def dias_desde(hist: dict, k: str, campanha: str | None, hoje: date) -> int | None:
    """Dias desde o último envio para esta pessoa (na campanha, ou em qualquer)."""
    melhor = None
    for e in hist.get("envios", []):
        if e.get("chave") != k or e.get("status") != "enviado":
            continue
        if campanha and e.get("campanha") != campanha:
            continue
        try:
            d = (hoje - date.fromisoformat(e["data"])).days
        except Exception:
            continue
        melhor = d if melhor is None else min(melhor, d)
    return melhor


def msg_aniversario(nome: str, cfg: dict) -> tuple[str, list[str]]:
    p = cfg.get("presente_nome", "Escova grátis")
    v = str(cfg.get("validade_dias", 15))
    texto = (f"Feliz aniversário, {nome}! 🎂✨\n\n"
             f"A {cfg.get('loja_nome','FAST Limão')} preparou um presente pra você: {p}, "
             f"válido pelos próximos {v} dias.\n\n"
             f"É só aparecer aqui na loja pra comemorar com a gente 💛\n"
             f"{cfg.get('loja_endereco_curto','')}\n\n— {cfg.get('assinatura','Equipe')}")
    return texto, [nome, p, v]


def msg_reativacao(nome: str, cfg: dict) -> tuple[str, list[str]]:
    # Sem desconto de propósito: são clientes que voltaram 3+ vezes pagando o
    # preço cheio. Abrir com promoção ensina a esperar promoção.
    texto = (f"Oi, {nome}! Tudo bem? 💛\n\n"
             f"Faz um tempinho que você não aparece aqui na "
             f"{cfg.get('loja_nome','FAST Limão')} e a gente sentiu falta.\n\n"
             f"Se quiser dar uma passada essa semana, é só chegar — sem hora marcada.\n"
             f"{cfg.get('loja_endereco_curto','')}\n\n— {cfg.get('assinatura','Equipe')}")
    return texto, [nome]


def main() -> int:
    if not DASH.exists():
        print("[wa] dashboard_data.json ausente — nada a fazer")
        return 0
    dash = json.loads(DASH.read_text(encoding="utf-8"))
    cfg_all = json.loads(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else {}
    cfg = _merge(PADRAO, cfg_all.get("disparo_wa", {}))
    camp_cfg = cfg_all.get("aniversario_campanha", {})
    hoje = datetime.now(BRT).date()
    hist = carregar_hist()
    opt_out = {e164(t) for t in cfg.get("opt_out", []) if e164(t)}

    fila: list[dict] = []
    recusas: dict[str, int] = {}
    def recusa(motivo):
        recusas[motivo] = recusas.get(motivo, 0) + 1

    if not cfg.get("ativo"):
        print("[wa] disparo_wa.ativo = false — fila montada vazia (kill switch)")

    anual = (dash.get("abas") or {}).get("anual") or {}
    candidatos: list[tuple[str, dict]] = []
    if cfg["campanhas"]["aniversario"].get("ativo"):
        for c in anual.get("aniversariantes") or []:
            if c.get("dias") == 0:
                candidatos.append(("aniversario", c))
    if cfg["campanhas"]["reativacao"].get("ativo"):
        rc = cfg["campanhas"]["reativacao"]
        for c in ((anual.get("churn_early") or {}).get("top") or []):
            if (c.get("n_visitas", 0) >= rc["min_visitas"]
                    and rc["min_dias_sem_vir"] <= c.get("dias_sem_vir", 0) <= rc["max_dias_sem_vir"]):
                candidatos.append(("reativacao", c))
    # Maior LTV primeiro dentro de cada campanha — se o teto cortar, corta o de menor valor
    candidatos.sort(key=lambda x: (x[0] != "aniversario", -(x[1].get("ltv") or 0)))

    por_campanha: dict[str, int] = {}
    vistos: set[str] = set()
    for campanha, c in candidatos:
        if not cfg.get("ativo"):
            recusa("kill switch desligado"); continue
        tel = e164(c.get("telefone", ""))
        if not tel:
            recusa("telefone inválido"); continue
        if tel in opt_out:
            recusa("opt-out"); continue
        k = chave(tel)
        if k in vistos:
            recusa("já está na fila de hoje"); continue
        d_glob = dias_desde(hist, k, None, hoje)
        if d_glob is not None and d_glob < cfg["cooldown_global_dias"]:
            recusa(f"cooldown global ({d_glob}d < {cfg['cooldown_global_dias']}d)"); continue
        cc = cfg["campanhas"][campanha]
        d_camp = dias_desde(hist, k, campanha, hoje)
        if d_camp is not None and d_camp < cc["cooldown_dias"]:
            recusa(f"cooldown de {campanha} ({d_camp}d)"); continue
        if por_campanha.get(campanha, 0) >= cc["teto_diario"]:
            recusa(f"teto diário de {campanha}"); continue
        if len(fila) >= cfg["teto_diario"]:
            recusa("teto diário global"); continue

        nome = (c.get("cliente") or "").split()[0].title() or "tudo bem"
        texto, params = (msg_aniversario if campanha == "aniversario" else msg_reativacao)(nome, camp_cfg)
        fila.append({
            "id": len(fila) + 1, "campanha": campanha, "cliente": c.get("cliente", ""),
            "telefone_e164": tel, "chave": k, "ltv": c.get("ltv", 0),
            "n_visitas": c.get("n_visitas", 0), "dias_sem_vir": c.get("dias_sem_vir"),
            "mensagem": texto, "template": cc["template"], "lingua": cc["lingua"],
            "params": params,
        })
        vistos.add(k)
        por_campanha[campanha] = por_campanha.get(campanha, 0) + 1

    payload = {
        "gerado_em": datetime.now(BRT).isoformat(timespec="seconds"),
        "data": hoje.isoformat(),
        "ativo": bool(cfg.get("ativo")),
        "janela_envio": cfg["janela_envio"],
        "total": len(fila),
        "por_campanha": por_campanha,
        "recusas": recusas,
        "fila": fila,
    }
    if "--resumo" not in sys.argv:
        FILA.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[wa] {hoje} · fila com {len(fila)} mensagem(ns) · {por_campanha or '—'}")
    for motivo, n in sorted(recusas.items(), key=lambda x: -x[1]):
        print(f"      descartado: {motivo} ({n})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
