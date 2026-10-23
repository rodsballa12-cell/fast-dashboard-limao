---
titulo: Campo novo de configuração tem mais de um leitor
data: 2026-10-23
custo: 23 dias mostrando o Spa em 37% da meta quando estava em 46%
status: ativo
---

# Campo novo de configuração tem mais de um leitor

## O que aconteceu

Em 30/09/2026 nasceu `meta_mensal_por_mes[YYYY-MM]` no `config.json`, para que
cada mês tivesse sua própria meta em vez de um número fixo. O motivo era bom:
o Spa abriu em 24/09 e não fazia sentido cobrar mês cheio de uma loja de seis
dias.

O campo foi ensinado a **um** leitor — o DRE do Spa
(`build_spa_financeiro._meta_mensal`). O outro leitor, o painel de operação do
Spa (`build_spa_dashboard._meta_mensal_spa`), continuou lendo o campo antigo
`meta_mensal`, que valia a provisória de R$ 50.000.

De 30/09 a 23/10/2026, **o painel do Spa e o DRE do Spa mostraram metas
diferentes para o mesmo mês**: R$ 50.000 contra R$ 40.000. Vinte e três dias
dizendo que a loja estava em 37% da meta quando estava em 46%.

## O que custou

Mais do que a porcentagem errada. A decisão "religar a verba do Spa" foi à mesa
**quatro vezes** entre 01/10 e 17/10 sem sair do papel. Uma decisão fica mais
difícil de tomar quando ninguém consegue dizer de quanto é o buraco — e o buraco
tinha dois tamanhos, dependendo de qual tela você olhava.

E num Conselho de 23/10 eu mesmo apresentei isso como "o Spa tem três metas,
e por isso ninguém sabe se ele está bem". Estava errado no diagnóstico e certo
no sintoma: o `config.json` sempre teve **uma** meta certa para outubro. Era o
código que tinha dois leitores, e só um sabia ler.

## A parte que dói

O conserto de 14/09/2026 foi exatamente este erro, com outros números — a meta
do Spa estava fixa em dois scripts, os dois com R$ 60.000. O comentário que
ficou na função daquele dia diz, com todas as letras:

> *"Duas fontes da verdade divergem sempre — inclusive quando uma delas acabou
> de ser corrigida."*

A função com esse aviso escrito nela é a mesma que voltou a divergir dezesseis
dias depois. **Aviso em comentário não impede repetição.** O que impede é a
busca, e ela é de dez segundos.

## A regra

**Ao criar um campo de configuração que vence sobre outro, procure todos os
leitores do campo antigo antes de considerar o trabalho feito:**

```bash
grep -rn "meta_mensal" scripts/ index.html
```

Se o campo novo é um override (`_por_mes`, `_por_unidade`, `_override`), a
pergunta não é "quem eu preciso mudar?" — é **"quem lê o campo antigo?"**.
A lista do grep é a resposta, e ela é completa.

## Como a auditoria ajuda a partir de agora

`auditoria_coerencia.py` já confere se as unidades somam no consolidado. O que
ela não conferia era **se dois leitores do mesmo número concordam**. Vale
ensinar: para cada unidade, a meta que o painel mostra tem de ser igual à que o
DRE mostra. É uma linha de verificação e pega esta família inteira de erro.
