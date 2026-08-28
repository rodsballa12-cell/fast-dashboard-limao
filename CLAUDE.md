# FAST Limão — contexto do repositório

Painel operacional da franquia FAST Escova Limão (São Paulo · Trinks id 276461),
publicado em GitHub Pages, mais o módulo de gestão de marketing.

Este arquivo é versionado: vale igual para sessões do Claude Code na web e na
máquina Windows.

## Estrutura

| Caminho | O que é |
|---|---|
| `index.html` | Painel completo. **Auto-gerado** pelo `publish_pages.py` do vault privado — não edite à mão |
| `assets/marketing.*` | Aba Marketing (CSS + JS). Editável — vive fora do HTML gerado |
| `scripts/github_refresh.py` | Puxa a API Trinks e escreve `data/dashboard_data.json` |
| `scripts/marketing_*.py` | Módulo de marketing (coleta, conteúdo, publicação) |
| `scripts/inject_marketing_tab.py` | Recoloca a aba Marketing no `index.html` gerado |
| `data/dashboard_data.json` | Snapshot Trinks — auto-gerado |
| `data/marketing_data.json` | Calendário, campanhas, métricas sociais, avaliações |

## Regras

- **Nunca edite `index.html` diretamente.** Ele é regenerado e a edição se perde.
  Mexeu na aba Marketing? Edite `assets/marketing.js` / `.css` e rode
  `python scripts/inject_marketing_tab.py`.
- **Publicação em rede social é sempre explícita.** Só `marketing_publicar.py
  --confirmar` manda algo para fora. Nenhum workflow publica sozinho.
- **Coletor não derruba refresh.** Falha do Google não pode impedir o Instagram de
  atualizar — erros vão para o campo `erros` do JSON e aparecem na aba.
- Idioma do produto: **português do Brasil**, inclusive em nomes de função e
  comentários, seguindo o código que já existe.

## Automação

| Workflow | Quando | O que faz |
|---|---|---|
| `refresh.yml` | 1×/h | Puxa Trinks → `dashboard_data.json` |
| `marketing.yml` | 6/6h + push em `index.html` | Coleta redes, reinjeta a aba; 08h BRT gera pauta com Claude |

O Task Scheduler do Windows roda o `publish_pages.py` de hora em hora e faz push —
isso dispara o `marketing.yml`, que reinjeta a aba.

## O que sincroniza entre a web e o Windows

Sincroniza (é git): todo o código, `data/`, workflows, este arquivo, `.claude/`.

**Não** sincroniza: segredos e tokens. Eles vivem em três lugares separados —
Secrets do Actions, configuração do environment em claude.ai/code, e `.env` local
no Windows. Detalhes em `docs/MARKETING_SETUP.md`.

## Rodar local

```bash
pip install -r scripts/requirements.txt
python scripts/marketing_refresh.py          # métricas
python scripts/marketing_refresh.py --conteudo   # + pauta do Claude
python -m http.server 8000                   # abre o painel em localhost:8000
```
