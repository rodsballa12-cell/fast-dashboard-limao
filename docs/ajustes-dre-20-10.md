# Ajustes na planilha · 20/10/2026 · para a sessão do PC

**Quem executa:** a sessão do Claude no PC (`C:\Users\rods_\dev\fast-dashboard-limao`).
**Por que não a nuvem:** a sessão da nuvem só alcança o repositório. O Excel
(`...\Franquia - FAST\Claude\Painel_Gestao_Financeira_SIIBELLO.xlsx`) e o vault
do Obsidian só existem no PC.

**Aprovado pelo Rodrigo em 20/10** ("Aprovo as 3"), depois da auditoria completa
da DRE. **Sobrou um único item para a planilha.** As outras duas decisões não
eram da planilha — estão explicadas no fim deste arquivo e já foram executadas
na nuvem.

---

## 1 · A provisão de comissão da Escova andou de novo

Em 18/10 a planilha passou de 35,10% para **37,43%**, que era a taxa executada
**do ano** — base mais larga (81 dias contra 17). A recomendação daquele dia foi
explícita: usar a do ano, não a do mês, e **revisar todo fechamento**, porque o
que move este número é a fatia de unha no mix.

Dois dias depois, as duas andaram:

| janela | base executada | comissão | taxa | era em 18/10 |
|---|---|---|---|---|
| outubro (01–20) | R$ 36.999,00 | R$ 14.427,00 | **38,99%** | 38,86% |
| ano (desde 23/07) | R$ 135.394,10 | R$ 51.872,03 | **38,31%** | 37,43% |

A taxa do **ano** subiu 0,88 ponto em dois dias. Não é ruído de um mês: é o mix
de outubro, que paga mais comissão, ganhando peso na média do ano inteiro.

### O que muda conforme a provisão

Custo fixo R$ 32.228,67 · insumos 6% · Simples 7% · projeção de outubro R$ 65.860,65.

| provisão | margem | ponto de equilíbrio | EBITDA na meta de R$ 60 mil | outubro na projeção |
|---|---|---|---|---|
| **37,43%** (hoje na planilha) | 49,57% | R$ 65.016,48 | −R$ 2.486,67 | **+R$ 418,46** |
| **38,31%** (ano, hoje) | 48,69% | R$ 66.171,43 | −R$ 3.014,67 | **−R$ 161,12** |
| 38,99% (outubro) | 48,01% | R$ 67.129,07 | −R$ 3.422,67 | −R$ 608,97 |

### APROVADO pelo Rodrigo em 20/10 às 11:52: **38,31%**

Mesma regra de 18/10 — a taxa do ano, base mais larga —, só com o número de
hoje. Custa **R$ 528/mês** na meta de R$ 60 mil contra os 37,43% atuais.

**Este é o único item deste arquivo que ainda precisa ser executado.** Os outros
dois estão aqui só como registro do que já foi feito na nuvem.

E muda a leitura do mês: com 37,43% a Escova atravessa o equilíbrio em outubro
por R$ 418; com 38,31% ela fica **R$ 161 abaixo**. É o fio da navalha dos dois
lados, mas a versão honesta é a segunda — e é a diferença entre dizer "a loja
virou" e "a loja chegou na porta".

Isto é **provisão de custo**, não cálculo de pagamento: não há regra de comissão
cadastrada no Trinks (`comissoes.habilitado` é `false`), e nenhum valor daqui
serve para pagar ninguém.

**Não mexer na do Spa:** 25,00% provisionado, 25,00% executado. Exata.

---

## 2 · Depois de salvar a planilha

```
python scripts/gerar_financeiro.py
python scripts/auditoria_dre.py
python scripts/auditoria_coerencia.py
python scripts/checa_nomes.py
git add data/ && git commit -m "dre: provisao de comissao da Escova a 38,31%" && git push
```

O `gerar_financeiro.py` mudou hoje: agora lê o a-receber do extrato **de cada
loja** e marca o caixa do Spa como não separável. Rodar ele vai reproduzir o que
a nuvem já gravou à mão — se o `auditoria_coerencia.py` acusar diferença depois,
é bug, não é ajuste pendente.

---

## As outras duas decisões não eram da planilha

**Caixa e a-receber do Spa (decisão aberta desde 09/10).** Não era célula vazia:
era número que ninguém ia buscar. O `gerar_financeiro.py` lia o a-receber só do
extrato da Escova, e o Spa saía com R$ 0,00 — enquanto o card da mesma tela
mostrava R$ 8.435,50, porque o card lê o extrato direto. O consolidado reportava
R$ 8.435,50 a menos que a soma das duas lojas. Corrigido no script, aplicado nos
três `financeiro.json`, e com conferência nova na `auditoria_coerencia.py` para
não voltar calado.

O **caixa** do Spa virou nulo, não zero: existe **uma** conta corrente da
holding, e o saldo aparece inteiro na Escova. Separar por loja não é possível com
uma conta só, e "R$ 0,00" fazia o card afirmar que o Spa está sem dinheiro.

**A coluna de outubro do Spa na meta.** Também não era da planilha — e não era
erro. A coluna do mês corrente ser a meta é coluna de **alvo**, e o painel não a
copia: desde 07/10 o card RESULTADO PROJETADO reconstrói o resultado sobre a
projeção do painel. O Spa já aparece com **−R$ 17.213,88**, não com os
−R$ 8.488,89 da planilha. Quem estava errado era o meu auditor, que lia a célula
e falava como se fosse o painel. Corrigido: agora ele mostra os dois números
lado a lado e chama a diferença pelo nome — R$ 8.724,99 de margem que o alvo
conta e o ritmo não traz.

---

## O que continua com o Rodrigo, fora da planilha

- **Quatro preços no Trinks.** Releitura forçada do catálogo às 11:04 de 20/10
  (apaguei o cache de 24h) confirma que continuam os antigos: PÉS E MÃOS R$ 83
  → 96 · FAST ESCOVA MODELADA R$ 99 → 109 · FAST HIDRATAÇÃO MASK R$ 39,50 → 89 ·
  FAST MAKE VIP R$ 149,50 → 189.
- **DESIGN SOBRANCELHAS** — cadastro R$ 60, cobrança R$ 57,29. R$ 65/mês. É o
  único desvio real que sobrou dos "R$ 3.180" de 18/09.
- **LIBERAÇÃO MIOFASCIAL (Spa)** — sai a R$ 89 com tabela de R$ 59. Qual vale?
- **Extrato Stone do Spa** — parado em 30/09 17:58, **20 dias**. É o que torna o
  R$ 8.435,50 de a-receber do Spa um número de três semanas atrás.
- **Verba de mídia do Spa** — o Marketing só mexe com "aprovado + nome da
  campanha + valor por dia" na mesma mensagem.
- **Conselhos de 18 e 19/10 não rodaram** e **12 atas nunca entraram no painel**
  (05 a 08/10 e outras) — `/sincronizar` resolve as atas.
- **Ficha de origem do Spa em 58,3%** — abaixo de 60% o ROAS do Spa é faixa.
