---
agente: marketing
data: 2026-09-29
hora: 08:00
gerado_por: tarefa agendada
---

# marketing · 2026-09-29 às 08:00

> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.
## Antes do parecer — um bloqueio que não é de marketing, mas trava a leitura

O repositório está no meio de um **rebase interativo** (`rebasing branch 'main' on fd437f1`), com **12 arquivos em conflito** (`UU`/`AA`) — entre eles `data/dashboard_data.json`, `data/financeiro.json` (raiz), o consolidado inteiro e vários caches (clientes, profissionais, serviços). Os dois JSONs de mídia que eu li (`data/midias_sociais.json` e `data/spa/midias_sociais.json`) **não** estão na lista de conflito, então o que trago abaixo é confiável — mas não sei se você já está resolvendo isso na mesma sessão do PC. Não mexi em nada (rebase é operação arriscada e as instruções do projeto proíbem alterar dado sem você mandar). Se não for você resolvendo agora, precisa de atenção antes de qualquer outro cargo ler dado do painel.

## Marketing — leitura de saúde (Escova + Spa)

**FATOS**

- **Frescor**: Escova gerada 28/09 08:15 (janela "hoje" = 28/09); Spa gerada 27/09 12:04. Hoje é 29/09 — os dois passaram de 24h sem refresh novo. O último commit de mídia no git (`93f43b7`) também é de 28/09 08:15; não houve outro depois. Vale confirmar se o refresh diário rodou hoje ou travou.
- **Entrega**: sem dia zerado com campanha ativa em nenhuma das duas contas nos últimos 30 dias — não é o caso de agosto que custou R$ 480.
- **Escova, CPA acima da meta é tendência, não ruído**: R$ 9,21 nos últimos 30d vs meta R$ 8,00 (~15% acima), e bate com o MTD de setembro (R$ 9,24) — isso já está registrado como P1 no painel (frequência 2,71 em zona de atenção, campanha `[VAGA ESCOVISTA] 100926` reservando R$ 6/dia há 17 dias sem entregar nada).
- **Escova, Instagram parado**: 8 dias sem postar (último post 20/09). É a origem do alcance orgânico despencando no fim da série diária (de ~7-9k/dia em 22-24/09 para 1.198 em 27/09).
- **Spa, CPA subindo rápido e ainda não está no radar curado**: a média de 30d (R$ 5,55) esconde uma escalada real — R$ 32,60 (25/09) → R$ 25,55 (26/09) → R$ 41,59 (27/09), contra menos de R$ 10 nas primeiras semanas. `alertas_topo` do Spa está vazio, ou seja ninguém ainda registrou isso.
- **ROAS medido segue só de agosto** (4,72x, atribuição real via `comoNosConheceu`, 75,8% de cobertura) — setembro ainda não fecha mês para ter leitura própria; Spa não tem funil ainda (aguarda campanha decolar + Trinks do Spa subir).

**RISCO**
- Se o CPA do Spa mantiver a trajetória dos últimos 3 dias, o custo por conversa deste mês pode passar da meta (R$ 25) rapidamente — hoje ainda parece bom só por causa da média acumulada dos dias baratos de pré-abertura.
- Silêncio de 8 dias no Instagram da Escova reduz o que alimenta reach orgânico logo na semana em que o CPA pago já está acima da meta — os dois problemas se somam.

**NÃO VEJO**
- Se o refresh de mídia rodou hoje (29/09) e falhou, ou se simplesmente ainda não rodou — não tenho acesso a log de execução daqui.
- Conversão real do Spa (Trinks do Spa ainda não alimenta o funil) — qualquer leitura de ROAS do Spa seria chute.

**DECISÃO** — sugiro, mas quem bate o martelo é você:
1. Confirmar se o rebase é intencional/em andamento por você, antes de qualquer outro cargo confiar no painel.
2. Postar algo na Escova ainda hoje (8 dias parado é a causa mais provável do reach caindo).
3. Olhar os 3 últimos dias de campanha do Spa antes que o CPA vire tendência de mês, como já aconteceu com a Escova.
