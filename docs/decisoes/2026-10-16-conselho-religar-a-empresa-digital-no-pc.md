# Religar a empresa digital no PC (login vencido e git travado)

**Data:** 2026-10-16 · **Quem decidiu:** Rodrigo (aprovou as 3 decisões do Conselho de 16/10)
**Departamentos ouvidos:** Memória, Operação

## Contexto
Conselhos de 12 a 15/10 não rodaram e as rotinas agendadas de 14 a 16/10
gravaram só "Failed to authenticate": o login do Claude no PC venceu em
13/10. Ao mesmo tempo, trabalho de 15/10 sem salvar fazia toda atualização
automática parar com "cannot pull with rebase: You have unstaged changes".
Rodrigo salvou esse trabalho às 09:24 de 16/10 (commit 1260cb7), o que resolve
a segunda trava. Falta o login. Mesma família do aprendizado de 08/10
(*alarme honesto mas mudo*): a falha foi dita e ninguém foi avisado por 4 dias.

## Decisão
1. Rodrigo entra de novo no Claude do PC (login).
2. Salvar o trabalho pendente: feito em 16/10.
3. Tarefa técnica: a rotina agendada deve avisar ativamente quando o teste de
   login falhar, em vez de só gravar no registro.

## Alternativas descartadas
- Rodar as rotinas só pela sessão da nuvem: não alcança Excel nem vault.

## O que esperamos
Rotinas de 17/10 (07:30 a 09:00) e Conselho das 22:30 rodando com análise de
verdade, e atas chegando ao repositório.

## Revisar em
2026-10-19

## Resultado
**EXECUTADA em 23/10/2026.** Religada em 22/10. A causa nao era a que se supunha: o login do PC tinha voltado como 'Anthropic Console account - API usage billing' em vez da assinatura Max, e cobrava de uma conta de API com saldo zero. Resolvido com /login na opcao 1. Custou 28 pareceres vazios entre 18 e 22/10.

_Fechada na varredura de 23/10/2026, com evidência no próprio repositório. Se o desfecho não confere, corrija aqui — este campo é a memória, e memória errada custa mais que memória vazia._
