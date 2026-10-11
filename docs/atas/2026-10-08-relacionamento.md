---
agente: relacionamento
data: 2026-10-08
hora: 09:00
gerado_por: tarefa agendada
---

# relacionamento · 2026-10-08 às 09:00

↑ [[76_Briefings_Agentes/00-INDEX|Briefings dos Agentes]]

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
Base lida, canal confirmado mudo, decisão parada há 12 dias. Parecer pronto.

---

PARECER · Relacionamento · 08/10/2026 · dado de 02/10 12h23 (**6 dias atrás** — mais velho que os 2 relógios do Financeiro)

SITUAÇÃO   🟡 atenção

FATOS
1. **89 clientes em alerta de churn, R$ 25.428 de LTV em risco** (base de 02/10). Como o dado tem 6 dias, quem constava com 14 dias sem vir naquela data já está em **20 dias hoje** — a lista real é mais vermelha do que o número mostra.
2. **6 aniversariantes passaram em branco entre 02/10 e 05/10** (Giovanna, Josicleia, Telma, Katia, Julia, Carolina) — nenhuma mensagem saiu: as duas filas (`wa_fila.json` e o kill switch `disparo_wa.ativo`) seguem em `false` desde antes dessa janela. Próxima dupla de aniversário é 10/10 (Thamyres e Catherine).
3. **A decisão do Conselho de 20/09** — "ligar a fila para os 69 clientes em risco, R$ 16.862 de LTV" — está registrada como aprovada e **sem resultado preenchido**. Em 12 dias sem execução, o próprio alerta de churn que ela endereçava cresceu de 69 para 89 clientes e de R$ 16.862 para R$ 25.428.

RISCO   Enquanto o canal segue mudo, o alerta de churn cresce sem nenhuma resposta: +20 clientes e +R$ 8.566 de LTV em risco entre 20/09 e 02/10 (12 dias). Se o ritmo se mantiver, são ~R$ 700/dia de LTV saindo da janela de reativação sem custo de contato — dinheiro que teria custo zero para recuperar e está sendo perdido só por falta de canal.

NÃO VEJO
- Se algum desses 89 já voltou entre 02/10 e hoje por atendimento manual (telefone, WhatsApp pessoal da recepção) — isso não aparece em `clientes_detalhes.json` nem em `churn_early`. → Operação/Pessoas, que vêem a agenda do dia.
- Por que o dashboard está parado em 02/10 enquanto o Financeiro já trabalha com commits de 07-08/10 — não é chave minha saber se o refresh do Trinks falhou ou só não rodou. → quem mantém `github_refresh.py`.

DECISÃO   O bloqueio de fundo continua sendo o mesmo de 14/09: sem acesso admin ao portfólio Meta, não dá para recriar o App e ligar o WhatsApp Cloud — isso já foi decidido como "não agir por ora". O que falta decidir agora é mais simples: a fila de 20/09 nunca foi efetivamente ligada (seguia dependendo do mesmo canal). Com o risco quase 50% maior do que quando a decisão foi tomada, vale o Rodrigo dizer se quer **aprovar contato manual** (ligação/WhatsApp pessoal da recepção) para os LTVs mais altos da lista — Daniela Rodrigues (R$ 2.053, 14→20 dias sem vir) à frente — enquanto o canal automatizado continua fora do ar.
