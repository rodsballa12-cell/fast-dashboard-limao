#!/usr/bin/env python3
"""Decisões sem resultado — tornar a NÃO-EXECUÇÃO visível.

Por que existe (23/10/2026): as três primeiras peças de saúde cuidam de
"a máquina parou". Esta cuida de "a máquina avisou e nada aconteceu", que
custa mais caro e não aparece em lugar nenhum.

A prova está no próprio repositório. A decisão sobre clientes sumidos foi
tomada em 11/10, 16/10, 17/10 e de novo em 20/10 — quatro vezes, com dono
nomeado e meta diária — e nenhuma ligação foi confirmada. O alarme tocou
todas as noites. Não faltou detecção; faltou execução, e a falta de execução
não tinha onde aparecer.

Medindo os 85 arquivos de `docs/decisoes/`:

    com "## Resultado" preenchido :  3
    com "## Resultado" em branco  : 81

A estrutura certa já existia — Executor, Em jogo, Revisão, Resultado. Ninguém
fecha o ciclo. Este script não inventa processo novo: ele conta o que já está
escrito e põe o número onde o Rodrigo olha.

O que NÃO faz, de propósito: não verifica se a decisão foi cumprida. Isso
exigiria uma regra escrita à mão por decisão, que envelhece e mente. Ele mede
o que é verdade para todas — há quanto tempo está aberta e se alguém registrou
desfecho — e deixa o julgamento com quem decide.

**Mudanca de 23/10/2026:** isto NAO aparece mais no painel. O Rodrigo tirou de
la e pediu detalhado no Conselho diario, e ele tem razao — um card de cinco
linhas ao lado dos KPIs vira paisagem em tres dias, e o que esta fila precisa
nao e de um lembrete, e de alguem lendo caso a caso. O script continua gerando
`data/decisoes.json`; quem le agora e o `/conselho`.

Uso:  python scripts/decisoes_abertas.py            # grava data/decisoes.json
      python scripts/decisoes_abertas.py ler        # resumo curto
      python scripts/decisoes_abertas.py conselho   # DETALHADO, para a ata
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "docs" / "decisoes"
SAIDA = RAIZ / "data" / "decisoes.json"
BRT = timezone(timedelta(hours=-3))

# Quantas o Conselho le em voz alta primeiro. O resto vai na lista completa:
# a regra "conselho que entrega dez itens nao decidiu nada" vale para o que ele
# PEDE ao Rodrigo, nao para o que ele mostra. Ver tambem `todas` no JSON.
NO_TOPO = 5

# Palavras que nao distinguem uma decisao de outra -- fora da comparacao de
# repeticao, senao "confirmar o saldo" e "confirmar a escala" viram parentes.
VAZIAS = {"a","o","as","os","de","da","do","das","dos","e","em","no","na","nos",
          "nas","um","uma","para","por","com","que","se","ao","aos","hoje",
          "agora","the","decisao","conselho","sobre","ate","antes","depois",
          "mais","ja","nao","sem","seu","sua","entre"}

# Marcadores de ciclo fechado. SUPERADA conta como fechada: a decisao foi
# absorvida por outra, nao abandonada.
FECHADA = re.compile(r"\*\*(?:SUPERADA|EXECUTADA|RECUSADA|APROVADA e EXECUTADA)\b", re.I)
PLACEHOLDER = re.compile(r"^_?\(?em branco", re.I)


def _secao(texto: str, nome: str) -> str:
    m = re.search(rf"^## {nome}\s*\n(.*?)(?=\n## |\Z)", texto, re.S | re.M)
    return m.group(1).strip() if m else ""


def _reais(txt: str) -> float | None:
    """R$ 8.724,99 -> 8724.99. Devolve None quando nao ha valor — e MUITA
    decisao nao tem: 'a visibilidade inteira do caixa do Spa' e um valor
    legitimo em jogo e nao vira numero."""
    m = re.search(r"R\$\s*([\d.]+(?:,\d+)?)\s*(mil|milh(?:ão|ao|ões|oes)|k)?\b",
                  txt, re.I)
    if not m:
        return None
    bruto, escala = m.group(1), (m.group(2) or "").lower()
    # "1.200" e mil e duzentos; "1,2" e um virgula dois. O separador de milhar
    # so e milhar quando sobram 3 digitos depois dele.
    if "," in bruto:
        bruto = bruto.replace(".", "").replace(",", ".")
    elif re.search(r"\.\d{3}\b", bruto):
        bruto = bruto.replace(".", "")
    try:
        v = float(bruto)
    except ValueError:
        return None
    # Ate 23/10/2026 "≈ R$ 16 mil" virava 16,00 e a decisao de dezesseis mil
    # reais era ordenada atras de uma de duzentos. A fila por dinheiro mentia.
    if escala == "mil" or escala == "k":
        v *= 1_000
    elif escala.startswith("milh"):
        v *= 1_000_000
    return v


def _revisao(texto: str, frontmatter: str) -> str:
    """Data de revisao marcada pela propria decisao. Vazio quando nao ha.

    Duas formas, porque o repositorio tem as duas:
      - secao `## Revisão` (ou `## Revisar em`) comecando com AAAA-MM-DD
      - frontmatter `revisao:` — so 1 dos 86 arquivos usa, mas e o formato novo

    Muita decisao diz "Sem prazo automático. Volte a esta decisão no próximo
    Conselho." Isso NAO e data: nao vence, e nao deve virar alarme falso.
    """
    m = re.search(r"^revisao:\s*(\d{4}-\d{2}-\d{2})", frontmatter, re.M)
    if m:
        return m.group(1)
    sec = re.search(r"^## Revis(?:ão|ao|ar em)[^\n]*\n(.*?)(?=\n## |\Z)",
                    texto, re.S | re.M)
    if not sec:
        return ""
    corpo = sec.group(1).strip()
    m = re.search(r"(\d{4}-\d{2}-\d{2})", corpo[:60])
    if m:
        return m.group(1)
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", corpo[:60])
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""


def _palavras(titulo: str) -> set:
    """Titulo -> conjunto de palavras que distinguem. Sem acento, sem vazias."""
    import unicodedata
    s = unicodedata.normalize("NFKD", titulo.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return {w for w in re.findall(r"[a-z]{3,}", s) if w not in VAZIAS}


def marcar_repetidas(abertas: list) -> list:
    """Quais decisoes abertas sao o MESMO pedido com outra data.

    O achado de 23/10/2026: o pedido de ligar para os clientes sumidos foi a
    mesa 11 vezes em 32 dias. Nao eram 11 problemas, era um problema e dez
    lembretes — e ninguem via isso porque cada um era um arquivo separado.

    Comparacao generica de proposito (sobreposicao de palavras do titulo, 50%),
    e nao uma lista de temas escrita a mao: lista de temas envelhece e passa a
    mentir sobre assunto novo. Falso positivo aqui custa uma linha na ata; a
    lista desatualizada custa a proxima repeticao passar batida.
    """
    chaves = [_palavras(d["titulo"]) for d in abertas]
    grupos = []  # cada grupo e uma lista de indices
    for i, ki in enumerate(chaves):
        if len(ki) < 2:
            continue
        for g in grupos:
            kg = chaves[g[0]]
            comuns = ki & kg
            # Sobreposicao, nao Jaccard. Jaccard pune titulo longo: "Confirmar
            # o saldo real na conta (XP)" e "Antes de antecipar o recebivel da
            # Stone, confirmar o saldo da Reserva XP" sao o mesmo pedido e
            # davam 0,25, porque o segundo arrasta seis palavras a mais.
            # Dividir pelo MENOR conjunto pergunta a coisa certa: o pedido
            # curto esta inteiro dentro do longo?
            menor = min(len(ki), len(kg))
            if menor and len(comuns) >= 3 and len(comuns) / menor >= 0.55:
                g.append(i)
                break
        else:
            grupos.append([i])
    for g in grupos:
        if len(g) < 2:
            continue
        # a mais recente e a que vale; as outras sao repeticoes dela
        g.sort(key=lambda i: abertas[i]["data"])
        viva = abertas[g[-1]]
        for i in g[:-1]:
            abertas[i]["repete"] = viva["arquivo"]
            abertas[i]["repete_titulo"] = viva["titulo"]
        viva["repetida_vezes"] = len(g)
    return abertas


def _titulo(texto: str) -> str:
    """O titulo de verdade, nao o paragrafo todo.

    `conselho_sync.yml` grava a decisao inteira na linha do H1:

        # Conselho 2026-10-17 · Decisão #1 · **Clientes sumindo: nomear quem
        da recepção usa o botão 📱, com meta por dia.** - Em jogo: ≈ R$ 16 mil,
        que é 133 clientes × ... - Se nada for feito: ... - Executa: ...

    Sem cortar, "titulo" vira um paragrafo de 400 caracteres: a comparacao de
    repeticao afoga no ruido (duas decisoes do mesmo assunto deixam de parecer
    parecidas porque cada uma arrasta um paragrafo diferente) e a ata fica
    ilegivel. Os tres cortes abaixo sao os rotulos que o proprio sync escreve.
    """
    linhas = texto.splitlines()
    if linhas and linhas[0].strip() == "---":          # frontmatter (formato novo)
        fim = next((i for i, l in enumerate(linhas[1:], 1) if l.strip() == "---"), 0)
        linhas = linhas[fim + 1:]
    titulo = next((l for l in linhas if l.strip()), "").lstrip("# ").strip()
    titulo = re.sub(r"^titulo:\s*", "", titulo)
    titulo = re.sub(r"\*\*|`", "", titulo)
    titulo = re.sub(r"^Conselho \d{4}-\d{2}-\d{2} · Decisão #\d+ · ", "", titulo)
    titulo = re.split(r"\s+-\s+(?:Em jogo|Se nada for feito|Executa)\b", titulo)[0]
    return titulo.strip(" .-—·")


def coletar() -> dict:
    hoje = datetime.now(BRT).date()
    abertas, fechadas = [], 0
    for f in sorted(PASTA.glob("*.md")) if PASTA.exists() else []:
        t = f.read_text(encoding="utf-8", errors="replace")
        resultado = _secao(t, "Resultado")
        tem_resultado = bool(resultado) and not PLACEHOLDER.match(resultado) and len(resultado) >= 25
        if tem_resultado or FECHADA.search(t):
            fechadas += 1
            continue

        titulo = _titulo(t)
        try:
            quando = date.fromisoformat(f.name[:10])
        except ValueError:
            quando = hoje
        fm = t.split("---")[1] if t.startswith("---") and t.count("---") >= 2 else ""
        revisao = _revisao(t, fm)
        em_jogo = _secao(t, "Em jogo") or ""
        em_jogo = "" if em_jogo.startswith("(não capturado") else em_jogo.split("\n")[0]
        # Primeira oracao, sem markdown. O campo costuma trazer o acordo
        # inteiro ("voce com o Financeiro; o gatilho e **abaixo de R$ 1.000..."),
        # e no painel isso vira ruido que empurra o titulo para fora da tela.
        executor = (_secao(t, "Executor") or "").split("\n")[0]
        executor = re.sub(r"\*\*|`", "", executor).split(";")[0].split(" — ")[0].strip()
        abertas.append({
            "arquivo": f.name,
            "titulo": titulo[:140],
            "data": quando.isoformat(),
            "dias": (hoje - quando).days,
            "em_jogo": em_jogo[:120],
            "valor": _reais(em_jogo),
            "executor": "" if executor.lower().startswith("a definir") else executor[:60],
            "revisao": revisao,
            # revisao marcada que ja passou: o ciclo que a propria decisao
            # pediu nao foi cumprido, e isso e pior que estar so aberta
            "revisao_vencida": bool(revisao and revisao < hoje.isoformat()),
        })

    # Dinheiro primeiro; sem valor, as mais velhas. Idade sozinha colocaria uma
    # decisao de rotina de julho na frente dos R$ 8 mil de ontem.
    abertas.sort(key=lambda d: (-(d["valor"] or 0), -d["dias"]))
    abertas = marcar_repetidas(abertas)
    return {
        "_desc": "Decisões sem desfecho registrado. Ver scripts/decisoes_abertas.py.",
        "gerado_em": datetime.now(BRT).replace(microsecond=0).isoformat(),
        "n_abertas": len(abertas),
        "n_fechadas": fechadas,
        "mais_antiga_dias": max((d["dias"] for d in abertas), default=0),
        "revisoes_vencidas": sum(1 for d in abertas if d["revisao_vencida"]),
        "repeticoes": sum(1 for d in abertas if d.get("repete")),
        "destaque": abertas[:NO_TOPO],
        # a lista inteira: quem le e o /conselho, nao o painel
        "todas": abertas,
    }


def _brl(v) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def imprimir_conselho(d: dict) -> None:
    """A leitura detalhada que o Conselho faz em voz alta.

    Tres blocos, nesta ordem, porque e a ordem do que custa caro:
      1. revisao vencida  — a propria decisao marcou data e a data passou
      2. repeticao        — o mesmo pedido com outra capa
      3. o resto          — por dinheiro, depois por idade
    """
    todas = d.get("todas") or []
    print(f"\n🕰️  DECISOES SEM DESFECHO · {d['n_abertas']} abertas · "
          f"{d['n_fechadas']} fechadas na historia · mais antiga ha {d['mais_antiga_dias']} dias")

    venc = [x for x in todas if x.get("revisao_vencida")]
    if venc:
        print(f"\n── ⏰ REVISAO VENCIDA ({len(venc)}) — a decisao marcou data e a data passou")
        for x in sorted(venc, key=lambda y: y["revisao"]):
            print(f"   revisao {x['revisao']} · aberta ha {x['dias']}d · "
                  f"{_brl(x['valor']) if x['valor'] else (x['em_jogo'][:30] or '—')}")
            print(f"      {x['titulo'][:88]}")
            if x.get("executor"):
                print(f"      executa: {x['executor']}")

    rep = [x for x in todas if x.get("repete")]
    if rep:
        print(f"\n── 🔁 PARECEM O MESMO PEDIDO ({len(rep)}) — CONFIRA antes de fechar como SUPERADA")
        for x in sorted(rep, key=lambda y: y["data"]):
            print(f"   {x['data']} · {x['titulo'][:70]}")
            print(f"      -> ja coberta por: {x['repete_titulo'][:70]}")

    resto = [x for x in todas if not x.get("repete") and not x.get("revisao_vencida")]
    if resto:
        print(f"\n── 📋 ABERTAS, SEM REPETICAO ({len(resto)}) — por dinheiro, depois idade")
        for x in resto:
            v = _brl(x["valor"]) if x["valor"] else (x["em_jogo"][:28] or "—")
            marca = f" · repetida {x['repetida_vezes']}x" if x.get("repetida_vezes") else ""
            print(f"   {x['dias']:>4}d  {v:<20} {x['titulo'][:62]}{marca}")
            if x.get("executor"):
                print(f"         executa: {x['executor'][:60]}")

    print(f"\n   Fechar e escrever o desfecho em `## Resultado` do arquivo — deu certo, "
          f"nao deu, ou foi abandonada. As tres contam.")
    print(f"   Arquivos em docs/decisoes/.\n")


def main() -> int:
    d = coletar()
    if len(sys.argv) > 1 and sys.argv[1] == "conselho":
        imprimir_conselho(d)
        return 0
    if len(sys.argv) > 1 and sys.argv[1] == "ler":
        print(f"  {d['n_abertas']} sem resultado · {d['n_fechadas']} fechadas · "
              f"mais antiga: {d['mais_antiga_dias']} dias")
        for x in d["destaque"]:
            v = f"R$ {x['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if x["valor"] else (x["em_jogo"] or "—")
            print(f"    {x['dias']:>4}d  {v:<22} {x['titulo'][:60]}")
        return 0
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[decisoes] {d['n_abertas']} sem resultado, {d['n_fechadas']} fechadas -> {SAIDA.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
