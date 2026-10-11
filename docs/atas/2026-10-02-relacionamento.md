---
agente: relacionamento
data: 2026-10-02
hora: 09:00
gerado_por: tarefa agendada
---

# relacionamento · 2026-10-02 às 09:00

↑ [[76_Briefings_Agentes/00-INDEX|Briefings dos Agentes]]

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
PARECER · Relacionamento · 02/10/2026 (sexta) · dado de 08:46 (painel) / 01/10 09h (fila WA)

**SITUAÇÃO** 🟡 atenção

**FATOS**
1. **Churn:** 93 clientes com 3+ visitas e 14+ dias sem voltar, R$ 27.002 de LTV em risco (dado de hoje). Em 20/09, quando o Conselho aprovou ligar a fila de WhatsApp pra esse grupo, eram 69 clientes e R$ 16.862 — alta de 35% em clientes e 60% em LTV em 12 dias, sem nenhum canal automático agindo nesse intervalo.
2. **Canal:** fila de WhatsApp de 01/10 saiu vazia (20 recusas, motivo "kill switch desligado" — `disparo_wa.ativo=false` no config.json) e o WhatsApp Cloud API segue sem App Meta desde 14/09. São dois bloqueios, não um: ligar só o interruptor não faria mensagem sair.
3. **Base:** dos 501 clientes, 300 recorrentes geram R$ 80.225 (83,6%) da receita do ano contra R$ 15.790 de 201 clientes de visita única. É esse grupo que já paga a conta e é também ele que está sumindo — não é problema de aquisição, é retenção.

**RISCO** Se o ritmo de 35% a cada 12 dias se mantiver, o grupo em risco passa de 100 clientes e R$ 30 mil nas próximas duas semanas, com o mesmo canal mudo. Junto, 1 aniversariante hoje (Giovanna Maia, R$ 158 de LTV) e mais 5 nos próximos 7 dias também não recebem mensagem automática — só sai se alguém lembrar de usar o botão 📱 do painel um por um.

**NÃO VEJO**
- Se algum desses 93 já foi contatado por telefone ou WhatsApp pessoal da recepção, fora do painel. → Operação/Pessoas, quem atende o balcão sabe.
- Se a não-execução da decisão de 20/09 foi uma escolha consciente (porque dependia do mesmo bloqueio do App Meta de 14/09) ou só ficou parada sem ninguém notar. → Memória, pra registrar a causa certa.

**DECISÃO** Ligar `disparo_wa.ativo` não é minha alçada e, pelo que já foi decidido em 14/09, não resolve sozinho — falta acesso admin ao portfolio Meta que o Rodrigo não tem hoje. A decisão real em aberto: buscar esse acesso (destrava Marketing e Relacionamento juntos) ou assumir que, enquanto isso não acontece, o contato com os clientes de maior LTV da lista — Daniela Rodrigues (R$ 2.053, 14 dias), Andressa Martins Mendes (R$ 877, 15 dias), Juliana Cavalieri (R$ 760, 34 dias) — é manual, pelo botão 📱 do painel ou telefone direto.
