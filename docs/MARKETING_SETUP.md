# Gestor de Marketing — setup

O módulo funciona em três camadas independentes. Nada é obrigatório: sem
credencial nenhuma, a aba já serve como calendário editorial manual. Cada conexão
que você liga acrescenta um pedaço.

| Camada | O que acrescenta | Credenciais |
|---|---|---|
| Calendário | Planejamento, status, campanhas | nenhuma |
| Google Meu Negócio | Avaliações, impressões, rotas, publicar post | `GMN_*` |
| Instagram / Facebook | Seguidores, alcance, posts recentes, publicar | `META_*` |
| Pauta com Claude | Ideias de post e respostas a avaliações | `ANTHROPIC_API_KEY` |

---

## Onde colocar os segredos — os três lugares

Esta é a parte que confunde. **Não existe um lugar só.** Cada ambiente lê as suas
próprias variáveis:

| Onde roda | Onde configurar | Vale para |
|---|---|---|
| GitHub Actions (automático, 6/6h) | Settings → Secrets and variables → Actions → *New repository secret* | a automação que roda sozinha na nuvem |
| Claude Code na web | configuração do *environment* em claude.ai/code | sessões de chat na web |
| Windows (sua máquina) | arquivo `.env` na raiz do repo, ou variáveis de ambiente do usuário | quando você roda o script à mão |

O `.env` está no `.gitignore` — ele nunca vai para o GitHub, e é por isso que
precisa ser recriado em cada máquina. **Segredo não sincroniza via git; código
sincroniza.**

Modelo de `.env` para Windows:

```
GMN_CLIENT_ID=...
GMN_CLIENT_SECRET=...
GMN_REFRESH_TOKEN=...
META_ACCESS_TOKEN=...
META_IG_USER_ID=...
META_PAGE_ID=...
ANTHROPIC_API_KEY=...
```

---

## 1. Google Meu Negócio

A API do Google Business Profile exige aprovação — **peça primeiro**, porque a
liberação leva alguns dias.

1. **Pedir acesso à API.** Preencha o formulário em
   <https://developers.google.com/my-business/content/prereqs> ("Request access").
   Use a conta Google que já administra a ficha da FAST Limão.
2. **Criar o projeto** em <https://console.cloud.google.com> e ativar as APIs:
   - My Business Account Management API
   - My Business Business Information API
   - Business Profile Performance API
   - Google My Business API (a v4, usada para avaliações e posts)
3. **Criar credencial OAuth 2.0** → tipo *Desktop app*. Guarde o *client id* e o
   *client secret*.
4. **Gerar o refresh token** no OAuth Playground
   (<https://developers.google.com/oauthplayground>):
   - engrenagem ⚙ → marque *Use your own OAuth credentials* → cole id e secret
   - escopo: `https://www.googleapis.com/auth/business.manage`
   - autorize com a conta que administra a ficha → *Exchange authorization code for tokens*
   - copie o **refresh token** (o access token expira em 1h e não serve aqui)
5. Preencha `GMN_CLIENT_ID`, `GMN_CLIENT_SECRET`, `GMN_REFRESH_TOKEN`.

`GMN_LOCATION_ID` e `GMN_ACCOUNT_ID` são opcionais — sem eles, o script descobre
sozinho a primeira ficha da conta. Preencha se você administra mais de uma unidade.

Teste:

```bash
python scripts/marketing_gmn.py
```

## 2. Instagram e Facebook

Exige uma conta Instagram **Business** (não Creator, não pessoal) vinculada a uma
Página do Facebook.

1. Crie um app em <https://developers.facebook.com/apps> → tipo *Business*.
2. Adicione os produtos **Instagram Graph API** e **Facebook Login**.
3. No Graph API Explorer, gere um token de usuário com as permissões:
   `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`,
   `instagram_basic`, `instagram_manage_insights`, `instagram_content_publish`,
   `business_management`.
4. **Troque por um token de longa duração** (60 dias) — o token curto expira em 1h:
   ```
   GET https://graph.facebook.com/v21.0/oauth/access_token
       ?grant_type=fb_exchange_token
       &client_id=SEU_APP_ID
       &client_secret=SEU_APP_SECRET
       &fb_exchange_token=TOKEN_CURTO
   ```
5. **Pegue o token da Página** (esse não expira, desde que venha de um token longo):
   `GET /me/accounts` → campo `access_token` da Página da FAST. É esse que vai em
   `META_ACCESS_TOKEN`.
6. **Descubra o id do Instagram:**
   `GET /{page_id}?fields=instagram_business_account` → `META_IG_USER_ID`.

Publicar no Instagram exige app em modo *Live* com revisão aprovada para
`instagram_content_publish`. Ler métricas funciona em modo desenvolvimento.

> Se a Graph API responder *"Unsupported get request"*, a versão da API expirou.
> Configure `META_API_VERSION` (ex.: `v23.0`) — o padrão é `v21.0`.

Teste:

```bash
python scripts/marketing_meta.py
```

## 3. Pauta com Claude

1. Crie uma chave em <https://console.anthropic.com> → API Keys.
2. Configure `ANTHROPIC_API_KEY` nos três lugares que você usa.

O gerador usa **Claude Opus 5** e sempre parte dos números reais do Trinks —
serviço mais vendido, horários ociosos, distância da meta do mês. Cada sugestão
traz o campo `porque`, com o dado que motivou a pauta.

```bash
python scripts/marketing_refresh.py --conteudo
```

---

## Uso no dia a dia

```bash
# atualizar métricas de todos os canais
python scripts/marketing_refresh.py

# atualizar + gerar pauta dos próximos 7 dias
python scripts/marketing_refresh.py --conteudo

# ver o que seria publicado (simulação, não publica nada)
python scripts/marketing_publicar.py --aprovados

# publicar de verdade
python scripts/marketing_publicar.py --aprovados --confirmar

# responder todas as avaliações que já têm rascunho
python scripts/marketing_publicar.py --responder-todas --confirmar
```

**Publicação nunca é automática.** O Actions só coleta métricas e gera sugestões;
mandar para fora exige você rodando `marketing_publicar.py --confirmar`.

## Aprovar uma pauta

As sugestões do Claude ficam em `conteudo_sugerido`. Para uma virar publicação de
verdade, mova o item para `calendario` em `data/marketing_data.json` e coloque
`"status": "aprovado"`. Instagram exige também `"midia"` com a URL pública da
imagem (o Graph API baixa a imagem da URL — não aceita upload de arquivo local).

Formato de um item do calendário:

```json
{
  "id": "2026-08-22-ig",
  "data": "2026-08-22",
  "canal": "instagram",
  "tipo": "feed",
  "titulo": "Escova lisa em 40 minutos",
  "legenda": "texto do post…",
  "hashtags": ["#fastescova", "#limaosp"],
  "cta": "Agende pelo link da bio",
  "midia": "https://.../foto.jpg",
  "status": "aprovado"
}
```

Status possíveis: `ideia` → `rascunho` → `aprovado` → `agendado` → `publicado`.

## Por que existe o `inject_marketing_tab.py`

O `index.html` é regenerado inteiro pelo `publish_pages.py` (vault do Rodrigo) a
cada refresh. Uma aba escrita à mão dentro dele seria apagada na hora seguinte.

Por isso a aba vive em `assets/marketing.css` + `assets/marketing.js`, e o injetor
recoloca as 13 linhas de ligação no HTML gerado. Ele é idempotente: rodar uma ou
dez vezes dá exatamente o mesmo arquivo, e `limpar()` devolve o HTML original byte
a byte.

O Actions reinjeta a cada push que toque o `index.html`, então a aba se recupera
sozinha. Para não depender disso, acrescente ao fim do `publish_pages.py`:

```python
subprocess.run([sys.executable, "scripts/inject_marketing_tab.py"], cwd=REPO_DIR)
```

Para checar sem escrever (útil em CI): `python scripts/inject_marketing_tab.py --check`.
