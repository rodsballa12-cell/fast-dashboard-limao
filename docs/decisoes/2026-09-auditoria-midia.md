# Auditoria de mídia · setembro/2026

**Data:** 15/09/2026 · **Fonte:** `data/midias_sociais.json` e
`data/spa/midias_sociais.json`, gerados em 14/09 às 18h3x (14,6h antes desta
leitura — dentro da janela de 24h, pipeline funcionando).

---

## Frescor e estado do pipeline

| Conta | Gerado em | Idade | Entrega zerada com gasto |
|---|---|---|---|
| Escova | 14/09 18h35 | 14,6h | nenhuma |
| Spa | 14/09 18h33 | 14,7h | nenhuma |

🔴 **Os dois arquivos carregam erro de token registrado:**
`HTTP 400 · "Error validating access token: The session has been invalidated
because the user changed their password or Facebook has changed the session
for security reasons."`

Os números são do último pull bem-sucedido. **Enquanto o `META_ACCESS_TOKEN`
não for renovado, não é possível medir nem alterar nada** — nem pausar uma
campanha ruim.

---

## Escova · o agregado esconde o problema

**R$ 2.506,27 em 30 dias · 15 campanhas ativas · 363 conversas · CPA médio
R$ 6,90** contra meta de R$ 8,00.

No agregado, está dentro. Aberto por campanha, não está.

### Benchmarks

| Par | Meta | Atual | Leitura |
|---|---|---|---|
| CPA mensagem | R$ 8,00 | **R$ 6,90** | ✅ dentro |
| CTR | 1,50% | **1,46%** | 🟡 marginalmente abaixo |
| CPM | R$ 12,00 | **R$ 9,99** | ✅ leilão barato |
| Frequência | alerta "ok" | 2,39 | ✅ no agregado |

MTD setembro: CPA R$ 7,89 — piorou contra os 30 dias, ainda dentro da meta.

### 🔴 MATAR · R$ 858,76 em campanhas que não entregam

| Campanha | Gasto 30d | CPA | Freq | CTR | Conversas |
|---|---|---|---|---|---|
| [ENGAJAMENTO][MSG][COMBOS 1,2,3] 210826 | R$ 221,34 | R$ 13,83 | **2,55** | 1,53% | 16 |
| [ENGAJAMENTO][MSG][COMBOS 4 E 5] 210826 | R$ 219,01 | R$ 14,60 | **2,64** | 1,38% | 15 |
| Post impulsionado "É OFICIAL" | R$ 150,87 | R$ 21,55 | 1,65 | 2,40% | 7 |
| [RECONHECIMENTO][BRANDING] 260826 | R$ 80,40 | R$ 80,40 | 1,60 | **0,05%** | 1 |
| [RECONHECIMENTO][BRANDING] 110826 | R$ 106,17 | — | — | — | **0** |
| [ENGAJAMENTO][DISTRIBUIÇÃO] 010926 | R$ 80,97 | — | — | — | **0** |
| **Total** | **R$ 858,76** | | | | **39** |

**É 34% da verba comprando 11% das conversas.** Ao CPA das campanhas
saudáveis (R$ 6,90), esses R$ 858 teriam comprado **124 conversas** em vez de
39 — uma diferença de 85 conversas por mês.

**Diagnóstico das duas [COMBOS]:** são as de **maior frequência** (2,55 e
2,64) e **menor CTR** (1,53% e 1,38%) da conta inteira. Isso não é oscilação
— é público saturado com criativo cansado. Rodam desde 21/08.

**Diagnóstico da [BRANDING] 260826:** CTR de **0,05%** é um clique a cada
2.000 impressões. O anúncio não interessa a ninguém.

### ✅ ESCALAR

| Campanha | Gasto | CPA | CTR |
|---|---|---|---|
| [ENGAJAMENTO][MSG][PLÁSTICA] 040826 | R$ 352,90 | **R$ 3,56** | **3,80%** |

CPA a **45% da meta** e o melhor CTR da conta. É a campanha que deveria estar
levando a verba das que vão morrer.

### Observação de marca

As campanhas ainda se chamam **[COMBOS]**. A regra de vocabulário mudou em
15/09 — é "pacote". Nome de campanha é interno, mas **se o criativo repete a
palavra, está fora da regra nova.** Conferir antes de qualquer relançamento.

---

## Spa · a conta que abre em 10 dias

**R$ 209,87 em 30 dias**, sendo:

| Tipo | Gasto | % |
|---|---|---|
| Vagas (massoterapeuta, recepção) | R$ 133,45 | 64% |
| **Comercial** ([COMBO INAUG]) | **R$ 76,42** | **36%** |

### O CPA de R$ 1,60 é ilusão de leitura

O painel mostra CPA médio de R$ 1,60 — quatro vezes melhor que a Escova.
**Das 131 conversas, 98 são de anúncio de vaga.** A única campanha comercial
tem CPA de **R$ 7,64**, contra meta de R$ 25 para a conta nova.

Ninguém deve planejar verba com o R$ 1,60.

### A inversão

| | Escova | Spa |
|---|---|---|
| Status | madura, 2 meses | **abre em 10 dias** |
| Verba comercial 30d | R$ 2.506 | **R$ 76** |
| Desperdício identificado | R$ 859 | — |

**A loja que precisa de tração tem R$ 76. A que já roda queima R$ 859 em
campanha que não converte.**

---

## Recomendações · preparadas, não executadas

Ordem de impacto:

**1 · Renovar o `META_ACCESS_TOKEN`** — sem isso nada abaixo é executável, nem
pausar. Custo: zero. Bloqueia: tudo.

**2 · Matar as 6 campanhas listadas** — libera **R$ 858,76/30d**, ou
**R$ 28,60/dia**, sem perder nada que esteja convertendo.

**3 · Levar a verba liberada para o Spa antes de 25/09** — ao CPA comercial
atual do Spa (R$ 7,64), R$ 28,60/dia compram ~3,7 conversas/dia. Da
aprovação até a abertura, cerca de **37 conversas** com quem ainda não conhece
a loja.

**4 · Escalar [PLÁSTICA]** — CPA R$ 3,56. Dobrar a verba dela ainda a deixaria
abaixo da meta de R$ 8.

**5 · Consolidar as 15 campanhas da Escova** — R$ 2.506 divididos por 15 dá
média de R$ 167 por campanha em 30 dias, ou R$ 5,57/dia cada. O algoritmo da
Meta não sai da fase de aprendizado com esse volume por conjunto.

---

## Alçada

Nada foi executado. Para criar ou alterar campanha, a regra registrada em
`docs/decisoes/2026-09-14-alçada-campanha-marketing.md` exige, na mesma
sessão, uma mensagem do Rodrigo com os três elementos: **"aprovado"** (ou
"criar campanha" / "publicar"), **o nome da campanha** e **o valor diário**.

---

## O que este parecer não enxerga

**Conversão real.** `funil_conversao` cruza mídia com Trinks por atribuição
**estimada**, não medida. Nenhum ROAS aqui é afirmado como medido. O elo que
falta é o campo `comoNosConheceu` na recepção — e, no Spa, nem isso existe
ainda, porque a unidade não tem API da Trinks.

**Portanto:** todos os números acima são de mídia, não de caixa. Uma conversa
barata não é uma cliente. Quem responde por conversão é a Operação.
