# A empresa digital passa a ter um agente por departamento, com língua comum

**Data:** 2026-09-14 · **Quem decidiu:** Rodrigo
**Departamentos ouvidos:** nenhum — esta é a decisão que os cria

## Contexto

O repositório tinha 21 scripts, 4 rotinas automáticas e 8 conectores, mas
nenhum organograma: não estava escrito quem respondia por qual número. O único
cargo existente, o `/marketing-fast`, vivia na máquina do Rodrigo e por isso
não existia para nenhuma sessão na nuvem.

## Alternativas descartadas

**Agent SDK** — serviria para construir um produto de software. A FAST não é
uma empresa de software; adotar isso significaria contratar programador para
refazer o que Skills entrega pronto.

**App de conversa** — não alcança disco. Foi exatamente o que travou a leitura
do vault do Obsidian nesta sessão.

**Cowork** — desenhado para trabalho sem forma de repositório. O escritório da
FAST é um repositório.

**Um único agente generalista** — testado informalmente e descartado: sem
alçada por cargo, qualquer recomendação chega com o mesmo peso, e o agente
opina sobre conector que não pode abrir.

## O que foi decidido

Claude Code no PC, com Skills como cargos. Sete fichas em `.claude/skills/`,
cada uma com as cinco partes obrigatórias: Cargo, Chaves, Rotina, Alçada e
Entrega.

Os departamentos conversam por um formato único (`PROTOCOLO.md`), cujo campo
`NÃO VEJO` obriga cada um a declarar a própria cegueira com endereço. O
`/conselho` cruza os pareceres procurando cadeia causal, contradição e
silêncio suspeito.

Divisão de superfícies: **PC julga, nuvem executa.** As rotinas de
`.github/workflows/` seguem na nuvem, sem depender de notebook ligado.

## O que esperamos

Que a decisão semanal de mídia e a leitura diária da operação deixem de
depender de o Rodrigo lembrar de olhar o painel, e que pelo menos um
cruzamento entre departamentos por mês produza conclusão que nenhum relatório
isolado daria.

## Revisar em

2026-10-14

## Resultado

_(em branco até a revisão)_
