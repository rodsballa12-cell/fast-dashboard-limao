# Zero por falta de dado e zero por falta de entrega são idênticos no arquivo

**Descoberto em:** 18/09/2026 · **Custo:** o detector construído para pegar
parada de entrega passou um dia apontando para o lugar errado.

## O que aconteceu

Em 17/09 a rotina de mídia falhou com o alerta certo pelo motivo errado:

> ⚠️ **Entrega despencou em 16/09** — R$ 14,31 contra mediana de R$ 94,19/dia,
> queda de 85%. *Foi assim que começou a parada de 27/08, que virou 4 dias
> zerados. Vale olhar hoje, não semana que vem.*

A entrega não despencou. **O token da Meta expirou às 11h do dia 16.** Os
R$ 14,31 eram o que a API tinha alcançado antes de morrer — não o gasto do dia.

O `alerta_entrega.py` foi escrito depois do episódio de 27–31/08, quando a
conta parou por quatro dias e ninguém viu (~R$ 480 queimados). Ele funcionou:
viu o número cair e gritou. Só que gritou **"vá olhar a conta de anúncio"**
quando o problema era credencial — duas investigações completamente diferentes.

## Por que isso é pior que não alertar

O alerta ia ficar vermelho todos os dias até alguém perceber, sempre com o
mesmo texto sobre a parada de agosto. **Alarme que não apaga ensina a ignorar
a cor vermelha** — e no dia em que a entrega parasse de verdade, já ninguém
estaria olhando.

## A correção

O script agora confere `_erro` nas janelas de `meta_ads` **antes** de julgar
qualquer número, e devolve `indef` (código 2, não falha a rotina):

> ❔ **A coleta falhou — não dá para avaliar a entrega.**
> A Meta recusou a chamada: *Session has expired on…*
> Os números zerados são ausência de DADO, não ausência de entrega.

Já existia um `indef` para "painel congelado há mais de X horas" — o padrão
estava certo e faltava um caso.

## A regra

**Antes de interpretar um número baixo, pergunte se ele foi medido.**

Ausência de dado e ausência do fenômeno parecem iguais no JSON — as duas
chegam como `0.0` — e pedem ações opostas. Todo detector que julga queda
precisa de um terceiro estado além de "ok" e "alerta": **"não consegui
medir"**.

É a terceira vez nesta semana que o mesmo padrão aparece: os PIX "sem
confirmação" que eram extrato atrasado, o `_erro` que grudava no arquivo
depois do token ser trocado, e agora este. **A família toda é a mesma:
confundir o que o sistema não viu com o que não aconteceu.**
