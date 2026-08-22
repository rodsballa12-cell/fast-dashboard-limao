"""Gera comentários acionáveis por aba do dashboard FAST Limão (walk-in only).

Cada aba retorna uma lista de {tipo, titulo, texto, acao} onde:
- titulo: manchete curta e específica
- texto: o QUE está acontecendo com número concreto
- acao: DECISÃO recomendada com impacto financeiro estimado quando possível

Tipos: critico > atencao > oportunidade > info
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

BRT = timezone(timedelta(hours=-3))  # Brasília sem DST

CDI_ANUAL = 0.145
CDI_MENSAL = (1 + CDI_ANUAL) ** (1/12) - 1  # ~1,133% a.m.
TAXA_ANTECIP_STONE = 0.0166                  # 1,66% a.m. Automática SIIBELLO
MDR_CREDITO = 0.0208

META_TICKET_MIN = 100
META_CATEG_PRODUTOS_PCT = 8
META_RETENCAO_PCT = 40  # walk-in maduro fica em 40-60% após 6 meses


def _fmt(v, prefix="R$ "):
    try:
        return f"{prefix}{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return f"{prefix}0,00"


def _mk(tipo, titulo, texto, acao=None):
    return {"tipo": tipo, "titulo": titulo, "texto": texto, "acao": acao or ""}


def _nome_mes(ym):
    nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    try:
        return nomes[int(ym.split("-")[1]) - 1]
    except Exception:
        return ym


# ============================================================
# DIÁRIO
# ============================================================
def _insights_diario(aba, hora_media_semanal, hoje: date):
    ins = []
    k = aba.get("kpis", {})
    m = aba.get("meta", {})
    hora_now = datetime.now(BRT).hour

    # 1. Ritmo do dia vs meta diária
    if m.get("meta"):
        pct = m.get("pct", 0)
        falta = m.get("falta", 0)
        if pct >= 100:
            ins.append(_mk("oportunidade", "Meta do dia batida",
                f"Caixa {_fmt(k.get('caixa',0))} já superou a meta diária de {_fmt(m['meta'])} ({pct:.0f}%).",
                "Toda venda daqui pra frente é margem pura. Oferecer produto adicional pra levar ticket médio pra cima."))
        elif pct >= 70 and hora_now < 18:
            ins.append(_mk("info", "Dia caminhando bem",
                f"{_fmt(k.get('caixa',0))} / {_fmt(m['meta'])} ({pct:.0f}%). Faltam {_fmt(falta)}.",
                "Manter cadência. Duas ou três escovas + hidratação fecham o dia."))
        elif pct < 50 and hora_now >= 15:
            horas_rest = max(0, 20 - hora_now)
            ins.append(_mk("atencao", "Ritmo abaixo do esperado",
                f"Só {pct:.0f}% da meta às {hora_now}h com {horas_rest}h úteis restantes.",
                "Postar story/status no WhatsApp com 'últimas vagas hoje' pode gerar 2-3 walk-ins na última hora."))

    # 2. Próximos picos previstos (base semanal)
    if hora_media_semanal and hora_now < 19:
        top_horas_fut = sorted(
            [h for h in hora_media_semanal if h.get("h", 0) > hora_now and h.get("media", 0) > 0.5],
            key=lambda x: -x.get("media", 0),
        )[:2]
        if top_horas_fut:
            hs = ", ".join(f"{h['h']}h ({h['media']:.1f} clientes/hora)" for h in top_horas_fut)
            ins.append(_mk("info", "Picos previstos ainda hoje",
                f"Base semanal aponta {hs} como as próximas horas de fluxo.",
                "Deixar equipe pronta nessas horas — sem pausa para almoço/lanche dentro dessas janelas."))

    # 3. Profissionais parados
    ranking = aba.get("ranking_prof") or []
    if len(ranking) >= 2 and k.get("atend_fin", 0) >= 4 and hora_now >= 14:
        zerados = [p for p in ranking if p.get("v", 0) == 0]
        if zerados:
            nomes = ", ".join(p.get("nome", "?").split()[0] for p in zerados[:3])
            ins.append(_mk("atencao", f"{len(zerados)} profissional(is) sem atendimento hoje",
                f"{nomes} ainda em zero de receita. Se não está em folga, é capacidade ociosa perdida.",
                "Realocar walk-ins da fila para elas. Se agenda continuar vazia, avaliar reduzir dia de trabalho na próxima semana."))

    # 4. Ticket do dia
    if k.get("n_trans", 0) >= 3:
        tkt = k.get("ticket_trans", 0)
        if tkt < META_TICKET_MIN * 0.7:
            ins.append(_mk("oportunidade", "Ticket médio do dia baixo",
                f"Ticket médio {_fmt(tkt)} — abaixo do saudável ({_fmt(META_TICKET_MIN)}).",
                "Padrão do dia é serviço avulso barato. Combo escova+hidratação (R$ 120) resolve. Falar com equipe agora."))
    return ins


# ============================================================
# SEMANAL
# ============================================================
def _insights_semanal(aba, mes_por_dow=None):
    ins = []
    k = aba.get("kpis", {})
    m = aba.get("meta", {})

    # 1. Meta semanal → projeção
    if m.get("meta") and m.get("dias_realizados", 0) > 0:
        pct = m.get("pct", 0)
        proj = m.get("projecao", 0)
        proj_pct = m.get("projecao_pct", 0)
        falta = m.get("falta", 0)
        need_dia = m.get("necessario_dia", 0)
        dias_rest = m.get("dias_restantes", 0)
        ritmo = m.get("ritmo_dia", 0)
        if proj_pct >= 100:
            ins.append(_mk("oportunidade", "Semana projeta bater meta",
                f"Projeção {_fmt(proj)} ({proj_pct:.0f}%). Ritmo atual {_fmt(ritmo)}/dia já basta.",
                "Semana no azul — usar a margem para testar preço ou combo novo sem risco."))
        elif proj_pct >= 85:
            ins.append(_mk("info", "Semana perto da meta",
                f"Projeção {_fmt(proj)} ({proj_pct:.0f}%). Precisa {_fmt(need_dia)}/dia nos {dias_rest} dias restantes vs atual {_fmt(ritmo)}/dia.",
                f"Faltam {_fmt(falta)}. Um sábado bom já fecha a semana."))
        else:
            gap = need_dia - ritmo
            ins.append(_mk("atencao", "Semana abaixo da meta",
                f"Projeção {_fmt(proj)} ({proj_pct:.0f}%). Gap de {_fmt(gap)}/dia para os {dias_rest} dias restantes.",
                "Ativar campanha WhatsApp pras top 20 clientes AGORA — retorno médio 3-4 walk-ins no fim de semana."))

    # 2. Melhor e pior dia da semana (base mensal)
    if mes_por_dow and len(mes_por_dow) >= 3:
        validos = [d for d in mes_por_dow if d.get("n", 0) > 0]
        if len(validos) >= 3:
            melhor = max(validos, key=lambda x: x.get("v", 0))
            pior = min(validos, key=lambda x: x.get("v", 0))
            if melhor.get("v", 0) > pior.get("v", 0) * 1.5 and pior.get("v", 0) > 0:
                ratio = melhor["v"] / pior["v"]
                ins.append(_mk("oportunidade", f"{melhor['nome']} rende {ratio:.1f}× {pior['nome']}",
                    f"{melhor['nome']}: {_fmt(melhor['v'])}/dia · {pior['nome']}: {_fmt(pior['v'])}/dia.",
                    f"Reforçar equipe no {melhor['nome']}. No {pior['nome']}, testar promoção ou reduzir 1 profissional pra cortar custo."))

    # 3. Concentração em 1 profissional
    ranking = aba.get("ranking_prof") or []
    if len(ranking) >= 2:
        total = sum(p.get("v", 0) for p in ranking)
        if total > 0:
            top = ranking[0]
            pct_top = top.get("v", 0) / total * 100
            if pct_top >= 40:
                ins.append(_mk("atencao", f"Concentração em {top.get('nome','?').split()[0]}",
                    f"{top['nome']} = {pct_top:.0f}% da receita da semana ({_fmt(top['v'])}). Se ficar doente ou pedir demissão, cai muita coisa junto.",
                    "Treinar 2ª profissional pros serviços que ela mais faz. Distribuir walk-ins de forma mais equilibrada nas próximas semanas."))

    return ins


# ============================================================
# MENSAL
# ============================================================
def _insights_mensal(aba, mes_anterior=None):
    ins = []
    k = aba.get("kpis", {})
    m = aba.get("meta", {})

    # 1. Projeção do mês
    if m.get("meta"):
        pct = m.get("pct", 0)
        proj = m.get("projecao", 0)
        proj_pct = m.get("projecao_pct", 0)
        need_dia = m.get("necessario_dia", 0)
        ritmo = m.get("ritmo_dia", 0)
        dias_rest = m.get("dias_restantes", 0)
        gap = need_dia - ritmo
        if proj_pct >= 100:
            excedente = proj - m['meta']
            ins.append(_mk("oportunidade", "Mês projeta ACIMA da meta",
                f"Projeção {_fmt(proj)} vs meta {_fmt(m['meta'])} ({proj_pct:.0f}%). Excedente estimado {_fmt(excedente)}.",
                f"Definir onde o excedente vai: reinvestir em marketing, comprar mais produto pra revenda, ou reserva de caixa."))
        elif proj_pct < 80:
            ins.append(_mk("critico", "Mês projeta ABAIXO de 80% da meta",
                f"Projeção {_fmt(proj)} ({proj_pct:.0f}%). Ritmo {_fmt(ritmo)}/dia vs necessário {_fmt(need_dia)}/dia. Gap: {_fmt(gap)}/dia.",
                f"Restam {dias_rest} dias úteis. Duas ações que funcionam: (1) mensagem para as top 30 clientes com combo do mês, (2) reforçar sáb/dom com todos os profissionais."))
        else:
            ins.append(_mk("atencao", "Mês precisa acelerar pra bater meta",
                f"Projeção {_fmt(proj)} ({proj_pct:.0f}%). Precisa +{_fmt(gap)}/dia acima do ritmo atual pelos próximos {dias_rest} dias.",
                "Foco: fechar cada walk-in com upsell (adicional escova + hidratação = +R$ 40 por atendimento)."))

    # 2. Comparação com mês anterior
    if mes_anterior:
        caixa_ant = mes_anterior.get("caixa", 0)
        caixa_atu = k.get("caixa", 0)
        dias_ant = mes_anterior.get("dias_op", 0)
        dias_atu = m.get("dias_realizados", 0)
        if dias_ant > 0 and dias_atu > 0:
            media_ant = caixa_ant / dias_ant
            media_atu = caixa_atu / dias_atu
            delta_pct = (media_atu / media_ant - 1) * 100 if media_ant > 0 else 0
            if abs(delta_pct) >= 10:
                tipo = "oportunidade" if delta_pct > 0 else "atencao"
                simbolo = "+" if delta_pct > 0 else ""
                acao_txt = ("Aumento consistente — vale entender o que mudou (equipe? campanha? sazonalidade?) e replicar."
                            if delta_pct > 0
                            else "Queda relevante — investigar: mesma equipe? mesma escala? algo mudou na região?")
                ins.append(_mk(tipo, f"Ritmo/dia {simbolo}{delta_pct:.0f}% vs mês anterior",
                    f"Este mês: {_fmt(media_atu)}/dia. Mês anterior: {_fmt(media_ant)}/dia.",
                    acao_txt))

    # 3. Ticket médio
    if k.get("ticket_trans", 0) > 0 and k.get("n_trans", 0) >= 20:
        tkt = k["ticket_trans"]
        n = k["n_trans"]
        if tkt < META_TICKET_MIN:
            upside = 20 * n
            ins.append(_mk("oportunidade", "Ticket médio abaixo do saudável",
                f"Ticket médio {_fmt(tkt)} vs referência {_fmt(META_TICKET_MIN)}. Volume: {n} transações no mês.",
                f"Cada +R$ 20 por atendimento = +{_fmt(upside)} no mês. Combos escova+hidratação e mãos+pés fazem isso naturalmente."))

    # 4. Retenção (novos vs recorrentes)
    nvr = aba.get("novos_vs_recorr") or {}
    if nvr:
        n_novos = (nvr.get("novos") or {}).get("clientes", 0)
        n_recorr = (nvr.get("recorrentes") or {}).get("clientes", 0)
        rec_novos = (nvr.get("novos") or {}).get("receita", 0)
        rec_recorr = (nvr.get("recorrentes") or {}).get("receita", 0)
        total = n_novos + n_recorr
        if total > 0:
            pct_recorr = n_recorr / total * 100
            if pct_recorr < META_RETENCAO_PCT:
                ins.append(_mk("atencao", f"Retenção baixa ({pct_recorr:.0f}% recorrentes)",
                    f"{n_novos} novos vs {n_recorr} recorrentes. Novos gastam {_fmt(rec_novos)}, recorrentes {_fmt(rec_recorr)}.",
                    "Loja abriu há pouco — normal ter muitos novos. Prioridade: fazer o cliente novo voltar. Cartão fidelidade + mensagem 20 dias após primeira visita costuma trazer 30% de volta."))
            else:
                ins.append(_mk("info", f"Retenção saudável ({pct_recorr:.0f}% recorrentes)",
                    f"{n_recorr} clientes voltaram — vale mais que 3× esse número em novos.",
                    "Continuar. Escalar aquisição sem sacrificar o cuidado com quem já vem."))

    # 5. Produtos sub-vendidos
    cats = aba.get("categorias") or {}
    prod = cats.get("produtos", {})
    caixa = k.get("caixa", 0)
    if caixa > 0 and prod.get("pct", 0) < META_CATEG_PRODUTOS_PCT:
        potencial = caixa * (META_CATEG_PRODUTOS_PCT / 100) - prod.get("v", 0)
        ins.append(_mk("oportunidade", "Produtos sub-vendidos no mês",
            f"Produtos = {prod.get('pct',0):.1f}% do caixa ({_fmt(prod.get('v',0))}). Se chegasse a {META_CATEG_PRODUTOS_PCT}%, seriam +{_fmt(potencial)}/mês.",
            "Vitrine no caixa + treinar a recepção pra oferecer 1 produto sempre no fechamento. Óleo/finalizador batem 90% de aceitação após escova."))

    # 6. Concentração top clientes (LTV)
    top_cli = aba.get("clientes_top") or []
    if len(top_cli) >= 5 and caixa > 0:
        # clientes_top só tem 'n' (visitas), não valor — usar top_ltv se disponível
        top_ltv_list = (aba.get("top_ltv") or {}).get("top") or []
        if len(top_ltv_list) >= 5:
            top5_valor = sum(c.get("v", 0) for c in top_ltv_list[:5])
            pct_top5 = top5_valor / caixa * 100
            if pct_top5 >= 25:
                nomes = ", ".join(c.get("nome", "?").split()[0] for c in top_ltv_list[:5])
                ins.append(_mk("atencao", f"Top 5 clientes = {pct_top5:.0f}% do caixa",
                    f"{nomes} concentram {_fmt(top5_valor)}. Perder uma dessas dói.",
                    "Tratamento VIP: reservar horário preferido, oferecer serviço extra grátis a cada 10 visitas, mensagem de aniversário."))

    return ins


# ============================================================
# ANUAL
# ============================================================
def _insights_anual(aba):
    ins = []
    k = aba.get("kpis", {})
    m = aba.get("meta", {})

    # 1. Meta anual
    if m.get("meta"):
        proj = m.get("projecao", 0)
        proj_pct = m.get("projecao_pct", 0)
        need_dia = m.get("necessario_dia", 0)
        ritmo = m.get("ritmo_dia", 0)
        if proj_pct >= 100:
            ins.append(_mk("oportunidade", "Ano projeta bater meta",
                f"Projeção {_fmt(proj)} ({proj_pct:.0f}%). Ritmo atual {_fmt(ritmo)}/dia já leva a meta.",
                "Planejar Q4 (nov/dez sempre são mais fortes por causa das festas). Reinvestir excedente em campanha de fim de ano."))
        elif proj_pct < 70:
            gap_ano = m.get("meta", 0) - proj
            ins.append(_mk("atencao", "Ritmo anual bem abaixo da meta",
                f"Projeção {_fmt(proj)} ({proj_pct:.0f}%). Precisa {_fmt(need_dia)}/dia (atual {_fmt(ritmo)}). Gap: {_fmt(gap_ano)}.",
                "Meta anual está agressiva pro ritmo atual. Duas rotas: (a) reduzir meta pra algo alcançável, (b) investir em captação — vale calcular custo por cliente novo primeiro."))

    # 2. Sazonalidade entre meses fechados
    meses = aba.get("meses") or {}
    if len(meses) >= 2:
        items = [(ym, v) for ym, v in meses.items() if v.get("caixa", 0) > 0]
        if len(items) >= 2:
            items.sort(key=lambda x: x[1]["caixa"])
            pior, melhor = items[0], items[-1]
            if melhor[1]["caixa"] > pior[1]["caixa"] * 1.3:
                ins.append(_mk("info", f"Sazonalidade: {_nome_mes(melhor[0])} > {_nome_mes(pior[0])}",
                    f"{_nome_mes(melhor[0])}: {_fmt(melhor[1]['caixa'])} · {_nome_mes(pior[0])}: {_fmt(pior[1]['caixa'])}.",
                    f"Prevê-se queda em {_nome_mes(pior[0])}: preparar promoção antecipada ou combo especial pra suavizar."))

    # 3. LTV top clientes
    ltv = (aba.get("top_ltv") or {}).get("top") or []
    if len(ltv) >= 10:
        top10_sum = sum(c.get("v", 0) for c in ltv[:10])
        caixa = k.get("caixa", 1)
        pct = top10_sum / caixa * 100
        avg = top10_sum / 10
        ins.append(_mk("info", f"Top 10 clientes = {_fmt(top10_sum)} ({pct:.0f}% do ano)",
            f"Média por cliente top: {_fmt(avg)}. Adquirir 1 novo cliente equivalente dá muito mais trabalho do que reter esses 10.",
            "Programa VIP: agenda prioritária + serviço-cortesia trimestral + surpresa de aniversário. Custo baixo, impacto alto."))

    # 4. Base de clientes: uma-vez vs recorrente
    top_ltv_all = aba.get("top_ltv") or {}
    uma = top_ltv_all.get("uma_vez", 0)
    duas = top_ltv_all.get("duas_mais", 0)
    total = uma + duas
    if total >= 20:
        pct_uma = uma / total * 100
        if pct_uma >= 45:
            ins.append(_mk("oportunidade", f"{uma} clientes vieram apenas 1 vez ({pct_uma:.0f}%)",
                f"Base tem {total} clientes únicos. Se converter 20% desses {uma} numa segunda visita, são ~{int(uma*0.2)} clientes a mais recorrentes.",
                "Campanha de reativação com voucher (R$ 30 off na próxima visita) pra quem só veio uma vez — investimento baixo, retorno alto."))

    return ins


# ============================================================
# STONE
# ============================================================
def _insights_stone(stone):
    ins = []
    if not stone:
        return ins

    por_p = stone.get("por_periodo") or {}
    mes = por_p.get("mes") or {}
    nc = stone.get("nao_conciliado") or {}

    # 1. PIX Trinks sem contrapartida no Stone — CRÍTICO (venda registrada, dinheiro NÃO caiu)
    orf_trinks = nc.get("orfaos_trinks") or []
    if orf_trinks:
        total = sum(o.get("valor", 0) for o in orf_trinks)
        ins.append(_mk("critico", f"{len(orf_trinks)} PIX registrado no Trinks mas SEM confirmação Stone",
            f"Total {_fmt(total)}. O sistema marca como recebido, mas o dinheiro NÃO caiu na conta.",
            "Verificar comprovante com o cliente hoje. Se não confirmar, corrigir Trinks pra não inflar caixa fantasma."))

    # 2. PIX Stone sem venda no Trinks — dinheiro entrou mas não foi lançado
    orf_stone = nc.get("orfaos_stone") or []
    if orf_stone:
        total = sum(o.get("valor", 0) for o in orf_stone)
        ins.append(_mk("atencao", f"{len(orf_stone)} PIX Stone SEM venda no Trinks",
            f"{_fmt(total)} caiu na conta mas não tem venda associada no sistema. Pode ser pagamento antecipado ou lançamento esquecido.",
            "Identificar cada cliente pelo nome do PIX e lançar retroativamente no Trinks — senão o DRE não bate no fim do mês."))

    # 3. Antecipação D+30 — vale a pena?
    a_receber = mes.get("resumo", {}).get("a_receber", 0)
    if a_receber >= 5000:
        custo_antecip = a_receber * TAXA_ANTECIP_STONE
        gasto_oport = a_receber * CDI_MENSAL
        liquido = custo_antecip - gasto_oport
        ins.append(_mk("info", f"{_fmt(a_receber)} a receber em cartão (D+30)",
            f"Antecipar tudo hoje custaria {_fmt(custo_antecip)} (1,66%). Se o dinheiro ficar parado 30d na aplicação Stone, você deixa de ganhar {_fmt(gasto_oport)} (CDI). Custo real da antecipação: {_fmt(liquido)}.",
            "Só antecipa se tem uso melhor pro dinheiro que render >14,5% a.a. Caso contrário, é mais barato esperar D+30."))

    # 4. Mix PIX vs Cartão
    taxa_pix = stone.get("taxa_pix_pct", 0)
    if taxa_pix >= 0.7:
        ins.append(_mk("oportunidade", f"PIX = {taxa_pix*100:.0f}% dos recebimentos",
            "Excelente pro fluxo: PIX cai D+0, cartão de crédito só D+30. E paga bem menos taxa.",
            "Manter incentivo ao PIX. Se rolar dar 3% de desconto por PIX ainda sobra margem — considere pra ticket alto."))
    elif taxa_pix < 0.4:
        ins.append(_mk("atencao", f"Só {taxa_pix*100:.0f}% em PIX",
            "Muito cartão significa dinheiro travado 30 dias e mais taxa (2,08% MDR + custo antecipação).",
            "Recepção deve pedir PIX PRIMEIRO. Se rolar 3-5% desconto no PIX, a margem paga o desconto e ainda melhora o fluxo."))

    # 5. Aplicação Stone rendendo
    app = stone.get("aplicacao_reserva") or {}
    saldo_app = app.get("saldo_aplicado", 0)
    if saldo_app >= 5000:
        rend_est = saldo_app * CDI_MENSAL
        ins.append(_mk("info", f"Aplicação Stone: {_fmt(saldo_app)}",
            f"Rendendo cerca de {_fmt(rend_est)}/mês se estiver acompanhando o CDI (14,5% a.a.). Bom hedge contra a antecipação.",
            "Confirmar no app Stone que a aplicação bate CDI. Se render menos, migrar pra Tesouro Selic ou CDB de banco digital (mesma liquidez, rendimento igual/melhor)."))

    return ins


# ============================================================
# AUDITORIA (novo)
# ============================================================
def _insights_auditoria(aud):
    ins = []
    if not aud or not aud.get("lista"):
        return ins
    r = aud.get("resumo_risco") or {}
    critico = r.get("critico", 0)
    atencao = r.get("atencao", 0)
    revisar = r.get("revisar", 0)

    if critico > 0:
        ins.append(_mk("critico", f"{critico} cancelamento(s) com padrão de skimming",
            "Nome do pagador no Stone bate com o cliente do agendamento cancelado. Isso é o padrão clássico de esconder receita.",
            "Abrir cada caso na aba Auditoria. Confrontar profissional envolvida hoje. Se confirmar, ação disciplinar."))
    elif revisar > 0:
        ins.append(_mk("atencao", f"{revisar} cancelamento(s) com valor/dia que batem no Stone",
            "Valor cancelado bate com um recebimento Stone do mesmo dia, mas o nome não confere. Provável colisão estatística (R$ 79 e R$ 47 são comuns), mas vale conferir.",
            "Revisar cada linha da aba Auditoria. Se for coincidência, sem ação. Se aparecerem 2+ envolvendo mesma profissional, aprofundar."))

    if atencao >= 3:
        # decompor atencao em sub-tipos
        lista = aud.get("lista") or []
        sem_prof = sum(1 for x in lista if x.get("sem_prof"))
        val_atip = sum(1 for x in lista if x.get("valor_atipico"))
        detalhe = []
        if sem_prof: detalhe.append(f"{sem_prof} sem profissional atribuída")
        if val_atip: detalhe.append(f"{val_atip} com valor fora do padrão")
        ins.append(_mk("atencao", f"{atencao} cancelamento(s) com anomalia operacional",
            f"Distribuição: {' · '.join(detalhe)}.",
            "Sem profissional → provavelmente registro velho do setup inicial da loja. Valor atípico → pode ser cortesia, meia porção ou erro de lançamento — perguntar à profissional."))

    return ins


# ============================================================
# GERADOR PRINCIPAL
# ============================================================
def gerar_insights(payload):
    """Retorna dict {aba: [insights]} para renderização."""
    abas = payload.get("abas") or {}
    stone = payload.get("stone")
    aud = payload.get("auditoria_cancelados")
    hoje = datetime.now(BRT).date()

    hora_media_sem = abas.get("semanal", {}).get("hora_media") or []
    semanal_por_dow = abas.get("semanal", {}).get("por_dow")

    # Mês anterior pra comparação — pega do anual.meses
    meses_ano = (abas.get("anual") or {}).get("meses") or {}
    mes_atual_ym = f"{hoje.year}-{hoje.month:02d}"
    mes_ant_ym = f"{hoje.year}-{hoje.month-1:02d}" if hoje.month > 1 else f"{hoje.year-1}-12"
    mes_anterior = meses_ano.get(mes_ant_ym)

    return {
        "diario":    _insights_diario(abas.get("diario", {}), hora_media_sem, hoje),
        "semanal":   _insights_semanal(abas.get("semanal", {}), semanal_por_dow),
        "mensal":    _insights_mensal(abas.get("mensal", {}), mes_anterior),
        "anual":     _insights_anual(abas.get("anual", {})),
        "stone":     _insights_stone(stone),
        "auditoria": _insights_auditoria(aud),
    }
