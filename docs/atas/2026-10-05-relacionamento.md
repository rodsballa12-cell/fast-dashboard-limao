---
agente: relacionamento
data: 2026-10-05
hora: 09:00
gerado_por: tarefa agendada
---

# relacionamento · 2026-10-05 às 09:00

↑ [[76_Briefings_Agentes/00-INDEX|Briefings dos Agentes]]

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
**PARECER · Relacionamento · 2026-10-05**
*(dado de churn/aniversariantes: 02/10 12h23 · dado da fila de WhatsApp: 01/10 15h41 — já 3 e 4 dias atrás de hoje)*

**SITUAÇÃO** 🔴 ação hoje

**FATOS**
1. **89 clientes em alerta de churn, R$ 25.428 de LTV em risco** (dado de 02/10, pode estar maior hoje). Eram 69 e R$ 16.862 quando o Conselho de 20/09 decidiu ligar a fila de WhatsApp para eles — a decisão nunca saiu do papel (`disparo_wa.ativo` continua `false`) e o grupo cresceu 29% em 12 dias, cerca de R$ 5.000/semana de cliente que já veio à loja e ninguém chamou de volta.
2. **6 aniversariantes já passaram da data sem mensagem** (02, 03, 04 e 05/10), R$ 816 de LTV somado. Mais 16 fazem aniversário nos próximos 14 dias (dado de 02/10) e vão entrar na mesma situação se nada mudar.
3. **Canal mudo nos dois níveis**: WhatsApp Cloud API desconectado desde 14/09 (falta acesso admin no Meta) *e* o interruptor geral desligado por cima disso. A fila chegou a montar e recusar tudo ("kill switch desligado") até 01/10 — e nem isso está rodando: 4 dias sem gerar fila nova, depois de ter rodado todo dia de 24/09 a 01/10.

**RISCO** No ritmo das duas últimas semanas, o grupo em risco de churn cresce ~R$ 5.000/semana em LTV não reativado enquanto a fila continuar desligada. Essa é a segunda vez que esse mesmo alerta sobe sem resposta — se ficar um terceiro dia sem decisão, o risco maior passa a ser o alarme virar rotina ignorada, não só o dinheiro.

**NÃO VEJO**
- *Resolvido desde ontem:* o arquivo `aniversarios_fila.json` parado em 09/09 não é pipeline quebrado — o fluxo antigo (`aniversarios.yml`) foi desativado de propósito em 04/09, substituído pelo `campanhas_wa.yml` que hoje junta aniversário e reativação dentro de `wa_fila.json`. O arquivo velho só ficou esquecido no repositório; vale a Memória arquivar ou apagar pra não confundir a próxima auditoria.
- *Novo:* `wa_fila.json` (a fila que substituiu o fluxo antigo) também parou de atualizar depois de 01/10, mesmo tendo rodado todo santo dia de 24/09 a 01/10 sem falhar. E o painel inteiro (`dashboard_data.json`) está parado desde 02/10 — 3 dias. As duas coisas pararem quase junto sugere uma causa comum (token, permissão do GitHub Actions). → Memória/infra, para achar o que travou.

**DECISÃO** Duas coisas acima da minha alçada, as mesmas de ontem, ainda sem resposta:
- A decisão do Conselho de 20/09 ("ligar a fila para os 69") está no limbo há 15 dias — nem executada, nem recusada. Precisa de um veredito: liga o `disparo_wa.ativo` agora ou arquiva formalmente.
- Enquanto o canal automatizado não volta, decidir se vale acionar os clientes de maior LTV da lista de 89 por telefone ou WhatsApp pessoal — eu priorizo quem chamar primeiro, mas não disparo nada sem você mandar.
