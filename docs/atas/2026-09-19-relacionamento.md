---
agente: relacionamento
data: 2026-09-19
hora: 09:00
gerado_por: tarefa agendada
---

# relacionamento · 2026-09-19 às 09:00

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
**PARECER · Relacionamento · 19/09/2026 (sábado)**
*Dado de: base e painel de 18/09 13h19 · fila de WhatsApp de 17/09 14h27 · fila de aniversário de 09/09. Nenhum é de hoje. Os "dias sem vir" abaixo valem para 18/09, então some 1 para hoje.*

**SITUAÇÃO** 🟡 atenção

**FATOS**
1. **70 clientes marcados como sumidos, R$ 16.437 de gasto histórico.** Eram 59 na ata de 18/09. As 20 maiores somam R$ 8.491, ou 52% do total.
   - **9 delas sumiram há 15 a 21 dias**, somando R$ 4.692:
     - Brenda Vontes (R$ 1.190)
     - Juliana Cavalieri (R$ 760)
     - Gabrielly Baltazar (R$ 719)
     - Fernanda Oliveira (R$ 522)
     - Rejane Bernado Costa (R$ 341)
     - Elaine Donato (R$ 317)
     - Celia Dias (R$ 295)
     - Alane Valesca (R$ 280)
     - Thais Taglieri (R$ 268)
   - As outras 11 estão há 28 dias ou mais (R$ 3.799).
   - A loja tem 58 dias de vida e 257 de 422 clientes vieram nos últimos 30 dias. Com essa idade, o número de sumidos sobe sozinho conforme a base envelhece.
2. **O critério "3+ visitas" conta serviços, não idas à loja.** Conferi na agenda: as "12 visitas" da Brenda são 12 serviços em **3 dias** (01/08, 11/08 e 28/08). O intervalo dela é de 10 e 17 dias, e hoje ela está em 22. Ela passou do próprio ritmo, mas não está "perdida". Uma cliente que veio uma vez e fez 3 serviços também entra na lista. **Não consegui medir quantos dos 70 são assim**, porque o Python não roda nesta sessão. Trate a lista como hipótese.
3. **Aniversários: 16 nos próximos 14 dias, R$ 1.950 de gasto somado (média R$ 122).** Hoje fazem aniversário Thais Gordenazi e Julia Rios, com R$ 130 somados e 1 visita cada. Thais Taglieri fez ontem e está **também na lista de sumidos**. É o melhor motivo de contato do dia, porque a mensagem de parabéns já vira a conversa. A fila automática de aniversário não roda há 10 dias (09/09). A de reativação foi montada em 17/09 e recusou 21 mensagens por interruptor desligado.

**RISCO** Hoje é sábado, que pesa 37,6% do movimento da semana. É o dia em que a cliente que recebe um toque volta mais rápido. O canal manual (botão 📱 do painel) depende de alguém clicar, e não vejo se está acontecendo. Se as 9 clientes de 15 a 21 dias voltarem uma vez cada, são cerca de R$ 1.060 (9 × ticket médio de R$ 117,75). Esse é o valor máximo desta semana. Não tenho histórico para dizer quanto a chance de voltar cai entre 21 e 28 dias, porque a loja é nova demais.

**NÃO VEJO**
- Se a recepção está clicando no 📱 para sumidas e aniversariantes. → Operação.
- Por que `aniversarios.yml` parou em 09/09. Esta é a **terceira** ata que pergunta (16/09, 18/09 e hoje) e ninguém respondeu. → quem cuida de `scripts/agenda` e dos workflows.
- Quantos dos 70 são realmente clientes de 3+ dias distintos. → precisa de sessão com Python.

**DECISÃO**
1. **WhatsApp Cloud continua como decidido em 14/09.** Não reabro sem acesso admin ao portfólio Meta.
2. **Recomendo corrigir o critério** para contar dias diferentes, não serviços. Isso muda o card de sumidos, então precisa do seu OK.
3. **Você ou a recepção:** vale chamar hoje, pelo 📱, as 9 clientes de 15 a 21 dias, começando pela Thais Taglieri (aniversário) e pela Brenda. Eu não envio nada.

**Nota sobre a minha ficha, para a Memória atualizar.** Ela está desatualizada em três pontos:
- Diz "411 clientes", e a base hoje tem 422.
- Trata os "0 contatos do HubSpot" como pendência, mas o HubSpot foi desligado em 14/09 e não há pendência.
- Sugere "recriar o App Meta" em DECISÃO, mas essa proposta foi recusada em 14/09.

Não rodei `auditoria_coerencia.py`. O Python não está disponível aqui e eu não alterei nenhum dado.
