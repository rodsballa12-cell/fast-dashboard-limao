---
agente: financeiro
data: 2026-10-02
hora: 08:30
gerado_por: tarefa agendada
---

# financeiro · 2026-10-02 às 08:30

↑ [[76_Briefings_Agentes/00-INDEX|Briefings dos Agentes]]

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
**PARECER · Financeiro · 02/10/2026 · dado de 30/09 (DRE às 18h13, dashboard às 22h, extrato Stone até 14h58)**

**SITUAÇÃO** 🟡 atenção

**FATOS**
1. Caixa da Escova é R$ 10.710 e o custo fixo do mês é R$ 28.794 — mesmo com o mês fechando no azul (R$ 587 de lucro em setembro), esse resultado só vira dinheiro se os R$ 28.185 a receber da Stone entrarem antes do próximo vencimento.
2. Da conciliação Stone×Trinks da Escova, o risco real aberto é R$ 1.227 (R$ 806 vendidos no Trinks sem par na Stone + R$ 421 cobrados pela Stone sem venda no Trinks) — bem menor que os R$ 28.637 "a receber", que são prazo normal de cartão em D+30, não risco.
3. O Spa fechou setembro com resultado de −R$ 12.620, mas operou só 6 dos 30 dias do mês (abriu em 25/09) contra um custo fixo de mês cheio (R$ 23.751). No ritmo desses 6 dias (~R$ 2.004/dia), um mês inteiro bateria ~R$ 60 mil — folgado sobre o fixo. Não é alarme ainda, é o primeiro mês e precisa se confirmar em outubro.

**RISCO:** os dois relógios do Financeiro estão parados no mesmo lugar — DRE e dashboard não se movem desde a noite de 30/09, e o extrato Stone também cobre só até às 14h58 daquele dia. Isso são quase 2 dias (hoje é 02/10) sem nenhum movimento — venda, PIX, conciliação — entrando em qualquer número deste parecer.

**NÃO VEJO**
- Caixa e a receber do Spa aparecem como R$ 0 no financeiro porque o Spa não tem conciliação Stone (`stone: null`) — não significa que não tem dinheiro, significa que esse número não é lido por aqui. → Operação, para dizer onde esse caixa está sendo controlado hoje.
- 34 dos 59 serviços da Escova têm preço médio praticado abaixo da tabela (de −6% a −56%, ex. Fast Hidratação Fast Mask a R$ 39,50 contra R$ 89 de tabela), mas não tenho o volume vendido de cada um para converter isso em reais de margem perdida. → Operação.
- R$ 3.602 em cancelamentos com valor na Escova desde a inauguração (fora os R$ 646 da semana de abertura) — não sei quanto foi reagendado e virou venda depois vs. perdido de fato.

**DECISÃO:** nenhuma acima da minha alçada hoje. A única pergunta para o Rodrigo: ele quer que eu trate a cegueira de caixa do Spa como prioridade antes do próximo parecer, já que é a loja mais nova e a que menos aparece no dado?
