---
titulo: "Plano técnico — de 1 loja para 600"
projeto: Franquia_FAST_Limao
tipo: plano-tecnico
status: rascunho-v1
criado: 2026-09-08
tags: [fast, arquitetura, multi-tenant, trinks, lgpd]
---

# Plano técnico — de 1 loja para 600

## 1. A boa notícia: metade do caminho já está andada

O painel foi construído, sem querer, de um jeito que ajuda. A loja não está escrita
no código — ela entra por fora:

| Como a loja é identificada hoje | Onde |
|---|---|
| Chave da API e ID do estabelecimento | Variáveis de ambiente (`TRINKS_API_KEY`, `TRINKS_ESTABELECIMENTO_ID`) |
| Nome, endereço, metas, cadeiras, palavras-chave de serviço | `data/config.json` |
| Dados | `data/*.json`, gerados a cada atualização |

Fiz a varredura: o nome "Limão" aparece **três vezes** em 5.500 linhas de código, e as
três são texto de exibição ou valor padrão — nenhuma é regra de negócio. Na prática,
**trocar as duas variáveis de ambiente e o `config.json` já gera o painel de outra loja.**

Isso significa que o trabalho pela frente não é reescrever o produto. É construir a
**embalagem multi-loja** em volta de um motor que já funciona.

## 2. Os sete gargalos reais

### 2.1 · BLOQUEADOR — o painel é público
`https://rodsballa12-cell.github.io/fast-dashboard-limao/` é uma URL aberta. Quem tiver
o link vê DRE, saldo em caixa, extrato Stone e a base de clientes com telefone.

Para a sua loja isso é um risco assumido por você. Para a loja de outro franqueado é
**dado pessoal de terceiro exposto por você** — LGPD, artigo 46. É o único item que
precisa estar resolvido **antes** da segunda loja entrar, inclusive num piloto gratuito.

*Correção barata (dias, não semanas):* colocar o painel atrás do Cloudflare Access
com lista de e-mails autorizados, ou trocar o GitHub Pages por hospedagem com senha.

### 2.2 · Um repositório por loja não escala
Hoje: 1 repo + 2 segredos + 5 workflows por loja. Em 600 lojas isso vira 600
repositórios, 1.200 segredos e — o pior — **toda correção de bug vira 600 deploys.**

### 2.3 · Cota da API Trinks
O plano padrão dá 10.000 requisições/mês por estabelecimento. Cada atualização custa
~27 requisições porque o script **repagina o ano inteiro** de agendamentos e transações
toda vez. Já houve um dia (01/09) que queimou 1.007 requisições — 10% da cota mensal.

Hoje isso está contido por um teto de ritmo no workflow, que é um curativo bom. Em
produto, precisa virar **ingestão incremental** (buscar só o que mudou desde a última
vez) e, em paralelo, uma **conversa comercial com a Trinks** — 600 lojas puxando dados
é um volume que justifica contrato de parceria, não plano de varejo.

*A ser confirmado com a Trinks:* a cota é por estabelecimento ou por conta? A resposta
muda o custo unitário do produto e está na lista de "8 números para validar".

### 2.4 · O financeiro depende de você
`gerar_financeiro.py` lê um Excel em `C:\Users\rods_\OneDrive\...` e o Stone entra por
um CSV baixado à mão. Nenhum dos dois existe na loja do outro franqueado.

Três saídas, em ordem de esforço: (a) o franqueado sobe o CSV/planilha por uma tela;
(b) modelo de DRE padronizado da rede preenchido no próprio produto; (c) integração
direta com a adquirente. Comece por (a) — resolve 80% com 10% do trabalho.

### 2.5 · WhatsApp em escala precisa de BSP
Um número + um template aprovado por loja. Em 600 lojas, o cadastro manual na Meta é
inviável: precisa de um **BSP** (Twilio, Zenvia, 360dialog, Gupshup) com Embedded
Signup — o franqueado conecta o número dele em 3 cliques.

Bom sinal: as travas de segurança que evitam desastre em escala (kill switch, opt-out,
cooldown, teto diário, janela de horário) **já estão escritas** em `campanhas_wa.py`.

### 2.6 · A configuração da loja é um JSON editado à mão
Palavras-chave de serviço, número de cadeiras, metas por recepcionista. Nenhum
franqueado vai editar JSON. Precisa de tela de configuração — com **padrões da rede**
já preenchidos, que é justamente o que a franqueadora agrega.

### 2.7 · Não existe cadastro, login, cobrança nem suporte
O produto hoje não tem porta de entrada. Isso é o MVP da Fase 1.

## 3. Arquitetura alvo

```
   Trinks API          Stone/CSV        Meta (BSP)      HubSpot
       │                   │                │              │
       └──────────┬────────┴────────────────┴──────────────┘
                  ▼
        ┌─────────────────────┐
        │  Fila de ingestão   │  1 job por loja, agendado
        │  (motor Python que  │  ~5x/dia, com controle de cota
        │   já existe hoje)   │
        └──────────┬──────────┘
                   ▼
        ┌─────────────────────┐
        │ Banco multi-loja    │  toda tabela tem loja_id
        │ (Postgres)          │  isolamento por linha
        └──────────┬──────────┘
                   ▼
     ┌─────────────┴──────────────┐
     ▼                            ▼
┌──────────────┐          ┌──────────────────┐
│ Painel LOJA  │          │ Painel REDE      │
│ (franqueado) │          │ (franqueadora)   │
│ o que existe │          │ ranking, bench-  │
│ hoje + login │          │ mark, alertas    │
└──────────────┘          └──────────────────┘
```

Duas decisões que economizam meses:

- **Não reescreva o motor.** O Python de análise vira uma biblioteca chamada por um
  worker, recebendo `loja_id` como parâmetro. É refatoração, não reconstrução.
- **O `index.html` de 280 KB vira o painel da loja quase como está**, alimentado por
  API em vez de arquivo JSON. Reescrever a interface do zero é a armadilha clássica
  que mata projetos assim.

## 4. Fases

| Fase | Duração | Entrega | Lojas | Marco comercial |
|---|---|---|---|---|
| **0 · Piloto** | 3–4 sem | Fechar o buraco de privacidade + 3 a 5 lojas no modelo atual, configuradas por você | 5 | Prova de valor com dados reais de outras lojas |
| **1 · MVP** | 8–10 sem | Login, banco multi-loja, onboarding da chave Trinks pelo próprio franqueado, painel da loja | 20–30 | Primeiras lojas pagando |
| **2 · Rede** | 6–8 sem | Painel da franqueadora (ranking e benchmark), financeiro sem Excel, cobrança | 100+ | Contrato master com a franqueadora |
| **3 · Escala** | 8–12 sem | WhatsApp via BSP, campanhas da rede, ingestão incremental, API | 600 | Produto de prateleira do ecossistema |

**Total: 6 a 9 meses** até estar pronto para os 600.

A Fase 0 é a mais importante e a mais barata. Cinco lojas com perfis diferentes (loja
madura, loja nova, shopping, rua) respondem as perguntas que nenhum plano responde:
o insight que serve para o Limão serve para as outras? Qual métrica cada franqueado
olha primeiro? Quanto tempo leva o onboarding?

## 5. Como executar sem ser programador

Você não vai escrever esse código — nem precisa. Três formatos, do mais barato ao
mais rápido:

1. **Você + Claude Code, como fez até aqui.** Funciona para as Fases 0 e 1. O limite
   aparece quando surge banco de dados, login e cobrança: não é a escrita do código
   que pesa, é a responsabilidade sobre dado de terceiro em produção.
2. **Você + um dev sênior parceiro** (meio período, R$ 12–20 mil/mês). O melhor
   custo-benefício. Você segue como dono do produto e das regras de negócio — que é
   onde está o valor que ninguém copia.
3. **Software house** (R$ 150–300 mil pelo projeto). Mais rápido, mais caro, e você
   fica dependente para cada mudança.

Recomendação: **2**, entrando na Fase 1. Fase 0 você faz sozinho comigo.
