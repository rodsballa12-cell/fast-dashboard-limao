# Conselho 2026-10-20 · Decisão #3 · **Spa: caixa e a-receber zerados no DRE há 11 dias**

**Data:** 2026-10-20 · **Hora do Conselho:** 11:30
**Origem:** Conselho matinal · Sincronizada automaticamente pelo
workflow `conselho_sync.yml`
**Status inicial:** pendente (aguarda o Rodrigo aprovar)

**APROVADA e EXECUTADA em 20/10/2026** — aberta desde 09/10, 11 dias. Não era célula vazia: o script lia o a-receber só do extrato da Escova. Spa agora R$ 8.435,50 (extrato de 30/09), consolidado R$ 44.464,81, caixa do Spa nulo com o motivo escrito. Conferência nova na auditoria_coerencia.py impede o zero de voltar calado. **Revisar em 2026-10-27**: o número do Spa só fica fresco quando o extrato da Stone sair de 30/09.

## Em jogo

a visibilidade inteira do caixa do Spa

## Texto original do briefing

> **Spa: caixa e a-receber zerados no DRE há 11 dias** · em jogo: a visibilidade inteira do caixa do Spa · executa: liquidado na nuvem, e não era da planilha. O gerar_financeiro.py lia o a-receber só do extrato da Escova; o Spa saía com R$ 0,00 enquanto o card da mesma tela mostrava R$ 8.435,50, porque o card lê o extrato direto. O consolidado reportava R$ 36.029,31 em vez de R$ 44.464,81. O caixa do Spa virou nulo, não zero: existe uma conta corrente da holding e o saldo aparece inteiro na Escova.

## Executor

liquidado na nuvem, e não era da planilha. O gerar_financeiro.py lia o a-receber só do extrato da Escova; o Spa saía com R$ 0,00 enquanto o card da mesma tela mostrava R$ 8.435,50, porque o card lê o extrato direto. O consolidado reportava R$ 36.029,31 em vez de R$ 44.464,81. O caixa do Spa virou nulo, não zero: existe uma conta corrente da holding e o saldo aparece inteiro na Escova

## Como sobrescrever

Se você mudou de ideia sobre esta decisão, rode `/sincronizar` manualmente
e responda com o status real (recusada/reprogramada/executada). Isso
sobrescreve o registro automático.

## Revisão

Sem prazo automático. Volte a esta decisão no próximo Conselho.

## Resultado

_(em branco até a revisão)_
