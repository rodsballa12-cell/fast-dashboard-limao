---
agente: relacionamento
data: 2026-09-20
hora: 09:00
gerado_por: tarefa agendada
---

# relacionamento · 2026-09-20 às 09:00

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
**PARECER · Relacionamento · 20/09/2026 (domingo) · dado de 18/09 (sexta) 13h19**

O dado tem dois dias, então somei 2 a todos os "dias sem vir". Não consegui buscar o repositório, porque o comando foi bloqueado aqui, e a ata de ontem também não conseguiu. Pode haver dado mais novo publicado. A fila de WhatsApp é de 17/09 14h27. A fila de aniversário de 09/09 é de um arquivo aposentado (ver o fim).

**SITUAÇÃO** 🟡 atenção

**FATOS**

1. **70 clientes sumidos, R$ 16.437 de gasto histórico. Hoje, 9 delas estão entre 17 e 23 dias sem vir, somando R$ 4.692 (média de R$ 521 cada).**
   - As 9 são Brenda Vontes (R$ 1.190), Juliana Cavalieri (760), Gabrielly Baltazar (719), Fernanda Oliveira (522), Rejane Bernado Costa (341), Elaine Donato (317), Celia Dias (295), Alane Valesca (280) e Thais Taglieri (268).
   - As outras 11 das 20 maiores já passam de 30 dias e somam R$ 3.799 (média de R$ 345). Quem sumiu há menos tempo vale mais por cabeça, e é a mais fácil de trazer de volta.

2. **O painel conta serviços, não dias de visita, e isso infla a recorrência.** Confirmei no código, em duas contas:
   - O alerta de sumidas ("3+ visitas") conta cada serviço como uma visita.
   - "Recorrentes: 244 de 422 (57,8%)" usa a mesma regra.
   - O próprio painel diz que a média é 1,44 dias de visita por cliente. Para 244 clientes terem vindo em 2+ dias diferentes, a média teria de ser pelo menos 1,58. No máximo cerca de 186 (44%) voltaram de fato em outro dia. Pelo menos uns 58 dos 244 são clientes de um dia só (escova, mãos e pés no mesmo dia).
   - Não sei quantos dos 70 sumidos são desse tipo.

3. **Aniversários: 11 clientes, R$ 1.297 de gasto somado, até 27/09.** Calculei pelas datas, porque o campo "dias" do painel está parado em 18/09.
   - **Hoje (20/09):** Grasieli Batista (R$ 114) e Rose Citty (R$ 79).
   - **Passaram sem mensagem em 18 e 19/09 (R$ 563):** Thais Taglieri (também está na lista de sumidas), Critane Sayuri, Thais Gordenazi e Julia Rios.
   - **Até 27/09 (R$ 541):** Fernanda Feitoza (21/09), Sabrina Silva Avezedo (22/09), Maria Francisca Alves (25/09), Paola Messina (26/09) e Mayda Couto Pollini (27/09).

**RISCO**
- **Prazo:** o próximo pico é sexta 25/09 (18,7% do movimento da semana, dia da inauguração do Spa) e sábado 26/09 (37,5%). Hoje, domingo, pesa 8,2%. A janela para chamar as 9 antes do fim de semana é de segunda a quarta (21 a 23/09). Em 26/09 elas estarão com 23 a 29 dias, na faixa onde já estão as outras 11.
- **Valor:** se as 9 voltarem uma vez ao ticket de R$ 117,75 por dia de visita, são R$ 1.060. É um cenário, não uma previsão. A ata de 19/09 conferiu na agenda que Brenda gastou R$ 1.190 em 3 dias (cerca de R$ 397 por dia), então a conta é conservadora para quem faz vários serviços.
- **Sem histórico:** a loja tem 59 dias de vida. Não sei dizer quanto cai a chance de voltar entre 21 e 28 dias.
- **Canal:** o envio automático está desligado. Em 17/09 a fila recusou 21 mensagens por causa do interruptor. Só o botão 📱 do painel funciona, um cliente por vez.

**NÃO VEJO**
- Se a recepção está usando o 📱 com sumidas e aniversariantes. → Operação.
- Se o convite de inauguração do Spa para a base da Escova já foi combinado. São 422 clientes, 99,3% com telefone. A ata de Marketing de 18/09 só cita o anúncio pago. → Marketing / Rodrigo.
- Quantos dos 70 sumidos e dos 244 "recorrentes" são de um dia só. Isso exige contar dias na agenda. → sessão com Python, que hoje não existe neste PC: `python3` só abre o atalho da Loja Microsoft.

**DECISÃO**
1. **Corrigir a contagem para dias diferentes** nos cards de sumidos e de recorrentes. Muda números que o painel mostra hoje, então precisa do seu OK. Sugiro também ensinar a auditoria a estranhar quando "% recorrentes" e "média de visitas" não combinam.
2. **Convite do Spa à base da Escova.** É campanha, então acima da minha alçada. Eu ordeno a lista por gasto e a recepção manda pelo 📱, um a um. Mandar para 419 pessoas à mão em 5 dias não cabe, então começaria pelas maiores. O texto só sai com a sua aprovação. Não tenho taxa de conversão da Escova para o Spa, porque o Spa ainda não abriu.
3. **Hoje ou segunda, pelo 📱:** as 9 sumidas e as 2 aniversariantes de hoje. Comece pela Thais Taglieri, porque a mensagem de aniversário já vira a conversa da volta, e pela Brenda. Eu não envio nada.

WhatsApp Cloud segue como decidido em 14/09, e não reabri o assunto.

**Resposta à pergunta que três atas fizeram (por que a fila de aniversário parou em 09/09):** não está quebrada. O fluxo antigo foi desligado de propósito em 04/09, porque gerou 9 pedidos de aprovação e 7 morreram sem resposta. Quem monta a fila hoje é a rotina das 10h, que sai vazia enquanto o interruptor está desligado. O card de aniversariantes do painel não depende dela.

**Para a Memória:** a minha ficha ainda diz 411 clientes (são 422), trata o HubSpot como pendência (foi desligado em 14/09) e manda recriar o App Meta (recusado em 14/09). Não segui esses três pontos. Além disso, o dado do painel ainda diz "CRM ativo, aguardando import".

Não rodei a auditoria de coerência, porque não há Python neste PC. Não alterei nenhum arquivo e não enviei nenhuma mensagem.
