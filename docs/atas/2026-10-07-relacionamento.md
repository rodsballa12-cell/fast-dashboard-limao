---
agente: relacionamento
data: 2026-10-07
hora: 09:00
gerado_por: tarefa agendada
---

# relacionamento · 2026-10-07 às 09:00

↑ [[76_Briefings_Agentes/00-INDEX|Briefings dos Agentes]]

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
Fiz a leitura da base (514 clientes na Escova, 40 no Spa) e a conferência dos conectores antes de escrever. Achado principal: não é só o WhatsApp que está mudo — o motor que monta a fila e o próprio painel pararam de atualizar há dias, e isso não aparece em nenhum card.

```
PARECER · Relacionamento · 07/10/2026 (quarta) · dado de 02/10 11:09 — ver RISCO

SITUAÇÃO   🔴 ação hoje

FATOS      1. 89 clientes em alerta de churn, R$ 25.428 de LTV exposto (dado de
              02/10). Em 20/09 eram 69 e o Conselho decidiu ligar a fila de
              WhatsApp para eles (R$ 16.862 em jogo) — `disparo_wa.ativo`
              continua `false` 17 dias depois, decisão nunca executada.
           2. `wa_fila.json` não é remontado há 6 dias (última vez: 01/10
              15:41), embora o workflow rode via cron todo dia às 10h. Isso é
              mais grave que "fila montada e não enviada": é a fila nem
              sendo montada.
           3. 313 dos 514 clientes da Escova (61%) fazem só 1-2 serviços,
              com oportunidade de cross-sell mapeada — ex.: cliente de
              R$ 4.985 de LTV e 56 visitas nunca fez Pés.

RISCO      O painel inteiro (Escova e Spa) está parado desde 02/10 11h —
           5 dias. O card de aniversariantes de hoje está lendo uma janela
           gerada em 02/10 e não cobre 04 a 07/10: se alguém nasceu nesses
           dias, não tem como ver pelo painel. Os "14 dias sem vir" do
           churn também são de 02/10 — hoje são pelo menos 5 dias a mais
           para cada cliente da lista, e o contador de 89 só cresce.
           Enquanto isso não voltar, a única defesa é o botão 📱 manual,
           e ele está lendo dado de 5 dias atrás.

NÃO VEJO   Por que `refresh.yml` (roda a cada ~20min, 11h-21h) e
           `campanhas_wa.yml` (cron diário) pararam de commitar ao mesmo
           tempo, dia 01-02/10. Pedi `gh run list` para ver o histórico de
           execuções do GitHub Actions e a sessão bloqueou o comando — não
           tenho chave para confirmar se os workflows estão desabilitados,
           com erro, ou com a cota da API estourada.
           → Operação/Memória: quem tem acesso ao Actions, isso precisa
           de uma olhada hoje, antes de qualquer outra leitura do painel
           ser confiável.

DECISÃO    Religar o pipeline automático está fora da minha alçada — depende
           de alguém checar o GitHub Actions. Recriar o App Meta e ligar
           `disparo_wa.ativo` seguem pendentes desde 14/09, com revisão
           marcada para 14/10 (em 7 dias).
```

Quer que eu registre esse achado do pipeline parado em `docs/aprendizados/` (cargo Memória), ou prefere investigar o GitHub Actions primeiro?
