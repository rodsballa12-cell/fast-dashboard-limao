---
agente: marketing
data: 2026-09-21
hora: 08:00
gerado_por: tarefa agendada
---

# marketing · 2026-09-21 às 08:00

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
PARECER · Marketing · segunda 21/09/2026 · o painel foi gravado em 18/09 às 11h22, mas a Meta só vale até 15/09

**SITUAÇÃO 🔴**, por falta de leitura e não por desempenho. O que consigo ver está dentro da meta. Não vejo o gasto de 16 a 21/09.

Tentei o Supermetrics para ver o gasto real e o acesso foi negado. O `git fetch`, que traria um refresh mais novo do GitHub, também foi negado. O parecer abaixo se apoia só no que está gravado no PC, e os pareceres de 19 e 20/09 já diziam a mesma coisa.

**FATOS**
1. **A última semana fechada está na meta.** De quarta 09 a terça 15/09 foram R$ 651 e 89 conversas, a R$ 7,31 cada, contra R$ 761 e 103 conversas (R$ 7,38) nos mesmos dias da semana anterior. A meta é R$ 8,00.
   - Você recebeu 14% menos conversas porque gastou 14% menos (R$ 93 por dia contra R$ 109), não porque o preço subiu.
   - Essa soma vem do parecer de 20/09. Só refiz 12 a 15/09 na série diária: R$ 355 e 54 conversas, R$ 6,57 cada. Domingo 13/09 foi o ponto fraco, com R$ 94 para 6 conversas (R$ 15,74).
2. **A chave da Meta expirou em 16/09, às 11h, e o "R$ 0" do painel não é campanha parada.** Os "R$ 0" de 7, 30 e 90 dias e o CPA em branco são erro de leitura.
   - O dia 16 mostra R$ 14,31, o que a Meta entregou antes de a chave cair. Os dias 17 a 21 não existem no arquivo.
   - Os números de Instagram dos últimos 30 dias (0 seguidores novos, 0 alcance) são zeros do mesmo erro. A série diária mostra 350 seguidores ganhos na janela, e ela para em 16/09.
3. **A faixa de alertas do topo do painel está velha, com dados de cerca de 08/09.** Ela diz "4 dias sem postar, último post em 03/09", e a série do próprio arquivo mostra último post em 11/09. Os quatro pontos pendentes vêm dessa mesma faixa:
   - o anúncio RETOQUE (R$ 7,31 por conversa contra R$ 3,43 do PLÁSTICA);
   - os dois combos a R$ 12,66 por conversa;
   - a fusão dos 3 anúncios de vaga;
   - a campanha de indicação com zero conversa.

   Não recomendo mexer em nenhum deles às cegas. Algum pode ter se resolvido sozinho ou piorado.

**RISCO:** a Escova tem cerca de R$ 94 por dia configurados, e 16 a 21/09 (seis dias) somam cerca de R$ 560 sem ninguém olhando. Isso inclui o sábado 19, o dia mais forte da loja.
- Se a conta parou como em 27 a 31/08 (R$ 480 perdidos), é dinheiro e conversa perdidos.
- Se rodou, não se perdeu nada. Eu não sei qual dos dois aconteceu.
- O Spa abre em 25/09, daqui a 4 dias, e está igualmente cego.

**NÃO VEJO**
- **Gasto e entrega de 16 a 21/09, nas duas contas.** → Rodrigo (Gerenciador de Anúncios), ou eu, se o Supermetrics for liberado nesta sessão.
- **Se o GitHub já tem um refresh mais novo que 18/09.** Se a chave for trocada, o refresh diário volta sozinho. → sessão do PC, com o `git fetch` liberado.
- **Se as cerca de 89 conversas por semana viram cliente na cadeira.** → Operação. O campo "como nos conheceu" não separa Instagram pago de orgânico.
- **Se as vagas a R$ 3,93 por conversa viram contratação.** → Pessoas.

**DECISÃO (Rodrigo)**
1. **Hoje, 2 minutos:** abra o Gerenciador de Anúncios no celular, nas contas FE - LIMÃO e FS - LIMÃO. Veja o gasto de 16 a 21/09 e se as campanhas seguem ativas. Se algum dia estiver zerado com campanha ligada, me avise, porque aí é 🔴 de verdade.
2. **Antes de 25/09, 15 minutos:** gerar a chave permanente (Usuário do Sistema), pelo roteiro em `docs/meta-token.md`. Já caiu três vezes em 9 dias. O roteiro tem seis passos e termina em rodar o refresh na hora para testar.
3. **Spa:** diga se a semana de abertura quer verba para cliente. Pelo último dado real (14/09), a campanha de cliente fez R$ 37 para cerca de 3 conversas, a R$ 12,31 cada, contra R$ 7,31 na Escova. Para executar preciso de "aprovado", o nome da campanha e o valor por dia. Sem os três, só preparo.
4. **Se quiser que eu leia em vez de perguntar:** libere o Supermetrics e o `git fetch` nesta sessão.

**Defeito de código (não é decisão sua):** o painel escreve "R$ 0" quando deveria escrever "não medido", e a faixa de alertas curada continua no topo como se fosse de hoje.

Não alterei nenhum arquivo.
