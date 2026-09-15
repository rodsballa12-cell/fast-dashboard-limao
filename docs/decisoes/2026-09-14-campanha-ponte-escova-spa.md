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

---

## 11. Atualização 15/09 · "pacote" substitui "combo"

**Decidido por Rodrigo em 15/09/2026.** A regra de vocabulário do cargo
`/marketing` dizia o oposto — *"combo" (não "pacote")*. Foi invertida em
`.claude/skills/marketing/SKILL.md` para não voltar atrás sozinha nas
próximas sessões.

### A colisão que isso cria, e como resolver

A tabela do Spa já usa as duas palavras, para **dois produtos diferentes**:

| Na tabela | O que é | Exemplo |
|---|---|---|
| "Combos" | vários cuidados **numa visita só** | Combo Fast Spa Detox · R$ 457 |
| "Tabela de Pacotes" | **10 sessões** do mesmo cuidado | Fast Spa Casual · R$ 1.790 |

Trocando "combo" por "pacote" nas peças, duas coisas muito diferentes passam
a se chamar igual: um produto de R$ 457 numa tarde e um de R$ 1.790 em dois
meses. A cliente pede "o pacote" no balcão e a recepção não sabe qual.

**Solução proposta — três palavras, três coisas:**

| Palavra | Significa | Onde já existe |
|---|---|---|
| **Pacote** | vários cuidados numa visita | substitui "combo" |
| **Plano** | várias sessões ao longo do tempo | **Plano Smart** já está na tabela |
| **Adicional** | 10–15 min acoplados, R$ 59 | já está na tabela |

"Plano" não é palavra nova — a própria tabela do Spa já batiza assim o
desconto de segunda a quarta. Só precisa valer para a linha inteira de
compre-10-leve-1, que hoje se chama "pacote".

**Se Rodrigo aprovar**, a tabela impressa precisa trocar o título "Tabela de
Pacotes" por "Planos" antes de 25/09. Se não aprovar, as peças usam "pacote"
e a recepção precisa de um script para desambiguar na hora.

### Peças afetadas

As cinco peças paradas no Canva dizem "COMBO". Todas precisam de ajuste de
texto antes de publicar:

| Peça | Texto atual | Vira |
|---|---|---|
| Story - CHEGOU COMBO | "CHEGOU COMBO · FAST ESCOVA LIMÃO" | "CHEGOU PACOTE..." |
| Story - CHEGOU COMBO NA FAST LIMÃO | "CHEGOU COMBO NA FAST LIMÃO · EM BREVE" | idem |
| Edgy Story | "COMBO CHEGANDO NA FAST LIMÃO" | "PACOTE CHEGANDO..." |
| Elegant Teaser | "EM BREVE · Combo · CHEGOU NA FAST LIMÃO" | "EM BREVE · Pacote..." |
| Luxurious Glow | "EM BREVE, Combo" | "EM BREVE, Pacote" |

Observação de redação: *"CHEGOU PACOTE"* soa pior que *"CHEGOU COMBO"* —
"pacote" pede artigo. A correção natural é **"CHEGOU O PACOTE"** ou, melhor
para o caso, **"CHEGARAM OS PACOTES"**. A linha de apoio
*"Mais de um cuidado. Uma passada só."* continua funcionando e passa a ser a
definição de pacote — vale mantê-la em todas.

---

## 12. Estratégia de migração · "As 50 Primeiras"

**Escrita em 15/09/2026, a pedido de Rodrigo.** Substitui a abordagem
genérica dos §4–5 por uma arquitetura fechada, com produto, preço, segmento,
calendário e teto de capacidade.

### 12.1 · O princípio: vender no sábado, entregar na terça

A leitura que organiza tudo está em dois números que parecem brigar:

- A Escova concentra **76,4%** do movimento em quinta, sexta e sábado —
  sábado sozinho é **40,8%**, com média de **49 clientes por sábado**.
- O desconto do Spa (Plano Smart, –10%) vale **de segunda a quarta**.

Quem lê rápido conclui que um não serve ao outro — foi o que este documento
disse no §10.3, e estava incompleto. A leitura certa é outra:

> **A Escova está lotada no sábado e vazia na terça. O Spa vai estar vazio na
> terça. É o mesmo problema, invertido.**

Pedir para a cliente fazer um serviço de Spa **no sábado** não cria receita
nova — compete com a hora mais cheia da própria Escova e ocupa a profissional
que já está no limite. Fazer a cliente **voltar na terça** é receita
incremental pura, num dia que hoje não existe para nenhuma das duas unidades.

Daí a arquitetura: **o sábado é o balcão de vendas. A terça é a entrega.**
A campanha não move a visita — ela cria uma segunda visita.

### 12.2 · Três produtos, em escada

**Degrau 1 · PASSE FUNDADORA — grátis, para as 404**

Ledterapia Capilar, 7 minutos, R$ 79 de valor, **grátis na primeira subida**
para quem é cliente da Escova, até 31/10.

Por que este e não outro: é cabelo (o motivo pelo qual ela já está no
prédio), são 7 minutos (cabe entre lavar e escovar) e é aparelho — **não
consome hora de massoterapeuta**, que é o recurso escasso na abertura.
Custo marginal perto de zero; função: fazer a cliente atravessar a porta uma
vez. Ninguém compra um serviço de R$ 149 num lugar em que nunca entrou.

**Degrau 2 · CARTELA FUNDADORA — a pré-venda do grupo VIP**

| | |
|---|---|
| O que é | 5 terapias de 45min (Renove-se em 45', Neuro Relax, Pernas e Pés ou Reflexologia — a escolha é da cliente, sessão a sessão) |
| Valor de tabela | 5 × R$ 149 = **R$ 745** |
| Preço fundadora | **R$ 490** — R$ 98 por sessão |
| Uso | segunda a quarta, até 31/12/2026 |
| Quantidade | **50 cartelas, numeradas de 1 a 50** |
| Onde | **só no grupo VIP**, 5 dias antes de qualquer outro canal |

R$ 98 por sessão é melhor que tudo o que existe na tabela hoje — o pacote
10+1 sai a R$ 135/sessão e o Plano Smart a R$ 122. É isso que faz dela uma
condição de fundadora, e não mais um desconto.

**A restrição de segunda a quarta não é uma concessão — é o produto.** É ela
que enche o dia vazio e que justifica o preço.

**Degrau 3 · O vínculo permanente**

A fundadora faz **Ledterapia Capilar grátis em toda escova que fizer**,
durante 2026.

Este é o degrau que transforma campanha em estrutura. Custa 7 minutos de
aparelho. Em troca, **toda visita à Escova passa a ter um toque no Spa** —
semana após semana, sem mídia, sem disparo, sem lembrete. A cliente não
precisa se lembrar do Spa: ela passa por ele toda vez que cuida do cabelo.

*(Prazo fechado em 2026 de propósito. Compromisso vitalício em lançamento de
loja é dívida que ninguém mede na hora de assumir.)*

### 12.3 · A base não é uma lista — são três

| Segmento | Qtd | O que é | Abordagem |
|---|---|---|---|
| **Embaixadoras** | **27** | 5+ visitas; a maior tem 44 visitas e R$ 2.155 gastos | Convite **nominal**, feito pela profissional que atende ela. Cartelas nº 1 a 27 reservadas. Não é venda — é "quero você na abertura". |
| **Fiéis** | **209** | 2 a 4 visitas; já têm hábito | Público-alvo da Cartela. É aqui que as 50 vagas se vendem. |
| **Adormecidas** | **168** | vieram uma vez e não voltaram | O Spa é a **desculpa de reativação** que a Escova não tinha. Não convide para voltar à escova — convide para conhecer o Spa com o Passe grátis. |

As 168 adormecidas são o ativo mais subestimado da operação. Uma tentativa de
reativação pela Escova já falhou por definição — elas não voltaram. Um
produto novo, no mesmo endereço, é o único argumento honestamente diferente
que existe.

### 12.4 · Por que o grupo VIP é o canal certo — e o único

Hoje, três canais estão bloqueados ao mesmo tempo: o token da Meta está
inválido (sem anúncio, sem medição), a WABA não existe em nenhuma das duas
unidades (sem disparo para os 411 telefones) e o Spa não tem API da Trinks
(sem placar automático).

**O grupo VIP não depende de nenhum dos três.** É o único canal direto,
permissionado e funcionando hoje. Isso não é um detalhe operacional — é o
motivo de a estratégia inteira ser construída sobre ele.

E ele resolve, de quebra, o problema de medição: **a cartela é numerada.**
Cada número vendido é um registro rastreável de quem veio da Escova, sem
depender de API nenhuma. O placar vem junto com o produto.

### 12.5 · O que torna o lançamento VIP especial (além do preço)

Desconto qualquer concorrente copia em uma tarde. O que não se copia:

1. **Número.** "Fundadora nº 7 de 50" — dito na entrega, impresso na cartela.
2. **Precedência.** O grupo VIP compra **5 dias antes** de o Instagram saber
   que existe. A informação é o prêmio, não só o preço.
3. **As três primeiras horas.** No sábado 27/09, das 9h às 12h, o Spa atende
   **só fundadoras**. O dia de maior movimento da Escova no ano, com a porta
   do lado aberta só para quem entrou primeiro.
4. **A parede.** Os 50 nomes numa placa na recepção do Spa. Custa uma placa.
   Dura anos.
5. **O preço travado.** Fundadora mantém condição Plano Smart em 2026, mesmo
   depois de a cartela acabar.

### 12.6 · Calendário — 12 dias

| Data | Canal | Movimento |
|---|---|---|
| **17/09 qui** | Grupo VIP | Teaser: "sexta eu abro 50 vagas de uma coisa que ainda não existe no Limão" |
| **18/09 sex** | Grupo VIP | **Abre a Cartela Fundadora.** 50 vagas. Só ali. |
| **18/09 sex** | Balcão | Profissionais convidam **nominalmente** as 27 embaixadoras |
| **19/09 sáb** | Balcão 15h–18h | **A maior janela de venda do período** — ~49 clientes na cadeira |
| **22/09 seg** | Grupo VIP | "Restam X de 50" (escassez real, número verdadeiro) |
| **24/09 qua** | IG Escova | Público geral descobre o Spa. Cartela **não** é oferecida aqui. |
| **25/09 sex** | Abertura | Fundadoras entram primeiro |
| **26/09 sáb** | Spa 9h–12h | **Exclusivo fundadoras** · 12h em diante, aberto |
| **A partir de 29/09 seg** | Spa | Começa a entrega das cartelas — o dia vazio deixa de ser vazio |

### 12.7 · Os números

**Receita da pré-venda (caixa antes de abrir):**

| Cenário | Cartelas | Caixa |
|---|---|---|
| Conservador | 25 de 50 | R$ 12.250 |
| Alvo | 40 de 50 | R$ 19.600 |
| Esgotado | 50 de 50 | **R$ 24.500** |

Vender 50 cartelas exige converter ~10% das 404 — ou ~25% de dois sábados de
balcão (98 clientes) somados ao grupo VIP. É ambicioso e é atingível.

⚠️ **Caixa não é receita do mês.** Entra antes de abrir e se converte em
serviço ao longo de três meses. Para fluxo de caixa de lançamento vale ouro;
para a meta de R$ 15.000/mês, entra diluído.

**O teto é a capacidade, não a demanda:**

50 cartelas × 5 sessões = **250 sessões de 45min** a entregar até 31/12.
Uma massoterapeuta em tempo integral, de segunda a quarta, entrega ~32
sessões/semana. Em ~13 semanas: ~430 sessões. **250 cabe, com folga de 40%.**

Se a contratação atrasar ou for meio período, **o teto cai junto** — 25
cartelas, não 50. Vender capacidade que não existe é a forma mais rápida de
transformar cliente fiel em cliente irritada.

### 12.8 · Três riscos, ditos antes

1. **Margem por sessão não validada.** R$ 98 por sessão de 45min precisa ser
   conferido contra a comissão da massoterapeuta. Se a comissão for 40%,
   sobram R$ 59 brutos por sessão. **Este é o único número desta estratégia
   que eu não consigo verificar** — a regra de comissão não está cadastrada
   no sistema. Rodrigo valida antes de a cartela ir ao ar.
2. **Canibalização do sábado.** Se a fundadora passar a usar o sábado no Spa
   em vez da escova, trocamos receita de lugar. A trava de segunda a quarta
   existe exatamente para impedir isso — **não abra exceção**, nem na semana
   de abertura.
3. **Promessa maior que a equipe.** Ver §12.7. O teto de vendas tem que ser
   recalculado no dia em que a equipe do Spa estiver fechada, não antes.

### 12.9 · O que trava hoje

| Precisa | De quem | Até |
|---|---|---|
| Validar margem de R$ 98/sessão | Rodrigo | 17/09 |
| Confirmar equipe do Spa (define o teto) | Rodrigo | 17/09 |
| Aprovar preço R$ 490 e a trava seg–qua | Rodrigo | 17/09 |
| Tamanho do grupo VIP (não sei quantas são) | Rodrigo | 16/09 |
| Imprimir 50 cartelas numeradas | Marketing | 18/09 |
| Folha de recepção (§9) | Operação | 24/09 |

---

## 13. Cartela Fundadora · mecânica detalhada

**Dados novos de Rodrigo, 15/09/2026:** comissão da massoterapeuta **30%**,
equipe **ainda em contratação**, grupo VIP da Escova com **67 integrantes**.

### 13.1 · A margem fecha

| | Cartela fundadora | Tabela cheia |
|---|---|---|
| Preço por sessão de 45min | R$ 98,00 | R$ 149,00 |
| Comissão 30% | R$ 29,40 | R$ 44,70 |
| **Contribuição por sessão** | **R$ 68,60** | R$ 104,30 |

Sacrifício: **R$ 35,70 por sessão** contra o preço cheio. Em troca vem caixa
antecipado, ocupação de um dia que hoje não existe e cinco visitas
garantidas de uma cliente que ainda não conhece o Spa.

Por cartela: R$ 490 de caixa, R$ 147 de comissão, **R$ 343 de contribuição**.

⚠️ **O que ainda não dá para afirmar:** se R$ 68,60 por sessão cobre o custo
fixo do Spa. O `data/spa/financeiro.json` está zerado — aluguel, energia e
rateio da unidade ainda não existem no sistema. A margem de contribuição está
correta; o lucro, não dá para calcular. Rodrigo é quem sabe se R$ 68,60 numa
hora de sala paga a hora da sala.

### 13.2 · 67 pessoas não compram 50 cartelas

Vender 50 cartelas para um grupo de 67 exigiria **75% de conversão** — não
acontece em nenhum canal, por melhor que seja a oferta.

Conversões realistas sobre 67:

| Conversão | Cartelas | Caixa |
|---|---|---|
| 15% (morno) | 10 | R$ 4.900 |
| 25% (bom) | 17 | R$ 8.330 |
| **37% (esgota o lote)** | **25** | **R$ 12.250** |
| 50% (excepcional) | 34 | R$ 16.660 |

**Decisão: o lote 1 são 25 cartelas, não 50.** Três motivos convergem:

1. **A escassez fica verdadeira.** 25 vagas para 67 pessoas é disputa real.
   50 vagas para 67 pessoas é uma vaga sobrando — e escassez que não morde
   não vende.
2. **A equipe não está fechada.** O §12.7 já dizia: teto cai junto com a
   contratação. Ela não fechou.
3. **Cabe folgado.** 25 cartelas = 125 sessões = **32% da capacidade** de uma
   profissional de segunda a quarta até 31/12. Sobra espaço para cliente de
   preço cheio no mesmo dia — que é o objetivo.

**O nome "As 50 Primeiras" continua de pé**, porque são 50 fundadoras no
total, em dois lotes:

| Lote | Qtd | Canal | Quando | Condição |
|---|---|---|---|---|
| **1** | 25 | **só grupo VIP** | 18 a 24/09 | nenhuma — vai agora |
| **2** | 25 | balcão + IG Escova | a partir de 29/09 | **só se a equipe estiver fechada E o lote 1 esgotar** |

O lote 2 esgotando o lote 1 vira notícia sozinho: *"as 25 primeiras acabaram
em 3 dias"* é a melhor peça de marketing que essa campanha pode ter, e ela é
gratuita.

### 13.3 · As regras da cartela

| Regra | Definição | Por quê |
|---|---|---|
| **O que dá direito** | 5 terapias de 45min | escolha sessão a sessão entre Renove-se em 45', Neuro Relax, Pernas e Pés Cansados e Reflexologia Podal |
| **Preço** | R$ 490 à vista (PIX) · até 3× de R$ 163,33 no cartão | parcelar levanta conversão; a taxa da Stone come parte — conferir no DRE |
| **Validade** | até **31/12/2026** | prazo curto força uso, uso cria hábito |
| **Uso** | **segunda, terça e quarta** | é o produto, não a concessão |
| **Hora marcada** | não — segue o DNA FAST | seg–qua o Spa está vazio, walk-in funciona |
| **Uma sessão presenteável** | 1 das 5 pode ser dada a outra pessoa | transforma cada fundadora em canal de captação |
| **Controle** | cartela física numerada, carimbada a cada uso + planilha na recepção | não existe API da Trinks no Spa (§9) |
| **Intransferível no restante** | as outras 4 são da titular | evita revenda |

A sessão presenteável é a peça mais subestimada dessa mecânica. Cada uma das
25 fundadoras pode trazer uma pessoa nova que nunca ouviu falar do Spa —
**até 25 clientes de aquisição a custo zero de mídia**, trazidas por quem já
confia na marca. Compare com R$ 6,90 por conversa no Meta.

### 13.4 · A entrega durante a semana

125 sessões distribuídas de 29/09 a 31/12, em 13 semanas de segunda a quarta:

| | |
|---|---|
| Sessões por semana | ~10 |
| Por dia (seg, ter, qua) | ~3 |
| Capacidade de uma profissional | ~10/dia |
| **Ocupação gerada pela cartela** | **~32%** |

Sobram ~7 vagas por dia para cliente de preço cheio. **A cartela não lota o
dia — ela dá um piso a um dia que hoje é zero**, e cria movimento que atrai
passante. Loja vazia não vende; loja com três clientes dentro vende.

**Ritmo esperado por fundadora:** 5 sessões em 13 semanas ≈ uma a cada 2 ou 3
semanas. É exatamente a frequência que cria hábito sem saturar.

### 13.5 · A sequência do grupo VIP

Quatro mensagens, nada mais. Grupo VIP que vira canal de anúncio diário
perde gente — e essas 67 são o ativo mais bem cuidado da operação.

**Mensagem 1 · quinta 17/09, manhã — só curiosidade, sem oferta**

> Meninas, sexta eu vou abrir aqui no grupo uma coisa que só vai existir
> para vocês 67.
>
> São 25 vagas. Quando acabar, acabou — e o Instagram só fica sabendo
> semana que vem.
>
> Amanhã, 10h. 💛

**Mensagem 2 · sexta 18/09, 10h — a oferta**

> Dia 25 abre o **Fast Spa Limão** — no mesmo prédio da sua escova, mesmo
> endereço, sem hora marcada. Massagem, tratamento facial, corporal.
>
> E vocês vão entrar antes de todo mundo.
>
> **CARTELA FUNDADORA · 25 vagas**
> 5 terapias de 45 minutos — você escolhe qual a cada visita:
> Renove-se em 45' · Neuro Relax · Pernas e Pés Cansados · Reflexologia Podal
>
> Na tabela: R$ 745
> **Fundadora: R$ 490** — R$ 98 a sessão, à vista ou em 3×
>
> O que só a fundadora tem:
> 🔢 sua cartela numerada de 1 a 25
> 🚪 o Spa só para vocês no sábado 26/09, das 9h às 12h
> 🎁 uma das 5 sessões você pode presentear quem quiser
> ✨ Ledterapia Capilar grátis em toda escova que fizer em 2026
> 🏛 seu nome na parede da recepção do Spa
>
> Uso de segunda a quarta, até 31/12.
>
> Quem quiser, responde **EU QUERO** aqui. Vou numerando na ordem.

**Mensagem 3 · segunda 22/09 — escassez verdadeira**

> Restam **[N] de 25**.
>
> [nomes das já numeradas, se autorizarem]
>
> Quinta abre o Spa. Quem entrar agora usa a primeira sessão na semana
> que vem.

**Mensagem 4 · quinta 25/09 — abertura**

> Abriu. 💛
>
> Fundadoras: sábado 9h às 12h o Spa é de vocês.
> Quem ainda não pegou cartela — restam [N] e o balcão começa a vender
> segunda.

**Regra para quem toca o grupo:** responder cada "EU QUERO" com o número
("você é a nº 9 💛"). O número é o produto tanto quanto a massagem.

### 13.6 · O que a recepção precisa saber decorado

1. **"Cartela é o quê?"** — 5 massagens de 45 min por R$ 490, usa de segunda
   a quarta até o fim do ano, você escolhe qual massagem a cada vez.
2. **"Posso usar sábado?"** — Não. A cartela é de segunda a quarta. No sábado
   o preço é o de tabela. *(Não abrir exceção: ver §12.8, risco 2.)*
3. **"E se eu não usar tudo?"** — Vale até 31/12. Depois disso não vale.
4. **"Posso dar de presente?"** — Uma das cinco, sim. As outras quatro são
   suas.
5. **"Quanto custa avulso?"** — R$ 149 a de 45 min.
6. **Se for cliente da Escova sem cartela** — Ledterapia Capilar de 7 min,
   grátis na primeira vez. *(Passe Fundadora, §12.2.)*

### 13.7 · O que falta para o lote 1 sair na quinta

| Precisa | Quem | Até |
|---|---|---|
| Aprovar R$ 490, trava seg–qua e lote de 25 | Rodrigo | 16/09 |
| Confirmar se R$ 68,60/sessão cobre o fixo do Spa | Rodrigo | 16/09 |
| Definir as 4 terapias elegíveis (proposta no §13.3) | Rodrigo | 16/09 |
| Imprimir 25 cartelas numeradas | Marketing | 17/09 |
| Planilha de controle na recepção | Operação | 18/09 |
| Quem responde o grupo VIP e numera | Rodrigo define | 17/09 |

---

## 14. Correção · o grupo VIP é só de aviso

**Rodrigo, 15/09/2026:** as 67 integrantes **não podem responder no grupo**.
É lista de transmissão / grupo com resposta bloqueada.

Isso invalida o mecanismo do §13.5, que mandava responder "EU QUERO" no
grupo. A copy daquela seção **não deve ser usada como está**.

### 14.1 · A arquitetura corrigida: três funções, três lugares

| Função | Onde acontece | Por quê |
|---|---|---|
| **Anunciar** | grupo VIP (transmissão) | 67 pessoas, canal direto, zero custo |
| **Fechar** | **balcão da Escova** | a cliente já está sentada, com a profissional na frente |
| **Recolher** | link de WhatsApp direto | para quem não passa na loja antes de 24/09 |

**O balcão passa a ser o canal principal de venda, e isso é uma boa notícia.**
Medindo as últimas 4 semanas, a janela de 18 a 24/09 tem:

| Dia | Atendimentos esperados |
|---|---|
| qui 18/09 | ~14 |
| sex 19/09 | ~30 |
| **sáb 20/09** | **~48** |
| seg 22/09 | ~7 |
| ter 23/09 | ~9 |
| qua 24/09 | ~15 |
| **Total** | **~124 clientes na cadeira** |

**25 cartelas em 124 atendimentos = 20% de conversão.** É uma meta de balcão
realista — muito mais do que pedir 37% de conversão de um grupo que nem
responder pode. E metade dessas 124 são clientes recorrentes, que já
conhecem a casa.

**Sábado 20/09 é o dia.** Quase metade da janela inteira num único dia, com
pico entre 15h e 18h.

### 14.2 · O link que substitui o "EU QUERO"

Para quem vê o aviso e não vem à loja, o CTA vira um link de WhatsApp com
texto já escrito — a cliente toca e só aperta enviar:

```
https://wa.me/5511966129197?text=Quero%20minha%20Cartela%20Fundadora
```

(número da Escova, `+55 11 96612-9197`, conforme
`data/config.json → unidades.escova.midia_ids.whatsapp_display_number`)

🔴 **Verificar antes de publicar:** esse número precisa ter WhatsApp ativo e
alguém respondendo. O `data/spa/BRIEF_MARKETING.md` registra que a WABA nunca
existiu e que **nenhuma mensagem jamais saiu por este sistema**. Conversa 1:1
no app comum funciona sem WABA — mas se o link cair num número que ninguém
atende, o lote morre na sexta-feira de manhã. **Testar mandando uma mensagem
para si mesmo antes das 10h de 18/09.**

### 14.3 · Por que a restrição ajuda

Três ganhos que o grupo aberto não daria:

1. **A loja controla o placar.** Ninguém disputa publicamente, ninguém
   reclama de ordem. "Restam 11" é o que a loja disser — e é verdade,
   porque a loja é quem numera.
2. **Venda vira conversa, não leilão.** No privado ou no balcão dá para
   explicar, contornar objeção e oferecer o parcelamento. No grupo, seria
   uma corrida.
3. **O grupo continua limpo.** 67 pessoas que aceitaram receber avisos não
   viram 67 pessoas conversando sobre preço. O ativo se preserva.

### 14.4 · Copy corrigida do grupo VIP

**Mensagem 1 · quinta 17/09, manhã**

> Meninas, amanhã às 10h eu abro aqui uma coisa que só existe para vocês 67.
>
> São 25 vagas. Quando acabar, acabou — e o Instagram só fica sabendo semana
> que vem. 💛

**Mensagem 2 · sexta 18/09, 10h**

> Dia 25 abre o **Fast Spa Limão** — mesmo prédio da sua escova, mesmo
> endereço, sem hora marcada.
>
> E vocês entram antes de todo mundo.
>
> **CARTELA FUNDADORA · 25 vagas**
> 5 terapias de 45 minutos — você escolhe qual a cada visita:
> Renove-se em 45' · Neuro Relax · Pernas e Pés Cansados · Reflexologia Podal
>
> Na tabela: R$ 745
> **Fundadora: R$ 490** — R$ 98 a sessão, à vista ou em 3×
>
> Só a fundadora tem:
> 🔢 cartela numerada de 1 a 25
> 🚪 o Spa só para vocês no sábado 26/09, das 9h às 12h
> 🎁 uma das 5 sessões você presenteia quem quiser
> ✨ Ledterapia Capilar grátis em toda escova que fizer em 2026
> 🏛 seu nome na parede da recepção
>
> Uso de segunda a quarta, até 31/12.
>
> **Como pegar a sua:**
> 👉 Vem na loja e fala com a gente — quinta, sexta ou sábado
> 👉 Ou toca aqui: wa.me/5511966129197
>
> A ordem dos números é a ordem de quem chegar. 💛

**Mensagem 3 · segunda 22/09**

> **Restam [N] de 25.**
>
> As fundadoras já numeradas vão receber a cartela na mão no dia da abertura.
>
> Quinta o Spa abre. Quem entrar agora usa a primeira sessão já na semana
> seguinte.
>
> 👉 wa.me/5511966129197

**Mensagem 4 · quinta 25/09**

> Abriu. 💛
>
> **Fundadoras:** sábado, 9h às 12h, o Spa é de vocês.
> Restam [N] cartelas — segunda o balcão começa a oferecer para todo mundo.

### 14.5 · O script de balcão (onde a venda acontece de verdade)

A profissional, no momento do pagamento, com a cliente ainda sentada:

> "[Nome], você viu o que abriu aqui do lado?
>
> Dia 25 abre o Fast Spa — massagem, no mesmo prédio, sem hora marcada.
>
> A gente separou 25 cartelas para as clientes de casa, antes de anunciar
> para o bairro. São 5 massagens de 45 minutos por R$ 490 — dá R$ 98 cada,
> e avulsa é R$ 149. Usa de segunda a quarta, até o fim do ano.
>
> Uma das cinco você pode dar de presente pra quem quiser.
>
> Quer que eu já reserve a sua? Sobraram [N]."

**Três regras para quem vende:**
1. Dizer o **número que resta**, sempre. É o que fecha.
2. Nunca prometer uso no sábado. *(§12.8, risco 2.)*
3. Se a cliente hesitar no preço: oferecer o **3× de R$ 163**, não desconto.

### 14.6 · O que muda no checklist

| Precisa | Quem | Até |
|---|---|---|
| 🔴 **Testar o WhatsApp da loja** (link wa.me responde?) | Rodrigo | 17/09 |
| Treinar as profissionais no script do §14.5 | Rodrigo | 17/09 |
| Definir quem numera e onde anota | Rodrigo | 17/09 |
| Imprimir 25 cartelas numeradas | Marketing | 17/09 |
