---
agente: financeiro
data: 2026-09-19
hora: 08:30
gerado_por: tarefa agendada
---

# financeiro · 2026-09-19 às 08:30

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
PARECER · Financeiro · 19/09/2026 (sábado) · dado de 18/09 às 13:47

**SITUAÇÃO** 🟡 atenção

**Dois relógios:**
- **DRE:** gerado ontem, 1 dia de atraso. O campo de data do DRE é carimbado com o dia em que o script roda, então ele não prova até quando o Excel foi preenchido. Setembro está idêntico ao de 16/09, ao centavo.
- **Extrato Stone:** cobre até 09/09, ou seja, 10 dias sem conciliação. O painel mostrava 209 h de atraso ontem.

**FATOS**

1. **O ponto de equilíbrio real é ~R$ 60,8 mil por mês, não R$ 58,7 mil.**
   - O painel trata o royalty (7% da receita) como custo fixo, mas ele cresce com a venda. Cada R$ 1.000 a mais rende R$ 449 de resultado, não R$ 519.
   - Com a meta cheia de R$ 60 mil o resultado seria **−R$ 360**, não os **+R$ 660** do meu parecer de 16/09. Esse número estava errado.
   - O próprio Excel confirma: janeiro/27 (R$ 60,7 mil) dá −R$ 33 e fevereiro/27 (R$ 65,3 mil) dá +R$ 2.011.

2. **O DRE de setembro usa R$ 45.469 de receita, que é projeção do Excel.**
   - O Trinks fechou R$ 24.292 em 17 dos 30 dias, com ritmo de R$ 1.429/dia. Isso projeta R$ 42.868, ou 71% da meta.
   - Contra o Trinks, setembro fica em cerca de **−R$ 8 mil**, não −R$ 6,9 mil (R$ 2,6 mil a menos de receita são R$ 1,2 mil a menos de resultado).
   - Para chegar aos R$ 45,5 mil do Excel faltam R$ 21,2 mil em 13 dias: **R$ 1.629/dia, 14% acima do ritmo atual**. Para zerar o mês seriam R$ 2.808/dia.

3. **Caixa de R$ 1.171 e a Stone sem extrato.**
   - O painel usa R$ 1.016/dia de custo fixo, então o caixa cobre pouco mais de 1 dia.
   - A agenda da Stone traz R$ 3.588 brutos em 19, 20 e 21/09, contra R$ 3.048 de custo fixo de 3 dias. Cobre no papel, sem folga, e **22/09 não tem recebível nenhum**.
   - Conciliação: o órfão real é R$ 35 (Lucas, 05/09), e o meu parecer de 16/09 já o achou no extrato da XP.
   - Os R$ 2.274 em 21 PIX depois de 09/09 são extrato faltando, não dinheiro sumido.
   - O card ainda soma R$ 21.183 de "risco", mas R$ 21.148 são cartão a receber em prazo normal. É o mesmo alarme falso de 15/09.

**RISCO** Se o caixa de R$ 1.171 estiver parado desde 16/09, o real pode ser pior e eu não sei. Antecipar os R$ 20.964 líquidos custa R$ 184,58 (0,87%), então é barato como reserva.

**NÃO VEJO**
- **Até que dia vai a conta XP.** O caixa está igual ao de 16/09 ao centavo. → Rodrigo. Só esta máquina alcança o Excel, e daqui não consegui abri-lo.
- **DRE do Spa zerado em todos os meses**, sem receita nem custo, a 6 dias da abertura. O consolidado hoje é só a Escova. → Rodrigo, bloco Spa do Excel.
- **Desconto fora da tabela em reais no mês.** Não recalculei. Em 16/09 eram R$ 1.101,50. → Operação.
- **Cancelados com valor:** R$ 2.812,50, contra R$ 2.663,50 em 16/09. → Conselho/Operação.

**DECISÃO**
1. Corrigir o cálculo do equilíbrio no painel, com o royalty como custo variável. Também é preciso registrar a correção do meu parecer de 16/09 em `docs/decisoes/` (só o cargo Memória escreve lá). Não mexi em nada.
2. Subir o extrato Stone (10º dia) e conferir a data da conta XP no Excel.
3. Antecipar recebível é opcional, a R$ 184,58.

Não rodei a auditoria de coerência, porque não alterei dado. Também não conferi se há refresh mais novo no GitHub: o acesso a comandos ficou restrito ao repositório.
