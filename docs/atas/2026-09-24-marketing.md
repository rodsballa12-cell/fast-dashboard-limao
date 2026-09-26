---
agente: marketing
data: 2026-09-24
hora: 08:00
gerado_por: tarefa agendada
---

# marketing · 2026-09-24 às 08:00

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
O painel de mídia está cego há 6 dias — e não é caso novo, é o mesmo problema já diagnosticado em 23/09 que ninguém corrigiu ainda.

```
PARECER · Marketing · 24/09/2026 (quinta) · dado de 18/09 às 11h22 (6 dias atrás)

SITUAÇÃO   🔴 ação hoje

FATOS
1. Meta Ads + Instagram (Escova e Spa) não atualizam desde que o token de
   acesso expirou em 16/09 às 07h. Confirmado nos dois arquivos (Escova e
   Spa): mesmo erro gravado no payload — "Session has expired on
   Wednesday, 16-Sep-26 07:00:00 PDT" — em todas as tentativas desde então.
2. A rotina automática (`midias_refresh.yml`) está configurada certo — três
   tentativas por dia, com early-exit — então não é falha de agendamento:
   é o token mesmo que morreu e ninguém trocou.
3. O Spa inaugura amanhã, 25/09. O aquecimento pré-abertura recomendado em
   18/09 (posts + campanha de reconhecimento) está rodando às cegas há uma
   semana inteira — não dá para saber se a verba está ativa, parada, ou
   vazando sem controle, na véspera da abertura.

RISCO   Se a campanha do Spa estiver ativa e ninguém estiver olhando, é o
   apagão de 27-31/08 se repetindo (~R$480 queimados em 4 dias sem ninguém
   perceber) — só que agora no pior momento possível. Se estiver parada,
   o Spa abre amanhã sem nenhum aquecimento de público. Cada dia sem
   corrigir piora as duas hipóteses.

NÃO VEJO
   Se as campanhas do Spa estão ativas ou pausadas agora na Meta — isso só
   o Gerenciador de Anúncios responde ao vivo. → conferir direto no
   app/site da Meta, hoje, antes da abertura de amanhã.

DECISÃO
   A correção já está escrita, passo a passo, em docs/meta-token.md — 15
   minutos, feita uma vez só, e só você tem login no Business Manager para
   fazer (cria um "usuário do sistema" com token que não expira mais).
   Isso está parado há 6 dias. Com o Spa abrindo amanhã, vale fazer hoje —
   e depois rodar manual o workflow "Refresh Midias Sociais (diario)" no
   GitHub para confirmar que voltou.
```

Isso é a segunda vez que esse alerta sobe (a primeira foi ontem, 23/09) sem correção — o resto do parecer normal (entrega vs benchmark, CPA, frequência) segue preso atrás do mesmo buraco de 6 dias, não vou repetir número de 16/09 como se fosse de hoje.
