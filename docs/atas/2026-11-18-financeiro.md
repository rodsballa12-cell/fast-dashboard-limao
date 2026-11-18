---
agente: financeiro
data: 2026-11-18
hora: 08:30
gerado_por: tarefa agendada
---

# financeiro · 2026-11-18 às 08:30

↑ [[76_Briefings_Agentes/00-INDEX|Briefings dos Agentes]]

PARECER · financeiro · qua 18/11/2026 · dado de 08h30 (custos) / 00h43 (vendas do Trinks até 17/11)

**Frescor:** o DRE de custos é de hoje (18/11), mas a **receita de novembro que está nele não é a venda real: são R$ 60.000 na Escova e R$ 50.000 no Spa, números redondos de projeção**. O extrato da Stone termina em 12/11 às 11h45 e está **133 h (5,5 dias) atrasado**. Por isso a conciliação está cega de 12/11 em diante.

SITUAÇÃO   🔴 ação hoje

FATOS
1. **Spa: o DRE conta com R$ 50.000 de receita em novembro, e o Trinks projeta R$ 25.603.** O realizado é R$ 11.820 em 16 dias, ou R$ 739 por dia, contra R$ 2.727 por dia necessários. Para empatar o mês o Spa precisa vender R$ 56.065. Faltam R$ 30,5 mil para esse ponto. O "−R$ 3.639 no mês" do painel subestima o buraco porque parte de uma receita que não vai existir.
2. **Escova: o Trinks projeta R$ 64.006 contra R$ 66.192 de equilíbrio, ou seja, faltam R$ 2,2 mil de venda.** O realizado é R$ 32.487 em 16 dias, 46% da meta de R$ 70.000. A margem que sobra das vendas caiu de 47,7% em outubro para 41,7% em novembro, e o motivo é de conta, não de operação: a partir de novembro entraram 6% de produtos (R$ 3.600), que eram zero em setembro e outubro. Preço e comissão (38,3%) não mudaram. Os R$ 20.267 comprados em estoque desde outubro continuam fora do resultado.
3. **Caixa:** a conta da Escova tem R$ 8.730 e a do Spa R$ 232 (mais R$ 12.231 na Reserva Stone, à parte). O custo fixo das duas lojas soma R$ 65,9 mil por mês. Há R$ 48.153 de cartão a receber (R$ 33.285 da Escova + R$ 14.867 do Spa), que chegam em média em 17 dias. Antecipar tudo da Escova custaria R$ 315. **O caixa livre hoje (R$ 8,9 mil) cobre só cerca de 14% do custo fixo do mês.** Ainda não é falta de dinheiro, mas o mês depende do recebível chegar no prazo.

RISCO
- O furo do Spa, que vai além de R$ 20 mil no resultado do mês, só aparece no painel quando o Excel trocar os R$ 50 mil pela venda real. Até lá, todo card de resultado do Spa está otimista.
- Conciliação da Escova: o painel acusa 16 vendas sem par na Stone (R$ 1.881). **Treze delas (R$ 1.698) são de depois de 12/11 às 11h45: é extrato atrasado, não dinheiro sumido.** O que é real são três lançamentos de R$ 53 no dia 06/11, no mesmo minuto (R$ 159), com cara de lançamento duplicado no Trinks. Há também 8 cobranças da Stone sem venda no Trinks (R$ 873). O total de "R$ 36.039 em risco" mistura esses casos com cartão a receber dentro do prazo normal e **não é risco**.
- Pontos cegos: cancelados com valor somam R$ 8.196 no painel da Escova. Desconto fora da tabela eu não avaliei hoje.

NÃO VEJO
- As datas de vencimento do aluguel, da folha e do royalty em novembro e dezembro, sem as quais não dá para dizer se o caixa aguenta até o cartão cair → Rodrigo/Excel.
- A data do saldo de R$ 8.730 da Escova (o campo não diz) → Excel.
- Por que o Spa está vendendo R$ 739 por dia → Operação.
- Se os 3 × R$ 53 de 06/11 são lançamento duplicado ou três clientes diferentes → Operação/recepção.
- Diferença de R$ 24 entre a lista de órfãos (R$ 1.857) e o total do card (R$ 1.881) → tarefa de código.
- Encargos da equipe CLT: só outubro está fechado (1,13, contra 1,75 em uso). Um mês só não basta para propor fator novo.

DECISÃO
1. **Trocar no Excel a receita de novembro do Spa (R$ 50.000) pela projeção real do Trinks**, ou aceitar que o resultado do Spa no painel fica irreal até o fechamento.
2. **Exportar hoje o extrato da Stone das duas lojas** (de 12/11 até agora) para fechar 5,5 dias de conciliação cega.
3. Definir a regra para lançar como custo os R$ 20.267 de estoque da Escova. Enquanto ela não existir, a margem de novembro aparece melhor do que é.

