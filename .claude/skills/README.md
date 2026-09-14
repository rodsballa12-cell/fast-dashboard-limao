# Quadro de funcionários · FAST Limão

Cada pasta aqui é um **funcionário especializado**: um cargo com chaves
próprias, rotina, alçada e uma entrega definida.

Isto é diferente dos robôs em `scripts/`. O robô busca o número no horário
marcado e não pensa. O funcionário lê o número, compara com a regra, julga e
escreve. Um não substitui o outro — o robô é a matéria-prima do funcionário.

## Contratados

| Cargo | Comando | Escreve? |
|---|---|---|
| Diretor de Operação | `/operacao-diaria` | não |
| Diretor Financeiro | `/financeiro` | não |
| Gerente de Marketing | `/marketing` | não |
| Gerente de Relacionamento | `/relacionamento` | não |
| Gerente de Pessoas | `/pessoas` | não |
| Guardião da Memória | `/memoria` | **sim** — só em `docs/decisoes/` |
| Conselho | `/conselho` | não |

Cinco departamentos apuram, a Memória registra, o Conselho cruza. **Só um
cargo escreve**, e num único lugar.

## Como eles conversam

Todos falam o mesmo formato, definido em `PROTOCOLO.md`. O campo que faz a
conversa acontecer é o **`NÃO VEJO`**: cada departamento declara em voz alta o
que está fora das próprias chaves, endereçado a quem tem a chave.

O `/conselho` junta os seis pareceres, casa cada `NÃO VEJO` com o dono da
resposta, e procura três coisas: **cadeia causal** (dois fatos que se
explicam), **contradição** (dois departamentos discordando da mesma
realidade) e **silêncio suspeito** (alguém marcou verde no que outro marcou
vermelho).

A conclusão que sai do cruzamento não estava em nenhum parecer isolado — esse
é o motivo de existir um conselho em vez de seis relatórios.

## Bloqueios que limitam cargos hoje

| Cargo | Trabalha com uma mão só porque |
|---|---|
| Operação | Spa ainda sem identificador do Trinks |
| Financeiro | DRE e extrato Stone entram à mão — dado envelhece |
| Relacionamento | App Meta apagado: monta fila e não envia |
| Pessoas | comissão sem regra cadastrada no Trinks |
| Marketing | o `/marketing-fast` da máquina do Rodrigo ainda não foi absorvido aqui |

## Onde cada cargo mora

Um cargo pode ser guardado em dois lugares, e a escolha decide quem consegue
enxergar aquele funcionário.

| Lugar | Quem enxerga | Serve para |
|---|---|---|
| `.claude/skills/` — **esta pasta** | qualquer sessão, no PC ou na nuvem | cargos que leem dado da FAST |
| `~/.claude/skills/` na máquina do Rodrigo | só o PC dele, mas em todo projeto | cargos pessoais, sem relação com a FAST |

**Regra:** cargo que abre arquivo desta empresa mora aqui, versionado junto do
dado que ele lê. Cargo guardado só na máquina existe para uma pessoa e some
quando o trabalho acontece em outro lugar.

Foi exatamente isso que aconteceu com o `/marketing-fast`: ele é citado em
`data/spa/MIDIAS_HANDOFF.md` como se fizesse parte da empresa, mas vive na
máquina do Rodrigo. Para as quatro rotinas que rodam na nuvem, esse
funcionário nunca foi contratado.

## Divisão de trabalho entre PC e nuvem

Decidido em 14/09/2026. Os cargos são exercidos no **Claude Code do PC** —
é a única superfície que alcança ao mesmo tempo o Obsidian, o Excel do DRE e
este repositório. Não é o app de conversa, que não vê disco; não é o SDK, que
serviria para construir um produto de software, e a FAST não é uma empresa de
software.

A nuvem continua responsável pelo que não pode depender de um notebook ligado:
as rotinas de `.github/workflows/`. **PC julga, nuvem executa.**

## Regra de ouro ao contratar

Toda ficha de cargo precisa das cinco partes: **Cargo · Chaves · Rotina ·
Alçada · Entrega.** A alçada é a que mais importa e a que mais se esquece — é
ela que separa um funcionário de alguém mexendo em coisa que não devia.
