# Conselho 2026-10-08 · Decisão #3 · Autorizar a Memória a rodar `auditoria_coerencia.py` com saída em UTF-8 (ou gravando o resultado num arquivo) para finalmente ler qual é a divergência real represada, em vez de repetir "travou" todo dia sem saber o que esconde

**Data:** 2026-10-08 · **Hora do Conselho:** 22:30
**Origem:** Conselho noturno · Sincronizada automaticamente pelo
workflow `conselho_sync.yml`
**Status inicial:** pendente (aguarda o Rodrigo aprovar)

## Em jogo

pelo menos os R$ 1.287 que o Financeiro já isolou como órfão real fora da reconciliação Stone×Trinks — pode ser isso, ou pode ser outra coisa que ninguém viu ainda

## Texto original do briefing

> Autorizar a Memória a rodar `auditoria_coerencia.py` com saída em UTF-8 (ou gravando o resultado num arquivo) para finalmente ler qual é a divergência real represada, em vez de repetir "travou" todo dia sem saber o que esconde · em jogo: pelo menos os R$ 1.287 que o Financeiro já isolou como órfão real fora da reconciliação Stone×Trinks — pode ser isso, ou pode ser outra coisa que ninguém viu ainda · se nada for feito: mais uma semana de atas repetindo o mesmo NÃO VEJO · executa: Memória, com sua autorização.

## Executor

Memória, com sua autorização

## Como sobrescrever

Se você mudou de ideia sobre esta decisão, rode `/sincronizar` manualmente
e responda com o status real (recusada/reprogramada/executada). Isso
sobrescreve o registro automático.

## Revisão

Sem prazo automático. Volte a esta decisão no próximo Conselho.

## Resultado


**EXECUTADA em 23/10/2026.**

A auditoria roda. `scripts/auditoria_coerencia.py` virou passo obrigatorio depois de qualquer mexida em dado (esta no CLAUDE.md) e em 23/10 passou a conferir tambem se as automacoes carimbaram sucesso, se alguma ata chegou vazia e se decisao antiga ficou sem desfecho (`24b285f`). Foi ela que achou as 12 atas orfas corrigidas em `a2df220`.

_Fechada na varredura de 23/10/2026, com evidencia no proprio repositorio. Se o desfecho nao confere, corrija aqui — este campo e a memoria, e memoria errada custa mais que memoria vazia._
