---
titulo: "FAST Insights — Business Plan detalhado v2"
projeto: Franquia_FAST_Limao
tipo: business-plan
status: rascunho-v2 · pós-leitura contratual
criado: 2026-09-08
tags: [fast, business-plan, saas, franquia, modelo-financeiro]
---

# FAST Insights — Business Plan detalhado

> ⚠️ **ATUALIZADO — o plano agora roda em dois cenários.** Ver [[08-modelo-obrigatorio-consolidado]].
> **Sem homologação:** venda loja a loja, R$ 319, teto de 65% da rede → capital de R$ 267 mil,
> caixa zera no mês 23, resultado de ano 3 de R$ 883 mil, 389 lojas.
> **Com homologação:** obrigatório em toda a rede, preço único de R$ 299, 25% da receita para a
> franqueadora → **capital de R$ 192 mil, caixa zera no mês 17, resultado de ano 3 de R$ 859 mil,
> 570 lojas.** Praticamente o mesmo resultado com 28% menos capital e seis meses de antecedência.
> As seções abaixo mantêm o detalhamento do cenário sem homologação; os dois estão lado a lado
> na planilha (aba Cenários) e no BP em HTML.

> **Leia antes:** [[05-analise-contratual]]. Este plano assume que a questão da
> titularidade (cláusula 13.13) será resolvida por acordo escrito com a franqueadora.
> **Sem esse acordo, nada abaixo é executável.**

---

## 1. Sumário executivo

| | |
|---|---|
| **O que é** | Painel de gestão que lê o Trinks e a adquirente da loja e devolve decisão: metas com sazonalidade, DRE, conciliação de recebíveis, auditoria de cancelamentos, CRM e campanhas |
| **Estágio** | Em produção há meses numa loja real (FAST Limão). 6 abas, atualização 5x/dia, ~5.500 linhas de código |
| **Mercado** | 431 lojas FAST em operação, 600 previstas. Trinks é **obrigatório por contrato** (cláusula 7.6) — o mercado é a rede inteira |
| **Modelo** | Fornecedor Homologado. Taxa de Software paga pela loja, no trilho que a cláusula 7.6 já criou. Painel da Rede vendido à franqueadora |
| **Preço** | R$ 199 / 349 / 549 por loja. Ticket médio modelado R$ 319 |
| **Economia unitária** | Margem de contribuição R$ 274/loja/mês (86%). Payback do CAC: 1,5 mês |
| **Capital necessário** | **R$ 192 mil com homologação · R$ 267 mil sem** |
| **Retorno** | Com homologação — ano 2: R$ 1,28 mi de receita. Ano 3: R$ 1,56 mi de receita, R$ 859 mil de resultado |
| **Ponto de equilíbrio** | 128 lojas pagando (92 com o Painel da Rede) — 21% a 30% da rede |
| **Risco nº 1** | A franqueadora reivindicar a titularidade pela 13.13 sem contrapartida |

**A tese em uma frase:** um produto já pronto, num mercado cativo por contrato, com
trilho de cobrança já existente e margem de 86% — travado por uma cláusula que precisa
virar acordo antes de qualquer expansão.

---

## 2. O problema

O franqueado FAST opera com quatro sistemas que não se falam: Trinks (agenda e vendas),
a máquina da adquirente (dinheiro), a planilha da franqueadora (metas) e o WhatsApp
(cliente). As perguntas do dia não têm resposta em nenhum deles isoladamente:

| Pergunta | Onde está o dado hoje | Por que não se responde |
|---|---|---|
| Estou dentro da meta hoje? | Trinks + planilha | A meta é mensal e linear; o dia não é. Terça não é sábado |
| Quanto vendi que ainda não caiu? | Trinks + extrato | Ninguém concilia venda a venda |
| Que profissional cancela demais? | Trinks | O relatório existe, mas sem base de comparação |
| Quem sumiu este mês? | Trinks | Não há régua de recorrência |
| Estou ganhando dinheiro? | Contador, 40 dias depois | Chega tarde demais para mudar algo |

Do lado da franqueadora, o problema é o mesmo invertido: 431 lojas e nenhuma visão
comparável entre elas. Ela sabe o que o franqueado reporta, quando reporta.

**Evidência do próprio piloto:** a Limão descobriu, pelo painel, R$ 2.560 em
cancelamentos com valor num único período, um desvio de tabela de preço em 9 dos 57
serviços do catálogo, e uma venda de R$ 228 que não passou pelo Stone. Nada disso
apareceria numa planilha mensal.

---

## 3. O produto

### 3.1 Módulos

| Módulo | O que entrega | Estado | Plano |
|---|---|---|---|
| **Painel operacional** | Meta do dia com peso por dia da semana, ocupação por cadeira, R$/hora de salão, ticket, comparação ajustada | ✅ produção | Essencial |
| **Auditoria** | Cancelamentos por profissional e serviço, desvio de tabela, risco quantificado | ✅ produção | Essencial |
| **Insights** | Comentário acionável automático por aba e por período | ✅ produção | Essencial |
| **Financeiro** | DRE mensal, ponto de equilíbrio, margem de contribuição, projeção | ⚠️ depende de Excel local | Gestão |
| **Conciliação** | Recebíveis, órfãos dos dois lados, análise de antecipação, fluxo de caixa | ⚠️ depende de CSV manual | Gestão |
| **Clientes** | Base ativa, churn, aniversariantes, ticket por cliente | ✅ produção | Gestão |
| **Campanhas** | WhatsApp de aniversário e reativação, com kill switch, opt-out, cooldown, teto e janela | ⚠️ pronto, desligado | Crescimento |
| **Painel da Rede** | Todas as lojas lado a lado, ranking, benchmark, alerta de queda | ❌ a construir | Franqueadora |

Os dois ⚠️ de dependência manual são o principal trabalho da Fase 2. O ❌ é o produto
que a franqueadora compra e não existe hoje em lugar nenhum.

### 3.2 A defensibilidade

Não é o código — é a calibragem. Peso por dia da semana medido em 42 dias de amostra,
meta por cadeira e por hora, as palavras-chave que classificam 57 serviços em cabelo,
unha e maquiagem, o critério do que é cancelamento suspeito, o tratamento de dias
atípicos e de semana do mês. Isso veio de meses operando uma loja de verdade.

Um BI genérico não tem isso. Uma consultoria de dados levaria meses para descobrir — e
descobriria observando uma loja, que é exatamente o que já foi feito.

**A vulnerabilidade:** parte dessa calibragem veio da franqueadora (metas oficiais,
tabela de preços, modelo de DRE). É o que a cláusula 21.1 protege e o que torna a
homologação necessária, não opcional.

---

## 4. Situação jurídica — a trava e as três estruturas

Detalhe completo em [[05-analise-contratual]]. Resumo do que muda o plano:

| Cláusula | Efeito |
|---|---|
| **13.13** | Cede à franqueadora a propriedade de toda inovação resultante da operação da unidade. A titularidade do produto é dela numa leitura literal |
| **13.11** | O mailing de clientes é propriedade exclusiva da franqueadora |
| **21.1** | Confidencialidade por 2 anos após o fim — multa R$ 200 mil |
| **19.3.3 (ix)** | Justo motivo de rescisão: "obter vantagem para si valendo-se do SISTEMA sob qualquer forma" |
| **7.6 / 12.8** | ✅ Trinks obrigatório em toda a rede; Taxa de Software já paga ao fornecedor homologado |
| **21.2.1** | ✅ Atividade concorrente = estabelecimentos de beleza. Software não é concorrência |
| **ToS Trinks** | Uso "nunca comercial" e vedada obra derivada sem contrato específico escrito |

### As três estruturas possíveis

| | **A · Licenciamento** | **B · Joint venture** | **C · Venda do ativo** |
|---|---|---|---|
| Quem é dono | Você (com licença à rede) | Sociedade nova, você e a franqueadora | Franqueadora |
| Você recebe | Royalty por loja ativa | Participação + pró-labore | Valor à vista + earn-out |
| Quem investe os R$ 267 mil | Você | A sociedade | Ela |
| Seu upside no ano 3 | R$ 883 mil de resultado | Sua fatia de R$ 883 mil | Zero após o pagamento |
| Risco 13.13 | Alto — ela pode contestar | Neutralizado pelo acordo | Neutralizado |
| Seu risco de capital | Todo seu | Dividido | Nenhum |
| **Recomendação** | Peça esta | **Aceite esta** | Só se A e B falharem |

**A leitura honesta:** A é o melhor cenário financeiro e o mais difícil de conseguir,
porque exige que a franqueadora abra mão de um direito que já tem no papel. B é o
provável, e é bom: neutraliza a 13.13, divide o capital e mantém seu upside. C põe
dinheiro no bolso e encerra o assunto — considere se a negociação travar ou se você
concluir que não quer tocar uma empresa de software.

**Regra inegociável em qualquer das três:** nada de código, repositório ou demonstração
técnica detalhada antes de documento assinado.

---

## 5. Mercado

### 5.1 Dimensionamento

| Camada | Definição | Lojas | Receita potencial/ano |
|---|---|---|---|
| **TAM** | Salões no Brasil que usam Trinks | ? *(a descobrir — item T6)* | — |
| **SAM** | Rede FAST: Escova + Spa | 431 hoje · 600 em 2027 | R$ 1,55 mi → R$ 2,15 mi |
| **SOM (ano 3)** | 65% de adoção na rede | 389 lojas | R$ 1,53 mi |

O contrato torna o Trinks obrigatório, então o SAM é a rede inteira — não uma fatia
dela. Isso é raro e é o maior ativo comercial do plano.

### 5.2 O cliente

**Franqueado FAST típico:** loja faturando ~R$ 97 mil/mês (média da rede), 8 a 16
profissionais, 2 recepcionistas, uma gerente. Não é analista de dados. Olha o
faturamento do dia e sente o resto. O que compra não é "dashboard" — é *"eu descubro
o problema na terça em vez de descobrir no fechamento do mês"*.

**Franqueadora:** 431 unidades, expansão de 159 lojas em 2026, faturamento de rede de
R$ 502 mi. O que compra é comparabilidade: saber qual loja está caindo antes de o
franqueado ligar pedindo socorro.

### 5.3 Concorrência

| Concorrente | Ameaça | Por que perdemos ou ganhamos |
|---|---|---|
| **Planilha do franqueado** | O real concorrente | Ganhamos: ela não atualiza sozinha nem cruza com a adquirente |
| **Relatórios do próprio Trinks** | Média | Ganhamos: eles mostram o que aconteceu, não o que fazer. E não veem o dinheiro |
| **Sults (CRM homologado)** | Média | Sobreposição parcial em CRM. *A descobrir — item F5* |
| **BI genérico (Power BI, Looker)** | Baixa | Exige alguém que saiba usar. Nenhum franqueado tem |
| **A Trinks lançar o produto** | **Alta** | Eles têm o dado. *A descobrir — item T7* |
| **A franqueadora construir** | **Alta** | 6 a 9 meses e uma equipe. Nossa vantagem é o tempo |

---

## 6. Modelo de negócio e precificação

### 6.1 Estrutura

Fornecedor Homologado, espelhando o que a rede já faz com Trinks e Sults:

```
FRANQUEADORA ──homologa──▶ FAST INSIGHTS ──assina Taxa de Software──▶ FRANQUEADO
     │                            │
     └── assina Painel da Rede ───┘         (cobrança direta da loja,
         R$ 8 a 15 mil/mês                   como cláusula 7.6 já prevê)
```

Duas fontes de receita, dois compradores, um canal. A franqueadora não paga pelas lojas
e não intermedia a cobrança — ela homologa e compra o produto dela.

### 6.2 Planos

| Plano | R$/mês | Inclui | % do faturamento da loja |
|---|---|---|---|
| **Essencial** | 199 | Painel operacional, metas com sazonalidade, insights, auditoria | 0,21% |
| **Gestão** | 349 | + DRE, fluxo de caixa, conciliação de recebíveis, clientes | 0,36% |
| **Crescimento** | 549 | + CRM, campanhas de WhatsApp, régua de reativação | 0,57% |
| **Painel da Rede** | 8.000–15.000 | Franqueadora: consolidado, ranking, benchmark, alertas | — |

**Mix modelado:** 40% Essencial · 45% Gestão · 15% Crescimento → **ticket médio R$ 319**.

**Racional do preço:** ancorado no percentual do faturamento, não no custo. A 0,3% da
receita, a decisão deixa de ser financeira e vira conveniência. O teto psicológico da
categoria no varejo de serviços fica por volta de 1%.

**Mensagens de WhatsApp são repassadas a custo** (~R$ 0,35/conversa — *a confirmar,
item N1*). Nunca embutir: custo variável dentro de preço fixo é como se perde margem sem
perceber.

**Desconto de volume:** R$ 249/loja acima de 300 lojas ativas, negociável no contrato
master.

### 6.3 O que NÃO fazer

- **Cobrar percentual do faturamento da loja.** Parece alinhado, mas transforma cada
  reajuste numa negociação e assusta o franqueado que está indo bem.
- **Plano gratuito.** O custo de suporte por loja (R$ 34) não sustenta freemium numa
  base de 600.
- **Vender direto ao franqueado sem homologação.** É o caminho que dispara 21.1 e
  19.3.3 (ix).

---

## 7. Go-to-market

### 7.1 As cinco etapas

| Etapa | Duração | O que acontece | Marco de saída |
|---|---|---|---|
| **0 · Contenção** | 2 sem | Fechar acesso público, suspender o que sai da loja, falar com advogado | Exposições contidas · parecer sobre a 13.13 |
| **1 · Acordo** | 4–8 sem | Trinks (contrato de parceria) + franqueadora (estrutura A, B ou C) | **Dois papéis assinados** |
| **2 · Piloto** | 8 sem | 5 lojas de perfis diferentes, gratuitas, configuradas por você | Evidência de valor fora da Limão |
| **3 · Homologação** | 4 sem | Entrar na lista de fornecedores homologados, contrato-tipo, preço oficial | Comunicado da franqueadora à rede |
| **4 · Escala** | contínuo | Conselho de Franqueados, convenção, onboarding self-service | 100 lojas no M12 |

O piloto é gratuito de propósito: 5 lojas × R$ 319 × 2 meses = R$ 3.190 de receita
abdicada para comprar a prova de que o produto funciona fora da Limão. É barato.

### 7.2 Canais, em ordem de eficácia

1. **A franqueadora comunicando à rede.** Um comunicado oficial vale mais que 600
   ligações. É o que a homologação compra.
2. **Conselho de Franqueados** (cláusula 1.4, participação exigida) — pauta natural, e
   você já tem assento.
3. **Convenção e encontros da rede** (cláusula 6.1 ix: encontros "para exposição de
   ideias, críticas e sugestões sobre o SISTEMA").
4. **Boca a boca entre franqueados.** O mais forte e o mais lento. Uma loja que descobre
   R$ 2.500 em cancelamentos conta para as outras.
5. **Grupos de WhatsApp da rede.** Informal, alto alcance, use com parcimônia.

### 7.3 Curva de adoção modelada

Logística com teto em 65% da rede, centrada no mês 16:

| Mês | 7 | 9 | 12 | 15 | 18 | 24 | 30 | 36 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Lojas pagando | 16 | 30 | 69 | 137 | 219 | 328 | 368 | 389 |
| % da rede | 4% | 7% | 15% | 29% | 44% | 60% | 65% | 65% |

**Por que 65% e não 100%:** lojas novas em ramp-up, franqueados multi-unidade que
negociam à parte, resistentes por princípio, e lojas em transição societária. Adoção
total em rede de franquia é ficção, mesmo com produto obrigatório.

---

## 8. Operações

| Função | Como funciona | Custo |
|---|---|---|
| **Onboarding** | Franqueado gera a chave da API no Trinks e cola no produto. Config da loja com padrões da rede pré-preenchidos. Meta: 20 min sem ajuda | ~R$ 400 (CAC) |
| **Suporte** | Canal único (WhatsApp Business), SLA de 1 dia útil. 1 pessoa para ~175 lojas | R$ 34/loja/mês |
| **Atualizações** | Deploy único atinge todas as lojas. É o ganho central do multi-tenant | — |
| **Incidentes** | Se o Trinks cai, o painel congela e avisa. Sem alarme falso | — |
| **Cobrança** | Boleto/cartão recorrente via plataforma (Asaas, Vindi). Inadimplência esperada baixa: cortar o painel é visível | R$ 3/loja/mês |

**Ponto de atenção operacional:** a cota da API Trinks. Hoje o refresh custa ~27
requisições e repagina o ano inteiro. Em 600 lojas isso é o principal custo técnico e a
principal fonte de fragilidade. A ingestão incremental (Fase 3) corta ~70% — é
investimento com retorno direto em margem.

---

## 9. Roadmap técnico

| Fase | Semanas | Entrega | Custo |
|---|---|---|---|
| **1 · MVP multi-loja** | 8–10 | Login, banco com `loja_id`, onboarding self-service, painel da loja alimentado por API | R$ 60 mil |
| **2 · Rede e autonomia** | 6–8 | Painel da franqueadora, financeiro sem Excel (upload de planilha e CSV), cobrança recorrente | R$ 50 mil |
| **3 · Escala** | 8–12 | Ingestão incremental, WhatsApp via BSP, campanhas da rede, API pública | R$ 45 mil |
| **4 · Expansão** | contínuo | Fast Spa, multi-unidade, app móvel, benchmarking anônimo entre lojas | — |

**Decisão de arquitetura que economiza meses:** não reescrever. O motor Python de
análise vira biblioteca chamada por um worker com `loja_id` como parâmetro; o
`index.html` de 280 KB vira o painel da loja quase como está, alimentado por API em vez
de arquivo. Reescrever a interface do zero é a armadilha que mata projetos assim.

---

## 10. Equipe

| Quando | Quem | Custo/mês |
|---|---|---|
| M1–M2 | Você + advogado de franquias (pontual) | R$ 5.000 |
| M3–M5 | + 1 dev sênior parceiro (meio período) | R$ 22.000 |
| M6–M8 | + 1 CS meio período | R$ 28.000 |
| M9+ | Regime: dev R$ 16k · CS R$ 6k · infra e contabilidade R$ 3k · seu pró-labore R$ 10k | R$ 35.000 |

**Você é o dono do produto**, não o programador: define as regras de negócio, negocia,
vende e atende. É onde está o valor que ninguém copia.

**Risco de pessoa-chave:** hoje só você entende as regras de negócio. Documentá-las é
tarefa da Fase 1, não do futuro — e é também o que torna a estrutura B ou C negociável
por um valor maior.

---

## 11. Modelo financeiro

### 11.1 Premissas

| Premissa | Valor | Origem |
|---|---|---|
| Ticket médio | R$ 319 | Mix 40/45/15 sobre 199/349/549 |
| Custo variável por loja | R$ 45 | Infra R$ 8 + suporte R$ 34 + cobrança R$ 3 |
| Margem de contribuição | **R$ 274 (86%)** | Calculado |
| CAC | R$ 400 | Onboarding + rateio de eventos da rede |
| Churn | 1,5%/mês | Estimativa conservadora — inclui fechamento de loja |
| Custo fixo em regime | R$ 35.000/mês | Seção 10 |
| Painel da Rede | R$ 10.000/mês a partir do M9 | Meio da faixa 8–15 mil |
| Rede | 431 → 600 lojas em 36 meses | Plano público de expansão |
| Teto de adoção | 65% da rede | Seção 7.3 |

### 11.2 Projeção mês a mês

| Mês | Lojas | Receita lojas | Painel Rede | Receita total | Custo var. | Custo fixo | Investim. | Resultado | Caixa acum. |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0 | 0 | 5.000 | 8.000 | −13.000 | −13.000 |
| 2 | 0 | 0 | 0 | 0 | 0 | 5.000 | 0 | −5.000 | −18.000 |
| 3 | 0 | 0 | 0 | 0 | 0 | 22.000 | 12.000 | −34.000 | −52.000 |
| 4 | 0 | 0 | 0 | 0 | 0 | 22.000 | 0 | −22.000 | −74.000 |
| 5 | 0 | 0 | 0 | 0 | 0 | 22.000 | 0 | −22.000 | −96.000 |
| 6 | 0 | 0 | 0 | 0 | 0 | 28.000 | 10.000 | −38.000 | −134.000 |
| 7 | 16 | 5.112 | 0 | 5.112 | 7.131 | 28.000 | 0 | −30.019 | −164.019 |
| 8 | 22 | 6.972 | 0 | 6.972 | 3.315 | 28.000 | 0 | −24.343 | −188.363 |
| 9 | 30 | 9.441 | 10.000 | 19.441 | 4.429 | 35.000 | 0 | −19.987 | −208.350 |
| 10 | 40 | 12.671 | 10.000 | 22.671 | 5.837 | 35.000 | 0 | −18.166 | −226.516 |
| 11 | 53 | 16.811 | 10.000 | 26.811 | 7.562 | 35.000 | 0 | −15.751 | −242.267 |
| 12 | 69 | 21.983 | 10.000 | 31.983 | 9.587 | 35.000 | 0 | −12.604 | −254.871 |
| 13 | 89 | 28.248 | 10.000 | 38.248 | 11.840 | 35.000 | 0 | −8.592 | −263.463 |
| **14** | 111 | 35.559 | 10.000 | 45.559 | 14.184 | 35.000 | 0 | −3.625 | **−267.088** ← pico |
| **15** | 137 | 43.737 | 10.000 | 53.737 | 16.425 | 35.000 | 0 | **+2.312** | −264.776 |
| 18 | 219 | 69.986 | 10.000 | 79.986 | 20.689 | 35.000 | 0 | +24.296 | −214.804 |
| 21 | 286 | 91.363 | 10.000 | 101.363 | 20.668 | 35.000 | 0 | +45.695 | −97.994 |
| **23** | — | — | — | — | — | — | — | — | **+0** ← caixa vira |
| 24 | 328 | 104.640 | 10.000 | 114.640 | 19.321 | 35.000 | 0 | +60.319 | +69.980 |
| 30 | 368 | 117.241 | 10.000 | 127.241 | 18.359 | 35.000 | 0 | +73.882 | +485.994 |
| 36 | 389 | 124.204 | 10.000 | 134.204 | 18.836 | 35.000 | 0 | +80.368 | +953.229 |

### 11.3 Resumo por ano

| | Ano 1 | Ano 2 | Ano 3 |
|---|---:|---:|---:|
| Receita | R$ 112.990 | R$ 968.140 | R$ 1.526.137 |
| Resultado | −R$ 254.871 | +R$ 324.852 | +R$ 883.248 |
| Lojas no fim do ano | 69 | 328 | 389 |

### 11.4 Os quatro números que importam

| | Valor | Leitura |
|---|---|---|
| **Capital necessário** | **R$ 267.088** | O pico de caixa negativo, no M14 |
| **Primeiro mês positivo** | **M15** | Resultado mensal vira |
| **Caixa acumulado zera** | **M23** | Você recupera o investido |
| **Ponto de equilíbrio operacional** | **128 lojas** (92 com Painel da Rede) | 21% a 30% da rede |

> ⚠️ **Correção importante em relação à v1.** O plano anterior falava em R$ 112 mil de
> investimento. Aquele número cobria só o custo de construir; **não incluía o prejuízo
> operacional até o caixa virar.** A necessidade real de capital é **R$ 267 mil** — 2,4x
> maior. É a diferença entre "dá para bancar do bolso" e "precisa de sócio, capital ou
> uma estrutura em que a franqueadora banque". Este número muda a decisão, então está
> em destaque.

### 11.5 Economia unitária

| Métrica | Valor |
|---|---|
| Margem de contribuição por loja | R$ 274/mês |
| Payback do CAC | 1,5 mês |
| LTV a 1,0% de churn | R$ 27.400 · LTV/CAC 68x |
| **LTV a 1,5% de churn** | **R$ 18.267 · LTV/CAC 46x** |
| LTV a 2,0% de churn | R$ 13.700 · LTV/CAC 34x |

Um LTV/CAC de 46x seria absurdo em SaaS normal. Aqui ele é real e diz uma coisa
específica: **neste negócio o risco não está na aquisição de clientes, está no canal.**
Conseguir a homologação é quase binário — com ela, o custo de vender tende a zero; sem
ela, não existe negócio. Toda a energia deve ir para a negociação, não para marketing.

### 11.6 Cenários

| Cenário | 1º mês positivo | Caixa zera | Capital necessário | Receita ano 3 | Resultado ano 3 |
|---|---:|---:|---:|---:|---:|
| **Base** | M15 | M23 | R$ 267.088 | R$ 1.526.137 | R$ 883.248 |
| Adoção metade (33% da rede) | M19 | M35 | R$ 327.402 | R$ 823.069 | R$ 291.624 |
| Homologação atrasa 6 meses | M21 | M29 | R$ 292.811 | R$ 1.417.651 | R$ 752.896 |
| Preço 20% menor | M17 | M27 | R$ 302.405 | R$ 1.244.028 | R$ 601.139 |
| Sem o Painel da Rede | M17 | M26 | R$ 335.658 | R$ 1.406.137 | R$ 763.248 |
| Revenue share 20% à franqueadora | M17 | M28 | R$ 318.259 | R$ 1.220.910 | R$ 578.021 |
| **Revenue share 35%** | M19 | M35 | R$ 377.326 | R$ 991.989 | R$ 349.100 |
| **Revenue share 50%** | M23 | **não volta** | R$ 474.338 | R$ 763.069 | R$ 120.180 |
| Pior caso combinado | M33 | **não volta** | R$ 500.221 | R$ 499.736 | −R$ 42.641 |

**O limite de negociação:** até **35% de participação** para a franqueadora o negócio
continua de pé. **A 50% ele para de se pagar em 36 meses.** Leve esse número para a mesa
— é a diferença entre uma parceria e um emprego mal pago.

### 11.7 Versão enxuta

Sem pró-labore e com estrutura mais leve (custo fixo em regime de R$ 25 mil):

| Variante | 1º mês positivo | Caixa zera | Capital | Resultado ano 3 |
|---|---:|---:|---:|---:|
| Enxuta | M13 | M21 | **R$ 214.871** | R$ 1.003.248 |
| Enxuta + share 35% | M17 | M29 | R$ 285.210 | R$ 469.100 |
| Enxuta + adoção metade | M16 | M28 | R$ 244.888 | R$ 411.624 |
| Enxuta + pior caso | M27 | não volta | R$ 356.567 | R$ 77.359 |

Abrir mão do pró-labore por 12 meses economiza R$ 52 mil de capital e antecipa o
break-even em 2 meses. Faz sentido se você tem a loja pagando suas contas.

---

## 12. Riscos

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| Franqueadora invoca a 13.13 sem contrapartida | **Alta** | Fatal | Negociar antes de expandir; nada de código antes do papel; advogado desde já |
| Franqueadora constrói internamente | Média | Fatal | Chegar com produto pronto; oferecer estrutura B (JV), em que fazer sozinha vira irracional |
| Trinks nega uso comercial | Média | Fatal | Conversar na semana 1; desenhar a ingestão trocável desde a Fase 1 |
| Trinks lança produto concorrente | Média | Alto | *A descobrir (item T7).* Se sim, negociar como parceiro em vez de competir |
| Capital de R$ 267 mil não aparece | **Alta** | Alto | Estrutura B ou C; ou versão enxuta a R$ 215 mil; ou faseamento com receita antecipada |
| Adoção abaixo de 33% | Média | Alto | Piloto valida antes de investir a Fase 2 |
| Vazamento de dado de cliente | Baixa | Fatal | Contenção na semana 1; contrato de operador com cada loja |
| Sults já faz parte disso | Média | Médio | *A descobrir (item F5).* Se sim, integrar em vez de competir |
| Pessoa-chave (você) | Média | Alto | Documentar as regras de negócio na Fase 1 |
| Concentração em cliente único | Média | Médio | O modelo de fornecedor homologado protege: a receita vem das lojas |

---

## 13. Marcos de decisão

Quatro portões. Em cada um, uma resposta honesta antes de gastar o próximo real.

| Portão | Quando | Critério para seguir | Se não |
|---|---|---|---|
| **G1 · Jurídico** | Semana 2 | O advogado vê caminho viável para a 13.13 | Pare. Vá para uso interno apenas (opção C do doc 05) |
| **G2 · Trinks** | Semana 4 | Existe caminho contratual para uso comercial da API | Pare ou repense a fonte de dados |
| **G3 · Franqueadora** | Semana 8 | Ela topa estrutura A, B ou C — qualquer uma delas por escrito | Avalie o produto genérico fora do SISTEMA |
| **G4 · Piloto** | Mês 4 | ≥ 4 das 5 lojas usam semanalmente e pagariam | Não invista as Fases 2 e 3 |

**O que torna este plano executável não é o otimismo dos números — é a disciplina dos
portões.** O pior desfecho possível não é o projeto não acontecer: é gastar R$ 267 mil
e perder a loja por ter pulado o G1.

---

## 14. O que fazer nos próximos 30 dias

| Semana | Ação | Entregável |
|---|---|---|
| 1 | Fechar acesso público · suspender sync HubSpot · ligar para a Trinks | Exposições contidas · respostas T1 a T4 |
| 2 | Advogado de franquias, com as 5 perguntas do doc 05 | Parecer sobre a 13.13 → **G1** |
| 3 | Entrevistar 8 franqueados · montar proposta e memorando | Evidência de demanda · documentos prontos |
| 4 | Reunião com a franqueadora | Decisão sobre estrutura → **G3** |

Ver [[07-plano-de-descoberta]] para os 34 itens de investigação, com responsável, prazo
e o que cada resposta muda.

> **Uma lacuna conhecida deste modelo:** a projeção está **antes dos impostos** da
> empresa de software (item N3). No Simples Nacional, o resultado do ano 3 cai de
> R$ 883 mil para algo entre R$ 700 mil e R$ 790 mil. Não muda a decisão, mas precisa
> entrar antes de virar proposta formal.
