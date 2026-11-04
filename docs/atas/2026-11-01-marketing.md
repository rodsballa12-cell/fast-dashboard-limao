---
agente: marketing
data: 2026-11-01
hora: 08:00
gerado_por: tarefa agendada
---

# marketing · 2026-11-01 às 08:00

↑ [[76_Briefings_Agentes/00-INDEX|Briefings dos Agentes]]

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
claude.exe : Permission allow rule (.claude\settings.json): Write(//c/Users/rods_/OneDrive/Franquia - FAST/Claude/**) 
is not matched by file permission checks — only Edit(path) rules are. Use Edit(//c/Users/rods_/OneDrive/Franquia - 
FAST/Claude/**) instead (Edit rules cover all file-editing tools).
No linha:5 caractere:5
+     & $cli -p "/$ag" 2>&1 | Out-String
+     ~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (Permission allo...editing tools).:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
Permission allow rule (.claude\settings.json): Write(//c/Users/rods_/dev/fast-dashboard-limao/scripts/marketing/**) is 
not matched by file permission checks — only Edit(path) rules are. Use 
Edit(//c/Users/rods_/dev/fast-dashboard-limao/scripts/marketing/**) instead (Edit rules cover all file-editing tools).
**Situação (Escova, `meta_ads`): entregando, mas o dado parou em 30/10.**

**Frescor**
- O pipeline direto da Meta rodou em 30/10 às 13:46. Hoje é 01/11, então faltam 31/10 e 01/11.
- A linha de 30/10 é parcial: R$ 24,40, 4 conversas. Não leia como queda.
- Não testei o Supermetrics. Ele só alimenta o Google Business, então não afeta esta leitura.

**Entrega (1 a 30/10)**
- Nenhum dia zerado, com gasto de R$ 58 a R$ 126 por dia. Passo 2 sem alerta.
- Melhores dias: 28 e 29/10, com 27 e 25 conversas a R$ 3,66 e R$ 3,87 cada.
- O pior dia foi 12/10, com 2 conversas a R$ 30,19.

**Contra a régua (`benchmarks`)**
- **CTR:** 1,2% contra meta de 1,5%, abaixo.
- **CPM:** R$ 11,44 contra R$ 12,00, dentro.
- **Frequência:** 2,79, em "atenção".
- **Custo por conversa:** o campo `cpa_msg_atual_30d` diz R$ 8,02, mas o texto curado dos direcionamentos diz R$ 9,70 (R$ 2.763,20 e 285 conversas). O campo repete o valor de `cpa_msg_mtd_setembro`, então parece velho. Eu usaria R$ 9,70, cerca de 21% acima da meta de R$ 8,00. Falta conferir se o campo está estagnado.

**Pauta registrada pelo humano (opinião curada, não medição)**
- ⛔ **COMBO SEMANAL:** sem gasto desde 08/10, com R$ 16/dia reservados e a campanha ativa. Aparece como P1 e precisa ser aberto no Gerenciador.
- Os COMBOS custam R$ 16,25 por conversa. O PLÁSTICA custa R$ 5,73.
- Facebook converte a R$ 6,43–7,15 e Instagram a R$ 12,85–15,29.
- Vagas: 90 conversas a R$ 4,75, mas ninguém mede quantas viram candidato.

**NÃO VEJO**
- Conversão real (de conversa para cliente atendida) e ROAS. A atribuição do funil é estimada e eu não li o `aviso_frescor`.
- O Spa (`meta_ads_spa`) não foi lido nesta passada.

Qual você quer: relatório da semana, calendário editorial (começo pelos ângulos da Angela), ou o Spa?

