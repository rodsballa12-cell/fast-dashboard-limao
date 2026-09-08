---
titulo: "FAST Insights — Business Plan v1"
projeto: Franquia_FAST_Limao
tipo: business-plan
status: rascunho-v1
criado: 2026-09-08
tags: [fast, business-plan, saas, franquia, precificacao]
---

# FAST Insights — Business Plan v1

> **Como ler este documento:** todo número marcado como *estimativa* é um modelo, não
> um fato. A seção 9 lista os 8 números que precisam ser confirmados antes de você
> apresentar isso para alguém. Os números de rede (unidades, faturamento) vêm de
> matérias públicas de setembro de 2026 e estão com fonte.

## 1. O problema

O franqueado FAST tem o Trinks, tem a máquina Stone, tem a planilha da franqueadora e
tem o WhatsApp. O que ele não tem é a resposta para as perguntas do dia:

- Estou dentro ou fora da meta **hoje**, considerando que hoje é terça e chove?
- Quanto do que vendi ainda não caiu na conta?
- Qual profissional está com cancelamento acima do normal?
- Quantas clientes sumiram este mês e ninguém chamou de volta?

Ele tem os dados espalhados por quatro sistemas e nenhum lugar onde eles se cruzam.
A franqueadora, do outro lado, tem 431 lojas e nenhuma visão comparável entre elas —
só o que cada franqueado reporta, quando reporta.

## 2. O produto

**FAST Insights** — painel de gestão que lê o Trinks e a adquirente da loja e devolve,
sozinho, o que precisa de decisão: metas ajustadas por sazonalidade real, DRE do mês,
conciliação de recebíveis, auditoria de cancelamentos, clientes em risco de churn e
campanhas de WhatsApp automáticas.

Está rodando em produção há meses numa loja real — a FAST Limão. Não é protótipo:
são 6 abas, atualização automática 5x/dia, motor de insights e campanhas com trava de
segurança. O produto foi construído resolvendo a dor de quem vai comprá-lo.

**A vantagem que ninguém copia rápido:** as regras de negócio. Peso por dia da semana,
meta por cadeira e por hora, palavras-chave que classificam serviço em cabelo/unha/
maquiagem, o que conta como cancelamento suspeito. Isso levou meses de operação real
para calibrar. Um concorrente genérico de BI não tem isso e não consegue inventar.

## 3. Mercado

| Indicador | Valor | Fonte |
|---|---|---|
| Lojas Fast Escova em operação (fim de 2026) | 401 | Times Brasil / Mapa das Franquias |
| Lojas Fast Spa em operação | 30 | idem |
| Contratos assinados (as duas marcas) | 490 | idem |
| Novas lojas previstas em 2026 | 159 | idem |
| Faturamento da rede projetado 2026 | R$ 502 mi (+55% sobre 2025) | idem |

Faturamento médio por loja ≈ **R$ 97 mil/mês** (R$ 502 mi ÷ 431 ÷ 12).

Esse número é a base da precificação: um plano de R$ 299/mês custa **0,3% do
faturamento da loja**. É a faixa em que a decisão de compra deixa de ser financeira e
passa a ser de conveniência — que é exatamente onde você quer estar.

- **Mercado endereçável hoje:** 431 lojas × R$ 299 × 12 = **R$ 1,55 mi/ano**
- **Com o plano de expansão (600 lojas):** **R$ 2,15 mi/ano**
- **Ecossistema Fast completo, incluindo Spa:** o mesmo motor serve, com outras
  palavras-chave de serviço

## 4. Modelo de negócio — três caminhos

| | A · Vender para a franqueadora | B · Vender loja a loja | C · Híbrido |
|---|---|---|---|
| Quem paga | Só a franqueadora | Só o franqueado | Os dois |
| Vendas a fazer | 1 | 600 | 1 + adesão |
| Receita por loja | Menor (desconto de volume) | Maior | Média |
| Risco | Cliente único; se trocar de fornecedor, acabou | Cobrança e suporte pulverizados | Diluído |
| Velocidade | Alta se aprovar, zero se não | Lenta e constante | Alta |

**Recomendado: C · Híbrido.**

- A **franqueadora** assina o *Painel da Rede* (ranking, benchmark, alertas de loja em
  risco) — R$ 8 a 15 mil/mês. Ela ganha visão que hoje não tem e paga por isso.
- O **franqueado** assina o plano da loja, **cobrado no mesmo boleto do royalty**. Esse
  detalhe é o mais valioso do modelo inteiro: elimina inadimplência, elimina cobrança
  individual e reduz o churn para perto de zero, porque cancelar exige um ato
  deliberado com a franqueadora.

A franqueadora vira seu canal de distribuição. Você não vende 600 vezes: você vende
uma vez e é homologado.

## 5. Preços

| Plano | Preço/loja/mês | O que entrega |
|---|---|---|
| **Essencial** | R$ 199 | Painel operacional, metas com sazonalidade, insights, auditoria de cancelamentos |
| **Gestão** | R$ 349 | Tudo do Essencial + DRE, fluxo de caixa, conciliação da adquirente |
| **Crescimento** | R$ 549 | Tudo do Gestão + CRM, campanhas de WhatsApp, régua de reativação |
| **Painel da Rede** | R$ 8–15 mil (franqueadora) | Consolidado de todas as lojas, ranking, benchmark, alertas |

Mensagens de WhatsApp são repassadas a custo (~R$ 0,35 por conversa de marketing,
tabela Meta Brasil — *confirmar*). Não embuta na mensalidade: custo variável dentro de
preço fixo é como se perde margem sem perceber.

*Desconto de volume no contrato master:* R$ 249/loja acima de 300 lojas ativas.

**Ticket médio modelado: R$ 319/loja/mês** (mix estimado de 30% Essencial, 50% Gestão,
20% Crescimento).

## 6. Custos

### Custo por loja (mensal, estimativa)

| Item | Valor | Observação |
|---|---|---|
| Infraestrutura | R$ 8 | Servidor, banco e armazenamento rateados |
| API Trinks | R$ 0 a ? | **Zero se a cota for do plano da loja. Item nº 1 a validar.** |
| Suporte | R$ 34 | 1 pessoa de CS para ~175 lojas |
| Cobrança | R$ 3 | Taxa da plataforma de pagamento |
| **Total** | **~R$ 45** | **Margem bruta ~86% sobre R$ 319** |

Margem bruta de SaaS saudável fica entre 70% e 85%. O modelo está no topo da faixa
porque o produto é leve — não tem processamento pesado nem armazenamento grande.

### Custo fixo (mensal, em regime)

| Item | Valor |
|---|---|
| Desenvolvimento e manutenção (1 dev sênior parceiro) | R$ 16.000 |
| Customer Success (1 pessoa) | R$ 6.000 |
| Infra base, ferramentas, contabilidade | R$ 3.000 |
| Seu pró-labore no projeto | R$ 10.000 |
| **Total** | **R$ 35.000** |

### Investimento até a Fase 2

| Fase | Custo | Prazo |
|---|---|---|
| 0 · Piloto (você + Claude Code) | ~R$ 2.000 | 3–4 semanas |
| 1 · MVP multi-loja | ~R$ 60.000 | 8–10 semanas |
| 2 · Painel da rede + cobrança | ~R$ 50.000 | 6–8 semanas |
| **Total** | **~R$ 112.000** | **~5 meses** |

## 7. Cenários

Premissa comum: ticket médio R$ 319/loja/mês, custo fixo R$ 35 mil/mês, custo variável
R$ 45/loja, base de 431 lojas crescendo para 600.

| | Conservador | **Base** | Agressivo |
|---|---|---|---|
| Adoção em 12 meses | 25% (110 lojas) | **50% (215 lojas)** | Contrato master (450 lojas) |
| Receita lojas/mês | R$ 35.090 | **R$ 68.585** | R$ 112.050 (a R$ 249) |
| Painel da Rede/mês | R$ 0 | **R$ 10.000** | R$ 15.000 |
| Receita total/mês | R$ 35.090 | **R$ 78.585** | R$ 127.050 |
| Custo variável/mês | R$ 4.950 | **R$ 9.675** | R$ 20.250 |
| Custo fixo/mês | R$ 35.000 | **R$ 35.000** | R$ 45.000 |
| **Resultado/mês** | **–R$ 4.860** | **+R$ 33.910** | **+R$ 61.800** |
| **Receita anual** | **R$ 421 mil** | **R$ 943 mil** | **R$ 1,52 mi** |

**Ponto de equilíbrio: 128 lojas pagando** (sem o Painel da Rede) ou **92 lojas**
(com o Painel da Rede a R$ 10 mil).

Ou seja: **basta 21% da rede** para o negócio se pagar. Esse é o número que torna o
projeto defensável — e é ele que você leva para a reunião, não a projeção otimista.

Ano 2, no cenário-base com 600 lojas e 60% de adoção: **R$ 1,5 mi de receita anual,
~R$ 790 mil de resultado.**

## 8. Riscos

| Risco | Impacto | O que fazer |
|---|---|---|
| **A franqueadora decide fazer internamente** | Fatal | Chegar antes com produto pronto e rodando. Propor licenciamento em vez de venda: ela leva a marca, você mantém o motor |
| **Dependência da Trinks** | Alto | Fechar parceria formal. Desenhar a camada de ingestão trocável desde a Fase 1 |
| **Cota/custo de API inviabiliza** | Alto | Item nº 1 da validação. Ingestão incremental reduz o consumo em ~70% |
| **LGPD — vazamento de dado de cliente** | Fatal | Fechar o painel público antes da loja nº 2. Contrato de operador de dados com cada loja |
| **Cliente único (franqueadora)** | Médio | O modelo híbrido protege: se ela sair, as lojas continuam |
| **Você é o único que entende o produto** | Médio | Documentar as regras de negócio. Este conjunto de documentos é o começo |
| **Conflito de papel: você é franqueado e fornecedor** | Médio | Declarar na primeira conversa. Vira vantagem se tratado com transparência, vira problema se descoberto depois |

## 9. Os 8 números que faltam validar

Nenhuma decisão grande antes destes:

1. **Cota da API Trinks é por estabelecimento ou por conta?** Muda o custo unitário.
2. **A Trinks tem programa de parceria/integrador?** Muda a relação inteira.
3. **Quantas das 431 lojas usam o Trinks?** Se a rede não é padronizada, o mercado é menor.
4. **A franqueadora já cobra taxa de tecnologia?** Se sim, entrar nela é o caminho mais curto.
5. **Existe projeto interno de BI na franqueadora?** Se existe, o jogo é parceria, não venda.
6. **Preço real da mensagem de WhatsApp** na tabela Meta Brasil vigente.
7. **Quanto o franqueado médio já gasta** com ferramentas de gestão hoje.
8. **Faturamento médio da loja madura** (o de R$ 97 mil é média com lojas novas puxando para baixo).

## 10. Próximos 30 dias

| Semana | O quê | Resultado esperado |
|---|---|---|
| 1 | Fechar o painel atrás de login. Ligar para a Trinks (itens 1 e 2) | Bloqueador de LGPD resolvido |
| 2 | Conversar com 5 franqueados: mostrar o painel e ouvir | Validação de que a dor é da rede, não só sua |
| 3 | Configurar 2 lojas piloto com dados reais | Prova de que roda fora do Limão |
| 4 | Apresentar para a franqueadora — ver [[03-conversa-com-a-franqueadora]] | Uma decisão: piloto oficial, sim ou não |

---

**Fontes de mercado:**
[Times Brasil — Fast Escova projeta crescer 55% e abrir 159 lojas em 2026](https://timesbrasil.com.br/empresas-e-negocios/wellness/lojas-fast-escova-crescimento-2026/) ·
[Mapa das Franquias — Ecossistema Fast, R$ 502 milhões](https://mapadasfranquias.com.br/noticia/fast-escova-investe-r-11-milhao-projeta-faturamento-de-r-502-milhoes-e-inaugura-nova-fase-como-ecossistema-fast/) ·
[Portal do Franchising — Fast Escova chega a 200 unidades](https://www.portaldofranchising.com.br/noticias/fast-escova-chega-a-200-unidades-em-funcionamento-no-brasil/)
