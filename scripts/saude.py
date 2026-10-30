#!/usr/bin/env python3
"""Saúde das automações — um lugar só para a pergunta "isso ainda funciona?".

Por que existe (23/10/2026): as mídias do Spa ficaram 42 horas paradas e
ninguém soube. Antes disso, 28 pareceres dos cargos saíram vazios por sete dias
seguidos sem um alarme. Sete dos quinze aprendizados em `docs/aprendizados/`
são a mesma falha: **a coisa quebrou sem fazer barulho.**

O vigia que existia media carimbo, não conteúdo — contava commits com `ata:` no
nome, então as 21 atas que diziam "Credit balance is too low" passaram por
saudáveis. E avisava abrindo issue no GitHub, onde o Rodrigo não olha.

Este arquivo responde três coisas, e só elas:

  QUEM rodou · QUANDO · DEU CERTO OU NÃO

Cada automação carimba a sua linha ao terminar, inclusive quando falha. O
painel lê e mostra uma faixa no topo quando algo está velho ou quebrado; a
auditoria lê o mesmo arquivo. Uma fonte, dois leitores.

NÃO entra no cofre: aqui só há nome de automação, horário e ok/falha. Nenhum
dado de cliente. Ficar em texto puro é o que deixa o painel desenhar a faixa
antes mesmo de pedir a senha.

Uso:
  python scripts/saude.py carimbar <nome> <ok|falha> ["detalhe"]
  python scripts/saude.py ler          # imprime o estado, para o olho humano
  python scripts/saude.py conferir     # sai !=0 se algo passou do limite
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# No Windows o console padrao e cp1252 e o ✅/🛑 abaixo derrubava o script;
# a auditoria, que le esta saida por subprocess, recebia vazio e nao acusava nada.
for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RAIZ = Path(__file__).resolve().parent.parent
ARQ = RAIZ / "data" / "saude.json"
BRT = timezone(timedelta(hours=-3))

# Quanto tempo cada automação pode ficar sem rodar antes de virar alarme.
# Os números saem do ritmo real de cada uma, não de chute:
#   refresh  roda de hora em hora das 10h às 21h  -> 3h de folga cobre um pulo
#            do cron e a madrugada nao conta (ver `madrugada_ok`)
#   midias   roda uma vez por dia, de manha       -> 30h cobre um dia pulado
#   conselho roda as 22:30                        -> 30h
LIMITES = {
    "refresh":  {"horas": 3,  "rotulo": "Painel (Trinks)",   "madrugada_ok": True},
    "midias":   {"horas": 30, "rotulo": "Mídias (Meta)",     "madrugada_ok": False},
    "conselho": {"horas": 30, "rotulo": "Conselho da noite", "madrugada_ok": False},
    "cargos":   {"horas": 30, "rotulo": "Pareceres dos cargos", "madrugada_ok": False},
    "stone":    {"horas": 72, "rotulo": "Extrato Stone",     "madrugada_ok": False},
}

# Fora deste intervalo a loja está fechada e o painel não tem o que buscar.
ABRE, FECHA = 9, 22


def _agora() -> datetime:
    return datetime.now(BRT)


def ler_arquivo() -> dict:
    if ARQ.exists():
        try:
            return json.loads(ARQ.read_text(encoding="utf-8"))
        except ValueError:
            pass
    return {"_desc": "Quem rodou, quando, e deu certo. Ver scripts/saude.py.",
            "automacoes": {}}


def carimbar(nome: str, resultado: str, detalhe: str = "") -> int:
    if resultado not in ("ok", "falha"):
        print(f"[saude] resultado tem de ser 'ok' ou 'falha', veio '{resultado}'", file=sys.stderr)
        return 2
    d = ler_arquivo()
    anterior = (d.get("automacoes") or {}).get(nome) or {}
    # "cargos" e carimbado por seis tarefas em sequencia. Sem esta regra, a
    # falha das 07:30 sumia quando a das 09:30 terminava bem.
    if (nome == "cargos" and resultado == "ok" and anterior.get("resultado") == "falha"
            and str(anterior.get("quando", ""))[:10] == _agora().date().isoformat()):
        print(f"[saude] {nome}: mantive a falha de hoje ({anterior.get('detalhe', '')[:60]})")
        return 0
    d.setdefault("automacoes", {})[nome] = {
        "quando": _agora().replace(microsecond=0).isoformat(),
        "resultado": resultado,
        "detalhe": detalhe[:300],
        # Guarda o ultimo SUCESSO separado do ultimo toque. Sem isso, uma
        # automacao que falha de hora em hora pareceria fresca: ela carimba
        # sempre, so que carimba "falha".
        "ultimo_ok": (_agora().replace(microsecond=0).isoformat() if resultado == "ok"
                      else anterior.get("ultimo_ok")),
    }
    d["gerado_em"] = _agora().replace(microsecond=0).isoformat()
    ARQ.parent.mkdir(parents=True, exist_ok=True)
    ARQ.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[saude] {nome} = {resultado}" + (f" · {detalhe[:80]}" if detalhe else ""))
    return 0


def _idade_horas(iso: str | None) -> float | None:
    if not iso:
        return None
    try:
        return (_agora() - datetime.fromisoformat(iso)).total_seconds() / 3600
    except ValueError:
        return None


def avaliar() -> list[dict]:
    """Uma linha por automação, com o veredito. Esta é a função que o painel
    e a auditoria consomem — para as duas dizerem a mesma coisa."""
    d = ler_arquivo()
    agora = _agora()
    fora = not (ABRE <= agora.hour < FECHA)
    out = []
    for nome, cfg in LIMITES.items():
        a = (d.get("automacoes") or {}).get(nome)
        if not a:
            out.append({"nome": nome, "rotulo": cfg["rotulo"], "estado": "sem_carimbo",
                        "texto": f"{cfg['rotulo']}: nunca carimbou"})
            continue
        # Horas desde o ultimo SUCESSO, nao desde o ultimo toque.
        h = _idade_horas(a.get("ultimo_ok"))
        if h is None:
            out.append({"nome": nome, "rotulo": cfg["rotulo"], "estado": "nunca_ok",
                        "texto": f"{cfg['rotulo']}: nunca terminou bem"})
            continue
        if cfg["madrugada_ok"] and fora:
            estado = "ok"          # loja fechada: nada a buscar, nao e alarme
        elif h > cfg["horas"]:
            estado = "velho"
        elif a.get("resultado") == "falha":
            estado = "falhou"      # ja teve sucesso, mas a ultima tentativa quebrou
        else:
            estado = "ok"
        out.append({"nome": nome, "rotulo": cfg["rotulo"], "estado": estado,
                    "horas": round(h, 1), "limite": cfg["horas"],
                    "detalhe": a.get("detalhe") or "",
                    "texto": f"{cfg['rotulo']}: {h:.0f}h sem terminar bem"
                             if estado == "velho" else
                             f"{cfg['rotulo']}: última tentativa falhou"
                             if estado == "falhou" else
                             f"{cfg['rotulo']}: ok"})
    return out


def ler() -> int:
    for l in avaliar():
        marca = {"ok": "✅", "velho": "🛑", "falhou": "⚠️",
                 "sem_carimbo": "❔", "nunca_ok": "🛑"}[l["estado"]]
        print(f"  {marca} {l['texto']}" + (f" · {l['detalhe']}" if l.get("detalhe") else ""))
    return 0


def conferir() -> int:
    ruins = [l for l in avaliar() if l["estado"] in ("velho", "falhou", "nunca_ok")]
    ler()
    if ruins:
        print(f"\n[saude] {len(ruins)} automacao(oes) com problema.")
        return 1
    print("\n[saude] todas em dia.")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "ler"
    if cmd == "carimbar":
        if len(sys.argv) < 4:
            sys.exit(__doc__)
        sys.exit(carimbar(sys.argv[2], sys.argv[3], " ".join(sys.argv[4:])))
    sys.exit({"ler": ler, "conferir": conferir}.get(cmd, lambda: sys.exit(__doc__))())
