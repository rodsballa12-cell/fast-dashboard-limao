# 2026-10-21 · **SULTS: leitura diária de todos os módulos, só das lojas Limão**

**Data:** 2026-10-21 · **Origem:** conversa com o Rodrigo na sessão do PC
**Status:** APROVADA e EXECUTADA em 21/10/2026

## Contexto

Até aqui o token do SULTS só podia ler **Comunicados**, porque ele também
consegue escrever em Compras e Chamados. O Rodrigo pediu uma varredura
completa e depois liberou o acesso ("acesso total"). A varredura achou chamados
em que a franqueadora espera resposta da loja e que nenhum painel mostrava. No
Spa, por exemplo, a lista de 6 pendências do projeto (14/10, cobrada em 20/10).

## Decisão

- `scripts/sults_leitura.py` lê Chamados, Compras, Comunicados e Checklists das
  duas lojas, **só com GET**, a cada rodada da agenda do PC (no máximo a cada 3 h).
- O token enxerga a **rede inteira** (489 unidades na Escova, 28 no Spa). O script
  filtra pela empresa Limão (Escova 683, Spa 95) e não grava nada de outra unidade.
- O resultado fica em `OneDrive\Franquia - FAST\Claude\SULTS\sults_limao.json`,
  **fora do repositório** (que é público).
- Os agentes leem conforme `.claude/skills/SULTS.md`. Nenhum agente responde,
  aceita ou fecha nada no SULTS.

## Alternativas descartadas

- Gravar em `data/`: o repositório é público e os chamados trazem contrato e jurídico.
- Guardar o bruto da rede para comparar com outras unidades: são dados de outros
  franqueados. O bruto da varredura foi apagado no mesmo dia.

## O que não dá para ler

Projetos, Implantação, Expansão e a lista de colaboradores pedem o token v1, que
não existe. A biblioteca do aplicativo Marketing continua sem API.

## Revisar em

2026-11-04: os briefings estão citando os chamados urgentes? Algum alarme
falso (chamado velho, pedido "Aguardando" que já foi entregue)?

## Resultado

_(em branco até a revisão)_
