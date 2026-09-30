# Meta do Spa em outubro: R$ 25.000, com super meta de R$ 30.000

**Data:** 2026-09-30 · **Quem decidiu:** Rodrigo
**Departamentos ouvidos:** Financeiro (leitura da planilha Meta_Limão)

## Contexto
O Spa abriu em 25/09/2026. A meta de setembro foi R$ 20.000 cheia, sem ratear
(decisão de 28/09). Outubro estava com R$ 30.000 provisórios no `config.json`.
Rodrigo mandou a planilha `Meta_Limão.xlsx` com três cenários, todos com ticket
médio de R$ 250 e mix de 35% pacote, 50% serviço, 15% vale-presente e 5%
produto, com 7% de desconto:

| Cenário | Receita total | Clientes / comandas |
|---|---|---|
| Meta 1 (até 30/09) | R$ 20.000 | 78 |
| Meta 2 | R$ 25.000 | 98 |
| Meta 3 | R$ 30.000 | 118 |

Decisão: **Meta 2 é a meta de outubro** e **Meta 3 é a super meta de outubro**.

## Alternativas descartadas
- Manter os R$ 30.000 provisórios como meta (a Meta 3 vira super meta, acima da meta).
- Ratear a meta de outubro: o Spa opera o mês inteiro, não há o que ratear.

## O que esperamos
Spa faturando ao menos R$ 25.000 em outubro (98 clientes/comandas a R$ 250);
R$ 30.000 (118 clientes) é a super meta. Em 30/09 o Spa estava com R$ 9,8 mil
em 7 dias operados.

## Onde está no sistema
`data/config.json` → `unidades.spa.meta_mensal_por_mes["2026-10"] = 25000` e
`super_meta_mensal_por_mes["2026-10"] = 30000`. Novembro (R$ 40.000) e dezembro
(R$ 50.000) continuam os provisórios, **não** vieram desta planilha.

## Revisar em
2026-11-02 (fechamento de outubro; definir novembro)

## Resultado
_(em branco até a revisão — preencher com o que aconteceu de verdade)_
