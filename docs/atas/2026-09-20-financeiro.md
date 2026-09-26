---
agente: financeiro
data: 2026-09-20
hora: 08:30
gerado_por: tarefa agendada
---

# financeiro · 2026-09-20 às 08:30

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
PARECER · Financeiro · 20/09/2026 (domingo) · dado de 18/09 às 13:47

**SITUAÇÃO** 🟡 atenção, igual a ontem

**Os dois relógios**
- **DRE:** o carimbo diz 18/09, 2 dias atrás. Esse carimbo é a data em que o script rodou, não a data até onde o Excel foi preenchido. Setembro está idêntico ao de ontem, ao centavo.
- **Extrato Stone:** cobre até 09/09, então a conciliação está cega há 11 dias.

**FATOS**
1. **Nenhum número se moveu desde ontem.** O caixa continua em R$ 1.171,37 e setembro continua em −R$ 6.882 sobre R$ 45.469 de receita. Essa receita é projeção do Excel: o ritmo do Trinks fecha o mês perto de R$ 42,9 mil, 71% da meta de R$ 60 mil.
2. **O ponto de equilíbrio do painel segue errado, e agora há segunda confirmação.**
   - A Memória refez a conta hoje (`2026-09-20-memoria.md`) e chegou ao mesmo número do meu parecer de ontem: **R$ 60.797**, contra os R$ 58.729 que o painel mostra.
   - Com a meta cheia de R$ 60 mil o resultado é **−R$ 358**, não +R$ 660. Ninguém corrigiu o painel, porque isso é mudança de dado e precisa do seu OK.
3. **Terça (22/09) é o dia apertado do caixa.**
   - A agenda da Stone não tem recebível nenhum para esse dia.
   - Os R$ 3.588 brutos de 19 a 21/09 cobrem os R$ 3.048 de custo fixo desses 3 dias, mas só no papel e sem folga.
   - O caixa de R$ 1.171 paga pouco mais de 1 dia (R$ 1.016/dia).

**RISCO** Se o dinheiro de 19 e 20/09 não tiver entrado, a terça começa sem cobertura. Antecipar os R$ 20.964 líquidos custa R$ 184,58 (0,87%), então é a saída barata para esse buraco. O alarme de R$ 21 mil de "risco" no card segue falso: R$ 21.148 são cartão em prazo normal. O órfão real continua sendo R$ 35, e os PIX depois de 09/09 são extrato faltando.

**NÃO VEJO**
- **O caixa real de hoje.** Não sei até que dia vai a conta XP, e o valor é o mesmo de 16/09. → Rodrigo.
- **O DRE do Spa** está zerado em todos os meses, e a loja inaugura em 25/09, daqui a 5 dias. O consolidado hoje é só a Escova. → Rodrigo, bloco Spa do Excel.
- **Desconto fora da tabela e cancelados com valor** (R$ 2.812,50, último número lido). Não recalculei porque o dado não mudou. → Operação.
- **Se há refresh mais novo no GitHub.** Esta sessão não conseguiu rodar `git fetch`, então o "nada mudou" vale para o que está nesta máquina.

**DECISÃO**
1. **Corrigir o equilíbrio no painel** (royalty como custo variável, R$ 58.729 → R$ 60.797). Preciso do seu OK, e a decisão pede registro em `docs/decisoes/` pela Memória.
2. **Antes de terça:** abrir o saldo da XP de hoje e subir o extrato Stone. Decida também se antecipa os recebíveis, opcional, a R$ 184,58.
3. **Preencher o DRE do Spa** antes do dia 25.

Não rodei a auditoria de coerência, porque não alterei nenhum dado.
