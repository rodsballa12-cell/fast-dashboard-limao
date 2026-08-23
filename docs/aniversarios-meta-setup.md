# Setup Meta Cloud API — Envio automático de aniversários

Guia passo-a-passo pra ativar o envio real de mensagens de aniversário via WhatsApp Business Cloud API (oficial Meta).

**Estado atual:** pipeline pronto rodando em `dry-run`. Falta configurar Meta + 2 secrets.

**Tempo total:** ~60 min ativos + 24-48h de espera pela aprovação do template.

**Custo:** grátis até 1.000 conversas de marketing por mês (FAST Limão não chega perto disso).

---

## Contexto específico da FAST Limão

| Item | Valor |
|---|---|
| Número WhatsApp Business | +55 11 96612-9197 |
| E.164 pra API | `5511966129197` |
| Status atual | **Em uso no app WhatsApp Business no celular da loja** |
| Endereço loja | Av. Dep. Emílio Carlos, 358 · Limão |
| Template Meta nome | `aniversario_fast_v1` |
| Presente configurado | Escova grátis (15 dias de validade) |

---

## ⚠️ Antes de começar: migração do número

Como o número **já está em uso no app WhatsApp Business** do celular da loja, precisa migrar pra Cloud API. Fluxo:

### 1. Backup das conversas atuais (opcional mas recomendado)
- Abre WhatsApp Business no celular
- **Configurações** → **Conversas** → **Backup de conversas**
- Faz backup pro Google Drive/iCloud
- Isso garante que se algo der errado, você recupera o histórico

### 2. Deslogar o número do app
- Depois que o Meta pedir (não faça antes)
- **Configurações** → **Contas** → **Excluir minha conta**
- Isso libera o número pra usar via Cloud API

### 3. Reconectar via WhatsApp Web (Multi-Device)
- Depois de migrar pra Cloud API, você usa o **Meta Business Inbox** (dentro do Business Manager) pra ver mensagens que chegam pra loja
- Ou pode usar clientes como `Chatwoot`, `Respond.io`, etc pra ter uma interface amigável

**Alternativa mais segura:** comprar um chip novo dedicado à API (~R$ 15/mês em operadoras empresariais) e manter o 96612-9197 no celular como está. Cliente veria "FAST Limão" no perfil da API separado do WhatsApp do dia-a-dia.

---

## Passo 1 · Criar Meta Business Manager (10 min)

1. Acesse https://business.facebook.com
2. **Criar conta** (canto superior direito)
3. Preencha:
   - Nome do negócio: **FAST Limão**
   - Seu nome: dono/responsável
   - Email de trabalho
4. Confirme o email
5. Adicione a página do Facebook da loja (obrigatório):
   - **Configurações do negócio** → **Contas** → **Páginas** → **Adicionar**
   - Se não tem página: crie uma nova (10min)

## Passo 2 · Adicionar WhatsApp Business Account (WABA) (15 min)

1. **Configurações do negócio** → menu esquerdo **Contas** → **WhatsApp**
2. Clica **Adicionar** → **Criar nova conta do WhatsApp Business**
3. Escolhe o método de verificação do número **+55 11 96612-9197**:
   - **SMS** (mais fácil) — recebe código no celular da loja
   - **Ligação** — Meta liga e fala o código
4. **⚠️ MOMENTO CRÍTICO:** o Meta vai pedir pra você deslogar do app WhatsApp Business ANTES de continuar
   - Só desloga quando Meta pedir explicitamente
   - Depois de deslogado, tem 5min pra inserir o código Meta
5. Insere código → número verificado ✅
6. Nome de exibição da conta: **FAST Limão** (esse nome aparece pros clientes)

## Passo 3 · Cloud API — obter credenciais de teste (5 min)

1. Vai em **WhatsApp** (menu superior) → **Configuração da API**
2. Você verá:
   - **Phone Number ID**: número tipo `1234567890123` (15-16 dígitos). **COPIE E ANOTE** — vai ser o `META_PHONE_NUMBER_ID`.
   - **WhatsApp Business Account ID (WABA ID)**: número tipo `9876543210987`. Anota também (pode precisar).
   - **Token de acesso temporário**: válido 24h — só pra teste. Pra produção você gera o permanente no Passo 5.
3. Nesse momento você pode enviar mensagem de teste pro seu próprio celular pra confirmar que funciona (rota `/messages` no console Meta).

## Passo 4 · Criar template message (10 min setup + 24-48h aprovação Meta)

1. **WhatsApp** → **Modelos de mensagem** → **Criar modelo**
2. Preenche:
   - **Nome**: `aniversario_fast_v1` (**exatamente esse nome, minúsculo, com underscore**)
   - **Idioma**: **Português (Brasil)** (`pt_BR`)
   - **Categoria**: **Marketing** (não Utility)
3. **Corpo da mensagem** (cole exatamente isso):

```
Feliz aniversário, {{1}}! 🎂

A FAST Limão preparou um presente pra você: {{2}}, válido pelos próximos {{3}} dias.

É só aparecer aqui na loja pra comemorar com a gente 💛
Av. Dep. Emílio Carlos, 358 · Limão

— Equipe FAST Limão 💛
```

4. **Exemplos dos parâmetros** (obrigatório pra Meta aprovar):
   - `{{1}}` — exemplo: `Karine`
   - `{{2}}` — exemplo: `Escova grátis`
   - `{{3}}` — exemplo: `15`
5. **Enviar pra aprovação**
6. Meta responde em **24-48h** por email + pelo dashboard. Se rejeitar, ajuste e reenvie (grátis).

**Motivos comuns de rejeição:**
- Categoria errada (Marketing vs Utility) — nossa categoria é Marketing (promocional)
- Texto genérico demais — nosso texto tá bom, personalizado com nome + presente
- Emojis demais — 3 emojis está OK, Meta aceita

## Passo 5 · Gerar Access Token permanente (10 min)

O token de teste dura 24h. Pra produção, precisa de um **System User Access Token** (permanente, não expira).

1. **Configurações do negócio** → menu esquerdo **Usuários** → **Usuários do sistema**
2. **Adicionar** → nome: `dashboard-api` → função: **Administrador**
3. Cria o usuário
4. Clica no usuário criado → **Adicionar ativos** → **WhatsApp Accounts** → seleciona sua WABA → **Controle total**
5. Volta na tela do usuário → **Gerar novo token**
6. **App:** seleciona o app associado (Meta cria automaticamente na WABA setup)
7. **Permissões** (marque todas):
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
   - `business_management`
8. **Expiração:** **Nunca** ← MUITO IMPORTANTE marcar essa opção
9. Clica **Gerar Token**
10. **COPIA E SALVA** o token — ele aparece **uma única vez**. Se perder, precisa gerar outro.

## Passo 6 · Colar secrets no GitHub (5 min)

1. Acessa repo: https://github.com/rodsballa12-cell/fast-dashboard-limao
2. **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret**:
   - Nome: `META_ACCESS_TOKEN`
   - Valor: cole o token permanente do Passo 5
4. **New repository secret** de novo:
   - Nome: `META_PHONE_NUMBER_ID`
   - Valor: cole o Phone Number ID do Passo 3

Pronto. A partir do próximo aniversariante que você aprovar via issue, envio será **real**.

## Passo 7 · Testar (5 min)

1. Cria manualmente uma mensagem de teste pra um número seu:
   - Vai em Actions do repo → workflow "Aniversários — fila diária" → **Run workflow**
   - Ou aguarde o cron das 08h BRT
2. Se tiver aniversariante hoje: abre issue automático
3. Comenta `approve all` no issue
4. Em ~30s: workflow secundário dispara, posta relatório e fecha issue
5. Cliente recebe no WhatsApp em segundos

## Troubleshooting

### Template não aprovado
- Meta manda email explicando motivo. Ajusta e reenvia grátis.
- Se rejeição foi por categoria: mude pra "Utility" (mais permissivo, mas com regras diferentes sobre horário de envio).

### Token expirou (não deveria se marcou "Nunca")
- Repete o Passo 5, gera novo token, atualiza o secret no GitHub.

### "Recipient not registered on WhatsApp"
- Cliente não tem WhatsApp naquele número. Sistema já loga e pula, não trava a fila.

### Cliente reclamou de spam
- Nunca envie pra quem não é aniversariante
- Nunca envie 2x pro mesmo cliente no mesmo período
- Se cliente pedir "sair", adicione o `cliente_id` numa lista de exclusão (pode ser um campo no `config.json` — `aniversario_optout_ids: [123, 456]`)

### Custo passou de 1.000 conversas/mês
- Marketing após 1000: ~R$ 0,30/mensagem
- Se aproximar do limite: alterar categoria pra Utility (mais barato) ou reduzir frequência

## Manutenção

- **Zero manutenção diária** — cron dispara sozinho, você só aprova quando o issue chega
- **Token permanente** — não expira, não precisa renovar
- **Meta pode revisar template** ocasionalmente — se rejeitar depois de aprovado, aparece email
- **Cliente respondendo à mensagem** — mensagens que a Meta receber podem ser vistas no **Meta Business Inbox** (dentro do Business Manager) ou via app integrador (Chatwoot, etc)

## Arquitetura do pipeline (referência)

```
08h BRT (cron)
  └─ workflow aniversarios.yml
      ├─ Roda scripts/aniversario_fila.py
      ├─ Detecta aniversariantes de hoje
      ├─ Prepara mensagem por cliente
      ├─ Commita data/aniversarios_fila.json
      └─ Cria issue "🎂 Aniversariantes DD/MM"

Você comenta "approve all" ou "approve 1 3" ou "skip"
  └─ workflow aniversarios_dispatch.yml (trigger: issue_comment)
      ├─ Roda scripts/aniversario_dispatch.py
      ├─ Se META_ACCESS_TOKEN existe: chama Meta Cloud API
      ├─ Se não: modo dry-run (só reporta)
      ├─ Posta relatório no issue
      └─ Fecha issue
```

## Contatos úteis

- **Suporte Meta Business:** https://business.facebook.com/business/help
- **Docs Cloud API:** https://developers.facebook.com/docs/whatsapp/cloud-api
- **Status API:** https://developers.facebook.com/status/
- **Meta Business Inbox** (pra ver conversas):
  Business Manager → Ferramentas → **Caixa de entrada**
