"""
Sincroniza um briefing de Conselho em Briefings/AAAA-MM-DD-conselho.md com o
dashboard: atualiza historico_conselhos[] em Escova/SPA/Consolidado,
adiciona recomendacoes[] "aprovadas" (uma por Decisão do Rodrigo), grava a
ata em docs/atas/ e uma decisão individual por arquivo em docs/decisoes/.

Modo AUTO (escolha do Rodrigo em 15/09/2026): todas as decisões viram
recomendação com status="aprovada" direto, sem confirmação manual. Fica no
Plano de Ação · Mídia com badge "aprovada · aguarda execução". Se depois
o Rodrigo mudar de ideia, ele roda /sincronizar manualmente pra
sobrescrever.

Uso:
  python scripts/sync_conselho.py Briefings/2026-09-14-conselho.md
  python scripts/sync_conselho.py --auto-latest   # pega o mais recente

Idempotente: se historico_conselhos[] já tem um bloco {data,hora,tipo}
igual, não aplica de novo.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIEFINGS_DIR = ROOT / "Briefings"
DATA_ESCOVA = ROOT / "data" / "midias_sociais.json"
DATA_SPA = ROOT / "data" / "spa" / "midias_sociais.json"
DATA_CONS = ROOT / "data" / "consolidado" / "midias_sociais.json"
DECISOES_DIR = ROOT / "docs" / "decisoes"
ATAS_DIR = ROOT / "docs" / "atas"


def brt_iso() -> str:
    return datetime.now(timezone(timedelta(hours=-3))).replace(microsecond=0).isoformat()


def slugify(txt: str, max_len: int = 40) -> str:
    """Slug simples: minúsculas, sem acento, hífen entre palavras."""
    import unicodedata
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
    txt = re.sub(r"[^\w\s-]", "", txt).strip().lower()
    txt = re.sub(r"[\s_]+", "-", txt)
    return txt[:max_len].strip("-") or "sem-titulo"


def fix_mojibake(text: str) -> str:
    """Reverte mojibake UTF-8→X→UTF-8 onde X pode ser cp850 (DOS Latin-1,
    usado por Windows Terminal em pt-BR), cp1252 (Windows ANSI) ou latin1.
    Prova cada um e devolve o que zera os artefatos box-drawing típicos
    (├, ─, ┼, Ô, ƒ). Se nenhum limpar, retorna original."""
    for enc in ("cp850", "cp1252", "latin1"):
        try:
            fixed = text.encode(enc, errors="replace").decode("utf-8", errors="replace")
        except Exception:
            continue
        # Bom fix reduz drasticamente os artefatos
        artef_orig = sum(text.count(c) for c in ("├", "─", "┼", "Ô", "ƒ", "Ü", "Ç"))
        artef_fix = sum(fixed.count(c) for c in ("├", "─", "┼", "Ô", "ƒ", "Ü", "Ç"))
        if artef_fix < artef_orig / 3:  # reduziu pelo menos 66%
            return fixed
    return text


def parse_briefing(path: Path) -> dict:
    """Extrai os campos estruturados do briefing. Robusto a variações de
    emoji e mojibake."""
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        raw = path.read_bytes().decode("cp1252", errors="replace")

    # Reverte mojibake se detectar chars box-drawing / diacríticos raros PT-BR
    if any(c in raw for c in ("├", "─", "┼", "Ô", "ƒ")):
        raw = fix_mojibake(raw)

    # data + hora do frontmatter YAML simples (ou nome do arquivo)
    data_iso = None
    hora = "22:30"
    m = re.search(r"^data:\s*(\S+)", raw, re.MULTILINE)
    if m:
        data_iso = m.group(1).strip()
    else:
        m = re.match(r"(\d{4}-\d{2}-\d{2})", path.stem)
        if m:
            data_iso = m.group(1)
    m = re.search(r"^hora:\s*(\S+)", raw, re.MULTILINE)
    if m:
        hora = m.group(1).strip()

    # Situação da mesa: cor por departamento. Aceita 🔴🟡🟢 ou tokens texto.
    mesa = {}
    for cargo, keys in [
        ("operacao", ["Operacao", "Operação"]),
        ("financeiro", ["Financeiro"]),
        ("marketing", ["Marketing"]),
        ("relacionamento", ["Relacionamento"]),
        ("pessoas", ["Pessoas"]),
    ]:
        for k in keys:
            m = re.search(rf"{k}\s*([^\n]+)", raw)
            if m:
                linha = m.group(1)
                if "🔴" in linha or "critico" in linha.lower() or "crítico" in linha.lower():
                    mesa[cargo] = "critico"
                elif "🟡" in linha or "atenc" in linha.lower():
                    mesa[cargo] = "atencao"
                elif "🟢" in linha or "ok" in linha.lower():
                    mesa[cargo] = "ok"
                break

    # Decisões: procura seção "DECISÕES DO RODRIGO" ou similar, extrai 1./2./3.
    decisoes = []
    dec_sec = re.search(
        r"(DECIS[OÕ]ES\s+DO\s+RODRIGO[^\n]*\n)(.*?)(?=\n(?:[🕳🕳️]|PERGUNTAS|MEMÓRIA|MEMORIA|📌|$))",
        raw, re.DOTALL | re.IGNORECASE
    )
    if dec_sec:
        bloco = dec_sec.group(2)
        # Aceita "1." ou "1)" no início da linha
        for m in re.finditer(r"^\s*(\d+)[.)]\s*(.+?)(?=\n\s*\d+[.)]|\n\s*$|\Z)", bloco, re.DOTALL | re.MULTILINE):
            n = int(m.group(1))
            texto_raw = m.group(2).strip().replace("\n", " ")
            texto_raw = re.sub(r"\s+", " ", texto_raw)
            # Título é o que vem antes do primeiro "·"
            partes = [p.strip() for p in texto_raw.split("·")]
            titulo = partes[0]
            em_jogo = ""
            executor = None
            for p in partes[1:]:
                pl = p.lower()
                if pl.startswith("em jogo"):
                    em_jogo = p.split(":", 1)[-1].strip()
                elif pl.startswith("executa"):
                    executor = p.split(":", 1)[-1].strip().rstrip(".")
            decisoes.append({
                "n": n,
                "titulo": titulo,
                "texto_completo": texto_raw,
                "em_jogo": em_jogo,
                "executor": executor,
            })
        decisoes = decisoes[:3]

    # Cruzamentos: bullets após "SÓ APARECE NO CRUZAMENTO" ou similar
    cruzamentos = []
    m = re.search(r"CRUZAMENTO[^\n]*\n(.*?)(?=\n(?:🎯|DECIS|PERGUNTAS|MEM))", raw, re.DOTALL | re.IGNORECASE)
    if m:
        for linha in m.group(1).splitlines():
            linha = linha.strip()
            if linha.startswith(("•", "-", "*", "·")):
                cruzamentos.append(linha.lstrip("•-*· ").strip())

    # Sem-dono: bullets em "PERGUNTAS SEM DONO"
    sem_dono = []
    m = re.search(r"PERGUNTAS\s+SEM\s+DONO[^\n]*\n(.*?)(?=\n(?:📌|MEM|$))", raw, re.DOTALL | re.IGNORECASE)
    if m:
        for linha in m.group(1).splitlines():
            linha = linha.strip()
            if linha.startswith(("•", "-", "*", "·")):
                sem_dono.append(linha.lstrip("•-*· ").strip())

    return {
        "data": data_iso,
        "hora": hora,
        "tipo": "noturno" if hora >= "18:00" else "matinal",
        "mesa": mesa,
        "decisoes": decisoes,
        "cruzamentos_chave": cruzamentos,
        "sem_dono": sem_dono,
        "raw": raw,
    }


def bloco_historico(parsed: dict, decisoes_docs: dict[int, str]) -> dict:
    """Monta o dict pra append em historico_conselhos[]."""
    return {
        "data": parsed["data"],
        "hora": parsed["hora"],
        "tipo": parsed["tipo"],
        "sincronizado_em": brt_iso(),
        "sincronizado_por": "auto (workflow conselho_sync.yml)",
        "ata": f"docs/atas/{parsed['data']}-conselho.md",
        "mesa": parsed["mesa"],
        "decisoes": [
            {
                "n": d["n"],
                "titulo": d["titulo"],
                "em_jogo": d["em_jogo"],
                "executor": d["executor"],
                "status": "aprovada",
                "revisao_em": None,
                "docs_decisao": decisoes_docs.get(d["n"]),
            }
            for d in parsed["decisoes"]
        ],
        "cruzamentos_chave": parsed["cruzamentos_chave"],
        "sem_dono": parsed["sem_dono"],
    }


def rec_from_decisao(d: dict, docs_path: str, parsed: dict) -> dict:
    """Uma recomendação por decisão, marcada 'aprovada'. Vira card no
    Plano de Ação · Mídia."""
    return {
        "sev": "warn",
        "titulo": f"[Conselho {parsed['data']}] {d['titulo']}",
        "detalhe": (d["em_jogo"] or d["texto_completo"])[:400],
        "acao": f"Executar: {d['executor']}." if d["executor"] else "Executor a definir.",
        "status": "aprovada",
        "aprovada_em": parsed["data"],
        "revisao_em": None,
        "docs_decisao": docs_path,
        "origem_conselho": parsed["data"],
    }


def ja_sincronizado(hc: list, parsed: dict) -> bool:
    return any(
        h.get("data") == parsed["data"]
        and h.get("hora") == parsed["hora"]
        and h.get("tipo") == parsed["tipo"]
        for h in hc
    )


def write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def escrever_decisoes_e_ata(parsed: dict) -> dict[int, str]:
    """Grava 1 md por decisão + 1 ata. Retorna map n → path relativo."""
    DECISOES_DIR.mkdir(parents=True, exist_ok=True)
    ATAS_DIR.mkdir(parents=True, exist_ok=True)
    data = parsed["data"]
    docs_map = {}

    for d in parsed["decisoes"]:
        slug = slugify(d["titulo"])
        fname = f"{data}-conselho-{slug}.md"
        fpath = DECISOES_DIR / fname
        rel = f"docs/decisoes/{fname}"
        docs_map[d["n"]] = rel
        if fpath.exists():
            continue  # idempotente
        conteudo = f"""# Conselho {data} · Decisão #{d['n']} · {d['titulo']}

**Data:** {data} · **Hora do Conselho:** {parsed['hora']}
**Origem:** Conselho {parsed['tipo']} · Sincronizada automaticamente pelo
workflow `conselho_sync.yml`
**Status inicial:** aprovada (modo auto — Rodrigo não desabilitou)

## Em jogo

{d['em_jogo'] or '(não capturado do briefing)'}

## Texto original do briefing

> {d['texto_completo']}

## Executor

{d['executor'] or 'A definir'}

## Como sobrescrever

Se você mudou de ideia sobre esta decisão, rode `/sincronizar` manualmente
e responda com o status real (recusada/reprogramada/executada). Isso
sobrescreve o registro automático.

## Revisão

Sem prazo automático. Volte a esta decisão no próximo Conselho.

## Resultado

_(em branco até a revisão)_
"""
        fpath.write_text(conteudo, encoding="utf-8")

    # Ata
    ata_path = ATAS_DIR / f"{data}-conselho.md"
    if not ata_path.exists():
        mesa_lines = "\n".join(
            f"| {cargo.capitalize()} | {cor} |" for cargo, cor in parsed["mesa"].items()
        ) or "| — | — |"
        dec_lines = "\n".join(
            f"| {d['n']} | {d['titulo']} | aprovada (auto) | [{docs_map[d['n']].split('/')[-1]}]({os.path.relpath(docs_map[d['n']], 'docs/atas')}) |"
            for d in parsed["decisoes"]
        )
        cruz = "\n".join(f"- {c}" for c in parsed["cruzamentos_chave"]) or "_(sem cruzamentos capturados)_"
        sem = "\n".join(f"- {s}" for s in parsed["sem_dono"]) or "_(sem perguntas sem dono capturadas)_"
        ata_content = f"""# Ata · Conselho FAST Limão · {data} {parsed['hora']}

**Tipo:** {parsed['tipo']}
**Sincronização:** automática pelo workflow `conselho_sync.yml` em {brt_iso()}

## Mesa

| Cadeira | Status |
|---|---|
{mesa_lines}

## Decisões

| # | Título | Status | Decisão individual |
|---|---|---|---|
{dec_lines}

## Cruzamentos-chave

{cruz}

## Perguntas sem dono

{sem}

## Como intervir

Se alguma decisão foi tomada erroneamente como aprovada, rode
`/sincronizar` manualmente pra corrigir os status.

## Resultado

_(em branco até a revisão)_
"""
        ata_path.write_text(ata_content, encoding="utf-8")

    return docs_map


DIRECIONAMENTO_WA = {
    "prioridade": "P2",
    "titulo": "❌ WhatsApp Cloud API descontinuado no curto prazo",
    "descoberta": "Rodrigo sem admin do portfolio Meta pra recriar App apagado — decidido no Conselho 14/09",
    "acao": "Priorizar CRM via canal alternativo (HubSpot standalone, telefone, WhatsApp Web pessoal). Reavaliar só se acesso admin for concedido.",
    "impacto_estimado": "58 clientes em risco seguem sem canal automatizado de mensagem",
}


def aplicar_json(path: Path, parsed: dict, docs_map: dict[int, str], is_escova: bool) -> str:
    if not path.exists():
        return f"SKIP {path} (nao existe)"
    d = load_json(path)
    hc = d.get("historico_conselhos") or []
    if ja_sincronizado(hc, parsed):
        return f"SKIP {path.name} · ja sincronizado ({parsed['data']} {parsed['hora']})"

    hc.append(bloco_historico(parsed, docs_map))
    d["historico_conselhos"] = hc

    # recomendações "aprovadas" — 1 por decisão
    rec = d.get("recomendacoes") or []
    for dec in parsed["decisoes"]:
        rec.append(rec_from_decisao(dec, docs_map[dec["n"]], parsed))
    d["recomendacoes"] = rec

    write_json(path, d)
    return f"OK   {path.name} · +{len(parsed['decisoes'])} recomendacoes · +1 historico"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("briefing", nargs="?", help="Path do briefing (Briefings/AAAA-MM-DD-conselho.md)")
    ap.add_argument("--auto-latest", action="store_true", help="Pega o briefing mais recente em Briefings/")
    args = ap.parse_args()

    if args.auto_latest:
        candidatos = sorted(BRIEFINGS_DIR.glob("*-conselho.md"), reverse=True)
        if not candidatos:
            print("ERRO: nenhum briefing em Briefings/", file=sys.stderr)
            return 1
        briefing = candidatos[0]
    elif args.briefing:
        briefing = Path(args.briefing)
        if not briefing.is_absolute():
            briefing = ROOT / briefing
    else:
        print("ERRO: passe o briefing ou use --auto-latest", file=sys.stderr)
        return 2

    if not briefing.exists():
        print(f"ERRO: briefing nao encontrado: {briefing}", file=sys.stderr)
        return 3

    print(f"[sync_conselho] lendo {briefing.relative_to(ROOT)}")
    parsed = parse_briefing(briefing)
    if not parsed["data"] or not parsed["decisoes"]:
        print(f"ERRO: briefing sem data ou decisoes parseaveis (data={parsed['data']}, decisoes={len(parsed['decisoes'])})", file=sys.stderr)
        return 4

    print(f"  data={parsed['data']} hora={parsed['hora']} tipo={parsed['tipo']}")
    print(f"  mesa={parsed['mesa']}")
    print(f"  decisoes={len(parsed['decisoes'])}: {[d['titulo'][:40] for d in parsed['decisoes']]}")

    docs_map = escrever_decisoes_e_ata(parsed)
    print(f"  docs/decisoes: {list(docs_map.values())}")
    print(f"  docs/atas: docs/atas/{parsed['data']}-conselho.md")

    for path, is_escova in [(DATA_ESCOVA, True), (DATA_SPA, False), (DATA_CONS, False)]:
        print(" ", aplicar_json(path, parsed, docs_map, is_escova))

    return 0


if __name__ == "__main__":
    sys.exit(main())
