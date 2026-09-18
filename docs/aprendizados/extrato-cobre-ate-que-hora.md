---
titulo: "Cobertura de extrato se mede em hora, não em dia"
data: 2026-09-18
cargo: Memória
status: vigente
custo: "3 PIX da tarde (R$ 261) apontados como pagamento sumido"
---

## O que aconteceu

Em 15/09 o painel abriu com *"15 PIX sem confirmação, R$ 1.599, ligue para cada
cliente hoje"*. Catorze eram posteriores ao último dia do extrato — extrato
atrasado, não dinheiro sumido. A correção da época separou os dois grupos
comparando **datas**: PIX com data maior que o último dia do extrato ia para
"fora da cobertura".

Em 18/09 o Rodrigo exportou o extrato do próprio dia. O último lançamento dele
era das **08h20** — a varredura da manhã. Todo PIX da tarde tinha data 18/09,
igual à data de cobertura do extrato, então passou no teste de data e voltou a
ser classificado como "pagamento que não caiu": Camila R$ 53 às 17h05, Caroline
R$ 119 às 16h52, mais um de R$ 89.

O mesmo erro de 15/09, três dias depois, com granularidade menor.

## Por que era quase invisível

Extrato exportado de manhã **nunca** contém o movimento da tarde. Isso não é
atraso, é o funcionamento normal. Mas "o extrato cobre até 18/09" lido como "o
extrato cobre o dia 18 inteiro" é uma leitura que parece óbvia e está errada
em todo export feito antes do fim do expediente — ou seja, quase todos.

## O que mudou

`stone_processor.py` passa a guardar a **hora** do último lançamento
(`extrato_cobre_ate_hora`) e a hora de cada PIX do Trinks, e compara hora com
hora. Venda sem hora informada assume fim do dia — só conta como coberta se o
extrato passou da meia-noite seguinte.

`insights.py` deixou de tratar como alerta o que é comportamento normal:
extrato do próprio dia vira `info` ("são movimentos que o extrato ainda não
alcança, nada a fazer"). Alerta só quando o extrato ficou para trás de um dia
para o outro.

## A regra

**Toda janela de cobertura tem duas pontas e as duas têm hora.** Comparar uma
fonte ao vivo (Trinks) com um snapshot manual (CSV Stone) em granularidade de
dia produz falso positivo sempre que o snapshot foi tirado no meio do dia.

E a regra maior, que este é o quinto caso: **o sistema não ter visto não é a
mesma coisa que não ter acontecido.** Antes de repetir um alarme, confira até
quando — dia *e* hora — vai a fonte que o gerou.
