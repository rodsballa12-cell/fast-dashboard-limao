---
agente: relacionamento
data: 2026-10-04
hora: 09:00
gerado_por: tarefa agendada
---

# relacionamento · 2026-10-04 às 09:00

↑ [[76_Briefings_Agentes/00-INDEX|Briefings dos Agentes]]

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
**PARECER · Relacionamento · 2026-10-04**
*(dado de churn/aniversariantes: 02/10 12h23 · dado da fila de WhatsApp: 01/10 15h41 — já dois dias atrás de hoje)*

**SITUAÇÃO** 🔴 ação hoje

**FATOS**
1. **89 clientes em alerta de churn, R$ 25.428 de LTV em risco** — eram 69 e R$ 16.862 quando o Conselho de 20/09 decidiu ligar a fila de WhatsApp para eles; a decisão nunca foi executada (`disparo_wa.ativo` continua `false`) e o grupo cresceu 29% em 12 dias.
2. **5 aniversariantes já passaram da data (02, 03 e 04/10) sem mensagem**, R$ 727 de LTV somado — e isso é anterior ao bloqueio do canal: `aniversarios_fila.json` não regenera desde **09/09**, quase um mês parado.
3. **Canal mudo nos dois lados**: WhatsApp Cloud API desconectado (decisão de 14/09, falta de acesso admin no Meta Business Manager) *e* o interruptor geral (`disparo_wa.ativo`) desligado por cima disso. A fila chegou a montar 20 clientes em 01/10 e recusou todos ("kill switch desligado") — nada saiu.

**RISCO** No ritmo das últimas duas semanas (69→89 clientes, +R$ 8.566 em 12 dias), o grupo em risco de churn cresce **~R$ 5.000/semana** em LTV não reativado enquanto ninguém religar a fila. Isso é dinheiro de cliente que já veio à loja, com custo de reativação zero — a perda não é de aquisição, é de relacionamento que já existia.

**NÃO VEJO** Por que `aniversarios_fila.json` parou em 09/09 enquanto `wa_fila.json` (o mesmo tipo de arquivo, outra campanha) seguiu regenerando até 01/10 — parece um pipeline específico travado, não só o kill switch geral. → Memória/infra, para achar onde essa rotina quebrou.

**DECISÃO** Duas coisas acima da minha alçada:
- A decisão do Conselho de 20/09 ("ligar a fila para os 69") está no limbo — aprovada mas nunca ligada. Precisa de um veredito seu: executa agora (ligar `disparo_wa.ativo`) ou arquiva formalmente, porque hoje ela nem conta como feita nem como recusada.
- Enquanto o WhatsApp Cloud API não volta (sem previsão — depende de acesso admin no Meta que não está no seu radar, por decisão de 14/09), decidir se vale acionar os 89 por canal manual (telefone, WhatsApp pessoal) — eu priorizo a lista, mas não disparo nada sem você mandar.
