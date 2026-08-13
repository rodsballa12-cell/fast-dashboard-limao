"""Gera insights acionaveis por aba do dashboard FAST.

Cada aba recebe uma lista de recomendacoes com tipo (critico/atencao/oportunidade/info),
titulo curto e texto explicativo com valor concreto para o Rodrigo decidir.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

# Referencias de mercado (para calculos de custo de capital)
CDI_ANUAL = 0.145  # 14,5% a.a.
CDI_MENSAL = (1 + CDI_ANUAL) ** (1/12) - 1  # ~1,133% a.m.
TAXA_ANTECIP_STONE = 0.0166  # 1,66% a.m. Automatica (SIIBELLO)

# Metas de saudade do negocio
META_TICKET_MIN = 100  # ticket medio saudavel
META_CATEG_PRODUTOS_PCT = 8  # produtos deveriam ser >= 8% (upsell)
META_TAXA_CANC = 5  # cancelamento <= 5%
META_RETENCAO_PCT = 60  # >= 60% clientes recorrentes


def _fmt(v, prefix="R$ "):
    try:
        return f"{prefix}{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return f"{prefix}0,00"


def _mk(tipo, titulo, texto, acao=None):
    return {"tipo": tipo, "titulo": titulo, "texto": texto, "acao": acao or ""}


def _insights_diario(aba, hora_media_semanal, hoje: date):
    """Insights para HOJE."""
    ins = []
    k = aba["kpis"]
    m = aba.get("meta", {})
    hora_now = datetime.now().hour

    # 1. Meta do dia — ritmo vs previsto
    if m.get("meta"):
        pct = m.get("pct", 0)
        falta = m.get("falta", 0)
        if pct >= 100:
            ins.append(_mk("oportunidade", "Meta do dia BATIDA",
                f"{_fmt(k['caixa'])} vs meta {_fmt(m['meta'])} ({pct:.0f}%). Cada atendimento acima é upside puro.",
                "Manter cadência · promover pacote para próximas horas"))
        elif pct >= 70 and hora_now < 18:
            ins.append(_mk("info", "Meta do dia perto",
                f"{_fmt(k['caixa'])} de {_fmt(m['meta'])} ({pct:.0f}%). Faltam {_fmt(falta)}.",
                "Confirmar agendamentos das últimas horas · evitar no-show"))
        elif pct < 50 and hora_now >= 15:
            ins.append(_mk("atencao", "Ritmo do dia abaixo do esperado",
                f"Só {pct:.0f}% da meta às {hora_now}h. Restam ~{max(0, 20-hora_now)}h úteis.",
                "Priorizar walk-ins · confirmar agenda restante · combo do dia"))

    # 2. Horas de pico esperadas (baseado em media semanal)
    if hora_media_semanal:
        top_horas = sorted(hora_media_semanal, key=lambda x: -x.get("media", 0))[:3]
        top_horas_fut = [h for h in top_horas if h.get("h", 0) > hora_now]
        if top_horas_fut and hora_now < 18:
            hs = ", ".join(f"{h['h']}h" for h in top_horas_fut)
            ins.append(_mk("info", "Horas de pico ainda por vir hoje",
                f"Média semanal indica {hs} como picos. Preparar equipe/estoque.",
                "Confirmar profissionais nas próximas horas de pico"))

    # 3. Categoria menor vendida
    cats = aba.get("categorias") or {}
    prod = cats.get("produtos", {})
    if prod.get("pct", 0) < META_CATEG_PRODUTOS_PCT and k.get("atend_fin", 0) >= 3:
        ins.append(_mk("oportunidade", "Produto sub-vendido hoje",
            f"Produtos = {prod.get('pct', 0)}% do caixa (meta ≥ {META_CATEG_PRODUTOS_PCT}%). Cada cliente é upsell.",
            "Ofertar produto complementar ao final de cada atendimento"))

    # 4. Ranking profissionais — quem está travando
    ranking = aba.get("ranking_prof") or []
    if len(ranking) >= 2 and k.get("atend_fin", 0) >= 4:
        top = ranking[0]
        zerados = [p for p in ranking if p.get("caixa", 0) == 0 or p.get("atend", 0) == 0]
        if zerados:
            nomes = ", ".join(p.get("nome", "?") for p in zerados[:3])
            ins.append(_mk("atencao", f"{len(zerados)} profissional(is) sem atendimento",
                f"{nomes} sem receita hoje. Verificar se estão de folga ou com agenda vazia.",
                "Realocar demanda · promover slots livres via WhatsApp"))

    return ins


def _insights_semanal(aba, mes_por_dow=None):
    """Insights para SEMANA."""
    ins = []
    k = aba["kpis"]
    m = aba.get("meta", {})

    # 1. Meta semanal — projecao
    if m.get("meta") and m.get("dias_realizados", 0) > 0:
        pct = m.get("pct", 0)
        proj = m.get("projecao", 0)
        proj_pct = m.get("projecao_pct", 0)
        falta = m.get("falta", 0)
        need_dia = m.get("necessario_dia", 0)
        dias_rest = m.get("dias_restantes", 0)
        if proj_pct >= 100:
            ins.append(_mk("oportunidade", "Projeção semanal supera meta",
                f"Ritmo atual projeta {_fmt(proj)} ({proj_pct:.0f}%). Meta {_fmt(m['meta'])}.",
                "Manter · avaliar aumentar meta próxima semana"))
        elif proj_pct >= 85:
            ins.append(_mk("info", "Projeção semanal perto da meta",
                f"Projeta {_fmt(proj)} ({proj_pct:.0f}%). Precisa {_fmt(need_dia)}/dia nos {dias_rest} dias restantes.",
                f"Foco em manter ritmo · faltam {_fmt(falta)}"))
        else:
            ins.append(_mk("atencao", "Semana abaixo da meta",
                f"Projeção {_fmt(proj)} ({proj_pct:.0f}%). Precisa {_fmt(need_dia)}/dia (média atual: {_fmt(m.get('ritmo_dia', 0))}/dia).",
                "Ativar campanha WhatsApp · combo semana"))

    # 2. Melhor e pior dia da semana (base historica do mes)
    if mes_por_dow and len(mes_por_dow) >= 3:
        # Filtrar dias com pelo menos 1 atendimento
        validos = [d for d in mes_por_dow if d.get("atend", 0) > 0]
        if len(validos) >= 3:
            melhor = max(validos, key=lambda x: x.get("caixa", 0))
            pior = min(validos, key=lambda x: x.get("caixa", 0))
            if melhor.get("caixa", 0) > pior.get("caixa", 0) * 1.5:
                ratio = melhor["caixa"] / max(pior["caixa"], 1)
                ins.append(_mk("oportunidade", f"{melhor['dow']} rende {ratio:.1f}× mais que {pior['dow']}",
                    f"{melhor['dow']}: {_fmt(melhor['caixa'])}/dia · {pior['dow']}: {_fmt(pior['caixa'])}/dia.",
                    f"Promoção específica no {pior['dow']} · avaliar reduzir equipe nesse dia"))

    # 3. Concentracao de profissionais
    ranking = aba.get("ranking_prof") or []
    if len(ranking) >= 2:
        total = sum(p.get("caixa", 0) for p in ranking)
        top = ranking[0]
        pct_top = (top.get("caixa", 0) / max(total, 1)) * 100
        if pct_top >= 40:
            ins.append(_mk("atencao", f"Concentração em {top['nome']}",
                f"{top['nome']} = {pct_top:.0f}% da receita semanal ({_fmt(top['caixa'])}). Risco se ficar doente/sair.",
                "Distribuir agenda · treinar 2º profissional para os serviços de maior valor"))

    return ins


def _insights_mensal(aba):
    """Insights para MÊS."""
    ins = []
    k = aba["kpis"]
    m = aba.get("meta", {})

    # 1. Projeção mensal e ritmo necessário
    if m.get("meta"):
        pct = m.get("pct", 0)
        proj = m.get("projecao", 0)
        proj_pct = m.get("projecao_pct", 0)
        need_dia = m.get("necessario_dia", 0)
        ritmo = m.get("ritmo_dia", 0)
        dias_rest = m.get("dias_restantes", 0)
        gap_ritmo = need_dia - ritmo
        if proj_pct >= 100:
            ins.append(_mk("oportunidade", "Mês projetando acima da meta",
                f"Projeção {_fmt(proj)} ({proj_pct:.0f}%). Ritmo atual {_fmt(ritmo)}/dia > necessário {_fmt(need_dia)}/dia.",
                "Definir meta stretch · reinvestir excedente"))
        elif proj_pct < 80:
            ins.append(_mk("critico", "Mês projeta ABAIXO de 80% da meta",
                f"Projeção {_fmt(proj)} ({proj_pct:.0f}%). Ritmo {_fmt(ritmo)}/dia vs {_fmt(need_dia)}/dia (gap {_fmt(gap_ritmo)}/dia).",
                f"Ação imediata: campanha de reativação · combo dos {dias_rest} dias restantes"))
        else:
            ins.append(_mk("atencao", "Mês perto da meta mas ainda gap",
                f"Projeção {_fmt(proj)} ({proj_pct:.0f}%). Precisa +{_fmt(gap_ritmo)}/dia acima do ritmo atual.",
                "Confirmar agendamentos próximos · reduzir cancelamentos"))

    # 2. Ticket médio
    if k.get("ticket_trans", 0) > 0:
        tkt = k["ticket_trans"]
        if tkt < META_TICKET_MIN:
            ins.append(_mk("oportunidade", "Ticket médio baixo",
                f"Ticket = {_fmt(tkt)} (meta ≥ {_fmt(META_TICKET_MIN)}). +R$ 20 por atendimento = +{_fmt(20 * k['n_trans'])}/mês.",
                "Ofertar upsell/combo antes do agendamento · treinar recepção"))

    # 3. Taxa cancelamento
    if k.get("taxa_canc", 0) > META_TAXA_CANC:
        canc_pct = k["taxa_canc"]
        # estimar valor cancelado — usar ticket_atend se disponivel
        atend_fin = k.get("atend_fin", 0)
        est_canc_atend = atend_fin * (canc_pct / (100 - canc_pct))  # convertendo pct pra qtd
        est_canc_valor = est_canc_atend * k.get("ticket_trans", 0)
        ins.append(_mk("atencao", f"Taxa de cancelamento {canc_pct:.1f}% (meta ≤ {META_TAXA_CANC}%)",
            f"~{est_canc_atend:.0f} atendimentos cancelados no mês, receita perdida ~{_fmt(est_canc_valor)}.",
            "Política de confirmação 24h antes via WhatsApp · cobrar sinal em serviços longos"))

    # 4. Novos vs recorrentes
    nvr = aba.get("novos_vs_recorr") or {}
    if nvr:
        n_novos = (nvr.get("novos") or {}).get("clientes", 0)
        n_recorr = (nvr.get("recorrentes") or {}).get("clientes", 0)
        total = n_novos + n_recorr
        if total > 0:
            pct_recorr = (n_recorr / total) * 100
            if pct_recorr < META_RETENCAO_PCT:
                ins.append(_mk("atencao", f"Retenção baixa: {pct_recorr:.0f}% recorrentes",
                    f"{n_novos} novos · {n_recorr} recorrentes. Meta ≥ {META_RETENCAO_PCT}%. Custo de aquisição sobe.",
                    "Programa fidelidade · agendar retorno na saída · WhatsApp em D+30"))
            else:
                ins.append(_mk("info", f"Retenção saudável: {pct_recorr:.0f}% recorrentes",
                    f"{n_novos} novos + {n_recorr} recorrentes. Base leal — proteger.",
                    "Manter · escalar aquisição sem sacrificar retenção"))

    # 5. Categoria PRODUTOS
    cats = aba.get("categorias") or {}
    prod = cats.get("produtos", {})
    serv = cats.get("servicos", {})
    if prod.get("pct", 0) < META_CATEG_PRODUTOS_PCT and serv.get("v", 0) > 0:
        # estimar upside se produtos chegassem a 8%
        caixa = k.get("caixa", 0)
        potencial = caixa * (META_CATEG_PRODUTOS_PCT / 100) - prod.get("v", 0)
        ins.append(_mk("oportunidade", "Produtos sub-vendidos no mês",
            f"Produtos {prod.get('pct',0)}% do caixa. Se chegasse a {META_CATEG_PRODUTOS_PCT}%, seriam +{_fmt(potencial)}/mês.",
            "Vitrine visível · treinar recepção para upsell no checkout"))

    # 6. Top clientes concentracao
    top_cli = aba.get("clientes_top") or []
    if len(top_cli) >= 5:
        top5_sum = sum(c.get("valor", 0) for c in top_cli[:5])
        caixa = k.get("caixa", 1)
        pct_top5 = (top5_sum / caixa) * 100
        if pct_top5 >= 30:
            nomes = ", ".join(c.get("nome", "?").split()[0] for c in top_cli[:5])
            ins.append(_mk("atencao", f"Top 5 clientes = {pct_top5:.0f}% do caixa",
                f"{nomes} concentram {_fmt(top5_sum)}. Perda de qualquer um impacta.",
                "Programa VIP · cortesia trimestral · monitorar frequência"))

    return ins


def _insights_anual(aba):
    """Insights ANO."""
    ins = []
    k = aba["kpis"]
    m = aba.get("meta", {})

    # 1. Meta anual — ritmo até 31/12
    if m.get("meta"):
        proj = m.get("projecao", 0)
        proj_pct = m.get("projecao_pct", 0)
        need_dia = m.get("necessario_dia", 0)
        ritmo = m.get("ritmo_dia", 0)
        if proj_pct >= 100:
            ins.append(_mk("oportunidade", "Ritmo anual bate meta",
                f"Projeção {_fmt(proj)} ({proj_pct:.0f}%). Ritmo {_fmt(ritmo)}/dia útil.",
                "Preservar cadência · planejar reinvestimento em Q4"))
        elif proj_pct < 85:
            ins.append(_mk("atencao", "Ritmo anual abaixo da meta",
                f"Projeção {_fmt(proj)} ({proj_pct:.0f}%). Precisa {_fmt(need_dia)}/dia (atual {_fmt(ritmo)}).",
                "Revisar precificação · escalar marketing digital"))

    # 2. Sazonalidade — melhor e pior mes
    meses = aba.get("meses") or {}
    if len(meses) >= 3:
        items = [(k2, v) for k2, v in meses.items() if v.get("caixa", 0) > 0]
        if len(items) >= 2:
            items.sort(key=lambda x: x[1]["caixa"])
            pior = items[0]
            melhor = items[-1]
            if melhor[1]["caixa"] > pior[1]["caixa"] * 1.3:
                nome_melhor = _nome_mes(melhor[0])
                nome_pior = _nome_mes(pior[0])
                ins.append(_mk("info", f"Sazonalidade: {nome_melhor} > {nome_pior}",
                    f"{nome_melhor}: {_fmt(melhor[1]['caixa'])} · {nome_pior}: {_fmt(pior[1]['caixa'])}.",
                    f"Ação: pacote/campanha em {nome_pior} para suavizar"))

    # 3. LTV top clientes — concentração e valor
    ltv = aba.get("top_ltv") or []
    if len(ltv) >= 10:
        top10_sum = sum(c.get("valor", 0) for c in ltv[:10])
        caixa = k.get("caixa", 1)
        pct = (top10_sum / caixa) * 100
        avg_top10 = top10_sum / 10
        ins.append(_mk("info", f"LTV Top 10 = {_fmt(top10_sum)} ({pct:.0f}% do ano)",
            f"Média por cliente top: {_fmt(avg_top10)}. Reter esses 10 vale o dobro de captar novos.",
            "Programa VIP · agenda prioritária · surpresa no aniversário"))

    return ins


def _nome_mes(ym):
    nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    try:
        m = int(ym.split("-")[1])
        return nomes[m - 1]
    except Exception:
        return ym


def _insights_stone(stone):
    """Insights STONE — antecipacao, MDR, fluxo."""
    ins = []
    if not stone:
        return ins

    por_p = stone.get("por_periodo") or {}
    mes = por_p.get("mes") or {}
    nc = stone.get("nao_conciliado") or {}

    # 1. Antecipacao vale a pena?
    a_receber = mes.get("resumo", {}).get("a_receber", 0)
    if a_receber >= 1000:
        # custo antecip 1,66% a.m. · CDI 14,5% a.a. ~1,13% a.m.
        # antecipar D+30 = pagar 1,66% agora vs ficar 30d parado (custo oport ~1,13%)
        custo_antecip = a_receber * TAXA_ANTECIP_STONE
        gasto_oport = a_receber * CDI_MENSAL
        liquido = custo_antecip - gasto_oport
        # se posso reinvestir a >= 15%aa, vale antecipar; se sobra >0.5%, vale pena
        if a_receber >= 5000:
            ins.append(_mk("oportunidade", "Antecipar D+30 tem custo real baixo",
                f"A receber: {_fmt(a_receber)}. Antecipação: {_fmt(custo_antecip)} (1,66%). Custo de oportunidade: {_fmt(gasto_oport)} (CDI). Custo líquido: {_fmt(liquido)}.",
                "Vale antecipar se caixa for reinvestido em algo >= CDI · senão, deixar cair no D+30"))

    # 2. PIX orfaos Stone (dinheiro entrou mas Trinks nao registrou)
    orf_stone = nc.get("orfaos_stone") or []
    if orf_stone:
        total = sum(o.get("valor", 0) for o in orf_stone)
        ins.append(_mk("atencao", f"{len(orf_stone)} PIX Stone SEM registro no Trinks",
            f"Total {_fmt(total)}. Dinheiro entrou mas venda não foi lançada.",
            "Investigar cliente por cliente · lançar em Trinks para bater DRE"))

    # 3. PIX orfaos Trinks (registrado no Trinks mas nao caiu)
    orf_trinks = nc.get("orfaos_trinks") or []
    if orf_trinks:
        total = sum(o.get("valor", 0) for o in orf_trinks)
        ins.append(_mk("critico", f"{len(orf_trinks)} PIX Trinks SEM confirmação Stone",
            f"Total {_fmt(total)} lançado como PIX mas dinheiro NÃO caiu ainda.",
            "Verificar comprovantes · cobrar cliente · corrigir Trinks se necessário"))

    # 4. Concentracao PIX vs Cartao
    taxa_pix = stone.get("taxa_pix_pct", 0)
    if taxa_pix >= 0.7:
        ins.append(_mk("oportunidade", f"PIX = {taxa_pix*100:.0f}% dos recebimentos",
            f"Alta % PIX é ótimo para caixa (D+0 vs D+30 do crédito). Baixo MDR.",
            "Continuar incentivando PIX · desconto de 3% pode ser upside líquido"))
    elif taxa_pix < 0.4:
        ins.append(_mk("atencao", f"Só {taxa_pix*100:.0f}% em PIX",
            f"Cartão de crédito D+30 trava fluxo de caixa. MDR ~2,08% + custo antecipação.",
            "Oferecer desconto 3-5% no PIX · treinar recepção para pedir PIX antes"))

    # 5. Aplicacao Stone
    app = stone.get("aplicacao_reserva") or {}
    saldo_app = app.get("saldo_aplicado", 0)
    if saldo_app >= 5000:
        rend_est_mes = saldo_app * CDI_MENSAL
        ins.append(_mk("info", f"Aplicação Stone: {_fmt(saldo_app)}",
            f"Rendimento estimado ~{_fmt(rend_est_mes)}/mês (CDI). Compara com custo antecipação.",
            "Verificar se aplicação Stone rende ≥ CDI · senão migrar para Tesouro/CDB"))

    return ins


def gerar_insights(payload):
    """Recebe o payload do dashboard e retorna dict {aba_nome: [insights]}."""
    abas = payload.get("abas") or {}
    stone = payload.get("stone")
    hoje = date.today()

    # media semanal de hora (base para insights diario)
    hora_media_sem = abas.get("semanal", {}).get("hora_media") or []

    return {
        "diario": _insights_diario(abas.get("diario", {}), hora_media_sem, hoje),
        "semanal": _insights_semanal(abas.get("semanal", {}), abas.get("semanal", {}).get("por_dow")),
        "mensal": _insights_mensal(abas.get("mensal", {})),
        "anual": _insights_anual(abas.get("anual", {})),
        "stone": _insights_stone(stone),
    }
