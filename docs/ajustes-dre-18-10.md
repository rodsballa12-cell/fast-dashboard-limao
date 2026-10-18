# Ajustes na planilha · 18/10/2026 · para a sessão do PC

**Quem executa:** a sessão do Claude no PC (`C:\Users\rods_\dev\fast-dashboard-limao`).
**Por que não a nuvem:** a sessão da nuvem só alcança o repositório. O Excel
(`...\Franquia - FAST\Claude\Painel_Gestao_Financeira_SIIBELLO.xlsx`) e o vault
do Obsidian só existem no PC.

**Aprovado pelo Rodrigo em 18/10** ("efetue os ajustes"). Os números abaixo já
estão apurados e conferidos; não precisa recalcular nada.

---

## 1 · A comissão da Escova está provisionada abaixo do realizado

A planilha provisiona **35,10%**. O realizado, calculado serviço por serviço
com a taxa oficial de cada categoria (`data/comissoes.json`, export do Trinks
BackOffice):

| janela | base executada | comissão | taxa |
|---|---|---|---|
| outubro (01–17) | R$ 34.743,00 | R$ 13.502,10 | **38,86%** |
| ano (desde 23/07) | R$ 133.138,10 | R$ 49.830,83 | **37,43%** |

A causa é o **mix**, não um erro: UNHAS é 39,2% da base executada e paga **50%**
— a maior taxa da casa. Escova paga 30%, Retoque e Maquiagem 40%.

### O que muda conforme a provisão

Custo fixo R$ 32.228,67 · insumos 6% · Simples 7%.

| provisão | margem de contribuição | ponto de equilíbrio | EBITDA na meta de R$ 60 mil | folga contra a projeção de outubro (R$ 65.289,63) |
|---|---|---|---|---|
| **35,10%** (hoje) | 51,90% | R$ 62.097,63 | −R$ 1.088,67 | +R$ 3.192,00 |
| **37,43%** (ano) | 49,57% | R$ 65.016,48 | −R$ 2.486,67 | +R$ 273,15 |
| 38,50% (meio) | 48,50% | R$ 66.450,86 | −R$ 3.128,67 | −R$ 1.161,23 |
| 38,86% (outubro) | 48,14% | R$ 66.947,80 | −R$ 3.344,67 | −R$ 1.658,17 |

### Recomendação

**Provisionar 37,43%** — o realizado do ano, que é a base mais larga (81 dias
contra 17). Não 38,86%: um mês só, e o mix oscila com a proporção de unha.

Com 37,43% o equilíbrio vai para **R$ 65.016** e outubro passa por **R$ 273** —
no fio, mas no azul. É a leitura honesta.

**Revisar todo fechamento de mês**, porque o que move este número é a fatia de
unha. Se ela crescer, a taxa sobe sozinha.

**Não mexer na do Spa:** 25,00% provisionado, 25,00% realizado. Está exata.

---

## 2 · Caixa e a-receber do Spa continuam zerados no DRE

`data/spa/financeiro.json → kpis.caixa_conta = 0.0` e `a_receber_stone = 0.0`.

Isso não é conta vazia — é campo não preenchido. **Decidido em 09/10** (decisão
#3 daquele Conselho) e aberto desde então. Enquanto estiver assim, nenhuma
cadeira pode dizer se o caixa do Spa cobre o custo fixo dele (R$ 32.488,89/mês).

Preencher no mesmo lugar onde os da Escova entram (hoje R$ 1.436,61 em conta e
R$ 35.734,02 a receber).

---

## 3 · Depois de salvar a planilha

```
python scripts/gerar_financeiro.py
python scripts/auditoria_coerencia.py
python scripts/checa_nomes.py
git add data/ && git commit -m "dre: provisao de comissao da Escova a 37,43% + caixa do Spa" && git push
```

O painel do artefato é republicado pela nuvem (ou com a skill `/publicar`).

---

## O que NÃO é da planilha

Estes continuam com o Rodrigo e não entram aqui:

- **Extrato Stone do Spa** — parado em 30/09 17:58, 18 dias. É exportar e subir.
- **Verba de mídia do Spa** — R$ 17/dia desde 29/09. O Marketing só mexe com
  "aprovado + nome da campanha + valor por dia".
- **Cinco toques de preço no Trinks** — PÉS E MÃOS R$ 83 → 96 · FAST ESCOVA
  MODELADA R$ 99 → 109 · FAST HIDRATAÇÃO MASK R$ 39,50 → 89 · FAST MAKE CASUAL
  R$ 139 → 159 · e conferir LIBERAÇÃO MIOFASCIAL do Spa, que sai a R$ 89 com
  tabela de R$ 59.
