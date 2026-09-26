---
agente: financeiro
data: 2026-09-23
hora: 15:30
gerado_por: tarefa agendada
---

# financeiro · 2026-09-23 às 15:30

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
**PARECER · Financeiro · 23/09/2026 (quarta) · dado de 18/09 às 13:47 (sexta)**

**SITUAÇÃO** 🔴 ação hoje

**Os dois relógios**
- **DRE:** carimbo de 18/09 — **5 dias** atrás. Ninguém tocou o Excel (ou pelo menos não regerou o `financeiro.json`) desde então.
- **Extrato Stone:** cobre até 09/09 — **14 dias** atrás, quase o dobro do que estava há dois dias no último parecer (12 dias em 21/09). A conciliação está cega há duas semanas.

**FATOS**
1. **Nada mudou desde 18/09:** caixa em R$ 1.171,37; setembro em −R$ 6.882 sobre R$ 45.469 de receita, contra meta de R$ 60.000. Mesmos números do parecer de 21/09 — a defasagem só cresceu.
2. **O "R$ 21.183 em risco" continua inflado:** R$ 21.148,14 é cartão em prazo normal (D+30, cronograma de liberação existe); o órfão de verdade é R$ 35,00 (1 venda). Não é alarme, é extrato atrasado.
3. **Correção do ponto de equilíbrio ainda parada:** o painel mostra R$ 58.729 (margem de 51,9%); a conta revisada com o royalty como custo variável dá R$ 60.797. Pendente do seu OK desde antes de 21/09 — já mais de uma semana sem decisão.

**RISCO**
- Caixa de R$ 1.171 cobre pouco mais de **1 dia** do custo fixo (~R$ 1.016/dia). Sem saber se a reserva da XP ainda está de pé, não dá pra dizer se amanhã está coberto.
- **Spa abre em 2 dias (25/09)** e o DRE do Spa continua zerado em tudo — custo fixo, caixa, receita. Ele vai começar a operar sem nenhuma referência para comparar o primeiro dia de caixa.
- Duas semanas de extrato Stone parado: se algo realmente sumir nesse intervalo, só vai aparecer quando alguém carregar um CSV novo — hoje ninguém saberia dizer.

**NÃO VEJO**
- **Saldo real na conta (XP), reserva incluída, hoje.** É o que decide se amanhã está coberto. Tentei checar se o Excel foi mexido depois de 18/09 e se há commit mais novo no GitHub (`git fetch`) — as duas checagens pediram aprovação e não rodaram nesta sessão. → Rodrigo, autorizar ou confirmar direto.
- **Desconto fora da tabela e comissão real do mês** — não recalculei, dado igual ao de 21/09. → Operação e Pessoas.

**DECISÃO**
1. Aprovar ou recusar a correção do equilíbrio (R$ 58.729 → R$ 60.797) — parada há mais de uma semana.
2. Confirmar se a reserva da XP ainda cobre o custo fixo até o próximo recebível entrar; se foi consumida, reabrir a discussão de antecipar (recusada em 14/09).
3. Preencher o bloco Spa no Excel antes de 25/09 — faltam 2 dias.
4. Se quiser, autorizo checar agora se há dado mais novo no Excel/GitHub do que 18/09 (`git fetch` + ler data de modificação do arquivo) — só peço o sinal verde.
