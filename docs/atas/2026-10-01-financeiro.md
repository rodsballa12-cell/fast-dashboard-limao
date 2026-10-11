---
agente: financeiro
data: 2026-10-01
hora: 08:30
gerado_por: tarefa agendada
---

# financeiro · 2026-10-01 às 08:30

↑ [[76_Briefings_Agentes/00-INDEX|Briefings dos Agentes]]

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
**PARECER · Financeiro · 30/09/2026 · dado de 18:13 (DRE) e 14:58 (Stone)**

**SITUAÇÃO** 🟡 atenção

**FATOS**
1. Escova fecha setembro com R$ 50.743,75 de receita contra R$ 28.793,87 de custo fixo (1,76×) e margem de contribuição de 50,9% — 1,9 ponto acima de agosto (49,0%). Mas o ganho não vem de comissão nem de imposto (ficaram parados em ~35% e 7%): vem só da linha de **produtos e insumos (CMV), que caiu de 1,8% da receita em agosto para 0,0% em setembro**.
2. Do R$ 29.864,33 que o painel soma como "risco não conciliado" na Stone, R$ 28.637,33 é recebível de cartão em D+30 — bate exatamente com o extrato, diferença zero, não é risco. O risco real é **R$ 1.227,00**: R$ 806,00 em 7 vendas do Trinks sem par na Stone (05/09 a 30/09) + R$ 421,00 em 3 cobranças da Stone sem venda no Trinks.
3. Spa fatura R$ 12.023,37 nos 5 dias desde a abertura (25/09) contra R$ 23.750,63 de custo fixo do mês — cobre 51%, esperado para um mês de abertura. Mas **ainda não tem Stone conectada** (`stone: null` no painel do Spa) — caixa e a receber aparecem zerados porque ainda não foram lidos, não porque estão vazios.

**RISCO** Se o CMV zerado de setembro for lançamento do Excel ainda não feito (e não custo real igual a zero), o resultado de R$ 586,76 deste mês está inflado — em agosto a mesma linha custou R$ 746,61, e se repetir o padrão o mês pode virar negativo de novo quando o Excel atualizar. Isso só aparece quando alguém comparar mês a mês; sozinho, o card não avisa.

**NÃO VEJO**
- Por que o CMV de setembro (Escova) foi a zero — se é lançamento pendente no Excel ou custo real. → Memória/Excel.
- Se os R$ 3.601,50 em 60 cancelamentos com valor (fora os R$ 646,00 dos 10 da inauguração) e os descontos fora da tabela (ex.: Fast Hidratação vendida 55,6% abaixo do preço de tabela) explicam parte da pressão sobre a margem — não leio o motivo do desconto nem do cancelamento. → Operação.
- Por que o Spa ainda não tem extrato Stone carregado — se é CSV pendente ou conta ainda não aberta no banco. → quem administra esse conector.

**DECISÃO** Nenhuma urgente hoje. Vale confirmar no Excel se o CMV de setembro da Escova já foi lançado antes de comemorar a melhora de margem, e cobrar o CSV da Stone do Spa antes do fechamento de setembro.
