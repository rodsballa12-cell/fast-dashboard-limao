# Spa abre no número da Escova — separação após 30 dias

**Data:** 2026-09-14 · **Quem decidiu:** Rodrigo
**Departamentos ouvidos:** Marketing, Relacionamento

## Contexto

O Spa inaugura em 25/09/2026 (11 dias). A ativação de um número dedicado no
WhatsApp Cloud API exige verificação de chip + possível migração de número em
uso — fluxo com risco de derrubar atendimento ativo num momento crítico de
abertura.

## O que foi decidido

O Spa abre usando o mesmo número de WhatsApp já configurado na Escova.
A separação por número próprio fica para após os primeiros 30 dias.

## Motivo

Tirar do caminho crítico qualquer risco de indisponibilidade do canal WA a
11 dias da abertura. Os templates aprovados na Escova já cobrem os clientes
do Spa sem nenhum passo adicional.

## Custo aceito

Conversas de clientes da Escova e do Spa ficam misturadas num único número
durante o período. A recepção precisa identificar manualmente de qual unidade
é cada cliente.

## Gatilho para reverter

Quando o volume de atendimento do Spa justificar um número dedicado — critério
operacional a ser avaliado na revisão. Indicador sugerido: > 30 conversas/mês
vindas de clientes identificados como Spa.

## Alternativas descartadas

**Número novo (chip dedicado):** viável tecnicamente (R$ 10–20), mas exigiria
verificação Meta + aprovação de templates na nova conta WA — risco de atraso
ou rejeição sem tempo de contornar antes de 25/09.

**Número existente 99024-3927:** listado no config como display do Spa, mas
não confirmado se está em uso ativo. Migrar para Cloud API retira o acesso
ao app WA convencional sem reversão imediata — descartado pelo risco.

## Revisar em

2026-10-25 — avaliar volume de atendimento do Spa e decidir se separação
de número é justificada.

## Resultado

_(em branco até a revisão)_
