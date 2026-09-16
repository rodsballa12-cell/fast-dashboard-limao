# O cron do GitHub Actions não é relógio — e um fire por dia é uma aposta

**Descoberto em:** 16/09/2026 · **Custo:** o painel de mídia passou o dia com
dado de 21 horas atrás, e a primeira explicação que apareceu foi a errada.

## O que aconteceu

O Rodrigo notou que a rotina de mídia não estava rodando. O `midias_refresh.yml`
tinha **um** fire por dia, `0 10 * * *` — 07h BRT. Medindo o que o GitHub
realmente entregou:

| agendado | rodou de fato | atraso |
|---|---|---|
| 14/09 10h UTC | 16h06 UTC | **6h06** |
| 15/09 10h UTC | 14h35 UTC | **4h35** |
| 16/09 10h UTC | não rodou até 11h56 UTC | ainda contando |

**O cron do GitHub Actions é "mais ou menos".** Em horário de pico a fila
atrasa horas, e às vezes o fire é descartado em silêncio. A documentação
avisa; a gente esquece.

Com um fire por dia, qualquer um desses atrasos significa painel parado o dia
inteiro. Não há segunda chance.

## A correção

Três fires — 10h, 12h e 14h UTC — e um early-exit que compara a **data em BRT**
do `gerado_em` com hoje:

```yaml
hoje=$(TZ=America/Sao_Paulo date +%Y-%m-%d)
ger=$(sed -nE 's/.*"gerado_em": *"([^"]+)".*/\1/p' data/midias_sociais.json | head -1)
if [ "${ger:0:10}" = "$hoje" ]; then echo "skip=true" >> $GITHUB_OUTPUT; fi
```

Três chances; o primeiro que chegar faz o trabalho e os outros dois terminam em
segundos sem tocar na API da Meta.

**Por data, não por horas de idade.** O trabalho é "uma atualização por dia" —
uma regra de "menos de 8h" erraria na virada, e uma de "menos de 24h" travaria
o refresh do dia seguinte quando o anterior atrasasse.

## O que já sabíamos e não aplicamos

O `refresh.yml` **já tinha esse remédio** desde 01/09, com o comentário no topo
dizendo "GitHub Actions pula fires de cron silenciosamente em horários de pico".
A solução existia no repositório, num arquivo ao lado, e o workflow de mídia
nasceu sem ela.

**Remédio conhecido não se aplica sozinho.** Quando um workflow novo entra,
vale perguntar quais defesas os vizinhos já têm.

## A parte que quase virou a explicação errada

A primeira hipótese levantada foi *"perdi o conector Supermetrics nesta sessão,
a rotina auto-vinculada não funciona mais"*. Duas coisas diferentes com o mesmo
nome:

| | o que é | onde vive |
|---|---|---|
| **Conector Supermetrics** | MCP de uma conversa do Claude | sessão de chat |
| **`SUPERMETRICS_API_KEY`** | segredo do GitHub, chamada HTTP do runner | o workflow |

O pipeline usa o **segundo**, e nunca soube que o primeiro existe. E o
Supermetrics só alimenta o Google Business Profile — **Meta Ads, Instagram e
Facebook vêm da Meta Graph API direta**, com `META_ACCESS_TOKEN`.

É a segunda vez que confundir os dois quase gerou uma conclusão errada. Por isso
a ficha do cargo Marketing já diz, em letras próprias: *uma falha no Supermetrics
NÃO cega os dados de Meta.*

## A regra

**Antes de culpar um conector, confira se o pipeline sequer o usa.** Abra o
workflow e leia de onde ele tira credencial. Leva trinta segundos e evita horas
procurando no lugar errado.
