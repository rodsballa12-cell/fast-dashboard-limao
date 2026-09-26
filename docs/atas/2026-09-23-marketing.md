---
agente: marketing
data: 2026-09-23
hora: 15:30
gerado_por: tarefa agendada
---

# marketing · 2026-09-23 às 15:30

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
Não precisei do terminal para isso — deu pra fechar a conta a partir do `data_inicio_domingo` do config (30/08 = domingo): **16/09 foi quarta**, **18/09 foi sexta**, **hoje, 23/09, é quarta**.

Encontrei um problema sério antes de chegar às métricas normais — deixo ele na frente porque é o que manda no resto do parecer.

---

```
PARECER · Marketing · 23/09/2026 (quarta) · dado de 18/09 às 11h22 (5 dias atrás)

SITUAÇÃO   🔴 ação hoje

FATOS
1. Meta Ads + Instagram (Escova e Spa) não atualizam desde 16/09 às 11h,
   quando o token de acesso expirou. As tentativas seguintes (17/09 e 18/09)
   já rodaram com o erro batendo — R$0,0 nos dois dias — e desde então
   nenhum commit entrou no repositório: nem mídia, nem dashboard, nem Trinks.
   5 dias corridos sem a rotina automática rodar, não só sem puxar dado da Meta.
2. A última leitura real de gasto é de 16/09: R$14,31 na Escova e R$14,04 no
   Spa — e nem isso é o gasto do dia, é só o que a API alcançou antes de cair
   (já registrado em docs/aprendizados/zero-por-falta-de-dado.md, 18/09).
3. O Spa inaugura em 25/09 — depois de amanhã. O aquecimento pré-abertura que
   o próprio painel recomendou em 18/09 (posts + campanha de reconhecimento,
   15 dias antes) está rodando às cegas há uma semana: não dá para saber se a
   verba está ativa, parada, ou vazando sem controle.

RISCO   Se a conta estiver ativa, é o apagão de 27-31/08 se repetindo
   (~R$480 em 4 dias, ninguém percebeu) — só que agora na pior janela
   possível, às vésperas da abertura do Spa. Se estiver parada, o Spa abre
   dia 25 sem nenhum aquecimento de público. As duas hipóteses pioram a cada
   dia sem alguém olhar direto no Gerenciador de Anúncios.

NÃO VEJO
   Se as campanhas estão de fato ativas ou pausadas agora na Meta — isso só
   o Gerenciador de Anúncios responde ao vivo, fora do meu alcance aqui.
   → conferir direto no app/site da Meta, hoje.

DECISÃO
   A correção definitiva já está escrita e é sua, Rodrigo — só você tem
   login no Business Manager: docs/meta-token.md, 15 minutos, uma vez só
   (cria um "usuário do sistema" com token que não expira mais, resolve
   isso para sempre). Depois de gerar e colar no GitHub, rodar manual o
   workflow "Refresh Midias Sociais (diario)" pra confirmar que voltou.
   Enquanto isso não acontece, vale abrir o Gerenciador de Anúncios pelo
   celular só pra ver se as campanhas do Spa estão ligadas — 2 minutos,
   sem precisar mexer em nada.
```

O resto do que eu normalmente reportaria (entrega vs benchmark, CPA, frequência, funil) está preso atrás desse mesmo buraco de 5 dias — não vou repetir número de 16/09 como se fosse de hoje.
