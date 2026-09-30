# Prompt da rotina de mídias — v2 (Escova + Spa)

Hora de regenerar as mídias das DUAS lojas com dados frescos do Supermetrics — rotina 2×/dia.
Antes de tudo: confirme que mcp____data_query e mcp____get_today existem nesta sessão. Se NÃO existirem, pare, não invente número, não commite e responda só: "❌ Perdi o conector Supermetrics nesta sessão — a rotina auto-vinculada não funciona mais; precisa anexar o conector a uma Routine pela UI do claude.ai."

Passos (tudo em /home/user/fast-dashboard-limao):
1. `git fetch origin main`. Se `git pull origin main --ff-only` falhar por histórico divergente, alinhe o main local ao origin/main (`git checkout -B main origin/main`) — o remoto é a verdade; commits locais de bot não valem nada.
2. Leia os TRÊS arquivos atuais — são o contrato de formato (mesmas chaves, mesma forma):
   - data/midias_sociais.json            (Escova — e os blocos meta_ads_spa / meta_ads_consolidado embutidos)
   - data/spa/midias_sociais.json        (Spa)
   - data/consolidado/midias_sociais.json (soma Escova + Spa)
   Chave desconhecida = PRESERVE.

Contas (não redescubra) — sempre timezone America/Sao_Paulo:
- Escova: Meta Ads FA act_1310973560614050 · Instagram IGI 17841439811993335 · Facebook FB 1177609485429072
- Spa:    Meta Ads FA act_1381925294040065 · Instagram @fastspa.limao (ig_user_id 17841441683971969, em data/config.json) · Facebook Fast Spa Limão (page id em data/config.json)

Janelas (converta get_today de UTC para BRT antes; D = hoje BRT): hoje D..D · 7d D-6..D · 30d D-30..D-1 · mtd dia 1..D · 90d D-89..D. As duas lojas usam as MESMAS janelas. Se a janela de 30d não andou desde o último refresh, não reconsulte os recortes de 30d (só os períodos móveis).

Para CADA loja, rode as mesmas consultas (campos e regras do prompt anterior: reach obrigatório em demografia/placement/campanhas/ad sets/anúncios; série completada com zeros até 30 pontos; CTR em %; deltas com compare_type=prev_range, compare_show=value; delta null quando o período anterior é zero):
- períodos hoje/7d/mtd/90d/30d; série diária 30d; por objetivo; campanhas; ad sets; anúncios; demografia; placement; região.
- Spa: preencher também data/spa/midias_sociais.json → meta_ads.breakdowns (hoje, 7d, mtd, 90d) com campanhas, ad sets, por objetivo, demografia e placement de cada janela. Spa começou a gastar em 09/09/2026: 90d = mtd enquanto não houver gasto anterior.
- Rode `campaign_and_resource_get` (status active) nas DUAS contas: conte campanhas ENABLED e some daily_budget dos ad sets ENABLED. Campanha que gastava e sumiu da lista de ativas é fato para o alerta (Spa: se a campanha de serviço parar, o gasto some sem "erro" nenhum).
- Instagram/Facebook das duas lojas: tente; se IGI der QUERY_AUTH_NOT_FOUND ou FB der LICENSE_DATA_SOURCE_NOT_AVAILABLE, preserve o bloco e registre no nota_conector — não invente.

Escrita:
- Escova → data/midias_sociais.json (regras de PRESERVAR/ATUALIZAR/REESCREVER do prompt anterior).
- Spa → data/spa/midias_sociais.json: mesmas regras; alertas_topo, deltas_vs_periodo_anterior, benchmarks (_atual_*), recomendacoes, direcionamentos_estrategicos e insights_narrativa reescritos com os números novos (não deixe texto de "pré-abertura" — o Spa abriu em 25/09). Preserve recomendações não-Meta (WhatsApp, Google Business).
- Consolidado → NÃO digite número. Depois de gravar Escova e Spa, rode `python3 scripts/consolida_midias.py`: ele soma as duas lojas, recalcula as razões, separa CPA de serviço × vaga POR LOJA, anexa o alarme de entrega e os alertas de cada loja em data/consolidado/midias_sociais.json. Os blocos meta_ads_spa / meta_ads_consolidado embutidos em data/midias_sociais.json seguem a mesma regra (Escova + Spa, nunca à mão).
- Separe leitura de vaga (recrutamento, conversa custa ~R$ 1–2) da de serviço no Spa: CPA de vaga não é CPA de cliente.
- Cuidado com afirmação forte: base nova; 1 visita não é churn (use churn_early do dashboard_data.json).
- status de campanhas/anúncios/placement só destes valores: escalar, manter, otimizar, revisar, matar, cortar, pausado, encerrado, aguardar, sem conversão, aguardar dados, manter (LINK_CLICKS), manter (AWARENESS).

Validação antes de commitar (nenhum pode falhar):
- `python3 scripts/validar_midias.py` (Escova)
- `python3 scripts/validar_midias.py data/spa/midias_sociais.json` — o único erro tolerado é "falta meta_ads.foco_geografico" (Spa não tem esse bloco); qualquer outro erro é seu.
- `python3 scripts/revisao_semanal.py > /dev/null` e `python3 scripts/auditoria_coerencia.py` (esta também confere que o consolidado usa um calendário só e a meta do Spa desde a abertura).

ALARME DE ENTREGA — para AS DUAS lojas:
`python3 scripts/alerta_entrega.py` e `python3 scripts/alerta_entrega.py data/spa/midias_sociais.json`
0 = normal (não notifique) · 1 = alerta/crítico (NOTIFIQUE) · 2 = não deu para avaliar (só mencione na resposta).
Se qualquer um sair 1: PushNotification status "proactive", UMA linha < 200 caracteres, sem markdown, começando pelo que o Rodrigo precisa fazer, com os números que o script imprimiu e nomeando a loja. Se os dois saírem 1, uma única notificação citando as duas. Queda que vem de campanha desativada (não de conta parada) também notifica, dizendo qual campanha parou. Nunca notifique quando ambos saírem 0.

Commit: `git add data/midias_sociais.json data/spa/midias_sociais.json data/consolidado/midias_sociais.json && git commit -m "midias: refresh <DD/MM HH:MM> BRT (escova + spa)" && git push origin main`. Push recusado → `git pull --rebase origin main`; se conflitar em arquivo de mídia, pegue a versão do remoto e REAPLIQUE sua atualização em cima (o workflow do Google escreve nesses arquivos também); nunca force. Nada mudou → não commite. Mexa APENAS nesses três arquivos.

PUBLICAR NO ARTEFATO — depois do push do commit (e só se houve commit):
1. `git pull --rebase origin main` e `python3 scripts/auditoria_coerencia.py` — auditoria vermelha NÃO publica (avise na resposta final).
2. `python3 scripts/build_artifact.py /tmp/painel.html` (embute os JSON; sem isso as abas Mídias abrem vazias).
3. `Artifact action=read url=https://claude.ai/artifact/3hfZcJU65a4VfNy8VYjmWD` (obrigatório antes de publicar).
4. `Artifact file_path=/tmp/painel.html url=https://claude.ai/artifact/3hfZcJU65a4VfNy8VYjmWD label="Mídias <DD/MM HH:MM> BRT · Escova + Spa"` — SEMPRE com esse url (sem ele cria um artefato novo); não passe favicon nem capabilities.
Se a sessão não tiver a ferramenta Artifact, pule este passo e diga na resposta final que o painel ficou com o dado antigo.

Resposta final, uma linha por loja: gasto 30d, conversas, CPA, resultado do alarme; e o alerta mais crítico geral (ou o erro); e se o artefato foi republicado.
