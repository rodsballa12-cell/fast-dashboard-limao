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
import datetime
import pathlib, json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOL = 0.01

# Derivados: percentuais, médias, taxas e deltas. Somá-los não faz sentido —
# o consolidado precisa recalcular a partir dos totais somados.
DERIVADO = re.compile(
    r"(_pct$|^taxa_|_delta|^ticket_|_medio$|_media$|^rs_hora|^hora_media|^visitas_(projetadas|restantes)$|^dias_op$|"
    r"^utilizacao|_atingimento|^pct_|^freq_)", re.I)
# Absolutos conhecidos: devem somar.
SOMAVEL = re.compile(
    r"(^caixa$|^caixa_conta$|^receita|^faturamento|^atend|^n_|^clientes_unicos$|"
    r"^cliente_dia$|^visitas_|^meta_mes$|^a_receber|^resultado_mes|^horas_|"
    r"^em_atendimento$)", re.I)


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
        # Só compara janelas em que a menor cabe inteira na maior. A semana
        # (seg-dom) começa no mês anterior nos primeiros dias do mês — em
        # 02/10/2026 a semana tinha 28/09 a 02/10 e o mês só 01-02/10, e a regra
        # acusava "semanal maior que mensal" como erro todo início de mês.
        try:
            hoje = datetime.date.fromisoformat(str(d.get("hoje"))[:10])
            seg = hoje - datetime.timedelta(days=hoje.weekday())
        except (TypeError, ValueError):
            hoje = seg = None
        v = dict(vals)
        pares = [("diario", "semanal"), ("diario", "mensal"), ("mensal", "anual")]
        if hoje is None or (seg.year, seg.month) == (hoje.year, hoje.month):
            pares.append(("semanal", "mensal"))
        if hoje is None or seg.year == hoje.year:
            pares.append(("semanal", "anual"))
        for j1, j2 in pares:
            v1, v2 = v[j1], v[j2]
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


def conferir_contra_trinks(achados, dash, unidade):
    """O painel bate com o que foi extraido do Trinks a mao?

    Pedido do Rodrigo em 28/10/2026, depois de subir um export do Trinks
    para a reuniao com a agencia: "garanta que batam". Ate entao os dois
    lados so se encontravam na frente da agencia.

    A referencia vive em `data/trinks_conferencia.json`, que e arquivo de
    cofre (financeiro). Sem ele, este passo nao reclama — so nao confere.
    A regra de comparacao e a do proprio scripts/conferir_trinks.py, nao
    uma copia: copia envelhece sozinha e passa a mentir.
    """
    ref_path = REPO / "data" / "trinks_conferencia.json"
    if not ref_path.exists():
        return
    if not isinstance(dash, dict):
        return
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "conferir_trinks", REPO / "scripts" / "conferir_trinks.py")
        ct = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ct)
        ref_tudo = json.loads(ref_path.read_text(encoding="utf-8"))
    except Exception as e:
        achados.append(("indef", f"nao consegui carregar a conferencia do Trinks: {e}"))
        return

    meses_ref = ref_tudo.get(unidade)
    if not isinstance(meses_ref, dict):
        return
    meses = (((dash.get("abas") or {}).get("anual") or {}).get("meses")) or {}
    for ym, r in meses_ref.items():
        if ym.startswith("_") or not isinstance(r, dict):
            continue
        m = meses.get(ym)
        if not isinstance(m, dict):
            continue
        fora = ct.divergencias(r, m)
        for campo, t, p in fora:
            achados.append(("aviso",
                f"{unidade} {ym}: `{campo}` nao bate com o Trinks — "
                f"Trinks {t}, painel {p}. Rode "
                f"`python3 scripts/conferir_trinks.py {unidade} {ym}` para o detalhe."))


def conferir_placar_agencia(achados, dash, nome):
    """Os sete numeros da reuniao com a agencia tem que estar no payload.

    O placar da aba Midias (28/10/2026) le tudo de
    `abas.anual.meses[YYYY-MM]`. Se um desses campos sumir do refresh, o
    bloco nao desaparece — ele mostra NAO VEJO numa linha e as outras seis
    continuam bonitas, o que e pior: a reuniao segue com um numero faltando
    sem ninguem perceber. Mesma licao de `densidade_dow` em 14/09.

    Confere o mes corrente e o anterior, que sao justamente os dois que o
    placar compara.
    """
    CAMPOS = {
        "meta":              "meta do mes",
        "caixa":             "faturamento",
        "ticket_medio":      "ticket medio (formula de 27/10)",
        "n_trans_com_pagto": "denominador do ticket medio",
        "atend_fin":         "atendimentos",
        "clientes_unicos":   "clientes no mes",
        "clientes_novos":    "clientes novos",
        "pacotes_n":         "pacotes vendidos",
        "dias_op":           "dias de operacao (base da comparacao por dia)",
    }
    if not isinstance(dash, dict):
        return
    meses = (((dash.get("abas") or {}).get("anual") or {}).get("meses")) or {}
    if not meses:
        achados.append(("erro",
            f"{nome}: `abas.anual.meses` ausente — o placar do negocio da aba "
            "Midias (o que a agencia pede) nao tem de onde ler."))
        return
    hoje = (dash.get("hoje") or "")[:7]
    if not hoje:
        return
    ano, mes = int(hoje[:4]), int(hoje[5:7])
    ant = f"{ano - 1}-12" if mes == 1 else f"{ano}-{mes - 1:02d}"
    for ym, rotulo in ((hoje, "mes corrente"), (ant, "mes anterior")):
        m = meses.get(ym)
        if not isinstance(m, dict):
            # mes sem movimento nao entra em `meses` — e esperado antes da
            # loja abrir, nao e falha.
            continue
        faltam = [f"`{k}` ({v})" for k, v in CAMPOS.items() if m.get(k) is None]
        if faltam:
            achados.append(("erro",
                f"{nome}: o {rotulo} ({ym}) esta sem " + ", ".join(faltam)
                + " — o placar da aba Midias vai mostrar NAO VEJO nessa linha "
                  "na proxima reuniao com a agencia."))


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


def conferir_calendario_e_metas(achados, esc, spa, cons):
    """Um calendário só e meta do Spa contada desde a abertura.

    Em 30/09/2026 o consolidado somava os dias das duas lojas (36 de 36) e a
    meta cheia do mês do Spa (R$ 80 mil), e o painel dizia "128% do ritmo" e
    "atrasado R$ 21 mil" na mesma tela. dias_op não é somável: é o calendário.
    """
    for aba in ("diario", "semanal", "mensal", "anual"):
        ke, ks, kc = kpis(esc, aba), kpis(spa, aba), kpis(cons, aba)
        me = ((esc.get("abas") or {}).get(aba) or {}).get("meta") or {}
        ms = ((spa.get("abas") or {}).get(aba) or {}).get("meta") or {}
        mc = ((cons.get("abas") or {}).get(aba) or {}).get("meta") or {}
        if not mc:
            continue
        esp = max(ke.get("dias_op") or 0, ks.get("dias_op") or 0)
        if kc.get("dias_op") != esp:
            achados.append(("erro", f"Calendário {aba}: dias_op do consolidado é {kc.get('dias_op')}, esperado {esp} (o maior das lojas, não a soma)"))
        if mc.get("dias_total") != me.get("dias_total"):
            achados.append(("erro", f"Calendário {aba}: dias_total do consolidado é {mc.get('dias_total')}, mas a Escova tem {me.get('dias_total')}"))
        cheia = (me.get("meta") or 0) + (ms.get("meta") or 0)
        if (mc.get("meta") or 0) > cheia + TOL:
            achados.append(("erro", f"Meta {aba}: consolidada {mc.get('meta')} passa da soma das metas cheias {cheia}"))
        # Painel e Financeiro têm que dizer a MESMA meta do mês (30/09/2026: R$ 63,9 mil
        # num e R$ 110 mil no outro). Spa no mês da abertura = meta cheia, sem ratear.
        if aba == "mensal":
            fc = carregar("data/consolidado/financeiro.json") or {}
            mf = (fc.get("kpis") or {}).get("meta_mes")
            if mf and abs(mf - (mc.get("meta") or 0)) > 1:
                achados.append(("erro", f"Meta mensal: o Painel consolidado diz {mc.get('meta')} e o Financeiro consolidado diz {mf}"))
        if mc.get("dias_realizados") is not None and mc.get("dias_total") is not None and mc["dias_realizados"] > mc["dias_total"]:
            achados.append(("erro", f"Calendário {aba}: {mc['dias_realizados']} dias realizados de {mc['dias_total']}"))
        ate = mc.get("meta_ate_hoje")
        if ate and mc.get("pct_ate_hoje") is not None:
            calc = round((kc.get("caixa") or 0) / ate * 100, 1)
            if abs(calc - mc["pct_ate_hoje"]) > 0.11:
                achados.append(("erro", f"Meta {aba}: pct_ate_hoje {mc['pct_ate_hoje']} não bate com caixa÷meta_ate_hoje ({calc})"))
        # o texto do painel não pode dizer "adiantado" e "atrasado" ao mesmo tempo
        if ate and ((kc.get("caixa") or 0) - ate) * ((mc.get("pct_ate_hoje") or 100) - 100) < 0:
            achados.append(("erro", f"Meta {aba}: saldo e percentual até hoje apontam para lados opostos"))


def conferir_conselho_sincronizado(achados):
    """A ata foi escrita — mas o painel aprendeu?

    Em 08/10/2026 o `historico_conselhos` dos tres paineis parava em 20/09,
    dezoito dias atras, enquanto `docs/atas/` tinha onze conselhos: 14, 15,
    16, 18, 19, 20, 21, 23, 25, 28 e 29 de setembro. **Oito dos onze nunca
    chegaram ao artefato.**

    A causa e mecanica: o `conselho_sync.yml` dispara em push para
    `Briefings/**-conselho.md`. Quem rodou os conselhos de 21 a 29/09 gravou a
    ata em `docs/atas/` e pulou a copia em `Briefings/` — o workflow nunca
    foi acionado, e o painel seguiu mostrando o conselho de 20/09 como se
    fosse o ultimo. Nada ficou vermelho. O Rodrigo abria o painel e lia uma
    reuniao de tres semanas atras.

    Mesma familia do resto deste arquivo: "a ata foi escrita" nao e "o painel
    aprendeu", do mesmo jeito que "o detector detectou" nao e "alguem foi
    avisado".
    """
    todas = sorted((REPO / "docs" / "atas").glob("*-conselho.md"))
    # Só conta ata de reunião de verdade (com decisões). "Não consegui rodar"
    # não ensina nada ao painel — mas é avisado à parte, abaixo.
    atas = [x.name[:10] for x in todas if re.search(
        r"DECIS[OÕ]ES\s+DO\s+RODRIGO", x.read_text(encoding="utf-8", errors="replace"), re.I)]
    falhas = [x.name[:10] for x in todas if x.name[:10] > (atas[-1] if atas else "")]
    if falhas:
        achados.append(("aviso",
            f"o Conselho de {', '.join(falhas[-3:])} nao rodou (a ata so registra a falha) — "
            f"a ultima reuniao de verdade e de {atas[-1] if atas else 'nunca'}. "
            f"Ver _execucoes.log no vault: costuma ser git travado no PC."))
    if not atas:
        return
    ultima_ata = atas[-1]

    mid = carregar("data/midias_sociais.json") or {}
    hist = [h.get("data") for h in (mid.get("historico_conselhos") or [])
            if isinstance(h, dict) and h.get("data")]
    sem_briefing = [a for a in atas if a not in hist]
    ultimo_painel = max(hist) if hist else None

    if ultimo_painel is None:
        achados.append(("erro",
            f"painel sem `historico_conselhos` nenhum, e docs/atas/ tem "
            f"{len(atas)} conselho(s) — o ultimo e de {ultima_ata}."))
    elif ultimo_painel < ultima_ata:
        achados.append(("erro",
            f"o painel mostra o conselho de {ultimo_painel} como o ultimo, mas "
            f"a ata mais nova em docs/atas/ e de {ultima_ata}. "
            f"{len(sem_briefing)} ata(s) nunca passaram pelo conselho_sync.yml. Quem abre o "
            f"painel esta lendo uma reuniao velha."))
    elif sem_briefing:
        achados.append(("aviso",
            f"{len(sem_briefing)} ata(s) de conselho que nunca entraram no painel "
            f"({', '.join(sem_briefing[-4:])}{'...' if len(sem_briefing) > 4 else ''}) "
            f"— o painel esta em dia com a ultima, mas essas ficaram de fora."))


def conferir_funil_roas(achados):
    """O ROAS existe, e de quando?

    O bloco `funil_conversao` do Spa passou da abertura ate 08/10/2026 com
    todos os contadores em zero e uma mensagem dizendo "ativa quando a
    primeira campanha rodar" — a campanha rodava desde 13/09. Ninguem viu
    porque zero nao chama atencao. O da Escova existia, mas era de agosto,
    escrito a mao: em outubro ainda dizia 4,72x de agosto.

    Agora `scripts/funil_roas.py` reescreve `apuracao_automatica` todo dia.
    Se ele parar de rodar, isto tem que doer aqui — e o mesmo motivo das
    outras checagens de bloco derivado deste arquivo.
    """
    for rel, nome in (("data/midias_sociais.json", "Escova"),
                      ("data/spa/midias_sociais.json", "Spa"),
                      ("data/consolidado/midias_sociais.json", "Consolidado")):
        mid = carregar(rel)
        if not mid:
            continue
        ap = ((mid.get("funil_conversao") or {}).get("apuracao_automatica") or {})
        if not ap.get("roas_extrapolado"):
            achados.append(("aviso",
                f"{nome}: `funil_conversao.apuracao_automatica` ausente ou sem "
                f"ROAS — scripts/funil_roas.py nao rodou. O card de ROAS vai "
                f"mostrar o ultimo numero escrito a mao, que pode ser de meses atras."))
            continue

        g = str(ap.get("gerado_em") or "")[:10]
        hoje = str((carregar("data/dashboard_data.json") or {}).get("hoje") or "")[:10]
        if g and hoje and g < hoje:
            achados.append(("aviso",
                f"{nome}: o ROAS atribuido e de {g} e o painel e de {hoje} — "
                f"a verba de hoje nao entrou nessa conta."))

        cob = (ap.get("atribuicao") or {}).get("cobertura_pct")
        if cob is not None and cob < 60:
            achados.append(("aviso",
                f"{nome}: so {cob}% das fichas dizem de onde o cliente veio. "
                f"Abaixo de 60% o ROAS vira uma faixa larga em vez de um "
                f"numero — a recepcao precisa perguntar em toda ficha nova."))


def conferir_caixa_a_receber(achados):
    """O a-receber do DRE bate com o extrato da propria loja?

    Ate 20/10/2026 o gerar_financeiro.py lia o a-receber SO do extrato da
    Escova. O Spa saia com R$ 0,00 no DRE enquanto o card da mesma tela
    mostrava R$ 8.435,50 -- porque o card le o extrato direto e o DRE lia uma
    copia que ninguem preencheu. O consolidado reportava R$ 8.435,50 a menos
    que a soma das duas lojas. Zero nao era conta vazia: era numero que
    ninguem foi buscar. Esta conferencia existe para que nao volte calado.

    E o caixa em conta nao e zero no Spa, e None: ha UMA conta corrente da
    holding, e o saldo dela aparece inteiro na Escova. "R$ 0,00" fazia o card
    afirmar que a loja esta sem dinheiro.
    """
    ar = {}
    for rel, fin, nome in (("data/dashboard_data.json", "data/financeiro.json", "Escova"),
                           ("data/spa/dashboard_data.json", "data/spa/financeiro.json", "Spa")):
        d, f = carregar(rel), carregar(fin)
        if not d or not f:
            continue
        nc = ((d.get("stone") or {}).get("nao_conciliado") or {})
        extrato = round(float(nc.get("a_receber_d30") or 0.0), 2)
        ar[nome] = extrato
        dre = float((f.get("kpis") or {}).get("a_receber_stone") or 0.0)
        if abs(extrato - dre) > 1.0:
            achados.append(("erro",
                f"{nome}: o DRE diz R$ {dre:,.2f} a receber da Stone e o extrato "
                f"da propria loja diz R$ {extrato:,.2f}. O card e o DRE vao "
                f"mostrar numeros diferentes na mesma tela."))
        caixa = (f.get("kpis") or {}).get("caixa_conta")
        if nome == "Spa" and caixa == 0:
            achados.append(("erro",
                "Spa: caixa em conta esta R$ 0,00 no DRE. Nao e conta vazia: ha "
                "uma conta corrente unica da holding, e o saldo aparece na "
                "Escova. O campo tem de ser nulo, com a observacao -- zero diz "
                "que a loja esta sem dinheiro."))

    fc = carregar("data/consolidado/financeiro.json")
    if fc and len(ar) == 2:
        soma = round(sum(ar.values()), 2)
        dre_c = float((fc.get("kpis") or {}).get("a_receber_stone") or 0.0)
        if abs(soma - dre_c) > 1.0:
            achados.append(("erro",
                f"Consolidado: a-receber da holding diz R$ {dre_c:,.2f} e as duas "
                f"lojas somam R$ {soma:,.2f} (Escova R$ {ar['Escova']:,.2f} + Spa "
                f"R$ {ar['Spa']:,.2f})."))


ESTOQUE_DESDE = "2026-10-28"


def conferir_estoque(achados, fin):
    """O estoque existe, soma entre as lojas e não está contado duas vezes?

    Pedido do Rodrigo em 27/10/2026: compra de material não é CAPEX nem
    despesa, é estoque, e "a auditoria tem de validar isso sempre". O perigo
    é um pagamento ficar no estoque E numa categoria CAPEX/OPEX do razão: o
    resultado paga a compra duas vezes. A conferência contra o razão é feita
    pelo gerar_financeiro.py (só ele abre a planilha); aqui se acusa o que ele
    gravou, e se o bloco sumiu.
    """
    blocos = {u: (fin.get(u) or {}).get("estoque") for u in ("escova", "spa", "consolidado")}
    faltando = [u for u, b in blocos.items() if not isinstance(b, dict)]
    if faltando:
        # Antes do primeiro gerar_financeiro.py com o estoque (27/10/2026) a
        # ausência é esperada; depois dele, é bloco que sumiu.
        gerado = str((fin.get("consolidado") or {}).get("gerado_em") or "")[:10]
        tipo = "erro" if gerado >= ESTOQUE_DESDE else "aviso"
        achados.append((tipo,
            f"Estoque: bloco ausente em {', '.join(faltando)}. O card de estoque "
            f"some do painel e as compras de material deixam de ser conferidas "
            f"contra o razão. Rode o gerar_financeiro.py no PC."))
        return
    for u, b in blocos.items():
        if b.get("status") == "erro_leitura":
            achados.append(("erro", f"Estoque ({u}): a leitura da aba quebrou — {b.get('erro')}"))
            return
    if blocos["consolidado"].get("status") == "aba_ausente":
        achados.append(("aviso",
            "Estoque: a planilha da Siibello ainda não tem a aba de estoque. "
            "Compras de material não estão sendo controladas."))
        return

    e, s, c = blocos["escova"], blocos["spa"], blocos["consolidado"]

    def _v(b, *ks):
        for k in ks:
            b = (b or {}).get(k)
        return b

    for rot, ks in (("compras", ("compras", "total")), ("estoque inicial", ("inicial", "valor")),
                    ("contagem", ("contagem", "valor")), ("fora do resultado", ("fora_do_resultado",))):
        a, b, t = _v(e, *ks), _v(s, *ks), _v(c, *ks)
        if all(isinstance(x, (int, float)) for x in (a, b, t)) and abs(a + b - t) > 1.0:
            achados.append(("erro",
                f"Estoque · {rot}: Escova {brl(a)} + Spa {brl(b)} = {brl(a + b)}, "
                f"mas o consolidado diz {brl(t)}."))

    for nome, b in (("Escova", e), ("Spa", s)):
        ini, cp, ct, cons = _v(b, "inicial", "valor"), _v(b, "compras", "total"), \
            _v(b, "contagem", "valor"), b.get("consumo_estimado")
        if all(isinstance(x, (int, float)) for x in (ini, cp, ct, cons)) and abs(ini + cp - ct - cons) > 1.0:
            achados.append(("erro",
                f"Estoque {nome}: consumo {brl(cons)} não fecha com inicial {brl(ini)} "
                f"+ compras {brl(cp)} − contagem {brl(ct)}."))
        if isinstance(cons, (int, float)) and cons < -1.0:
            achados.append(("erro",
                f"Estoque {nome}: a contagem ({brl(ct)}) é maior que o inicial mais as "
                f"compras ({brl(ini + cp)}). Faltou lançar compra, ou a contagem tem "
                f"custo errado."))
        # O estoque inicial também foi comprado: se não estiver aberto em itens
        # com a origem do pagamento, ninguém garante que não está no CAPEX.
        # Em 27/10/2026 os R$ 15.542,16 do Spa eram exatamente Tulipia + Glossex
        # + Mercado Livre, que estavam lançados no CAPEX ao mesmo tempo.
        itens = _v(b, "inicial", "itens")
        if isinstance(ini, (int, float)) and ini > 0:
            if itens is None:
                achados.append(("aviso",
                    f"Estoque {nome}: o inicial de {brl(ini)} não está aberto em itens "
                    f"(coluna G = 'Inicial' nas compras). Não dá para garantir que essas "
                    f"compras não estão também no CAPEX ou na despesa."))
            elif abs(itens - ini) > 1.0:
                achados.append(("erro",
                    f"Estoque {nome}: o inicial diz {brl(ini)} e os itens que o compõem "
                    f"somam {brl(itens)}."))
        sem_uso = _v(b, "contagem", "sem_uso") or 0
        if _v(b, "contagem", "data") and sem_uso:
            achados.append(("aviso",
                f"Estoque {nome}: {sem_uso} produto(s) contado(s) sem o uso marcado "
                f"(serviço ou revenda). O custo do atendimento e o da revenda ficam misturados."))

    cf = c.get("conferencia") or {}
    if cf.get("status") != "ok":
        achados.append(("indef",
            f"Estoque: compras não conferidas contra o razão ({cf.get('status') or 'sem conferência'})."))
    else:
        for x in cf.get("conflitos_capex_opex") or []:
            achados.append(("erro",
                f"Estoque: pagamento contado duas vezes — {x}. Ou é estoque, ou é "
                f"CAPEX/despesa; nos dois lugares o resultado paga a compra duas vezes."))
        if abs(cf.get("diferenca") or 0) > 1.0:
            achados.append(("erro",
                f"Estoque: o razão tem {brl(cf.get('razao_estoque_total') or 0)} classificados como "
                f"estoque e a aba de estoque tem {brl(cf.get('compras_xp_total') or 0)} de "
                f"compras pela conta XP (diferença de {brl(cf.get('diferenca') or 0)})."))
        sp = cf.get("compras_sem_par_no_razao") or []
        if sp:
            achados.append(("aviso",
                f"Estoque: {len(sp)} compra(s) pela conta XP sem pagamento no razão — "
                f"{'; '.join(sp[:3])}{' …' if len(sp) > 3 else ''}"))
        fc = cf.get("razao_fora_do_controle") or []
        if fc:
            achados.append(("aviso",
                f"Estoque: {len(fc)} pagamento(s) classificado(s) como estoque no razão "
                f"e fora da aba de estoque — {'; '.join(fc[:3])}{' …' if len(fc) > 3 else ''}"))
        if cf.get("compras_cartao_nao_conferidas"):
            achados.append(("indef",
                f"Estoque: {cf['compras_cartao_nao_conferidas']} compra(s) no cartão ainda "
                f"não conferida(s) contra a aba Cartão_Pessoal."))
        if cf.get("compras_sem_loja"):
            achados.append(("aviso",
                f"Estoque: {len(cf['compras_sem_loja'])} compra(s) sem loja definida, "
                f"rateadas 50/50 por falta de informação."))

    fora = c.get("fora_do_resultado") or 0
    if fora > 0 and not _v(c, "amortizacao", "regra"):
        achados.append(("aviso",
            f"Estoque: {brl(fora)} em compras de material estão fora do resultado "
            f"porque a regra de amortização ainda não foi definida. O lucro do "
            f"painel está maior do que será quando a regra entrar."))


def conferir_saude_automacoes(achados):
    """As automacoes carimbaram que funcionaram, e isso bate com os arquivos?

    Existe porque o vigia antigo media CARIMBO, nao CONTEUDO. Ele contava
    commits com `ata:` no nome, entao as 21 atas que diziam "Credit balance is
    too low" passaram por saudaveis durante sete dias. E as midias nao eram
    vigiadas por ninguem: ficaram 42 horas paradas e o alarme que existia
    (um issue no GitHub) toca numa sala onde o Rodrigo nao entra.

    Aqui a conferencia e dupla, e e a dupla que importa:
      1. o que `scripts/saude.py` julga (ultimo SUCESSO, nao ultimo toque)
      2. a data dentro de cada arquivo, por unidade -- porque ja aconteceu de
         a Escova atualizar e o Spa nao, no mesmo commit
    """
    import subprocess
    try:
        r = subprocess.run([sys.executable, "-X", "utf8", str(REPO / "scripts" / "saude.py"), "conferir"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=60)
        linhas = [l for l in (r.stdout or "").splitlines()
                  if l.strip().startswith(("🛑", "⚠️"))]
        if r.returncode == 1 and not linhas:
            # saiu com erro mas nao disse qual automacao: o check quebrou, nao passou.
            achados.append(("aviso",
                "Saude: scripts/saude.py falhou sem dizer o que esta vermelho "
                f"({(r.stderr or '').strip().splitlines()[-1:] or ['sem stderr']}). "
                "Sem isso nenhuma automacao esta sendo vigiada."))
        for linha in linhas:
            achados.append(("aviso", f"Saude: {linha.strip()[2:].strip()}"))
    except Exception as exc:
        achados.append(("aviso", f"Saude: nao consegui rodar scripts/saude.py ({type(exc).__name__})."))

    # As tres unidades, uma a uma. O consolidado some do radar quando so se
    # olha a Escova -- e foi exatamente o que aconteceu em 21-23/10.
    from datetime import datetime, timedelta, timezone
    agora = datetime.now(timezone(timedelta(hours=-3)))
    for rel, nome, limite in (
            ("data/midias_sociais.json",             "Midias Escova",      36),
            ("data/spa/midias_sociais.json",         "Midias Spa",         36),
            ("data/consolidado/midias_sociais.json", "Midias Consolidado", 36)):
        d = carregar(rel)
        if not d:
            achados.append(("aviso", f"{nome}: arquivo ausente."))
            continue
        g = d.get("gerado_em")
        try:
            h = (agora - datetime.fromisoformat(g)).total_seconds() / 3600
        except Exception:
            achados.append(("aviso", f"{nome}: sem data de geracao legivel ({g!r})."))
            continue
        if h > limite:
            achados.append(("aviso",
                f"{nome}: {h:.0f}h sem atualizar (limite {limite}h). "
                f"Uma unidade parada e as outras frescas e o sinal de rodada pela metade."))


def conferir_atas_vazias(achados):
    """Ata existe != reuniao aconteceu.

    Entre 18 e 22/10/2026, 28 pareceres dos cargos foram commitados com uma
    linha so: "Credit balance is too low". O erro da API virou o texto da ata,
    o script tratou como parecer valido e deu commit. Sete dias assim, sem um
    alarme -- porque todo mundo media que o commit existiu.
    """
    import re
    from datetime import date, timedelta
    pasta = REPO / "docs" / "atas"
    if not pasta.exists():
        return
    limite = (date.today() - timedelta(days=2)).isoformat()
    vazias = []
    for f in sorted(pasta.glob("*.md")):
        if f.name[:10] < limite:
            continue
        t = f.read_text(encoding="utf-8", errors="replace")
        # Erro de credencial, ou ata que nao tem corpo nenhum depois do cabecalho.
        corpo = re.sub(r"^---.*?---", "", t, flags=re.S).strip()
        corpo = re.sub(r"^#.*$|^↑.*$", "", corpo, flags=re.M).strip()
        # Erro de credencial so vale quando E o parecer (corpo curto). Um conselho
        # de 8 KB que cita "Credit balance is too low" esta relatando o problema.
        erro = re.search(r"credit balance|too low|quota|rate limit", corpo, re.I)
        if (erro and len(corpo) < 400) or len(corpo) < 120:
            vazias.append(f.name[:-3])
    # Ata que nao existe nao aparece em glob nenhum. Se o cargo gravou ontem e o
    # horario de hoje ja passou, a falta e o sinal (Operacao diaria, 23/10).
    from datetime import datetime
    agora = datetime.now()
    hoje_s, ontem_s = date.today().isoformat(), (date.today() - timedelta(days=1)).isoformat()
    for f in sorted(pasta.glob(f"{ontem_s}-*.md")):
        cargo = f.name[11:-3]
        if (pasta / f"{hoje_s}-{cargo}.md").exists():
            continue
        m = re.search(r"^hora:\s*(\d{1,2}):(\d{2})", f.read_text(encoding="utf-8", errors="replace"), re.M)
        if m and agora.hour * 60 + agora.minute > int(m[1]) * 60 + int(m[2]) + 90:
            achados.append(("aviso",
                f"Ata de {cargo} de hoje nao existe (ontem saiu as {m[1]}:{m[2]}). "
                f"A tarefa agendada nao rodou ou nao commitou."))
    if vazias:
        achados.append(("erro",
            f"{len(vazias)} ata(s) dos ultimos 2 dias sem parecer de verdade "
            f"({', '.join(vazias[:4])}{'...' if len(vazias) > 4 else ''}). "
            f"O cargo rodou e nao produziu nada -- credencial, permissao de "
            f"escrita ou limite de uso."))


def conferir_decisoes_sem_desfecho(achados):
    """O bloco que o painel le existe, e alguem esta fechando o ciclo?

    Duas conferencias diferentes:
      1. o derivado sobreviveu (regra da casa: bloco que some nao avisa)
      2. ha decisao muito velha sem desfecho -- o sintoma que esta peca mede

    O numero de corte e 60 dias porque e o prazo que a propria casa usa: "decisao
    que nao vira nota e decisao que vai ser retomada do zero daqui a dois meses".
    """
    d = carregar("data/decisoes.json")
    if not d:
        achados.append(("aviso",
            "data/decisoes.json ausente — o /conselho le este arquivo para a secao "
            "de decisoes sem desfecho (saiu do painel em 23/10/2026). "
            "Rode scripts/decisoes_abertas.py."))
        return
    g = str(d.get("gerado_em") or "")[:10]
    hoje = datetime.date.today().isoformat()
    if g and g < hoje:
        achados.append(("aviso", f"Decisoes: o bloco e de {g} e hoje e {hoje}."))
    if (d.get("mais_antiga_dias") or 0) >= 60:
        achados.append(("aviso",
            f"{d['n_abertas']} decisao(oes) sem desfecho registrado, a mais antiga "
            f"ha {d['mais_antiga_dias']} dias. Decisao que nao vira nota e retomada "
            f"do zero dois meses depois."))


def conferir_override_tem_todos_os_leitores(achados):
    """Campo que vence sobre outro foi ensinado a TODOS os leitores do antigo?

    Em 30/09/2026 nasceu `meta_mensal_por_mes[YYYY-MM]`, que vence sobre
    `meta_mensal`. O DRE do Spa aprendeu a ler; o painel do Spa nao. Por 23 dias
    as duas telas mostraram metas diferentes para o mesmo mes -- R$ 50.000 contra
    R$ 40.000 -- e a decisao "religar a verba do Spa" voltou quatro vezes a mesa
    sem ninguem conseguir dizer de quanto era o buraco.

    Nao e conferencia de dado, e de codigo: quem le o campo antigo tem de
    conhecer o override. Ver docs/aprendizados/campo-novo-de-config-tem-mais-de-um-leitor.md

    Para somar um par novo, basta acrescentar em PARES: (campo antigo, override).
    """
    PARES = [("meta_mensal", "meta_mensal_por_mes"),
             ("super_meta_mensal", "super_meta_mensal_por_mes")]
    raiz = pathlib.Path(__file__).resolve().parent
    for antigo, override in PARES:
        for py in sorted(raiz.glob("*.py")):
            if py.name == pathlib.Path(__file__).name:
                continue
            try:
                src = py.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            # le o campo antigo de um dicionario de config?
            le_antigo = (f'get("{antigo}")' in src or f"get('{antigo}')" in src
                         or f'["{antigo}"]' in src)
            if le_antigo and override not in src:
                achados.append(("erro",
                    f"{py.name} le `{antigo}` e nao conhece `{override}`. O override "
                    f"nasceu para vencer sobre ele: este leitor vai mostrar numero "
                    f"diferente dos que ja aprenderam. Foi exatamente o que escondeu "
                    f"a meta do Spa por 23 dias."))


def conferir_preco_realizado(achados):
    """O card de preco voltou a comparar com o que foi cobrado?

    O card antigo comparava a tabela da franqueadora com o preco CADASTRADO no
    Trinks e nunca olhava quanto saiu. Em 18/09 ele acusou "36 servicos fora da
    tabela"; o achado foi redecidido em 11/10 e em 16/10 ganhou dono — a gerente
    da loja. Um mes cobrando de alguem um numero que media pacote sendo
    consumido. Se `scripts/preco_praticado.py` parar de rodar, o card volta a
    acusar desconto inexistente e a conversa comeca de novo.
    """
    for rel, nome in (("data/dashboard_data.json", "Escova"),
                      ("data/spa/dashboard_data.json", "Spa"),
                      ("data/consolidado/dashboard_data.json", "Consolidado")):
        d = carregar(rel)
        if not d:
            continue
        pr = ((d.get("catalogo_servicos") or {}).get("preco_realizado") or {})
        if not pr.get("itens"):
            achados.append(("aviso",
                f"{nome}: `catalogo_servicos.preco_realizado` ausente — "
                f"scripts/preco_praticado.py nao rodou. O card de preco volta a "
                f"comparar com o cadastro em vez do que foi cobrado, e passa a "
                f"acusar resgate de pacote como desconto."))
            continue
        g = str(pr.get("gerado_em") or "")[:10]
        hoje = str(d.get("hoje") or "")[:10]
        if g and hoje and g < hoje:
            achados.append(("aviso",
                f"{nome}: a apuracao de preco e de {g} e o painel e de {hoje}."))
        n_cad = pr.get("n_cadastro_desatualizado") or 0
        if n_cad:
            achados.append(("aviso",
                f"{nome}: {n_cad} servico(s) cobrados ACIMA do preco do catalogo do "
                f"Trinks. Ou o preco subiu e ninguem registrou, ou esta sendo "
                f"lancado no servico errado — confira em `preco_realizado.acoes`."))


def conferir_taxa_comissao(achados):
    """Categoria sem taxa cadastrada cai no padrao de 30% em silencio.

    Em 18/10/2026 o Spa aparecia com taxa efetiva de 29,64% contra 25% da
    DRE. A leitura obvia — "a comissao do Spa esta acima do provisionado" —
    estava errada: 92,8% da base executada dele cai em CORPORAL e ADICIONAIS,
    dois nomes que nao existem no comissoes.json, e o fallback de 30% inflou a
    conta em R$ 605 no mes. O proprio arquivo diz "SPA uniforme 25% em todas as
    categorias". ADICIONAIS vs "Adicional": uma letra.

    Na Escova o desvio e real (UNHAS pesa 39% da base a 50%), mas MAKE cai nos
    30% quando "Maquiagem" esta mapeada a 40% — para o outro lado.

    Comissao paga gente. Numero errado aqui nao e card feio, e folha errada.
    """
    for rel, nome in (("data/dashboard_data.json", "Escova"),
                      ("data/spa/dashboard_data.json", "Spa")):
        d = carregar(rel)
        if not d:
            continue
        com = d.get("comissoes") or {}
        faltam = com.get("categorias_sem_taxa") or []
        if not faltam:
            continue
        # Quanto da base executada do mes esta nessas categorias
        ex = ((d.get("abas") or {}).get("mensal") or {}).get("ranking_prof_executor") or []
        base = sem = 0.0
        alvo = {str(x).strip().lower() for x in faltam}
        for p in ex:
            for cat, v in (p.get("por_cat") or {}).items():
                base += v
                if str(cat).strip().lower() in alvo:
                    sem += v
        pct = (sem / base * 100) if base else 0
        tipo = "erro" if pct >= 50 else "aviso"
        achados.append((tipo,
            f"{nome}: {len(faltam)} categoria(s) de servico sem taxa de comissao "
            f"cadastrada ({', '.join(faltam[:4])}) — caem no padrao de "
            f"{(com.get('regra_padrao_pct') or 0.30) * 100:.0f}%. Sao "
            f"{brl(sem)} de {brl(base)} da base executada do mes ({pct:.1f}%). "
            f"Enquanto nao entrarem no data/comissoes.json, a comissao por "
            f"profissional e a taxa efetiva estao erradas — e comissao paga gente."))


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

    conferir_calendario_e_metas(achados, dash["escova"], dash["spa"], dash["consolidado"])
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

    conferir_taxa_comissao(achados)
    conferir_preco_realizado(achados)
    conferir_caixa_a_receber(achados)
    conferir_estoque(achados, fin)
    conferir_saude_automacoes(achados)
    conferir_atas_vazias(achados)
    conferir_decisoes_sem_desfecho(achados)
    conferir_override_tem_todos_os_leitores(achados)
    for _u in ("escova", "spa", "consolidado"):
        conferir_placar_agencia(achados, dash.get(_u), _u.capitalize())
    for _u in ("escova", "spa"):
        conferir_contra_trinks(achados, dash.get(_u), _u)
    conferir_funil_roas(achados)
    conferir_conselho_sincronizado(achados)

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
