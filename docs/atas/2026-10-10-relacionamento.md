---
agente: relacionamento
data: 2026-10-10
hora: 09:00
gerado_por: tarefa agendada
---

# relacionamento · 2026-10-10 às 09:00

↑ [[76_Briefings_Agentes/00-INDEX|Briefings dos Agentes]]

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
PARECER · Relacionamento · 10/10/2026 · dado de 02/10/2026 (painel, 8 dias atrasado) e 01/10/2026 (fila de WhatsApp)

SITUAÇÃO 🟡 atenção

FATOS
1. 89 clientes em alerta de churn (14-120 dias sem vir), R$ 25.428 de LTV em risco — dado de 02/10. Em 20/09 o Conselho mandou ligar a fila de WhatsApp pra 69 desses clientes, R$ 16.862; não saiu nenhuma mensagem (canal desligado) e em 3 semanas a lista cresceu 29% em LTV sem ninguém tocar.
2. Hoje, 10/10, é aniversário de 2 clientes — Thamyres Caldro Matos e Catherine Cristine, R$ 491 de LTV somado — e nenhuma recebe mensagem: `aniversarios_fila.json` não é recalculado desde 09/09 (31 dias) e o disparo geral recusou 20 envios hoje porque o interruptor está desligado.
3. A carteira em si está bem: 514 clientes, 60,9% recorrentes, ticket médio R$ 121,59. O problema não é a base, é o canal mudo.

RISCO O custo sobe toda semana sem avisar: R$ 16.862 → R$ 25.428 em risco de churn em 21 dias, zero mensagens enviadas. Cliente que passa dos 120 dias sem vir sai da janela de reativação e fica mais caro trazer de volta. Aniversariante é o contato mais barato que existe — já é cliente, custo de reativação zero — e está sendo perdido todo dia que a fila fica parada.

NÃO VEJO
- O painel está datado de 02/10 (8 dias atrás): os 89 em alerta e os 16 aniversariantes de 14 dias provavelmente já são maiores hoje. → Operação/Memória, conferir por que o refresh não roda desde então.
- `midias_sociais.json → hubspot.mensagem` ainda diz "aguardando import da base", mas a decisão de 14/09 foi desligar o HubSpot de propósito (Trinks já é o cadastro) — a mensagem sugere uma pendência que não existe. → Memória, corrigir o texto.
- `aniversarios_fila.json` parado em 09/09 sem explicação registrada — a rotina que gera essa fila parece ter parado de rodar. → quem mantém `scripts/agenda/rodar_agente.ps1`, conferir.

DECISÃO Recriar o App Meta (exige acesso admin ao portfolio) continua sendo o único jeito de destravar o canal — ficou parado em 14/09 por falta desse acesso. Até resolver isso, cabe ao Rodrigo decidir se vale abrir contato manual (telefone/WhatsApp pessoal) com os clientes de maior LTV da lista de churn; eu monto a lista priorizada, mas não decido abrir esse canal alternativo.
