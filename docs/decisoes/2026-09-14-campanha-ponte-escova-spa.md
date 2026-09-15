# Campanha PONTE · levar a cliente da Escova para o Spa

**Data:** 2026-09-14 · **Status:** proposta, aguardando Rodrigo
**Departamento:** Marketing · **D-day:** 25/09/2026 (faltam 11 dias)

---

## 1. O ativo que ninguém está usando

A Escova tem, hoje, uma base própria — medida em `data/clientes_detalhes.json`
e `data/agendamentos_ano_cache.json` (fechamento 14/09/2026):

| Número | Valor | Por que importa |
|---|---|---|
| Clientes cadastradas | 411 | 339 mulheres (82%) |
| Com atendimento finalizado | 404 | base real, não cadastro frio |
| Ativas nos últimos 30 dias | 261 | passam na loja este mês |
| Recorrentes (2+ visitas) | 236 | já têm hábito de voltar |
| Telefone cadastrado | 411 (100%) | canal direto existe |
| Opt-in de marketing | 411 (100%) | permissão existe |
| Ticket médio por atendimento | R$ 62,24 | piso a ser elevado |

**A leitura:** uma conversa paga no Meta custa R$ 6,90 na Escova. Falar com
uma cliente que já está sentada na cadeira custa R$ 0,00. O Spa abre com uma
lista de 261 mulheres que passam fisicamente ao lado dele todo mês — e nenhuma
peça criada até agora fala com elas.

**Aritmética da meta:** meta do Spa = R$ 15.000/mês. Se 15% das 261 ativas
fizerem uma visita ao Spa no primeiro mês, a um ticket-alvo de R$ 280, são
~39 clientes e ~R$ 11.000 — cerca de 70% da meta vindo da base, sem mídia
nova. A 10%, são ~R$ 7.300. Este é o argumento central da campanha.

---

## 2. O que já existe (inventário real, 10 peças no Canva)

A pasta `C:\Users\rods_\OneDrive\Franquia - FAST\Claude\Pecas` **não é
acessível desta sessão** — este agente roda na nuvem, não no seu PC. O
inventário abaixo veio do Canva conectado, onde as 10 peças foram criadas
hoje (14/09). Se houver peça só no OneDrive que não subiu para o Canva, ela
não está contada aqui.

### Bloco COMBO (marca Escova) — 5 peças
| Peça | Texto | Link |
|---|---|---|
| Edgy Story | "COMBO CHEGANDO NA FAST LIMÃO · Mais de um cuidado. Uma passada só." | [ver](https://www.canva.com/d/kUXWxpvxEJEQ1af) |
| Elegant Teaser | "EM BREVE · Combo · CHEGOU NA FAST LIMÃO" | [ver](https://www.canva.com/d/xKD7pLgq47PTQ_A) |
| Luxurious Glow | "EM BREVE, Combo · Mais de um cuidado. Uma passada só." | [ver](https://www.canva.com/d/sst85wwCBNjznVZ) |
| Story CHEGOU COMBO | "CHEGOU COMBO · FAST ESCOVA LIMÃO" | [ver](https://www.canva.com/d/9P44Q3vQe0mWh6u) |
| Story CHEGOU COMBO 2 | "CHEGOU COMBO NA FAST LIMÃO · EM BREVE" | [ver](https://www.canva.com/d/moenCSIh-f-dgE4) |

### Bloco SPA (inauguração) — 4 peças
| Peça | Texto | Link |
|---|---|---|
| Textured Silk | "FALTAM 11 DIAS · fast spa limão · @fastspa.limao" | [ver](https://www.canva.com/d/WhEPJFm3PR2DLiA) |
| Elegant Spa Details | "INAUGURACAO · 25/09" | [ver](https://www.canva.com/d/SvYzYQmC2ZOUaDN) |
| Inviting Spa Setting | "Uma pausa só sua · INAUGURAÇÃO · 25/09" | [ver](https://www.canva.com/d/Dp31F7rcr0cZW6c) |
| Relaxing Spa Massage | "Massagem sem hora marcada · aqui do lado · 25/09" | [ver](https://www.canva.com/d/dMhmQRw24X9qIiv) |

### Peça com defeito — 1
"Sophisticated Portrait for FAST ESCOVA LIMÃO" traz texto corrompido:
*"Ailhot / CABELO + CORPONO MESMOLUGAR, / ac U 1-30"*. É texto gerado dentro
da imagem, embaralhado. **Não publicar.** A ideia por trás dela
("cabelo + corpo no mesmo lugar") é boa e vale refazer com texto editável.

### Diagnóstico do inventário

**O que está certo:** "Massagem sem hora marcada · aqui do lado" é a melhor
linha do conjunto inteiro. Diz o DNA da FAST (sem hora marcada), diz a
proximidade física e diz o serviço — em seis palavras. Está na peça menos
óbvia do lote.

**Os quatro problemas:**

1. **Nenhuma peça tem CTA.** Todas informam, nenhuma manda fazer nada. A
   régua do cargo é "CTA claro em todo post" — 10 de 10 estão fora dela.
2. **"EM BREVE" e "CHEGOU" convivem no mesmo lote.** Duas peças dizem que o
   combo chegou, três dizem que vem aí. Publicadas na mesma semana, a conta
   se contradiz.
3. **Nenhuma peça fala com a cliente da Escova.** Todas falam com um
   desconhecido do bairro. Não existe a peça que diz *"você, que já vem aqui
   toda semana"* — que é exatamente a campanha pedida.
4. **O combo é anunciado sem existir.** O Spa não tem tabela de preço no
   sistema (`data/spa/dashboard_data.json → catalogo_servicos` = tudo zero,
   `trinks_estabelecimento_id` = null). Peça que promete combo sem preço
   fechado gera conversa que a recepção não sabe responder.

---

## 3. Dois alertas que precedem qualquer peça

### 🔴 O token da Meta está inválido nas duas contas

`data/midias_sociais.json` e `data/spa/midias_sociais.json` (gerados hoje,
18h29 e 18h33) carregam, nos dois arquivos:

> `HTTP 400 · "Error validating access token: The session has been
> invalidated because the user changed their password or Facebook has
> changed the session for security reasons."`

Os números que o painel mostra são o último pull bem-sucedido, não dado de
agora. **Consequência prática:** enquanto o `META_ACCESS_TOKEN` não for
renovado, não há como medir a campanha nem criar/alterar anúncio. Renovar o
token é a tarefa zero — antes de qualquer criativo.

### 🟡 As conversas do Spa são currículo, não cliente

O Spa aparece com CPA de R$ 1,60 por conversa — 4x melhor que a Escova. É
ilusão de leitura. Das 131 conversas dos últimos 30 dias:

| Campanha | Conversas | CPA | O que é |
|---|---|---|---|
| [VAGA MASSOTERAPEUTA] 100926 | 52 | R$ 1,55 | contratação |
| [VAGA RECEPÇÃO] 100926 | 38 | R$ 0,94 | contratação |
| [VAGA MASSOTERAPEUTA] 090926 | 8 | R$ 1,14 | contratação |
| **[COMBO INAUG] 130926** | **10** | **R$ 7,64** | **comercial** |

Só 10 conversas comerciais, a R$ 7,64 — pior que a Escova (R$ 6,90), o que é
normal para conta nova sem histórico. Ninguém deve planejar verba com base no
R$ 1,60.

### 🟡 O canal mais barato da campanha está desligado

A WABA (WhatsApp Business) não existe em nenhuma das duas unidades — nunca
existiu (`data/spa/BRIEF_MARKETING.md`, correção de 14/09). São 411 telefones
com opt-in que não podem ser acionados por disparo. Até a WABA sair, a ponte
com a base tem que ser feita no balcão e no Stories, na mão.

---

## 4. A campanha · PONTE

**Ideia central:** a cliente já está sentada 45 minutos ao lado do Spa. A
campanha não precisa convencê-la a vir até o Limão — ela já está no Limão.
Precisa convencê-la a subir.

**Linha-mestra:** *"Você já vem cuidar do cabelo. Agora dá pra cuidar do
resto — aqui do lado, sem hora marcada."*

**Assimetria que decide os canais:** o Instagram da Escova alcançou 138.605
pessoas em 30 dias, com 1.828 seguidores. O do Spa alcançou 9.818, com 204.
O Spa não tem público — a Escova tem. Por três semanas, a conta da Escova é o
veículo de lançamento do Spa, não uma conta que "indica a outra".

### Canais, por custo de conversão

| # | Canal | Alcance | Custo | Estado |
|---|---|---|---|---|
| 1 | Balcão da Escova | 261 ativas/mês | R$ 0 | ✅ disponível hoje |
| 2 | Stories/Feed IG Escova | 138,6k/30d | R$ 0 | ✅ disponível hoje |
| 3 | WhatsApp 1:1 da base | 411 telefones | R$ 0 | 🔴 sem WABA |
| 4 | Meta Ads (público da Escova) | pago | verba | 🔴 token inválido |
| 5 | IG orgânico Spa | 9,8k/30d | R$ 0 | ✅ mas fraco sozinho |

**A peça mais importante desta campanha é física, não digital:** um cartão na
mão da cliente, entregue no pagamento, por quem acabou de fazer a escova
dela. Custo de impressão, conversão de balcão. Nenhum criativo de Instagram
compete com isso.

### Fase 1 · D-11 a D-1 (14 a 24/09) — "a base fica sabendo"

| Quando | Canal | Peça | CTA |
|---|---|---|---|
| Todo dia | IG Escova Stories | contagem regressiva (usar a "FALTAM 11 DIAS", trocando o número) | "arrasta pra cima e entra na lista" |
| 16/09 | IG Escova Feed | "Cabelo + corpo no mesmo lugar" (refazer a peça defeituosa) | "comenta EU QUERO" |
| 18/09 | Balcão | **cartão PONTE** (peça nova, ver §5) | entregue no pagamento |
| 20/09 | IG Escova Stories | caixinha "o que você faria com 30 min só seus?" | responder |
| 22/09 | IG Escova Feed+Reels | bastidor da montagem do Spa | "segue @fastspa.limao" |
| 24/09 | Ambos | "amanhã" | "chega a partir das X" |

### Fase 2 · D-0 a D+3 (25 a 28/09) — "abertura"

| Quando | Canal | Peça | CTA |
|---|---|---|---|
| 25/09 manhã | IG Escova + Spa | "ABRIU · Massagem sem hora marcada, aqui do lado" | "sobe e experimenta" |
| 25 a 28/09 | Balcão | cartão PONTE + convite verbal da profissional | agendar na hora |
| 25 a 28/09 | Stories | primeira cliente atendida (com autorização escrita) | "hoje ainda tem horário" |
| 27/09 (sáb) | IG Escova | "sábado de cuidar de você" | — |

### Fase 3 · D+4 a D+30 (29/09 a 25/10) — "vira hábito"

- **Combo Escova + Spa** vira produto de prateleira, com preço fechado.
- **Segmentação da base**: as 236 recorrentes recebem convite diferente das
  168 de visita única. Quem já volta toda semana é candidata a combo
  recorrente; quem veio uma vez é candidata a reativação com o Spa de isca.
- **Meta Ads** (depois do token): público personalizado com os 411 telefones
  da base + lookalike 1% desse público. É o público mais qualificado que a
  conta terá, e ainda não foi criado.
- **Medição**: campo `comoNosConheceu` na recepção do Spa precisa ter a opção
  **"Cliente da Escova"** desde o dia 1. Sem isso, a campanha inteira fica
  sem placar — o painel não consegue provar de onde veio a cliente.

---

## 5. Peças a criar (9) — copy pronta

Todas em tom FAST: feminino, direto, CTA no fim. Vocabulário: "chegada",
"combo", "profissional", "cuidar". Proibido: "milagre", "recupera", "escova
barata", nome de concorrente, promessa de resultado físico.

**1 · CARTÃO DE BALCÃO (frente/verso, impresso)** — *a peça mais importante*
> **Frente:** Você já está aqui. / Sobe. / **fast spa limão** · aqui do lado
> **Verso:** Massagem sem hora marcada, no mesmo endereço da sua escova.
> Av. Dep. Emílio Carlos, 358 · a partir de 25/09
> *Mostre este cartão na primeira visita.* → @fastspa.limao

**2 · STORY CONTAGEM (série diária, 11 peças de 1 arte)**
> FALTAM **[N]** DIAS / fast spa limão / *aqui do lado da sua escova*
> CTA: sticker "me avisa quando abrir"
> *(a arte "Textured Silk" já serve — só trocar o número e acrescentar a
> linha "aqui do lado da sua escova" e o sticker)*

**3 · FEED · CABELO + CORPO (refazer a peça defeituosa)**
> CABELO + CORPO / no mesmo lugar
> Legenda: "Você vem toda semana cuidar do cabelo. A partir de 25/09, dá pra
> cuidar do resto sem sair do prédio. Massagem sem hora marcada, aqui do
> lado. Comenta EU QUERO que a gente te avisa na abertura."

**4 · STORY · A CADEIRA E A MACA (foto dupla)**
> "45 minutos na cadeira. / 30 minutos na maca. / Uma passada só."
> CTA: "arrasta pra cima"

**5 · FEED · ABRIU (25/09)**
> ABRIU / fast spa limão / massagem sem hora marcada
> Legenda: "Aqui do lado da Fast Escova Limão, mesmo endereço. Sem hora
> marcada, como você já conhece. Sobe e experimenta."

**6 · STORY · PRIMEIRA CLIENTE** — foto real, **só com autorização escrita**
> "[Nome] fez a escova e subiu." / CTA: "hoje ainda tem horário"

**7 · CARROSSEL · COMO FUNCIONA (5 cards)**
> 1. Você faz sua escova como sempre / 2. Sobe / 3. Escolhe o cuidado /
> 4. Sem hora marcada / 5. Volta pra vida
> CTA: "salva esse post"

**8 · CRIATIVO DE ANÚNCIO · PONTE** (para quando o token voltar)
> Público: personalizado com os 411 telefones + lookalike 1%
> Copy: "Você já é cliente da Fast Escova Limão. O Fast Spa abriu no mesmo
> endereço. Massagem sem hora marcada. Chama no WhatsApp."
> *(mirar 45-54 e 35-44 feminino — são 51% da verba e os melhores CPAs da
> Escova hoje: R$ 8,06 e R$ 6,11)*

**9 · PEÇA DE OFERTA** — 🔒 **bloqueada, depende de você** (ver §6)

---

## 6. Três decisões que são suas, não minhas

**a) Qual é a oferta-ponte?** Três formatos possíveis:

| Formato | Como funciona | Custo real | Risco |
|---|---|---|---|
| **Experimentação** (recomendado) | 15 min de massagem grátis para cliente da Escova, na primeira visita, até 31/10 | tempo ocioso da agenda nova, não margem | ocupa agenda que poderia ser paga — pequeno nas 2 primeiras semanas |
| **Combo** | Escova + massagem por preço fechado | margem do combo | precisa de preço e de acerto com o massoterapeuta |
| **Valor** | R$ X de desconto na primeira visita | desconto direto | ancora o Spa no preço, não no cuidado |

A experimentação é a mais forte para a abertura: preenche agenda vazia, cria
a primeira experiência e não ensina a cliente a esperar desconto.

**b) Qual o preço do Spa?** Nenhuma peça com número pode sair sem isso. O
sistema não tem tabela do Spa (`catalogo_servicos` = zero,
`trinks_estabelecimento_id` = null).

**c) Qual a verba de mídia do Spa para outubro?** Hoje o Spa gastou R$ 79,65
(14/09), quase tudo em anúncio de vaga. Não há decisão de verba comercial
registrada.

---

## 7. O placar (o que eu vou cobrar de mim)

| Métrica | Meta 1º mês | Onde se mede |
|---|---|---|
| Clientes da Escova que visitaram o Spa | 39 (15% das 261 ativas) | `comoNosConheceu` = "Cliente da Escova" |
| Receita vinda da base | R$ 11.000 | Trinks Spa |
| CPA de conversa comercial do Spa | ≤ R$ 8,00 | `meta_ads` conta FS - LIMÃO |
| Seguidores @fastspa.limao | 204 → 800 | IG insights |
| Cartões PONTE entregues | 100% das clientes atendidas | contagem no balcão |

**Sem o campo `comoNosConheceu` configurado no Spa, nada disso tem placar** —
e a campanha vira opinião. Esta é a tarefa operacional número um antes de
25/09.

---

## 8. Ordem de execução (o que fazer primeiro)

| # | Tarefa | Quem | Prazo | Trava o quê |
|---|---|---|---|---|
| 1 | Renovar `META_ACCESS_TOKEN` | Rodrigo | hoje | toda medição e todo anúncio |
| 2 | Criar opção "Cliente da Escova" no cadastro do Spa | Rodrigo/Operação | até 24/09 | o placar inteiro |
| 3 | Decidir a oferta-ponte (§6a) | Rodrigo | até 17/09 | peças 1, 3, 9 |
| 4 | Imprimir cartão PONTE | Marketing | até 18/09 | o canal mais barato |
| 5 | Não publicar a peça defeituosa; refazer | Marketing | até 16/09 | — |
| 6 | Alinhar "EM BREVE" × "CHEGOU" no calendário | Marketing | até 15/09 | coerência da conta |
| 7 | Criar WABA das duas unidades | Rodrigo | até 20/09 | disparo para 411 telefones |
| 8 | Público personalizado (411 telefones) + lookalike | Marketing | após tarefa 1 | anúncio da fase 3 |

---

**Nada foi publicado, alterado ou gasto.** Criação e alteração de campanha
dependem da alçada registrada em `docs/decisoes/2026-09-14-alçada-campanha-marketing.md`:
mensagem do Rodrigo, na mesma sessão, com "aprovado"/"criar campanha" + nome
da campanha + valor diário.

---

## 9. Atualização 15/09 · o Spa não tem API da Trinks

**Confirmado em 15/09/2026**, rodando `trinks_discover.yml` (runs
34860767570 e 34911825308): a API key devolve `totalRecords: 1` — só o
estabelecimento **276461 · SAO PAULO - SP - LIMAO FE** (Escova). O Spa não é
visível por ela, e Rodrigo confirmou que **o Spa ainda não tem API
provisionada**.

### O que isso quebra além do preço

O §7 deste plano media a campanha pelo campo `comoNosConheceu` da recepção do
Spa. Esse campo mora na Trinks. Sem API, o painel não lê — e a campanha abre
**sem placar automático**. Também ficam de fora: agendamento, faturamento e
cadastro de cliente do Spa. O painel do Spa segue em `_mock: true`.

### Fallback obrigatório · folha de recepção

Uma planilha ou caderno na recepção do Spa, a partir de 25/09, uma linha por
cliente atendida:

| DATA | NOME | TELEFONE | VEIO DA ESCOVA? (S/N) | SERVIÇO | VALOR |
|---|---|---|---|---|---|

Resolve três coisas ao mesmo tempo:
1. **Mede a campanha** — a coluna "veio da Escova" é o placar.
2. **Alimenta o cadastro** quando a API for provisionada.
3. **Cruza com a base** — o telefone bate com as 411 clientes já cadastradas
   na Escova, permitindo medir de verdade quem migrou.

Sem essa folha, a única leitura possível no fim de outubro é opinião.

### O que continua bloqueado

| Item | Depende de | Estado |
|---|---|---|
| Preço nas peças | tabela digitada por Rodrigo ou API | 🔴 aberto |
| Peça 9 (oferta) | decisão da oferta + preço | 🔴 aberto |
| Peça "CHEGOU COMBO" (já pronta) | preço do combo | 🔴 parada |
| Placar automático | API Trinks do Spa | 🔴 sem previsão |
| Medição da campanha | folha de recepção | 🟡 fazer até 24/09 |

### O que NÃO depende de preço (pode andar hoje)

Peças 1 (cartão PONTE), 2 (contagem), 3 (cabelo + corpo), 4 (cadeira e maca),
5 (ABRIU), 6 (primeira cliente) e 7 (como funciona) — sete das nove. Nenhuma
carrega número. A campanha não precisa esperar a tabela para começar a
aquecer a base.

---

## 10. Atualização 15/09 · a tabela do Spa chegou

Recebida por print (3 páginas). Transcrita abaixo — esta passa a ser a
referência de preço até a API da Trinks existir.

### Terapia Corporal
| Serviço | Duração | Preço |
|---|---|---|
| Pós-operatório | 1h30 | R$ 229 |
| Fast Spa Detox 🆕 | 1h20 | R$ 199 |
| Fast Spa Casual | 1h | R$ 179 |
| Liberação Miofascial | 45min | R$ 179 |
| Renove-se em 45' | 45min | R$ 149 |
| Neuro Relax 🆕 | 45min | R$ 149 |
| Pernas e Pés Cansados | 45min | R$ 149 |
| Reflexologia Podal | 45min | R$ 149 |

### Outras linhas
| Serviço | Duração | Preço |
|---|---|---|
| Fast Aconchego (gestante, a partir do 3º mês) 🆕 | 1h | R$ 199 |
| Fast Spa Kids (6–12 anos) | 45min | R$ 129 |
| Banho de Lua | 1h | R$ 249 |
| Revitalização Corporal | 30min | R$ 109 |
| Pescoço & Colo | 30min | R$ 89 |
| Mãos | 20min | R$ 69 |
| **Ledterapia Capilar** | **7min** | **R$ 79** |
| Pós-operatório Facial | 45min | R$ 139 |
| Drenagem Linfática Facial | 15min | R$ 59 |
| Limpeza de Pele Super VIP + Spa dos Lábios | 1h15 | R$ 199 |
| Limpeza de Pele Casual | 1h | R$ 159 |
| Revitalização Facial | 30min | R$ 79 |
| Peeling Glow Revitalizante | 15min | R$ 129 |
| Hiper-hidratação Facial | 15min | R$ 79 |

### Combos e adicionais
- **Combo Fast Spa Detox** — R$ 457 · **Combo Fast Spa Casual** — R$ 437
- **Adicionais** (só acoplados a outro serviço), 10–15min, **todos R$ 59**:
  pedras quentes, ventosaterapia, liberação miofascial, manta térmica,
  máscara de LED, relaxante na cabeça, relaxante facial, mãos e antebraço,
  revitalização dos pés, revitalização das mãos
- **Pacotes** compre 10 leve +1 (de R$ 990 a R$ 2.290) e **Plano Smart**
  (–10%, uso de segunda a quarta)

---

### 10.1 · Correção de uma conta que eu dei errada

No §1 deste plano projetei R$ 11.000 vindos da base, usando o ticket-alvo de
R$ 280 que está na configuração do cargo. **Esse ticket não existe na
tabela.** O serviço avulso mais caro é R$ 249; a faixa real das terapias é
R$ 149–199. Só os combos (R$ 437 e R$ 457) passam de R$ 280.

Refazendo com preço real, 39 clientes da base (15% das 261 ativas):

| Cenário | Conta | Receita |
|---|---|---|
| Conservador | 39 × R$ 149 | R$ 5.811 |
| Com attach de adicional em 40% | + 16 × R$ 59 | **R$ 6.755** |
| Otimista (metade pega 1h+) | 39 × R$ 179 + attach | R$ 7.900 |

**A base carrega ~45% da meta de R$ 15.000, não 70%.** O resto tem que vir de
mídia paga e passante. Isso não enfraquece a campanha — ela continua sendo a
receita mais barata do mês —, mas desfaz a ideia de que a base sozinha
resolve setembro/outubro.

### 10.2 · O produto-ponte estava escondido na tabela

**LEDTERAPIA CAPILAR · 7 minutos · R$ 79.**

É o melhor produto de entrada do Spa para a cliente da Escova, por três
razões que nenhum outro serviço junta:

1. **É cabelo.** A cliente está no prédio exatamente por isso. Não exige
   mudar de assunto — "seu cabelo cai? sobe 7 minutos".
2. **São 7 minutos.** Cabe no intervalo entre lavar e escovar. Não compete
   com a agenda dela, não exige voltar outro dia.
3. **Não consome hora de massoterapeuta** — é aparelho. Numa loja que abre
   sem equipe rodada, isso importa.

**Recomendação de oferta-ponte (substitui a do §6a):** a experimentação
gratuita deixa de ser "15 min de massagem" e passa a ser **a Ledterapia
Capilar de 7 minutos, grátis na primeira visita para cliente da Escova, até
31/10**. Custa 7 minutos de aparelho, não uma hora de profissional.

**E o segundo argumento de venda está no preço:**
Drenagem Linfática Facial, 15min, **R$ 59** — menos que o ticket médio da
Escova (R$ 62,24). A frase de balcão se escreve sozinha: *"custa menos que
sua escova e leva 15 minutos"*.

### 10.3 · Quatro problemas que a tabela revelou

**1. "Combo" agora significa duas coisas.** Na Escova, as peças paradas no
Canva anunciam "CHEGOU COMBO" querendo dizer *mais de um cuidado numa
passada*. Na tabela do Spa, "Combo" é um produto fechado de R$ 437/457
(limpeza de pele + LED + terapia + drenagem). Publicar as duas coisas na
mesma semana faz a cliente pedir na recepção um combo que não existe pelo
preço que ela imaginou. **Decidir uma das duas antes de publicar.**

**2. O Plano Smart não serve para a cliente da Escova.** Ele vale de segunda
a quarta. A Escova concentra **76,4% dos atendimentos em quinta, sexta e
sábado** — sábado sozinho é 40,8%. A cliente da base vem no fim de semana; o
desconto está no começo. Não ancore a campanha PONTE no Plano Smart — ele é
produto para outro público (empresa, bairro, aposentada), não para quem sai
da cadeira da Escova.

**3. "Quick Massage" é vendida sem ter preço.** Aparece dentro do Combo Fast
Spa Casual e no pacote de R$ 990, mas não tem linha própria na tabela. A
recepção não vai saber cotar quando perguntarem avulso.

**4. "MÃOS" existe nas duas unidades com significados diferentes.** Na Escova
é manicure; no Spa é hidratação de 20min por R$ 69. Mesma palavra, dois
serviços, um prédio.

### 10.4 · A janela da campanha, medida

Distribuição real dos 967 atendimentos finalizados da Escova:

| Dia | Atendimentos | % |
|---|---|---|
| Sábado | 395 | 40,8% |
| Sexta | 200 | 20,7% |
| Quinta | 144 | 14,9% |
| Quarta | 81 | 8,4% |
| Segunda | 62 | 6,4% |
| Terça | 54 | 5,6% |
| Domingo | 31 | 3,2% |

Pico de horário: **16h–18h** (338 atendimentos na faixa).

**Consequência operacional:** o cartão PONTE tem que estar na mão de quem
atende **quinta, sexta e sábado, das 15h às 18h**. É quando 3 de cada 4
clientes da base passam pela loja. E a inauguração cai numa **sexta (25/09)**,
com o **sábado 27/09** logo em seguida — o dia de maior movimento da Escova no
ano inteiro. O Spa precisa estar com equipe completa nesse sábado.
