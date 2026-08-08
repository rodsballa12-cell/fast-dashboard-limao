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

## Fonte
Código de geração e integração vive no vault privado do Rodrigo:
`02-PROJETOS/Franquia_FAST_Limao/62_Integracao_Trinks/`
