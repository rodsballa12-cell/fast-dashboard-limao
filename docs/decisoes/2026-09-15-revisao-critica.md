# Revisão crítica · o que estava errado

**Data:** 15/09/2026 · Revisão independente do plano de lançamento, com
verificação direta nos dados do repositório.

**Quatro afirmações minhas estavam erradas.** Todas foram conferidas contra
os arquivos e estão corrigidas abaixo. Os documentos de campanha e estratégia
seguem válidos no desenho; o que muda são números e duas decisões.

---

## 1 · A comissão da Escova estava no sistema o tempo todo

Eu registrei três vezes que "a comissão da Escova não está cadastrada" e usei
isso para barrar o Pacote Escova + Spa.

`data/comissoes.json` existe, foi exportado do Trinks BackOffice em
**08/09/2026** e traz `"Escova": 0.30`.

**Consequência:** o Pacote Escova + Spa de R$ 790 foi descartado por uma
pendência que não existia há uma semana. Com a comissão real, ele entrega
**R$ 553 de contribuição por venda contra R$ 342 do pacote de R$ 489** — e a
massagem nele sai a R$ 129, **acima** dos R$ 114,62 da oferta oficial, então
não fura o lançamento. **Vale reabrir.**

---

## 2 · A Ledterapia já é vendida na Escova, por R$ 69

Eu a chamei de "produto-ponte escondido na tabela" do Spa, a R$ 79, e a
transformei no brinde da campanha.

`data/servicos_cache.json`: **FAST LED TERAPIA · R$ 69,00 · 7 min ·
categoria TRATAMENTO** — no cardápio da Escova.

**Três consequências:**

1. **A cliente pode comparar R$ 69 e R$ 79 no mesmo prédio.** A peça diz
   "vale R$ 79"; o balcão de baixo vende por R$ 69.
2. **Dar de graça um serviço que a Escova vende ensina que ele não vale
   nada** — e tira receita de um serviço que já é vendido.
3. **Ela deixa de cumprir a função para a qual foi escolhida.** O argumento
   era "fazer a cliente atravessar a porta do Spa". Se a Ledterapia pode ser
   entregue na Escova, a porta não é atravessada.

**Se o Spa tem aparelho próprio: NÃO VERIFICÁVEL** nos dados.

**Decisão necessária antes de 17/09:** ou o brinde vira outro serviço que só
existe no Spa (drenagem facial de 15 min, R$ 59, é o candidato natural), ou a
peça passa a dizer R$ 69 e assume que é um serviço da Escova ofertado como
cortesia.

---

## 3 · A base é muito menos recorrente do que eu disse

Eu contei **atendimentos** e chamei de **visitas**. Uma cliente que fez
escova + mãos no mesmo dia aparecia como duas visitas.

| O que eu disse | O que é |
|---|---|
| 236 recorrentes (2+ visitas) | **90** clientes voltaram em outro dia |
| 168 adormecidas (1 visita) | **314** — 77,7% da base veio uma vez só |
| 27 embaixadoras (5+ visitas) | **8** |
| "a maior tem 44 visitas" | **19 visitas** (44 era o nº de serviços) |

**Segmentação corrigida:**

| Segmento | Qtd | % |
|---|---|---|
| Vieram **uma vez** e não voltaram | **314** | 77,7% |
| Voltaram 2 a 4 vezes | 82 | 20,3% |
| Voltaram 5+ vezes | 8 | 2,0% |

**Isso muda o eixo da campanha.** O plano foi desenhado para uma base fiel
que, na verdade, não existe: **três em cada quatro clientes vieram uma vez e
sumiram.** O problema da Escova não é falta de produto para quem volta — é
que quase ninguém volta.

A boa notícia: o Spa é a melhor desculpa de reativação que a loja já teve,
porque é a única coisa genuinamente nova a dizer para 314 pessoas. A má: uma
oferta de 5 sessões de uso restrito é o produto errado para quem nunca
voltou nem uma vez.

---

## 4 · Sábado tem 30 clientes, não 48

48,5 é a média de **atendimentos** por sábado. Pessoas distintas, nos quatro
últimos sábados: **34 · 33 · 26 · 28 → média 30,2**.

A janela de balcão de 18 a 24/09 cai de ~124 para **~92 pessoas**.

---

## 5 · A margem não é a que eu calculei

Eu disse "contribuição de R$ 342,30 por pacote". É margem **após comissão**,
não contribuição.

`data/financeiro.json → premissas`: `insumos 0.12` · `simples 0.07` ·
`inadimplencia 0.02`. Com a comissão de 30% do Spa, o custo variável é
**51%**, não 30%.

| | Como eu disse | Com as premissas da casa |
|---|---|---|
| Contribuição por pacote | R$ 342,30 | **R$ 239,61** |
| Por sessão | R$ 68,46 | **R$ 47,92** |
| 20 pacotes | R$ 6.846 | **R$ 4.792** |

**30% a menos.** E ainda faltam duas linhas que ninguém modelou: a **taxa do
3× de R$ 163** (não há MDR de parcelado nas premissas) e a **escova bônus**
do pacote oficial — 8 resgates × R$ 79 = R$ 632 de receita não faturada na
Escova, numa unidade que fecha o mês em **−R$ 8.785**.

---

## 6 · A meta de R$ 15.000 depende de uma premissa não declarada

O placar prevê R$ 21.700 de caixa (8 Renove-se + 20 pacotes). Lido de duas
formas:

| Regra | Resultado |
|---|---|
| **Caixa** | ~R$ 18.000/mês → bate a meta |
| **Serviço entregue** | ~R$ 6.240/mês → **41,6% da meta** |

**2,9× de diferença, e nenhum documento diz qual vale.** A estratégia §12.7
tinha o aviso em negrito — *"caixa não é receita do mês"* — e o roteiro o
perdeu numa das reescritas.

E setembro não fecha de jeito nenhum: o Spa abre dia 25 e o mês tem **6 dias**
de operação. R$ 15.000 ÷ 6 = R$ 2.500/dia, contra um teto físico de ~R$ 1.937
com uma profissional e a agenda 100% cheia desde o primeiro dia.

---

## 7 · Nenhuma oferta pode ser usada quando a base está no prédio

76,4% do movimento é quinta, sexta e sábado. O pacote de R$ 489 é **segunda a
quarta, sem exceção**.

O sábado 26/09 das 9h às 12h é vendido como exclusivo do grupo — **e o único
produto exclusivo do grupo não pode ser usado nele.** As 30 pessoas que
estarão no prédio naquela manhã não têm o que comprar.

---

## 8 · Erros operacionais que matam a execução

| Problema | Onde | Correção |
|---|---|---|
| **O link do Instagram aponta para a pré-venda cancelada** | frente 2 | o post de 14/09 diz "PRÉ-VENDAS ABERTAS" (cancelado em 15/09), 213 de alcance, 6 curtidas |
| **Todos os CTAs usam o WhatsApp da Escova** | todas as mensagens | o Spa tem número próprio: **+55 11 99024-3927** |
| **O opt-in é de SMS e e-mail, não de WhatsApp** | estratégia §1 | `recebeSMSMarketing` e `recebeEmailMarketing`. Não há campo de consentimento para WhatsApp |
| **344 envios manuais sem dono** | frente 2 | `config.json → disparo_wa` está `ativo: false`, `teto_diario: 20` — 18 dias de trabalho |
| **Não há lista das 67 na recepção** | mensagem 3 | "é só falar que você é do grupo" sem lista = qualquer um compra o R$ 489 |
| **A WABA sumiu do checklist** | roteiro | campanha 100% WhatsApp com o canal sem API |
| **Datas erradas sobrevivem na estratégia** | §10.4, §12.5, §14.1 | "sábado 27/09" e "sáb 20/09" são domingos |

---

## 9 · Mídia · o custo da conversa subiu 32%

Os R$ 6,90 por conversa que eu citei em três documentos são a média de 30
dias, que ainda carrega agosto.

| | Meta | 30d | Setembro | Últimos 7d |
|---|---|---|---|---|
| CPA mensagem | R$ 8,00 | R$ 6,90 ✅ | R$ 7,89 ⚠️ | **R$ 8,26 ❌** |
| CPM | R$ 12,00 | R$ 9,99 ✅ | R$ 12,16 ❌ | R$ 12,29 ❌ |
| CTR | 1,50% | 1,46% ❌ | 1,48% ❌ | 1,39% ❌ |

**O custo corrente é R$ 8,26, acima da meta.** Toda comparação que eu fiz
("uma conversa paga custa R$ 6,90") está desatualizada.

E o alcance dos Stories da Escova é **424 pessoas em 30 dias**, não 138.605 —
esse número é o alcance total da conta, majoritariamente de feed impulsionado.
O canal que a estratégia elegeu como nº 2 é **327 vezes menor** do que o plano
supõe.

---

## 10 · O que eu recomendo agora, por impacto

**1 · Criar um produto de quinta a sábado.** É quando 76,4% da base está no
prédio e não há nada para vender. Serviços curtos que não consomem hora de
massoterapeuta: drenagem facial 15' (R$ 59), revitalização facial 30' (R$ 79),
pescoço & colo 30' (R$ 89). 30 pessoas × 4 sábados × 20% = 24 vendas/mês ≈
**R$ 1.896 a preço cheio**.

**2 · Decidir a regra de reconhecimento da meta.** Caixa ou serviço entregue.
É a diferença entre 120% e 42% da meta de outubro.

**3 · Reabrir o Pacote Escova + Spa de R$ 790.** A pendência que o barrou não
existe. Contribuição 62% maior que a do pacote de R$ 489, e não fura o
lançamento.

**4 · Trocar o brinde da Ledterapia** por algo que só exista no Spa, ou
assumir o preço de R$ 69 da Escova.

**5 · Mexer na mídia esta semana.** Pausar as campanhas identificadas na
auditoria libera ~R$ 30/dia; o Spa abre em 10 dias com R$ 76 de verba
comercial. E renovar o `META_ACCESS_TOKEN` hoje — sem ele, nada é executável
nem mensurável.

---

## O que este documento não resolve

A composição das **67 do grupo VIP** não está em arquivo nenhum — não há lista
nem etiqueta. Não é possível garantir que as ~344 da frente 2 não incluem
pessoas do grupo, nem montar a lista de elegibilidade na recepção sem que
alguém a escreva à mão.
