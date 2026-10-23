# Meta do Spa em outubro revisada: R$ 40.000, com super meta de R$ 60.000

**Data:** 2026-10-02 (registrada em 2026-10-16) · **Quem decidiu:** Rodrigo
**Departamentos ouvidos:** Financeiro (leitura da planilha "Meta Limão outubro")
**Substitui:** `2026-09-30-meta-spa-outubro-25k-super-30k.md` (a nota antiga fica como está; este registro vale daqui em diante)

## Contexto
Em 30/09 a meta de outubro do Spa foi fixada em R$ 25.000 (super R$ 30.000).
Em 02/10 Rodrigo escolheu, na nova planilha da franqueadora, três degraus:
Meta 1 = R$ 40.000 (a meta), Meta 2 = R$ 50.000 (degrau intermediário, só
informativo) e Meta 3 = R$ 60.000 (super meta). A revisão ficou só no
`config.json`; a nota de 30/09 não foi atualizada, e o Conselho de 16/10 achou
as duas versões em circulação (quem lia a nota via o Spa em 52%, quem lia o
painel via 32%).

## Alternativas descartadas
- Manter R$ 25.000 / R$ 30.000 da decisão de 30/09.

## O que esperamos
Spa faturando ao menos R$ 40.000 em outubro. Em 15/10 estava em R$ 12.968
(71,8% da meta do período); no ritmo, perto de R$ 28,7 mil.

## Onde está no sistema
`data/config.json` → `unidades.spa.meta_mensal_por_mes["2026-10"] = 40000`,
`super_meta_mensal_por_mes["2026-10"] = 60000`,
`meta_intermediaria_por_mes["2026-10"] = 50000`.

## Revisar em
2026-11-02 (fechamento de outubro; definir novembro)

## Resultado

**CONFIRMADA em 23/10/2026.** O Rodrigo reafirmou a escolha ao responder o Conselho de 23/10: meta de outubro **R$ 40.000**, super meta **R$ 60.000**.

Aplicado no mesmo dia: o painel do Spa lia a provisoria de R$ 50.000 porque `build_spa_dashboard._meta_mensal_spa()` nao conhecia o override mes a mes que nasceu em 30/09 — so o DRE conhecia. De 30/09 a 23/10 o painel disse que o Spa estava em 37% da meta quando estava em 46%. Os dois leitores agora leem o mesmo campo.

_Fechada na varredura de 23/10/2026, com o conserto no mesmo commit._
