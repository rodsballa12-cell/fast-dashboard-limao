# Script escrito num sistema e executado em outro precisa do encoding do destino

**Descoberto em:** 15/09/2026 · **Custo:** o instalador das tarefas agendadas
não rodou na primeira tentativa.

## O que aconteceu

Escrevi `scripts/agenda/instalar_tarefas.ps1` de uma sessão Linux, com
comentários e mensagens em português — acentos e travessões. Salvo em UTF-8
**sem BOM**, que é o padrão sensato em qualquer lugar que não seja o Windows.

Na máquina do Rodrigo só existe **Windows PowerShell 5.1**, que ao ler um
arquivo sem BOM assume a *codepage do sistema* em vez de UTF-8. Os 74
caracteres não-ASCII viraram lixo, e o script parou de fazer parse.

O diagnóstico veio da sessão do PC, não daqui: **quem executa enxerga o que
quem escreve não vê.**

## A parte que quase passou batido

Corrigido o instalador, sobrava `rodar_agente.ps1` com o mesmo defeito — mas
com apenas **uma** linha acentuada, dentro do texto do briefing. Esse script
teria rodado normalmente e produzido, todo dia, um cabeçalho corrompido no
arquivo entregue ao Rodrigo.

**O bug menor era o mais perigoso**: o grande falha na cara; o pequeno entrega
resultado errado em silêncio, por tempo indeterminado.

## A regra

**Ao escrever código para outro sistema operacional, o encoding faz parte da
interface** — como caminho de arquivo e fim de linha.

Para PowerShell 5.1: **UTF-8 com BOM**, sempre. Vale para `.ps1`, `.bat` e
`.cmd` que tenham qualquer caractere fora do ASCII.

E marque o motivo no topo do arquivo. Editor que salva "UTF-8 sem BOM" —
comportamento padrão de muitos — reintroduz o problema sem avisar, e a próxima
pessoa vai achar que o BOM era lixo.

## Alternativa considerada

Escrever os scripts em ASCII puro elimina a dependência. Descartado: perder
acento em mensagem que o Rodrigo lê todo dia custa mais que um BOM no topo do
arquivo. A escolha é manter o texto legível e declarar o requisito.
