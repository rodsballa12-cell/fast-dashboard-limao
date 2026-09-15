# Conselho 14/09 · Não configurar WhatsApp Cloud API

**Data:** 2026-09-14 · **Quem decidiu:** Rodrigo
**Origem:** Conselho noturno 22:30 · Decisão #2 (cobrança da reunião matinal)
**Status:** recusada
**Cobrança de:** [2026-09-14-conselho-ata-app-meta.md](./2026-09-14-conselho-ata-app-meta.md)

## Contexto

Reunião da manhã de 14/09 decidiu reconectar o App Meta — desbloquearia
Marketing (token Graph API) e Relacionamento (WhatsApp Cloud) em ação
única. Ficou parado durante o dia.

Conselho da noite cobrou execução, agora sabendo que o token Meta Graph
já foi resolvido em separado (renovação do `META_ACCESS_TOKEN` no cron
via Graph API Explorer). Restava só a parte do WhatsApp Cloud, que exige
recriar App Meta no portfolio "Fast Escova Limão" no Business Manager.

## Decisão

**Não configurar WhatsApp Cloud API no curto prazo.**

## Motivo

Rodrigo não tem acesso admin ao portfolio Meta necessário para recriar
o App Meta apagado. Sem admin, não dá para:
- Criar novo App Meta associado ao portfolio correto
- Vincular a WhatsApp Business Account (WABA)
- Emitir permanent access token com escopo WhatsApp
- Registrar os `phone_number_id` de Escova e Spa

Buscar essa promoção admin não está no radar do Rodrigo agora.

## Consequência

- **58 clientes em risco continuam sem canal automatizado** de mensagem
  (era o principal ganho esperado do WhatsApp Cloud)
- Fluxo de aniversariantes, reativação de churn e follow-up de conversas
  Meta Ads seguem manuais ou via canais alternativos
- Marketing continua operando normalmente (Graph API já reconectada)
- SPA (número +55 11 99024-3927 registrado no portfolio Fast Spa 2026)
  também fica sem CRM automatizado

## Executor

Nenhum · decisão de não agir.

## Alternativas que ficam em aberto

- Priorizar CRM via HubSpot standalone (sem integração WA)
- Manter contato via canais manuais (telefone, WhatsApp Web pessoal)
- Trocar plano de CRM se ganhar acesso admin no futuro

## Revisão

Só se o acesso admin ao portfolio Meta for concedido. Sem prazo definido
(reavaliar em próximo Conselho quando/se essa situação mudar).

## Impacto no dashboard

- `data/midias_sociais.json → whatsapp_cloud_api.mensagem` atualizada
  para refletir a decisão (era "aguardando promoção a admin", agora
  "descontinuado no Conselho 14/09")
- Novo direcionamento estratégico P2 "❌ WhatsApp Cloud API
  descontinuado no curto prazo" para não repetir a discussão em próximo
  Conselho sem novidade

## Resultado

Sem ação a executar. Registrar em `docs/aprendizados/` se o pattern se
repetir (bloqueio por falta de acesso admin em decisões estratégicas).
