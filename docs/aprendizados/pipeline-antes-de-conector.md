# Um agente que não sabe por onde o dado chega reporta quebra onde não há

**Destilado em:** 2026-09-14
**Origem:** revisão do cargo /marketing após o conselho de 14/09

## Regra

Antes de declarar qualquer fonte de dados como quebrada ou indisponível,
o agente deve identificar **qual caminho específico falhou** e verificar se
existe um caminho alternativo que ainda entrega o dado.

## Por que isso aconteceu

O cargo /marketing descrevia Supermetrics como a fonte de dados ao vivo de
Meta Ads e Instagram. Na prática, esses dados chegam via Meta Graph API direta
(`scripts/refresh_midias.py`). O Supermetrics existe no projeto, mas cobre
apenas o bloco Google Business (`scripts/refresh_google.py`).

Como o cargo não conhecia a arquitetura real, interpretou uma falha isolada
no Supermetrics como "dados de Meta indisponíveis" — alarme falso. O IG do
Spa (202 seguidores) estava no painel sem o Supermetrics estar conectado,
porque nunca dependeu dele.

## Como aplicar

1. Antes de declarar 🔴 num conector, leia o JSON que o painel usa e veja
   se ele está fresco. Se sim, o pipeline está funcionando independente do
   que acontece com outros conectores.

2. Quando aprender que um dado vem de um caminho específico, registre isso
   nas chaves do cargo — não assuma que "Supermetrics" ou "API X" é a única
   fonte de tudo.

3. A pergunta certa não é "o conector Y está funcionando?" — é "o dado que
   preciso está presente e fresco onde vou lê-lo?"

## Padrão que se repete

Este erro aparece sempre que um agente é documentado com base em como
*deveria* funcionar (intenção original) em vez de como *realmente* funciona
(arquitetura atual). A documentação envelhece; o código muda. Toda vez que
um cargo for atualizado, conferir se os caminhos descritos batem com os
scripts reais.
