---
agente: relacionamento
data: 2026-09-23
hora: 15:30
gerado_por: tarefa agendada
---

# relacionamento · 2026-09-23 às 15:30

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
## PARECER · Relacionamento · 23/09/2026 (quarta) · dado de 18/09 13:19

**⚠️ Frescor:** minha fonte mais recente é o painel gerado sexta-feira 18/09 às 13h19 — **5 dias atrás**. A fila de WhatsApp (`wa_fila.json`) é de 17/09, e a fila de aniversariantes (`aniversarios_fila.json`) é de 09/09 (praticamente inútil, a aniversariante dela já passou). Os "dias sem vir" abaixo estão todos defasados em +5 dias.

**SITUAÇÃO** 🟡 atenção

**FATOS**
1. Carteira Escova saudável: 422 clientes cadastrados, 57,8% recorrentes (244), LTV médio R$169,93 — dado de 18/09.
2. **70 clientes sumidos** (3+ visitas, 14+ dias sem vir), LTV em risco **R$16.437,10** — dado de 18/09. Em 14/09 o Conselho registrou 58 clientes nessa mesma situação: o número cresceu enquanto o canal seguia mudo.
3. Nenhum aniversariante em 23 ou 24/09. O próximo é **25/09 — Maria Francisca Alves —, mesmo dia da inauguração do Spa**; na semana seguinte vêm mais 6 (26 a 30/09). SPA em si ainda não tem base de clientes (0 cadastro, churn zerado — natural, ainda não abriu).

**RISCO**
O canal automatizado continua morto: WhatsApp Cloud API nunca chegou a existir (decisão do Conselho de 14/09: sem acesso admin ao portfolio Meta pra recriar o App apagado), e o interruptor geral (`disparo_wa.ativo`) está desligado no config. A fila de 17/09 confirma — 21 recusas por "kill switch desligado", 0 enviados. Sem contato, o resgate estimado de 30–40% do LTV em risco (**R$4.931 a R$6.575**) fica parado, e o volume de sumidos sobe (58→70 em 12 dias) sem nada automático rodando atrás. O ponto mais quente: sete aniversariantes caem bem na semana da inauguração do Spa (25 a 30/09) e, do jeito que está, nenhum recebe mensagem nenhuma.

**NÃO VEJO**
- Se algum desses 70 já voltou entre 18/09 e hoje — preciso de um refresh mais novo do Trinks. → quem roda `github_refresh.py` (sessão do PC / Operação).
- HubSpot segue com 0 contatos, mensagem "aguardando import da base" sem mudar desde antes — não sei se esse import está no radar de alguém. → Marketing.

**DECISÃO**
Não há nada novo a decidir sobre o WhatsApp Cloud — já foi levado ao senhor em 14/09 e ficou definido não perseguir, sem prazo de revisão. O que sobra: usar WhatsApp pessoal/Web pra contatar manualmente os de maior LTV da lista de sumidos (Brenda Vontes R$1.190, Juliana Cavalieri R$760, Gabrielly Baltazar R$719) e os sete aniversariantes da semana do Spa — é a alternativa que o próprio Conselho deixou em aberto. Se quiser, eu priorizo a lista completa dos 70 por LTV pro senhor mandar manualmente.
