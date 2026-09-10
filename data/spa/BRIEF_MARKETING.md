# Brief · setup mídia SPA + recuperação WhatsApp Escova

**Pra:** gerente Marketing FAST
**De:** Rodrigo (dono)
**Contexto:** Fast SPA Limão inaugura 25/09/2026. Painel unificado
(Escova + SPA + Consolidado) já tem toda a infra pronta pra receber
os dados assim que as contas de mídia forem provisionadas.

---

## 🎯 Objetivo

Deixar as **3 pendências de mídia** resolvidas pra dashboard SPA
subir com dado real na abertura (25/09), aproveitando pra recuperar
o **WhatsApp Cloud da Escova** (perdido quando o App Meta foi deletado).

---

## ✅ O que já foi feito (não precisa mexer)

**SPA · Meta (Ad Account + IG + FB):**
- `meta_ad_account_id`: `act_1381925294040065` (FS - LIMÃO)
- `ig_user_id`: `1038797859315263` (@fastspa.limao)
- `facebook_page_id`: `871300609405142` (Fast Spa Limão)
- Portfolio Meta: **Fast Spa 2026**
- Mesmo `META_ACCESS_TOKEN` da Escova tem acesso (mesmo admin)

**SPA · Instagram + Facebook:** contas criadas, seguidores começando

**Já pode rodar:** pull Supermetrics MCP apontando pros IDs SPA →
gera `data/spa/midias_sociais.json` no repo → dashboard pega automático.

---

## 📋 Pendências (o que precisa fazer)

### 1. WhatsApp Cloud API · Escova (recriar) + SPA (criar)

**Escova** — status atual: App Meta que gerenciava WhatsApp foi
deletado; secret `META_PHONE_NUMBER_ID` no GitHub Actions **não
existe** (só `META_ACCESS_TOKEN`). Nada dispara desde então (kill
switch `disparo_wa.ativo: false`).

**SPA** — status atual: número `+55 11 99024-3927` registrado no
portfolio Fast Spa 2026 como contato, mas **WABA (WhatsApp Business
Account) não foi criada**. Rodrigo tentou pelo mobile, sem sucesso.

**O que fazer (fluxo pras 2 unidades no desktop, ~30 min):**

Pra CADA unidade (Escova e SPA):

1. Meta Business Manager → **Configurações do Negócio** →
   Portfolio correto (**Fast Escova Limão** ou **Fast Spa 2026**)
2. Menu esquerdo → **Contas** → **Contas do WhatsApp** → **+ Criar**
3. Nome da WABA:
   - Escova: **Fast Escova Limão**
   - SPA: **Fast Spa Limão**
4. Adiciona número:
   - Escova: o número que já era usado (verificar histórico)
   - SPA: `+55 11 99024-3927`
5. Verificação SMS/voz
6. **Display Name** (aparece pro cliente):
   - Escova: **Fast Escova Limão**
   - SPA: **Fast Spa Limão**
   - Submete pra aprovação Meta (24-48h)
7. **Templates** — reaprovar em cada WABA:
   - `aniversario_fast_v1` (mensagem de aniversário com voucher)
   - `reativacao_fast_v1` (mensagem pra cliente sumido)
   - Copy da Escova serve pra SPA (só troca "FAST Escova" por "FAST SPA")

**Depois de tudo aprovado, me manda:**
```
ESCOVA:
  whatsapp_business_account_id: ______________
  whatsapp_phone_number_id: ______________
  Display Name aprovado? sim / não

SPA:
  whatsapp_business_account_id: ______________
  whatsapp_phone_number_id: ______________
  Display Name aprovado? sim / não
```

Rodrigo cadastra no `data/config.json` e nos GitHub Secrets
(`META_ESCOVA_PHONE_NUMBER_ID` + `META_SPA_PHONE_NUMBER_ID`).

---

### 2. Google Business Profile · SPA

**Status:** não criado ainda.

**Config decidido:**
- Nome: **Fast SPA Limão**
- Endereço: **Av. Dep. Emílio Carlos, 358 · Limão · São Paulo**
  (mesmo prédio da Escova — Google aceita 2 negócios no mesmo endereço
  quando categorias são distintas)
- Categoria principal: **Spa**
- Categorias secundárias: **Salão de beleza**, **Estúdio de massagem**
- Telefone: **+55 11 99024-3927**

**O que fazer:**

1. `https://business.google.com/create` (mesma conta Google que
   gerencia o da Escova)
2. Adicionar empresa → preencher com o config acima
3. Verificação: cartão postal (5-14 dias) OU vídeo/telefone (mais rápido)
4. Depois de verificado:
   - Upload de 8-12 fotos (fachada, interior, área de massagem, produtos)
   - Horário (mesmo da Escova? verificar)
   - Descrição curta (750 chars)
   - **Sinalizar categorias secundárias** pra aparecer em buscas amplas

**Depois de criado, me manda:**
```
SPA:
  google_business_location_id: ______________ (URL: business.google.com/dashboard/l/XXXXX)
```

---

### 3. HubSpot · SPA (só se aplicável)

**Status:** desconhecido — o portal Escova (`51943728`) é compartilhado?

**Pergunta:** SPA vai ter portal HubSpot próprio ou vai compartilhar
com Escova (mesmo funil, listas separadas por tag)?

Se compartilhar → nada a fazer, backend já usa portal Escova.
Se separado → me manda `hubspot_portal_id` da SPA.

---

## ⏱ Timeline sugerida

| Prazo | Tarefa | Bloqueia |
|---|---|---|
| Semana 1 | Criar Google Business SPA + WABAs (Escova + SPA) | verificação começa |
| Semana 2 | Aguardar Display Names + Google verificação | — |
| Semana 3 | Aprovar templates WhatsApp | disparo automático |
| **25/09 (D-DAY)** | **SPA abre** com Meta Ads + IG + FB + GBP + WA rodando | receita começa |

Se qualquer coisa atrasar, o dashboard continua funcionando com o que
tiver — as pendências ficam sinalizadas na aba Mídia (chip amarelo
"Aguardando").

---

## Contato Rodrigo

- WhatsApp Rodrigo: (verificar no cadastro)
- Repositório com o config: https://github.com/rodsballa12-cell/fast-dashboard-limao
- Config file: `data/config.json → unidades.spa.midia_ids` (linhas 30+)
- Handoff técnico: `data/spa/MIDIAS_HANDOFF.md` (schema completo)
