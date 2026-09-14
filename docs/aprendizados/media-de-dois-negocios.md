# A média de dois negócios não descreve nenhum dos dois

**Descoberto em:** 14/09/2026 · **Quase custou:** uma recomendação de escala
que mataria a melhor manhã da semana.

## O que aconteceu

O painel traz `densidade_hora`: atendimentos simultâneos por hora, agregando
todos os dias. Ela dizia que o pico do salão era **1,67 simultâneos às 16h** —
número baixíssimo para 16 cadeiras instaladas.

Em cima disso eu recomendei abrir às 10h em vez de 9h: "as duas primeiras
horas somam menos que uma hora do pico".

Rodrigo pediu para separar por dia da semana antes de mexer. Separando:

| | 9h | 11h | 17h |
|---|---|---|---|
| Sábado | **1,98** | **2,76** | **3,90** |
| Terça | 0,08 | 0,33 | 1,01 |

**Sábado às 11h é mais cheio que o pico de segunda, terça ou quarta.** A média
de 1,67 não existia em nenhum dia real: era o encontro de um sábado lotado com
quatro dias vazios.

E a recomendação estava errada no pior lugar possível — **cortar as 9h teria
atingido exatamente a manhã que funciona.**

## A regra

**Antes de agir sobre uma média, pergunte do que ela é média.** Se a variável
que gera o número tem regimes diferentes — dia da semana, unidade, turno,
canal — a média é um artefato estatístico, não uma descrição da realidade.

Sintoma de alerta: **a média não se parece com nenhum caso concreto.** 1,67
simultâneos não era o retrato de sábado (3,90) nem de terça (1,01). Quando
isso acontece, desagregue antes de decidir.

## A ferramenta

`scripts/densidade_dow.py` calcula a densidade real por dia da semana × hora,
a partir dos agendamentos com hora de início e duração. O Conselho usa nas
janelas semana e mês; o cargo de Pessoas usa para falar de escala.

`abas.*.densidade_hora` continua servindo para ritmo intradiário do dia
corrente — mas **não serve para escala**, e a ficha de Pessoas diz isso.

## O crédito

A desagregação foi pedida pelo Rodrigo, não proposta por mim. Eu tinha os dois
números — a curva agregada e os 1.022 agendamentos brutos — e usei o mais fácil.

**Quando existe dado bruto disponível, a agregação pronta é conveniência, não
fonte.** Vale checar contra o bruto antes de recomendar algo irreversível.
