#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confere se os números batem entre si — unidades, períodos e arquivos.

Por que existe: em 14/09/2026 uma conferência manual achou em minutos que a
meta mensal do SPA estava em R$ 60.000 dentro de um payload marcado
`_pre_abertura: True`, com todo o resto zerado. A meta tinha sido herdada da
Escova e ninguém zerou. Enquanto o SPA está em zero-state o erro passa
despercebido; no dia em que ele abrir com meta real, o consolidado vai
continuar mostrando uma meta só e a holding vai parecer estar batendo número
que não bateu.

Esse é o tipo de defeito que nenhum departamento acha sozinho: cada um olha o
próprio card e cada card, isolado, está certo.

O QUE CONFERE
  1. Unidades  — escova + spa = consolidado, campo a campo
  2. Períodos  — diário ≤ semanal ≤ mensal ≤ anual (acumulados)
  3. Zero-state — unidade em pré-abertura não pode ter KPI diferente de zero
  4. Frescor   — arquivos que deveriam ser do mesmo momento

CAMPO SOMÁVEL vs DERIVADO
  Somar percentual, ticket médio ou taxa é erro de aritmética, não conferência.
  O script classifica pelo nome do campo e só soma o que é absoluto. Campo que
  não casa com nenhuma regra é reportado como NÃO CLASSIFICADO — para ser
  classificado, não para ser ignorado em silêncio.

SAÍDA
  0 = tudo bate · 1 = divergência real · 2 = não deu para avaliar
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOL = 0.01

# Derivados: percentuais, médias, taxas e deltas. Somá-los não faz sentido —
# o consolidado precisa recalcular a partir dos totais somados.
DERIVADO = re.compile(
    r"(_pct$|^taxa_|_delta|^ticket_|_medio$|_media$|^rs_hora|^hora_media|"
    r"^utilizacao|_atingimento|^pct_|^freq_)", re.I)
# Absolutos conhecidos: devem somar.
SOMAVEL = re.compile(
    r"(^caixa$|^caixa_conta$|^receita|^faturamento|^atend|^n_|^clientes_unicos$|"
    r"^cliente_dia$|^visitas_|^meta_mes$|^a_receber|^resultado_mes|^horas_|"
    r"^dias_op$|^em_atendimento$)", re.I)


def carregar(rel: str):
    p = REPO / rel
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def kpis(d, aba="mensal"):
    if not isinstance(d, dict):
        return {}
    return ((d.get("abas") or {}).get(aba) or {}).get("kpis") or {}


def brl(v):
    return f"R$ {v:,.2f}".replace(",", "~").replace(".", ",").replace("~", ".")


def conferir_unidades(achados, esc, spa, cons, rotulo, extrair):
    """escova + spa = consolidado, campo a campo."""
    ke, ks, kc = extrair(esc), extrair(spa), extrair(cons)
    if not kc:
        achados.append(("indef", f"{rotulo}: consolidado sem dados para conferir"))
        return
    nao_classificados = []
    for campo in sorted(set(ke) | set(ks) | set(kc)):
        a, b, c = ke.get(campo), ks.get(campo), kc.get(campo)
        if not all(isinstance(x, (int, float)) and not isinstance(x, bool)
                   for x in (a, b, c)):
            continue
        if DERIVADO.search(campo):
            continue  # derivado: o consolidado recalcula, não soma
        if not SOMAVEL.search(campo):
            nao_classificados.append(campo)
            continue
        soma = a + b
        if abs(soma - c) > TOL:
            achados.append(("erro",
                f"{rotulo} · {campo}: escova {a} + spa {b} = {round(soma,2)}, "
                f"mas o consolidado diz {c} (diferença de {round(c-soma,2)})"))
    if nao_classificados:
        achados.append(("indef",
            f"{rotulo}: {len(nao_classificados)} campo(s) sem classificação — "
            f"{', '.join(nao_classificados[:6])}"
            + (" …" if len(nao_classificados) > 6 else "")))


def conferir_periodos(achados, d, nome):
    """Acumulados só podem crescer: diário ≤ semanal ≤ mensal ≤ anual."""
    janelas = ["diario", "semanal", "mensal", "anual"]
    for campo in ("caixa", "atend_total"):
        vals = []
        for j in janelas:
            v = kpis(d, j).get(campo)
            if not isinstance(v, (int, float)):
                vals = []
                break
            vals.append((j, v))
        if not vals:
            continue
        for (j1, v1), (j2, v2) in zip(vals, vals[1:]):
            if v1 - v2 > TOL:
                achados.append(("erro",
                    f"{nome} · {campo}: {j1} ({v1}) é maior que {j2} ({v2}) — "
                    "um acumulado maior não pode ser menor que o menor"))


# Numa loja que ainda não abriu, o REALIZADO tem que ser zero — mas a
# EXPECTATIVA não. Meta existe antes de a loja abrir; é o alvo com que ela
# nasce. Esta distinção foi acrescentada em 14/09/2026, quando a regra original
# acusou como defeito uma meta de R$ 15.000 legitimamente definida para o SPA.
EXPECTATIVA = re.compile(r"(^meta|_meta$|_meta_|^orcamento|^previsto)", re.I)


def conferir_zero_state(achados, fin, dash, nome):
    """Unidade que ainda não abriu não pode ter REALIZADO diferente de zero."""
    if not isinstance(fin, dict) or not fin.get("_pre_abertura"):
        return
    sujos = [(k, v) for k, v in (fin.get("kpis") or {}).items()
             if isinstance(v, (int, float)) and abs(v) > TOL
             and not EXPECTATIVA.search(k)]
    for k, v in sujos:
        achados.append(("erro",
            f"{nome} está marcada como pré-abertura ({fin.get('_data_inauguracao','?')}) "
            f"mas o campo `{k}` vale {brl(v)} — isso é realizado, não expectativa, "
            f"e uma loja fechada não realiza nada. "
            "Enquanto tudo o mais é zero o erro não aparece; quando a unidade "
            "abrir com número real, ele passa a contaminar o consolidado."))



def conferir_bloco_derivado(achados, dash, nome, sem_agendamentos_ok=False):
    """O mapa de escala tem que existir e ser da mesma execução do payload.

    `densidade_dow` é gravado por um passo separado, depois do refresh. Em
    14/09/2026 a chave sumiu do arquivo publicado: a tarefa agendada do PC
    regenerou o payload do zero e não rodava esse passo. O card do painel
    simplesmente não aparecia, e nada acusava — some silencioso é o pior tipo
    de falha, porque parece decisão de layout.
    """
    if not isinstance(dash, dict):
        return
    dd = dash.get("densidade_dow")
    if not dd:
        if sem_agendamentos_ok:
            return  # unidade em pré-abertura: não há agendamento para medir
        achados.append(("erro",
            f"{nome}: bloco `densidade_dow` ausente do payload — o card Mapa de "
            "escala não vai renderizar. Rode scripts/densidade_dow.py --gravar."))
        return
    g_pay = (dash.get("gerado_em") or "")[:10]
    g_dd = (dd.get("gerado_em") or "")[:10]
    if g_pay and g_dd and g_pay != g_dd:
        achados.append(("aviso",
            f"{nome}: o mapa de escala é de {g_dd} e o payload de {g_pay} — "
            "o passo de densidade não rodou no último refresh."))


def conferir_frescor(achados, arquivos):
    """Consolidado e unidade têm que sair da MESMA execução, não do mesmo dia.

    Precisão de minuto, não de data. Em 14/09/2026 a versão que só comparava o
    dia deixou passar um consolidado de 20h05 convivendo com uma Escova de
    21h00: o painel da holding ficou uma hora atrás sem ninguém notar, porque
    os números estavam perto. Causa: dois pipelines escrevem os mesmos
    arquivos — o workflow do GitHub, que regenera unidade + consolidado, e a
    tarefa agendada do PC, que regenera só a Escova e faz push.
    """
    marcas = {}
    for rel, d in arquivos.items():
        g = (d or {}).get("gerado_em")
        if isinstance(g, str) and len(g) >= 16:
            marcas[rel] = g[:16]
    if len(set(marcas.values())) > 1:
        achados.append(("erro",
            "consolidado e unidade vieram de execuções diferentes — "
            + " · ".join(f"{Path(k).name}={v}" for k, v in marcas.items())
            + ". O consolidado está descrevendo um momento que já passou; "
            "rode scripts/consolida_dashboard.py."))


def main() -> int:
    achados: list[tuple[str, str]] = []

    dash = {u: carregar(p) for u, p in {
        "escova": "data/dashboard_data.json",
        "spa": "data/spa/dashboard_data.json",
        "consolidado": "data/consolidado/dashboard_data.json"}.items()}
    fin = {u: carregar(p) for u, p in {
        "escova": "data/financeiro.json",
        "spa": "data/spa/financeiro.json",
        "consolidado": "data/consolidado/financeiro.json"}.items()}

    if not dash["consolidado"] or not fin["consolidado"]:
        print("⚠️  Consolidado ausente — nada a conferir.")
        return 2

    for aba in ("mensal", "anual"):
        conferir_unidades(achados, dash["escova"], dash["spa"], dash["consolidado"],
                          f"Operação {aba}", lambda d, a=aba: kpis(d, a))
    conferir_unidades(achados, fin["escova"], fin["spa"], fin["consolidado"],
                      "Financeiro", lambda d: (d or {}).get("kpis") or {})

    for u, d in dash.items():
        if d:
            conferir_periodos(achados, d, f"Operação {u}")
    for u in ("escova", "spa"):
        conferir_zero_state(achados, fin[u], dash[u], f"Unidade {u}")

    # Os TRÊS payloads, não só a Escova. Em 15/09/2026 a auditoria passou verde
    # enquanto o card "Mapa de escala" estava vazio no painel da holding: a
    # consolidação roda antes do passo de densidade, então o bloco nunca chegava
    # lá. Conferir só a unidade que sempre tem o dado é não conferir nada.
    conferir_bloco_derivado(achados, dash["escova"], "Escova")
    conferir_bloco_derivado(achados, dash["consolidado"], "Consolidado")
    conferir_bloco_derivado(achados, dash["spa"], "Spa", sem_agendamentos_ok=True)

    # O bloco de balcão por pessoa nasce dentro do github_refresh, num try/except
    # cujo print vai para o log do Actions que ninguém lê. Mesma lição do mapa de
    # escala: se some, tem que doer aqui, não passar despercebido no painel.
    bv = dash["escova"].get("balcao_vendedor") if isinstance(dash["escova"], dict) else None
    if not bv or not (bv.get("por_janela") or {}).get("ano"):
        achados.append(("aviso",
            "Escova: bloco `balcao_vendedor` ausente ou vazio — o card "
            "\u0022Balc\u00e3o por pessoa\u0022 n\u00e3o vai renderizar e as metas nominais "
            "da recep\u00e7\u00e3o ficam sem acompanhamento."))

    conferir_frescor(achados, {
        "data/dashboard_data.json": dash["escova"],
        "data/consolidado/dashboard_data.json": dash["consolidado"]})

    erros = [m for t, m in achados if t == "erro"]
    avisos = [m for t, m in achados if t == "aviso"]
    indef = [m for t, m in achados if t == "indef"]

    if erros:
        print(f"🛑 {len(erros)} divergência(s) — os números não batem entre si")
        for m in erros:
            print(f"   • {m}")
    if avisos:
        print(f"⚠️  {len(avisos)} aviso(s)")
        for m in avisos:
            print(f"   • {m}")
    if indef:
        print(f"❔ {len(indef)} ponto(s) não avaliado(s)")
        for m in indef:
            print(f"   • {m}")
    if not achados:
        print("✅ Tudo bate: unidades somam no consolidado, períodos coerentes, "
              "zero-state limpo.")

    return 1 if erros else (2 if indef and not achados else 0)


if __name__ == "__main__":
    sys.exit(main())
