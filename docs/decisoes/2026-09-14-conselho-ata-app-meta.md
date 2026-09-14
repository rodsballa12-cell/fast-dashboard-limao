# Conselho 14/09 — descoberta App Meta e decisões da reunião

**Data:** 2026-09-14 · **Quem decidiu:** Rodrigo
**Departamentos ouvidos:** Operação, Financeiro, Marketing, Relacionamento, Pessoas, Memória

## Contexto

Reunião ordinária do Conselho FAST Limão com dados reais das duas unidades
(Escova operacional; Spa em estado zero — sem Trinks ID configurado).

## Cadeia causal A — a descoberta que justifica o conselho existir

Marketing declarou 🔴 por HTTP 400 no token da Meta Graph API.
Relacionamento declarou 🔴 por WhatsApp bloqueado (App Meta apagado).

**Esses são o mesmo problema, não dois.**

O token Meta e o WhatsApp Business ambos dependem do mesmo App Meta no
Business Manager. Quando o App foi apagado, o token foi invalidado (HTTP 400)
e o canal WA foi derrubado. Uma única ação — recriar e reconectar o App Meta
— resolve os dois 🔴 simultaneamente.

Sem o cruzamento entre os pareceres de Marketing e Relacionamento, os dois
bloqueios pareceriam problemas separados exigindo ações separadas.

## Outros fatos da reunião

- DRE com 9 dias de defasagem (gerado 05/09); extrato Stone com 115,9h (5 dias).
  Os dois atrasos são independentes e se somam silenciosamente.
- `stone.nao_conciliado.orfaos_trinks_v = R$ 1.599` (15 vendas Trinks sem par
  na Stone) — não é perda confirmada, mas cega a conciliação enquanto o extrato
  Stone estiver defasado.
- Comissão real 37,4% vs premissa DRE de 32% → diferença de R$ 2.663/mês que
  invalida a análise de margem sem reconciliação com o cargo Pessoas.
- Spa: zero Trinks ID — nenhum dado operacional disponível. Bloqueio técnico,
  não ausência de negócio.

## Decisões

1. **Reconectar App Meta** — desbloqueio de Marketing (token) + Relacionamento
   (WhatsApp) em uma única ação. Executa: Rodrigo no Meta Business Manager.
   Revisão: após reconexão confirmada.

2. **Apurar comissão real** — Pessoas e Financeiro precisam reconciliar o gap
   37,4% × 32% antes da próxima análise de margem. A DRE atual usa premissa
   errada. Executa: Rodrigo revisa regras de comissão no Trinks.

3. **Cadastrar Trinks ID do Spa** — sem ele, Operação e Financeiro do Spa são
   cegos. Executa: Rodrigo localiza o `estabelecimentoId` no painel Trinks Spa.

## Alternativas descartadas

Tratar Marketing 🔴 e Relacionamento 🔴 como bloqueios separados — exigiria
dois fluxos de diagnóstico e custaria mais tempo. O cruzamento mostrou que
a causa-raiz é única.

## O que esperamos

Após reconectar o App Meta:
- Meta Ads voltam a reportar (HTTP 400 resolvido)
- Canal WhatsApp Business reativado
- Ambos os departamentos saem de 🔴 na próxima reunião

## Revisar em

2026-10-14 — verificar se os três bloqueios foram resolvidos e se a margem
foi recalculada com comissão real.

## Resultado

_(em branco até a revisão)_
