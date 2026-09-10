# SPA · handoff mídias sociais

Este arquivo documenta o que o painel espera receber em
`data/spa/midias_sociais.json` pra ativar a aba **📣 Mídia** do
Consolidado e a preview individual do SPA quando abrir (25/09/2026).

## Como funciona hoje

- **Escova:** `data/midias_sociais.json` é atualizado pelo gerente
  Marketing FAST (Supermetrics MCP · Meta Ads + Instagram Insights +
  Facebook Insights + Google Business + HubSpot + WhatsApp Cloud).
  Trigger manual via `/marketing-fast`.
- **SPA:** vai receber o MESMO schema em `data/spa/midias_sociais.json`,
  gerado a partir das contas próprias da SPA (não compartilha com Escova).
- **Consolidado:** o frontend pega automaticamente das duas pastas e junta
  no card `📣 Mídia · ano 2026`. Sem código pra mudar.

## O que preencher antes do primeiro pull

Editar `data/config.json → unidades.spa.midia_ids` com os IDs oficiais:

| Campo | O que é | Como pegar |
|---|---|---|
| `meta_ad_account_id` | Ad Account da Meta pra SPA | Meta Business → Configurações → Contas → Contas de anúncios (formato `act_XXXXXXXXX`) |
| `meta_ad_account_nome` | Rótulo legível | Ex: "FS - LIMÃO" |
| `ig_handle` | Perfil Instagram Business da SPA | Ex: `@fastspa.limao` (sem @) |
| `ig_user_id` | IG User ID | Meta Graph API: `GET /me/accounts?fields=instagram_business_account` |
| `facebook_page_id` | Página FB da SPA | Meta Business → Páginas → configuração |
| `facebook_page_nome` | Nome da página | Ex: "Fast SPA Limão" |
| `google_business_location_id` | Business Profile SPA | Google Business Profile Manager → gerenciar location |
| `google_business_nome` | Nome público | Ex: "Fast SPA Limão - SPA Day" |
| `whatsapp_phone_number_id` | WhatsApp Cloud número SPA | Meta Business → WhatsApp → Configuração → Números |
| `hubspot_portal_id` | Portal HubSpot | HubSpot → Configurações → Conta e faturamento → Portal ID |

## Schema esperado do JSON

Idêntico ao `data/midias_sociais.json` da Escova. Estrutura mínima:

```json
{
  "gerado_em": "2026-09-25T08:20:00-03:00",
  "fonte": "Supermetrics MCP · SPA",
  "janelas": { ... },
  "kpi_estrela": { "explicacao": "..." },
  "instagram": { "handle": "fastspa.limao", "followers": N, "ig_user_id": "..." },
  "meta_ads": {
    "ad_account_id": "act_...",
    "ad_account_nome": "FS - LIMÃO",
    "por_periodo": { "hoje": {...}, "7d": {...}, "mtd": {...}, "30d": {...}, "90d": {...} },
    "serie_diaria_30d": [ ... ],
    "por_objetivo_30d": [ ... ],
    "anuncios_30d": [ ... ],
    "ad_sets_30d": [ ... ],
    "top_campanhas_30d": [ ... ],
    "verba_setembro": N
  },
  "facebook_page": { "nome": "...", "page_id": "...", "conectado": true },
  "google_business": {
    "nome": "...", "location_id": "...", "conectado": true,
    "kpis_30d": { "actions_phone": N, "actions_directions": N, "views_total": N },
    "rating": { "estrelas_media": 4.9, "reviews_total": N },
    "serie_diaria_30d": [ ... ]
  },
  "google_ads": { "conectado": false },
  "hubspot": { "portal_id": "...", "contatos": N },
  "whatsapp_cloud_api": { "conectado": false, "mensagem": "..." },
  "benchmarks": { "cpa_msg_meta": 25, "ctr_meta": 1.5, "cpm_meta": 20 },
  "direcionamentos_estrategicos": [ ... ],
  "recomendacoes": [ ... ],
  "insights_narrativa": [ ... ],
  "alertas_topo": [ ... ],
  "deltas_vs_periodo_anterior": { ... },
  "funil_conversao": { ... }
}
```

Rodar o validador antes de commitar:

```bash
python3 scripts/validar_midias.py data/spa/midias_sociais.json
```

## Fluxo esperado

1. **Contas provisionadas** (Meta Business Manager cria Ad Account, IG
   Business linkado, Facebook Page, Google Business Profile, WhatsApp
   Cloud number, HubSpot portal se separado).
2. **IDs preenchidos** em `data/config.json → unidades.spa.midia_ids`.
3. **Gerente Marketing FAST** roda o Supermetrics MCP apontando pros
   novos IDs e commita o payload em `data/spa/midias_sociais.json`.
4. **Frontend** pega automático:
   - Aba SPA → `📣 Mídia · ano 2026` renderiza dado real
   - Aba Consolidado → soma Escova + SPA nos KPIs, ranking, funil
   - Banner de scaffolding some sozinho quando payload SPA existe

Nenhum código muda entre o "SPA preview escova" e "SPA real". A
detecção é automática via `fetchUnidade('midias_sociais.json')`.
