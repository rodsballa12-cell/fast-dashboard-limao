# Pasta de entrada do extrato Stone

Largue aqui o CSV que você exporta do app da Stone. Não precisa fazer mais nada.

Um robô acorda em seguida, **soma** o arquivo ao histórico em
`data/stone_extrato.csv`, apaga o que você subiu e manda o painel se atualizar.
Leva poucos minutos.

## Por que não subir direto por cima do arquivo antigo

A exportação da Stone traz só uma janela — normalmente o mês corrente. Trocar o
histórico por ela apagaria julho e agosto, e com eles a visão do ano, o
histórico da Reserva Stone e a base de recebíveis em D+30.

O robô resolve isso somando: mantém tudo que já existia, acrescenta o que é
novo e descarta o que está repetido. Subir o mesmo arquivo duas vezes não
causa problema nenhum.

## Quando ele recusa

- **Arquivo de outra conta Stone.** Um extrato descreve uma conta. Se o Spa
  ganhar terminal próprio, o arquivo dele é `data/spa/stone_extrato.csv`, não
  este. Misturar as duas transformaria o dinheiro de uma loja em "não
  conciliado" da outra.
- **Arquivo que não é extrato da Stone** (colunas diferentes).

Arquivo recusado **fica aqui, intacto**, e o robô falha de propósito para você
receber o aviso do GitHub. Nada é perdido e o histórico não é tocado.

## Para rodar na mão

```bash
python3 scripts/stone_merge.py            # soma o que estiver nesta pasta
python3 scripts/stone_merge.py --dry-run  # só mostra o que faria
```
