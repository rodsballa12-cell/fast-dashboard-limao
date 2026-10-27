---
titulo: Proposta Colégio Del Rios — 27 professoras, plano mensal Escova + Unha + Spa
data: 2026-10-27
versao: 2 — corrige dois erros da versão 1
status: RASCUNHO — nenhum preço foi comunicado a ninguém
base: DRE 20/10/2026 · comissões data/comissoes.json (18/10/2026)
---

# Colégio Del Rios · 27 professoras

**Nada aqui foi enviado.** Rascunho para aprovar, corrigir ou descartar.

## Duas correções da versão de ontem

**1. Usei a comissão média, e a média escondia o que importa.** O Trinks cobra
por categoria, e as taxas são muito diferentes:

| Categoria | Comissão | Sobra de cada R$ 1 cobrado |
|---|---|---|
| **Escova** | 30% | R$ 0,50 |
| **Unhas** | **50%** | R$ 0,30 |
| Massagem (Spa) | 25% | R$ 0,53 |

A média de 38,31% do DRE fazia a escova parecer pior do que é (41,7% quando é
50%) e não mostrava que **unha é o serviço de comissão mais cara da casa**.

**2. Calculei o piso de desconto errado.** Tratei o custo como se ficasse
parado quando o preço cai. Não fica: **comissão, Simples e royalty são
percentuais do que foi cobrado** — caem junto com o desconto. Só o insumo é
por sessão. O piso aritmético real é 83–89%, não os 30–45% que eu disse.

Isso não quer dizer que dê para descontar 80%. Quer dizer que **o limite é
comercial, não aritmético**: o que impede é não ensinar a cliente a esperar
metade do preço, não a conta.

## A regra que muda a proposta

**Cada R$ 1,00 de desconto custa diferente conforme onde ele cai:**

| Descontar… | custa de margem |
|---|---|
| **Unha** | **R$ 0,36** |
| Escova | R$ 0,56 |
| Massagem | R$ 0,61 |

É o contrário da intuição: **o desconto tem de cair no item de comissão alta**,
porque metade dele é pago pela comissão que deixa de ser devida.

Na prática, com a mesma cesta e **praticamente o mesmo preço para a professora**:

| Como dar o desconto | Ela paga | Margem/ano nas 27 |
|---|---|---|
| 15% em tudo | R$ 215,90 | R$ 28.947 |
| **40% só na unha** | **R$ 215,60** | **R$ 30.448** |

**Mesmo preço no bolso dela, R$ 1.501 a mais por ano no seu.** E "40% de
desconto na unha" vende melhor que "15% em tudo".

## O plano

**ESCOVA + UNHA — o plano base**

| | |
|---|---|
| 2 escovas no mês | R$ 158,00 (preço cheio) |
| 1 pés e mãos | R$ 57,60 (**40% off** de R$ 96) |
| **Mensalidade** | **R$ 215,60** |
| Margem por professora | R$ 93.98 |
| **27 professoras** | **R$ 2,537/mês · R$ 30,448/ano** |

**+ SPA — a subida**

| | |
|---|---|
| O plano base | R$ 215,60 |
| 1 massagem relaxante | R$ 59,00 (preço cheio — é o item que menos convém descontar) |
| **Mensalidade** | **R$ 274.60** |
| Margem por professora | R$ 125.25 |
| **27 professoras** | **R$ 3,382/mês · R$ 40,580/ano** |

## Por que terça e quarta, e por que isso é a proposta

Terça vale 5,8% da semana e quarta 8,1% — juntas **R$ 8.340/mês**, contra
R$ 21.600 do sábado sozinho. O plano base traz **R$ 5.821/mês**: isso é
**+70% nesses dois dias**, com cadeira que hoje não rende nada.

E cabe com folga: as cadeiras de cabelo operam a **11%** de ocupação e as de
unha a **6,3%** — a mais vazia da casa. As 54 escovas e 27 pés-e-mãos do plano
dão cerca de 10 atendimentos por dia nesses dias, espalhados em 12 horas.

**Dar desconto para sábado seria tirar cadeira de quem paga inteiro no único
dia com fila.** Em terça, a cadeira vazia não rende nada — e é por isso que o
desconto cabe ali e não em qualquer dia.

Vale notar: **MÃOS é o serviço mais vendido da casa** — 130 das 552 sessões do
mês. Unha não é um acessório do plano; é o que a loja mais faz.

## O que o Rodrigo decide

1. **Quem paga:** o colégio (contrato, receita garantida) ou cada professora?
2. **Sessão não usada:** acumula 30 dias, vence, ou vira crédito?
3. **Com Spa ou só Escova + Unha?** O Spa sobe a mensalidade 27% e a margem 31%.
4. **Terça e quarta fechado, ou abre exceção?** A recomendação é fechar.

## Onde isto ainda pode estar errado

**As comissões de `data/comissoes.json` vêm do BackOffice do Trinks, exportadas
em 08/09 e atualizadas em 18/10. Mas `comissoes.habilitado` continua `false`** —
ou seja, a regra está no cadastro de serviços e não no motor de comissão. Se
na hora de pagar a conta for outra, a margem muda.

Antes de assinar 12 meses, confirmar a regra de comissão vale mais que qualquer
ajuste de preço aqui.

**Frescor:** DRE de 20/10 (7 dias), extrato Stone até 16/10 (11 dias), e esta
sessão leu do artefato de 23/10 porque o cofre não abre na nuvem.
