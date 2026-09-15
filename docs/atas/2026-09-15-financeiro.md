---
agente: financeiro
data: 2026-09-15
hora: 10:20
gerado_por: sessão de análise
dado_de: 2026-09-15T03:05 BRT
---

# financeiro · 2026-09-15 às 10:20

```
PARECER · Financeiro · 15/09/2026 · dado de 03h05

SITUAÇÃO   🟡 atenção
```

## FATOS

**1. O "risco não conciliado" de R$ 22.747 era R$ 35.**

O card somava três coisas diferentes na mesma linha. Separadas:

| | valor | o que é |
|---|---|---|
| A receber em cartão (D+30) | R$ 21.148 | dinheiro vendido, prazo normal da Stone — **não é risco** |
| PIX posteriores ao extrato | R$ 1.564 | o extrato para em 09/09; não dá pra conferir o que veio depois |
| **Órfão real** | **R$ 35** | um PIX de 05/09, Lucas de Pinho Garcia, dentro do período e sem contrapartida |

O briefing das 09h de hoje abriu com 🔴 *"15 PIX sem confirmação, R$ 1.599, conferir
comprovante com cada cliente hoje"*. Catorze desses quinze eram de 12, 13 e 14/09 —
**depois do último dia que o extrato cobre.** Não é dinheiro que não caiu: é dinheiro
que ninguém ainda olhou. A ação certa custa dois minutos (exportar o extrato), não
quinze ligações constrangedoras.

Corrigido hoje em `scripts/stone_processor.py`: o que está fora da cobertura do
extrato passa a ser contado à parte, e vira um pedido de exportação, não um alarme.

**2. O mês projeta R$ 46.079 de R$ 60.000 — e o buraco inteiro está em três
categorias, nenhuma delas serviço de cadeira.**

| categoria | meta/mês | ritmo atual | % | gap |
|---|---:|---:|---:|---:|
| Serviços gerais | 33.600 | 36.418 | **108%** | +2.818 |
| Pacotes | 14.400 | 5.432 | 38% | −8.968 |
| Fast Retoque | 8.400 | 3.397 | 40% | −5.003 |
| Produtos | 3.600 | 954 | 27% | −2.646 |
| **Total** | **60.000** | **46.079** | **77%** | **−13.799** |

A cadeira está entregando **acima** do que a franqueadora pediu. O que não está
acontecendo é a venda de balcão — e as três categorias somam R$ 16.617 de gap, mais
do que o gap do mês inteiro.

**3. Setembro vai fechar ~19% acima de agosto e ainda assim "abaixo da meta".**

Agosto fechou R$ 38.641. Setembro projeta R$ 46.079. A meta de R$ 60.000 é **55% acima
do melhor mês que o salão já teve**, num negócio com 54 dias de operação. O alerta
🔴 "abaixo de 80% da meta" está vermelho todo dia desde que existe, e alarme que
nunca apaga deixa de ser lido.

## RISCO

O extrato Stone está parado em 09/09 há 6 dias. Enquanto estiver, **toda conciliação
de PIX dos últimos dias vira alarme falso** — e o próximo pode ser um órfão de
verdade que ninguém vai distinguir dos catorze que não eram.

Não há DRE desde 05/09. Sem ela, "margem" é palpite: sei o que entrou, não sei o que
saiu.

## NÃO VEJO

- **Quantas recepcionistas estão no salão hoje.** A meta de R$ 60.000 é construída
  sobre **duas**, cada uma com R$ 13.200/mês em pacote + retoque + produto. Se há
  uma, a meta está errada por R$ 13.200. → **Pessoas**
- **R$ 855 no ranking de setembro atribuídos a "Prof desligado #735928"**, com zero
  atendimentos e zero horas. 4,3% do caixa do mês sem serviço associado. → **Pessoas**
- Custo fixo mensal. Sem ele não consigo dizer se segunda-feira (R$ 45,75/hora contra
  média de R$ 133,12) paga o próprio dia. → **Rodrigo**

## DECISÃO

1. **Exportar o extrato Stone hoje** para `data/stone_extrato.csv`. É o que destrava
   a conciliação e apaga o alarme falso na origem.
2. **A meta de R$ 60.000 é plano ou é esticada?** Se for plano, existe um buraco
   estrutural de R$ 14.000/mês que campanha de WhatsApp não fecha — e a conversa é
   com a franqueadora. Se for esticada, 77% com o negócio crescendo 19% ao mês é
   resultado bom, e o painel precisa parar de pintar isso de vermelho.
