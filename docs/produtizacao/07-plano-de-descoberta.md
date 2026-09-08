---
titulo: "Plano de descoberta — os 34 itens que faltam"
projeto: Franquia_FAST_Limao
tipo: plano-de-descoberta
status: rascunho-v1
criado: 2026-09-08
tags: [fast, descoberta, due-diligence, validacao]
---

# Plano de descoberta

> Todo plano de negócio é uma pilha de suposições. Este documento lista as que sobraram,
> em ordem de quanto elas mudam a decisão — e não em ordem de curiosidade.
> **Versão interativa, com as respostas salvas:** https://claude.ai/code/artifact/7d10e93e-3111-45fe-a2b3-ca7196ac2f88
> (seção 10 da página). Marque o que já respondeu e anote a resposta — fica gravado.

## Como usar

Cada item tem **o que muda** — a consequência prática da resposta. Se um item não muda
nada, ele não deveria estar aqui, e você pode ignorá-lo sem culpa.

Prioridades:

| | Significado |
|---|---|
| 🔴 **Bloqueante** | Nada avança sem a resposta. Faça primeiro, mesmo que seja desconfortável |
| 🟠 **Estrutural** | Define o modelo de negócio. Precisa estar respondido antes de investir |
| 🟡 **Refinamento** | Melhora o plano. Pode ser respondido enquanto o resto anda |

---

## As três ondas

| Onda | Prazo | Itens | Objetivo | Portão |
|---|---|---|---|---|
| **1 · Sobrevivência** | 14 dias | J1 J2 J3 J7 · T1 T2 T3 | Descobrir se existe caminho legal e técnico | **G1 + G2** |
| **2 · Modelo** | 30 dias | J4 J5 J6 · T4 T5 · F1 a F9 · M1 M2 | Descobrir qual estrutura de negócio é possível | **G3** |
| **3 · Refino** | 90 dias | T6 T7 · M3 M4 · P1 a P5 · N1 N2 N3 | Ajustar preço, custo e produto com dado real | **G4** |

**Regra:** não gaste um real da Fase 1 antes de fechar a Onda 1. O custo de descobrir é
uma hora de advogado e três telefonemas; o custo de não descobrir está quantificado na
seção 10 do [[05-analise-contratual]].

---

## J · Jurídico — 7 itens

*Responde: advogado de franquias. Custo estimado: R$ 1.500 a R$ 3.000 por uma consulta
de 1 a 2 horas, mais R$ 3.000 a R$ 6.000 se houver redação de documentos.*

| # | Pergunta | Prio | O que muda |
|---|---|:--:|---|
| **J1** | A cláusula 13.13 alcança um software que eu escrevi? Uma cessão universal e gratuita de tudo que o franqueado criar é exigível, ou é abusiva num contrato de adesão? | 🔴 | **Tudo.** Se alcança, o único caminho é negociar. Se é questionável, você negocia de outra posição |
| **J2** | A Lei de Software (9.609/98) muda algo, sendo o autor pessoa física, fora de vínculo empregatício e com ferramentas próprias? | 🔴 | Define a força do seu argumento de titularidade |
| **J3** | Qual o risco real das três exposições atuais (painel público, sync HubSpot, campanhas) e em que ordem corrigir? | 🔴 | Define o que fazer nesta semana |
| **J4** | Como demonstrar o produto à franqueadora sem entregar o ativo? Existe NDA ou memorando que preserve minha posição? | 🟠 | Define se a reunião da semana 4 pode acontecer |
| **J5** | Qual estrutura societária usar: PJ separada, sociedade com a franqueadora, ou contrato de licenciamento? Eu posso ser sócio de uma software house sendo franqueado? (21.2.1 sugere que sim) | 🟠 | Define a estrutura A, B ou C da seção 4 do [[06-business-plan-detalhado]] |
| **J6** | Sendo franqueado **e** fornecedor homologado ao mesmo tempo, há conflito a tratar no contrato de fornecimento? | 🟠 | Define cláusulas do contrato de homologação |
| **J7** | Se eu construir do zero um produto genérico para salões, fora do horário e sem material dos MANUAIS, a 13.13 ainda alcança? Que provas de segregação preciso produzir **desde já**? | 🟠 | Define se o plano B existe — e as provas precisam começar antes, não depois |

---

## T · Trinks — 7 itens

*Responde: comercial e parcerias da Trinks. Custo: telefonemas e uma reunião.*

| # | Pergunta | Prio | O que muda |
|---|---|:--:|---|
| **T1** | Existe autorização para uso comercial da API? Os Termos vedam uso "nunca comercial" e obra derivada sem contrato específico — qual é o processo para obter esse contrato? | 🔴 | **Se não existe caminho, não há produto** sobre a API do Trinks |
| **T2** | A cota de 10.000 requisições/mês é por estabelecimento ou por conta? | 🔴 | Se for por conta, o custo unitário muda completamente e o modelo precisa ser refeito |
| **T3** | Existe programa formal de parceiro ou integrador? Contrato-tipo, requisitos, prazo de aprovação? | 🔴 | Define o prazo da Onda 1 e se há atalho |
| **T4** | O modelo comercial de parceria envolve taxa, revenue share, ou é gratuito? | 🟠 | Entra direto no custo variável por loja (hoje modelado como R$ 0) |
| **T5** | A API tem endpoints incrementais (`updated_since`, delta, webhooks)? Ou só paginação completa? | 🟠 | Define o custo da Fase 3 e se a economia de 70% de requisições é real |
| **T6** | Quantos salões no Brasil usam Trinks? Existe base fora da rede FAST? | 🟡 | Dimensiona o TAM e a viabilidade do plano B (produto genérico) |
| **T7** | A Trinks tem, ou planeja, um produto próprio de BI ou gestão financeira? | 🟠 | Se sim, o jogo é parceria e não competição — e o timing fica urgente |

---

## F · Franqueadora — 8 itens

*Responde: diretoria e área de expansão/operações da FE Franchising. Cuidado: perguntar
já sinaliza intenção. Faça depois de J1 e J4.*

| # | Pergunta | Prio | O que muda |
|---|---|:--:|---|
| **F1** | Existe projeto interno de BI, dados ou painel da rede em andamento? | 🟠 | Se existe, o jogo é parceria ou venda do ativo — não licenciamento |
| **F2** | Quem decide a homologação de um fornecedor? Qual o processo e o prazo típico? | 🟠 | Define o cronograma real da etapa 3 do go-to-market |
| **F3** | Quais os critérios de homologação — certificações, seguro, capital, contrato-tipo? | 🟠 | Pode exigir estrutura societária e capital antes do previsto |
| **F4** | Existe contrato-tipo de Fornecedor Homologado? Que termos traz (exclusividade, revenue share, prazo, rescisão)? | 🟠 | **Entra direto no modelo financeiro.** Ver os cenários de revenue share |
| **F5** | Qual o escopo do Sults hoje? Ele já faz, ou vai fazer, parte do que o FAST Insights faz? | 🟠 | Se houver sobreposição, o caminho é integrar em vez de competir |
| **F6** | A franqueadora coleta dados das lojas hoje? Como, com que frequência, e o que faz com eles? | 🟡 | Dimensiona o valor do Painel da Rede e o preço que ele suporta |
| **F7** | O Conselho de Franqueados pode pautar isso? Quando é a próxima reunião? | 🟡 | É o canal mais barato de validação com a rede |
| **F8** | Qual o apetite: comprar o ativo, licenciar, entrar como sócia, ou construir? | 🟠 | Define qual das três estruturas propor primeiro |

---

## M · Mercado e cliente — 4 itens

*Responde: 8 a 10 franqueados, em conversas de 20 minutos. Custo: seu tempo.*

| # | Pergunta | Prio | O que muda |
|---|---|:--:|---|
| **M1** | Qual a primeira métrica que o franqueado olha de manhã? E qual pergunta ele não consegue responder hoje? | 🟠 | Define o que vai no plano Essencial — e o que corta |
| **M2** | Quanto pagaria por isso? (teste de preço: mostre R$ 199, R$ 349 e R$ 549 e observe a reação) | 🟠 | Valida ou derruba o ticket de R$ 319, que sustenta todo o modelo |
| **M3** | Que ferramentas usa além de Trinks e Sults, e quanto gasta por mês com elas? | 🟡 | Mostra o orçamento já disponível e a disposição real de pagar |
| **M4** | Quantas lojas da rede são multi-unidade, com o mesmo dono? | 🟡 | Muda o produto (visão consolidada) e o preço (desconto por grupo) |

**Como perguntar sem sinalizar demais:** peça ajuda, não venda. *"Estou montando um
controle para a minha loja e queria saber o que você olha na sua."* Você é franqueado
falando com franqueado — é a conversa mais natural do mundo, e a mais informativa.

---

## P · Produto e técnico — 5 itens

*Responde: você, medindo. Custo: tempo e o piloto.*

| # | Pergunta | Prio | O que muda |
|---|---|:--:|---|
| **P1** | Qual o custo real de infraestrutura por loja, medido com 5 lojas rodando? | 🟡 | Hoje modelado em R$ 8. Se for R$ 30, a margem cai de 86% para 78% |
| **P2** | Quantas requisições por loja/mês em regime, com ingestão incremental? | 🟠 | Se estourar a cota, o produto não escala sem contrato especial com a Trinks (T2, T4) |
| **P3** | Quais adquirentes as lojas da rede usam? Stone é universal? Elas têm API? | 🟠 | Define se a conciliação (plano Gestão) funciona fora da Limão ou vira upload manual |
| **P4** | Quanto do financeiro dá para automatizar sem o Excel? A franqueadora tem modelo de DRE padronizado? | 🟠 | Se houver modelo da rede, a Fase 2 encolhe muito. Se não, cada loja tem um jeito |
| **P5** | Qual BSP de WhatsApp usar, com que custo de setup por loja e por conversa? | 🟡 | Define a viabilidade do plano Crescimento (R$ 549) |

---

## N · Números e operação — 3 itens

| # | Pergunta | Prio | O que muda |
|---|---|:--:|---|
| **N1** | Preço real da conversa de marketing no WhatsApp, tabela Meta Brasil vigente | 🟡 | Hoje estimado em R$ 0,35. É repasse, então não afeta margem — mas afeta a proposta |
| **N2** | Custo real de suporte por loja, medido no piloto (horas por loja/mês) | 🟡 | Hoje modelado em R$ 34. É o maior componente do custo variável |
| **N3** | Regime tributário da PJ de software: Simples, Lucro Presumido, alíquota de ISS no município | 🟠 | Pode consumir 6% a 16% da receita — **hoje não está no modelo financeiro** |

> ⚠️ **N3 é a lacuna mais séria do modelo.** A projeção da seção 11 do
> [[06-business-plan-detalhado]] está **antes de impostos sobre a receita da software
> house**. No Simples Nacional (anexo III, ~6% a 16% conforme faturamento), o resultado
> do ano 3 cairia de R$ 883 mil para algo entre R$ 700 mil e R$ 790 mil. Não muda a
> decisão, mas precisa entrar antes de o plano virar proposta formal.

---

## Painel de controle

| Categoria | Itens | 🔴 | 🟠 | 🟡 | Prazo alvo |
|---|---:|---:|---:|---:|---|
| J · Jurídico | 7 | 3 | 4 | 0 | 14 dias |
| T · Trinks | 7 | 3 | 3 | 1 | 14 a 30 dias |
| F · Franqueadora | 8 | 0 | 6 | 2 | 30 dias |
| M · Mercado | 4 | 0 | 2 | 2 | 30 dias |
| P · Produto | 5 | 0 | 3 | 2 | 90 dias |
| N · Números | 3 | 0 | 1 | 2 | 90 dias |
| **Total** | **34** | **6** | **19** | **9** | — |

**Seis itens bloqueantes. Um advogado e três telefonemas.** É todo o custo de descobrir
se este projeto existe — contra R$ 267 mil de capital e a loja em risco se a ordem for
invertida.

---

## O que já foi respondido

Registro do que saiu da lista, para não ser reinvestigado:

| Pergunta | Resposta | Fonte |
|---|---|---|
| Quantas lojas da rede usam Trinks? | **100%** — é obrigatório | Contrato, cláusula 7.6 |
| A franqueadora cobra taxa de tecnologia? | **Sim** — Taxa de Software, paga direto ao fornecedor homologado | Contrato, cláusula 7.6 |
| Existe caminho de fornecedor terceiro cobrando das lojas? | **Sim** — Trinks e Sults já fazem exatamente isso | Contrato, cláusulas 7.6 e 12.8 |
| A não concorrência impede montar uma software house? | **Não** — atividade concorrente é definida como estabelecimentos de beleza | Contrato, cláusula 21.2.1 |
| A Trinks permite uso comercial dos dados? | **Não, sem contrato específico escrito** | Termos de Uso Trinks |
| Quem é dono da base de clientes? | **A franqueadora** | Contrato, cláusula 13.11 |
| Tamanho e crescimento da rede | 431 lojas, R$ 502 mi, +159 lojas em 2026 | Imprensa, 09/2026 |
