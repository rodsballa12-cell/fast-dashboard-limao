# FAST Limão · Painel Trinks

Dashboard operacional da franquia FAST Escova Limão (SP · Trinks id 276461).

**Publicado em:** https://rodsballa12-cell.github.io/fast-dashboard-limao/

## Atualização automática
- Task Scheduler local (Rodrigo Garcia) roda `publish_pages.py` de 1h em 1h
- Script puxa dados frescos da API Trinks (via `trinks_delta.py` do vault)
- Regenera `index.html` com KPIs atualizados
- `git push` → GitHub Pages atualiza em ~30s

## Estrutura
- `index.html` — dashboard completo (auto-gerado)
- `data/dashboard_data.json` — snapshot dos dados (auto-gerado)
- `assets/marketing.*` — aba Marketing (CSS + JS, editáveis à mão)
- `data/marketing_data.json` — calendário editorial, campanhas, métricas sociais
- `scripts/marketing_*.py` — coleta, geração de pauta e publicação

## Gestor de Marketing
Aba **📣 Marketing** no painel: calendário editorial, avaliações do Google,
métricas de Instagram/Facebook e pauta gerada pelo Claude a partir dos números
reais do Trinks.

- Métricas atualizam de 6 em 6h via `.github/workflows/marketing.yml`
- Pauta do Claude é gerada 1×/dia, às 08h de Brasília
- Publicar é sempre manual: `python scripts/marketing_publicar.py --aprovados --confirmar`
- Setup das credenciais: [`docs/MARKETING_SETUP.md`](docs/MARKETING_SETUP.md)

Funciona sem nenhuma credencial — nesse modo a aba é um calendário editorial manual.

## Fonte
Código de geração e integração vive no vault privado do Rodrigo:
`02-PROJETOS/Franquia_FAST_Limao/62_Integracao_Trinks/`
