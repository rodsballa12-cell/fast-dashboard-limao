---
agente: relacionamento
data: 2026-09-16
hora: 09:00
gerado_por: tarefa agendada
---

# relacionamento · 2026-09-16 às 09:00

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
**PARECER · Relacionamento · 16/09/2026 · dado de hoje (base) / 15/09 (fila WhatsApp)**

**SITUAÇÃO** 🟡 atenção

**FATOS**
1. 59 clientes em alerta de churn, R$ 13.758,10 de LTV em risco — mesma faixa dos 58 citados na decisão de 14/09 sobre o WhatsApp Cloud; a base não piorou, mas também não foi trabalhada.
2. 3 aniversariantes hoje — Marcia Roseli, Ludmila Peleias, Caroline Solto Lima — e a fila de aniversário (`aniversarios_fila.json`) não é regenerada desde 09/09, 7 dias atrás.
3. Brenda Vontes, uma das cinco maiores LTV da base (R$ 1.190, 12 visitas), está há 19 dias sem vir — exatamente o perfil que a régua de reativação (3+ visitas, 14 a 120 dias sem vir) foi feita pra pegar.

**RISCO** Sem disparo automático (kill switch geral desligado em `config.json`, WhatsApp Cloud descontinuado em 14/09 por falta de acesso admin Meta), o único canal que sobrou é o botão 📱 manual do painel — que depende de alguém clicar, um por um, nos 59 alertas e nos 3 aniversariantes de hoje. Não tenho como confirmar se isso está acontecendo. Cada dia sem contato empurra parte desses 59 para fora da janela de reativação (120 dias é o corte da régua) — a partir daí, R$ 13.758 de LTV deixa de ser "recuperável" e passa a ser "perdido".

**NÃO VEJO**
- Se a recepção está de fato usando o botão 📱 para os aniversariantes e para os alertas de churn — é ação manual fora do sistema. → Operação/recepção.
- Por que a fila de aniversário parou de ser gerada há 7 dias (09/09) enquanto a de reativação continua rodando diariamente (última em 15/09, vazia por kill switch) — pode ser cron parado. → time técnico.

**DECISÃO** Nenhuma pendente hoje acima do que já foi decidido em 14/09 (não reconfigurar WhatsApp Cloud, sem prazo). Se quiser, posso listar a ordem de prioridade de contato manual de hoje (Brenda Vontes primeiro, depois os 3 aniversariantes) — mas quem clica e envia é você ou a recepção, não eu.
