# As duas unidades migram para o WhatsApp Cloud API

**Data:** 2026-09-14 · **Quem decidiu:** Rodrigo
**Departamentos ouvidos:** Relacionamento, Marketing

## Contexto

Nenhuma das duas unidades tinha WABA (WhatsApp Business Account) na Cloud API.
A auditoria do histórico mostrou que os campos `whatsapp_*` da Escova foram
`null` em todos os commits, e `data/wa_historico.json` nunca existiu: o disparo
automático jamais enviou uma mensagem. Os dois números rodam hoje o
**aplicativo** WhatsApp Business, que é coisa diferente da Cloud API.

Números confirmados:

| Unidade | Número |
|---|---|
| Escova | +55 11 96612-9197 |
| Spa | +55 11 99024-3927 |

Em aberto no momento da decisão: 58 clientes em alerta de churn, R$ 13.417 de
LTV exposto, e o Spa inaugurando em 11 dias sem canal de mensagem.

## Alternativas descartadas

**Só o Spa agora** — era a recomendação, por ser risco quase zero (ninguém
conversa nele ainda). Descartada: deixaria a Escova, que tem os 411 clientes e
todo o LTV em risco, sem automação por tempo indeterminado.

**Chip novo só para a API** — mantinha o atendimento intacto, mas a mensagem de
reativação sairia de um número desconhecido da cliente, e a resposta cairia
onde ninguém olha. Reativação existe para gerar resposta; descartada por
esvaziar o próprio propósito da campanha.

**Não migrar** — Spa inaugura sem disparo e a régua de reativação segue parada.

## O que foi decidido

As duas unidades vão para a Cloud API.

## O custo aceito, explicitamente

Um número só existe no aplicativo **ou** na Cloud API, nunca nos dois. Ao
migrar, **os dois números saem do aplicativo WhatsApp Business** e as mensagens
passam a chegar apenas pela API.

Isso significa que **a recepção perde a ferramenta que usa hoje para responder
cliente à mão** até existir uma caixa de entrada ligada à API. Num salão sem
hora marcada, onde o cliente pergunta "tem vaga agora?", esse é um custo
operacional real, e foi aceito de forma consciente.

## Sequência acordada

1. **Spa primeiro** — ensaio de risco baixo, valida o fluxo inteiro
2. **Escova depois**, só com a caixa de entrada resolvida ou uma alternativa
   combinada com a recepção

## O que esperamos

Disparo de aniversário e reativação funcionando nas duas unidades antes de
25/09, e a régua alcançando os 58 clientes hoje em alerta de churn.

## Revisar em

2026-10-14 — verificar se as mensagens saíram, se houve resposta de cliente
perdida por falta de caixa de entrada, e se a recepção conseguiu trabalhar.

## Resultado

_(em branco até a revisão)_
