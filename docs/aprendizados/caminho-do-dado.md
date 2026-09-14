# Um agente precisa saber o caminho real do dado, não um plausível

**Descoberto em:** 14/09/2026 · **Custo:** duas horas quase gastas consertando
o que não estava quebrado.

## O que aconteceu

O `/marketing` tentou puxar Meta ao vivo pelo Supermetrics, levou um HTTP 400,
e declarou no parecer do Conselho que o painel estava cego e o token quebrado.
O Conselho acreditou e montou uma cadeia causal inteira em cima disso:
"token Meta e WhatsApp são o mesmo App, uma ação resolve os dois".

Nada disso era verdade. A verificação mostrou:

- `META_ACCESS_TOKEN` no GitHub: **funcionando** — a rotina puxou dado novo no
  mesmo dia, 2.644 linhas alteradas
- Supermetrics: **autenticado**, e uma consulta real devolveu gasto dia a dia
  das duas contas, sem cache
- App do WhatsApp: esse sim, apagado — e sozinho

Existiam **três credenciais diferentes**. Duas estavam boas. O agente
generalizou de uma falha para "tudo caiu".

## A raiz

O cargo tinha a instrução "usa Supermetrics para dados ao vivo", mas
**o pipeline do painel não usa Supermetrics para Meta** — usa a Meta Graph API
direta. O agente foi por um caminho plausível que não era o caminho real, e
interpretou o erro daquele caminho como diagnóstico do sistema todo.

## A regra

**Toda ficha de cargo precisa dizer por onde o dado realmente chega**, fonte
por fonte, com a credencial de cada uma. E toda vez que um agente for declarar
algo quebrado, ele precisa:

1. Nomear **qual caminho** falhou, não "o sistema"
2. Testar os outros caminhos antes de generalizar
3. Conferir o frescor do dado que já está gravado

## Por que isso importa mais que o episódio

Um departamento gritando vermelho errado custa igual a um calado. Da primeira
vez você perde dinheiro por não enxergar; da segunda, perde tempo consertando
o que não quebrou — e começa a desconfiar dos alertas verdadeiros.

Vale para qualquer agente, em qualquer departamento.
