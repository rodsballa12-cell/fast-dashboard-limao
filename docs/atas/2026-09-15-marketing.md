---
agente: marketing
data: 2026-09-15
hora: 10:20
gerado_por: sessão de análise
dado_de: 2026-09-14T18:35 BRT
---

# marketing · 2026-09-15 às 10:20

```
PARECER · Marketing · 15/09/2026 · dado de 14/09 18h35

SITUAÇÃO   🟡 atenção
```

O dado de mídia é de ontem às 18h35 porque **o token da Meta foi invalidado** — a API
respondeu `HTTP 400: the session has been invalidated because the user changed their
password`. Desde então o painel de mídia não atualiza.

## FATOS

**1. A mídia não é o problema do mês. É a parte que está funcionando.**

Setembro, 01 a 14, cruzando o que saiu com o que entrou:

| | agosto (mês fechado) | setembro (01–14) |
|---|---:|---:|
| Investido | R$ 2.565 | R$ 1.380 |
| Clientes novos no Trinks | 218 | 86 |
| **Custo por cliente novo** | **R$ 11,77** | **R$ 16,05** |
| Receita dos novos | R$ 28.560 | R$ 11.835 |
| Receita por cliente novo | R$ 131 | R$ 138 |
| **Retorno sobre o investido** | **11,1×** | **8,6×** |

Cada real de anúncio voltou como R$ 8,60 de caixa novo. Não existe alavanca no salão
com esse multiplicador. **Recomendar "campanha de WhatsApp para as top 30" enquanto
isso está de pé é olhar para o lado errado.**

**2. O retorno caiu 22% e dá para ver exatamente onde.**

Mesmo dinheiro, um terço menos de gente: contra a primeira quinzena de agosto, o
gasto subiu 1,4% e as impressões caíram **30%**, os cliques **36%** e as conversas
**31%**. O custo por conversa subiu **47%**.

A causa está identificada há uma semana e não se moveu: **[RETOQUE] gasta igual a
[PLÁSTICA] e entrega metade.** Nos 30 dias, R$ 467,72 por 64 conversas (R$ 7,31)
contra R$ 449,84 por 131 conversas (R$ 3,43). CTR 2,76% contra 3,96%. O criativo do
RETOQUE não é trocado desde **28/07** e o ad set ainda se chama "35+" com a idade já
configurada em 35-54.

**3. O Instagram cresce e não entrega ninguém na porta — por desenho.**

30 dias: 138.605 de alcance, 2.401 visitas ao perfil, 294 seguidores novos. E
`website_clicks: 0`, `profile_activity: 0`. O perfil tem 1.828 seguidores e **nenhum
caminho de saída**: sem link de agendamento, sem botão. O orgânico está construindo
audiência, não movimento.

## RISCO

Com o token invalidado, **as campanhas continuam gastando e eu paro de ver.** A média
é R$ 98/dia. Cada dia sem leitura é R$ 98 gastos às cegas, e o [RETOQUE] — que já
entrega metade — é onde o dinheiro está concentrado.

## NÃO VEJO

- **Se as 175 conversas de setembro viraram visita.** O salão é sem hora marcada, não
  existe elo entre a conversa e a cadeira. O que substituiria isso é o campo
  `comoNosConheceu` no cadastro da recepção. → **Relacionamento / Pessoas**
- **A conta do Spa está 71% investida em vagas de emprego** (Massoterapeuta,
  Recepção), a 10 dias da inauguração. A única campanha comercial, [COMBO INAUG],
  teve CPA de R$ 12,31. → **Rodrigo**

## DECISÃO

1. **Renovar o token da Meta** (`META_ACCESS_TOKEN` nos secrets do GitHub). Sem isso
   nada abaixo pode ser verificado.
2. **Trocar o criativo do [RETOQUE] ou mover a verba para [PLÁSTICA].** Segunda
   semana com o mesmo apontamento; a diferença acumulada é de ~R$ 230/mês jogados
   fora, e é a decisão mais barata da lista.
3. **Spa inaugura em 10 dias com 29% da verba em campanha comercial.** Se a
   inauguração é dia 25, a virada de verba precisa acontecer esta semana.
