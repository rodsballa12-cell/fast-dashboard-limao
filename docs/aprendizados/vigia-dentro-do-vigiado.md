# O vigia que mora dentro do vigiado

**Descoberto em:** 15/09/2026 · **Custo:** o painel de mídia passou a manhã
inteira mostrando dados da véspera, e o briefing de Marketing das 08h os
apresentou como se fossem do dia. Ninguém soube até o Rodrigo perguntar, às 10h.

## O sintoma

Nenhum. É esse o ponto.

Não houve erro, e-mail de falha, run vermelho nem card quebrado. O
`midias_refresh.yml` simplesmente **não foi chamado** — o GitHub nunca entregou
o cron. Um workflow que não roda não produz log, e não produzir log é
indistinguível de não ter nada a dizer.

## A parte que parecia resolvida

O repositório já tinha dois detectores de mídia, ambos escritos depois de
episódios caros:

- `alerta_entrega.py` — nasceu do episódio de 27–31/08, quando a conta parou de
  entregar por quatro dias com tudo ativo e queimou ~R$ 480.
- `auditoria_coerencia.py` — nasceu da meta de R$ 60.000 herdada no payload
  zerado do SPA.

Os dois estavam ligados, rodando, testados. E os dois eram chamados **de dentro
do `midias_refresh.yml`** — o único workflow cuja ausência eles precisariam
detectar.

> **Detector que só roda quando o pipeline roda não detecta pipeline parado.**

É óbvio depois de escrito. Não era antes, porque o raciocínio ao ligar um
detector é "onde eu tenho o dado fresco na mão?", e a resposta é sempre "dentro
do pipeline que acabou de buscá-lo".

## A parte pior: o defeito já vinha acontecendo

Olhando o histórico dos runs depois do fato:

| Dia | Alvo | Saiu | Atraso |
|---|---|---|---|
| 12/09 | 07h | 10h18 | +3h18 |
| 13/09 | 07h | 11h01 | +4h01 |
| 14/09 | 07h | 13h06 | +6h06 |
| 15/09 | 07h | não saiu | — |

Em **nenhum** desses dias o pipeline quebrou. Ele entregou — depois das 08h, e
portanto depois do briefing de Marketing, que leu dado da véspera nos quatro
dias e não disse em nenhum.

A régua do cargo aceitava "atualizado há menos de 24h" como sinal de saúde. Dado
de 15h30 de idade passa nessa régua com folga. A régua não estava errada para a
pergunta que respondia — *o pipeline quebrou?* — mas estava respondendo a
pergunta errada. A que importava era *o dado é de hoje?*

## As três regras

**1. O vigia mora fora do vigiado.** A checagem de que um pipeline entregou tem
que rodar num processo que sobrevive à morte dele. Aqui o `refresh.yml` — que
tem 7 slots × 2 fires e entregou até no dia em que o de mídia sumiu — virou o
vigia do de mídia.

**2. "Não quebrou" e "está fresco" são perguntas diferentes.** Todo dado com
carimbo de tempo precisa das duas réguas, e a segunda tem que ser apertada o
bastante para o uso: um refresh diário das 07h não pode ser auditado por uma
janela de 24h, porque a janela cobre o defeito inteiro.

**3. Número velho tem a mesma cara de número certo.** Um dado ausente grita; um
dado defasado é lido em voz normal e decidido em cima. A única defesa é **dizer
a idade em voz alta** — todo parecer agora carrega `dado de DD/MM HHhMM` no
cabeçalho, e marca o atraso quando não é do dia.

## O teste que pega isso antes

Ao ligar qualquer detector, pergunte:

1. Qual falha ele existe para pegar?
2. Se essa falha acontecer, **ele chega a rodar**?

Se a resposta da 2 depende da 1 não ter acontecido, o detector é decorativo.
