# Um agente que não sabe por onde o dado chega reporta quebra onde não há

**Destilado em:** 2026-09-14 · **Origem:** o conselho de 14/09 e a auditoria
que o revisou. Consolida duas notas escritas em paralelo no mesmo dia — uma no
PC, outra na nuvem — sobre o mesmo episódio.

## Regra

Antes de declarar qualquer fonte de dados quebrada, o agente precisa dizer
**qual caminho específico falhou** e verificar se existe outro caminho que
ainda entrega o dado.

## O que aconteceu

O `/marketing` tentou puxar Meta ao vivo pelo Supermetrics, levou um HTTP 400,
e declarou no parecer que o painel estava cego. O Conselho acreditou e montou
uma cadeia causal inteira em cima disso: *"token Meta e WhatsApp são o mesmo
App, uma ação resolve os dois."*

Nada disso era verdade. A verificação mostrou três credenciais distintas:

| | Estado real |
|---|---|
| `META_ACCESS_TOKEN` no GitHub | **funcionando** — puxou dado novo no mesmo dia, 2.644 linhas alteradas |
| Supermetrics | **autenticado** — uma consulta real devolveu gasto dia a dia das duas contas, sem cache |
| App do WhatsApp | apagado — e sozinho |

Duas das três estavam boas. O agente generalizou de uma falha para "tudo caiu".

## A causa

A ficha dizia "usa Supermetrics para dados ao vivo", mas **o painel não usa
Supermetrics para Meta** — usa a Meta Graph API direta
(`scripts/refresh_midias.py`). O Supermetrics cobre só o bloco Google Business
(`scripts/refresh_google.py`).

A prova mais limpa: o Instagram do Spa aparecia no painel com 202 seguidores
**sem estar conectado no Supermetrics** — porque nunca dependeu dele.

## Como aplicar

1. Antes de declarar 🔴 num conector, leia o JSON que o painel usa e veja se
   está fresco. Se estiver, o pipeline funciona, independente do que acontece
   com outros conectores.
2. Ao aprender que um dado vem de um caminho específico, registre isso nas
   **Chaves** do cargo — com a credencial de cada caminho.
3. A pergunta certa não é *"o conector Y está funcionando?"* — é **"o dado que
   preciso está presente e fresco onde vou lê-lo?"**

## O padrão que se repete

Este erro aparece sempre que um cargo é documentado por como o sistema
*deveria* funcionar, em vez de como *realmente* funciona. A documentação
envelhece; o código muda. Toda vez que uma ficha for atualizada, confira se os
caminhos descritos batem com os scripts reais.

## E o custo de errar para o outro lado

Um departamento gritando vermelho errado custa igual a um calado. Da primeira
vez você perde dinheiro por não enxergar; da segunda, perde tempo consertando
o que não quebrou — e começa a desconfiar dos alertas verdadeiros.
