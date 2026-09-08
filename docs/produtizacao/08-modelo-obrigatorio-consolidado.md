---
titulo: "Homologação obrigatória com cobrança consolidada — análise"
projeto: Franquia_FAST_Limao
tipo: analise-de-modelo
status: rascunho-v1
criado: 2026-09-08
tags: [fast, modelo-de-negocio, homologacao, contrato]
---

# Homologação obrigatória com cobrança consolidada

> **A ideia:** o FAST Insights vira software de uso obrigatório para toda a rede, como o
> Trinks e o Sults já são, e a franqueadora cobra das lojas e repassa a você de forma
> consolidada — uma fatura, não 600.

## 1. Veredito

**Faz sentido, e é provavelmente o melhor desenho disponível — com duas condições.** O
contrato já tem o mecanismo pronto, os números melhoram em quase todos os eixos, e o
risco principal do plano (o canal) deixa de existir. As duas condições estão na seção 5:
o preço e a participação andam juntos, e o contrato precisa de quatro travas.

## 2. O contrato já faz isso — e você não precisa inventar nada

| Cláusula | O que diz | Por que importa |
|---|---|---|
| **7.6** | "os softwares que devem ser utilizados pelo FRANQUEADO são: Trinks (ERP) e Sults (CRM) ... custo ... a ser pago aos fornecedores homologados" | O precedente exato. Já existe software obrigatório com mensalidade paga a terceiro |
| **12.8** | "deverá utilizar **obrigatoriamente** os SOFTWARES ... indicados pela FRANQUEADORA ... utilizar-se do FORNECEDOR HOMOLOGADO" | Obrigatoriedade não precisa ser criada, só estendida a mais um item da lista |
| **12.11** | "Se e quando a FRANQUEADORA estabelecer deverão ser alterados os softwares ... deve o FRANQUEADO realizar tempestivamente a troca e arcar com todos os custos" | Permite **acrescentar** software durante a vigência |
| **2.3** | a franqueadora pode alterar padrões, "o que pode implicar, inclusive, em **custos adicionais** ... com o que desde já expressamente concorda" | Alcança os 431 contratos já assinados, não só os novos |
| **xlii** | "Utilizar **somente** os softwares indicados pela FRANQUEADORA" | Fecha a porta para um concorrente entrar por baixo |
| **6.2.1 e 19.3.3 (iv)** | descumprimento gera multa de R$ 3.000 por infração ou rescisão | A obrigação tem dente. Não é sugestão |

**Tradução:** a franqueadora pode tornar o produto obrigatório para toda a rede sem
alterar um único contrato. Para franqueados novos, basta constar da Circular de Oferta
de Franquia, como a Lei 13.966/2019 exige para fornecedores e taxas obrigatórias.

## 3. O que muda nos números

Premissas do cenário obrigatório, e por quê:

| Premissa | Voluntário | Obrigatório | Razão |
|---|---|---|---|
| Teto de adoção | 65% | **95%** | Não é venda, é obrigação. Os 5% são lojas em implantação e em transição |
| Mês central da curva | 16 | **12** | A franqueadora marca prazo; não há convencimento loja a loja |
| Inclinação | 0,32 | **0,45** | Implantação em bloco, não gota a gota |
| CAC | R$ 400 | **R$ 50** | Não há esforço de venda — só onboarding |
| Custo variável | R$ 45 | **R$ 42** | Some a cobrança por loja: é uma fatura só |
| Preço | R$ 319 | **R$ 249** | Custo imposto a todos precisa ser defensável até para a loja mais fraca |

Resultado (os quatro cenários estão na aba Cenários da planilha):

| Cenário | 1º mês positivo | Caixa zera | Capital necessário | Receita ano 3 | Resultado ano 3 | Lojas |
|---|---:|---:|---:|---:|---:|---:|
| **Voluntário (base)** | M15 | M23 | R$ 267.088 | R$ 1.526.137 | R$ 883.248 | 389 |
| Obrigatório · sem participação | M10 | M16 | R$ 178.701 | R$ 1.748.830 | R$ 1.051.296 | 570 |
| Obrigatório · participação 20% | M12 | M19 | R$ 200.150 | R$ 1.399.064 | R$ 701.530 | 570 |
| **Obrigatório · participação 30%** | M13 | M21 | **R$ 215.809** | R$ 1.224.181 | R$ 526.647 | 570 |
| Obrigatório a R$ 299 · participação 30% | M12 | M18 | R$ 198.024 | R$ 1.453.133 | R$ 755.599 | 570 |

Leia a linha do meio com atenção. **Cedendo 30% da receita e cobrando 22% menos por
loja, você ainda precisa de menos capital (R$ 216 mil contra R$ 267 mil) e chega ao azul
dois meses antes.** O que se perde é upside no ano 3; o que se ganha é quase todo o
risco de execução.

## 4. A regra de negociação: preço e participação andam juntos

Qual participação você pode ceder e ainda ficar igual ao cenário voluntário? Depende do
preço que sobreviver à negociação:

| Preço obrigatório | Participação de indiferença | Capital nesse ponto |
|---|---:|---:|
| R$ 249 | **9,6%** | R$ 188 mil |
| R$ 299 | **23,9%** | R$ 190 mil |
| R$ 319 | **28,4%** | R$ 191 mil |

**A leitura para a mesa:** se a franqueadora quer 30% da receita, o preço não pode cair
para R$ 249. Se ela quer o preço em R$ 249 para vender à rede, a participação dela não
pode passar de 10%. Os dois pedidos juntos existem — mas custam metade do seu resultado.

Isso é o que você leva escrito, e é a diferença entre negociar com dado e negociar com
sensação.

## 5. Os quatro riscos do consolidado — e as travas que os resolvem

A cobrança consolidada é excelente para o caixa e péssima para a soberania. Quem cobra,
manda. Quatro riscos, e a cláusula que neutraliza cada um:

| Risco | O que acontece na prática | Trava a pedir no contrato |
|---|---|---|
| **Concentração total** | 100% da receita num único pagador. Um atraso de 60 dias e você financia a rede inteira | Pagamento até o dia 10 do mês seguinte, com multa e juros, e **direito de cobrar as lojas diretamente** se o atraso passar de 60 dias |
| **Perda do relacionamento** | Sem contrato com a loja, trocar de fornecedor não custa nada a ninguém: você perde 100% de uma vez, não aos poucos | Prazo mínimo de 48 meses, renovação automática, e **aviso prévio de 12 meses** para descontinuar |
| **Controle do preço** | Quem cobra define o reajuste. Cada renovação vira uma negociação em que você tem zero alavanca | Reajuste **por índice** (IPCA ou IGP-M), não por negociação |
| **Dependência somada à 13.13** | Ela já tem argumento de titularidade e passa a ter também o cliente e o caixa | Cláusula afastando **expressamente** a 13.13 para este produto, e direito de ofertar direto às lojas por 24 meses se ela rescindir |

Sem as quatro, o modelo consolidado transforma um negócio em um emprego sem carteira.
Com as quatro, ele é melhor que o voluntário em quase tudo.

## 6. Um efeito colateral bom: a LGPD fica limpa

No modelo voluntário há uma zona cinzenta: você trata dado de cliente de outra loja sem
que ninguém seja claramente o controlador. No modelo obrigatório e consolidado, os
papéis ficam óbvios e alinhados com o que o contrato já diz na cláusula 13.11 — **a
franqueadora é a controladora** (o mailing é propriedade dela), **você é o operador**.
Um contrato de operador com a franqueadora cobre as 600 lojas de uma vez, em vez de 600
contratos individuais.

## 7. O que muda na proposta

A conversa deixa de ser "deixem eu vender para a rede" e passa a ser **"vamos padronizar
a gestão da rede, como vocês já fizeram com o Trinks e o Sults"**. É um pedido muito
mais fácil de aprovar, porque:

- fala a língua que a franqueadora já usa (fornecedor homologado, padronização, cláusula 12.8);
- entrega a ela o que ela não tem — visão comparável das 431 lojas — sem custo direto;
- dá a ela uma nova linha de receita, se houver participação;
- e resolve o problema dela de franqueado que não sabe o próprio número.

**O que continua igual:** nada disso acontece antes do parecer sobre a cláusula 13.13.
Um modelo de dependência total só é seguro depois que a titularidade estiver resolvida
por escrito — ver [[05-analise-contratual]].

## 8. Recomendação

Peça **obrigatório a R$ 299 com participação de até 25%**, com as quatro travas da
seção 5. Aceite até 30% se o preço ficar em R$ 299. Recuse a combinação R$ 249 com 30%:
ela custa metade do seu resultado e não sobra prêmio pelo risco.

Se a franqueadora não quiser participação nenhuma e só quiser padronizar a rede, melhor
ainda — é o cenário de R$ 1,05 milhão de resultado no ano 3 com o menor capital de todos
os desenhos analisados.
