# Mapa do painel — quem responde por cada card

O painel tem 6 abas e ~50 cards. Este arquivo diz **de quem é cada um**, para
que nenhum fique órfão e nenhum tenha dois donos.

Fonte da verdade única: se um card mudar de dono, muda **aqui**, não na ficha
de cada cargo.

🔗 https://rodsballa12-cell.github.io/fast-dashboard-limao/

---

## 🏢 Operação — *"a casa está cheia?"*

**Abas:** Painel (inteira)

| Card | O que vigiar |
|---|---|
| `renderKPIs` · `renderMetaProgress` · `renderAncora` | ritmo contra a meta do dia |
| `renderPaceIntraday` | o dia está atrasado agora, não no fim |
| `renderDiario` · `renderSemanal` · `renderMensal` · `renderAnual` | tendência por janela |
| `renderBarsDow` · `renderBarsHora` · `renderHeatmapMeta` | onde a agenda tem buraco |
| `renderUtilizacao` | cadeira parada é receita perdida |
| `renderCategoriaNativa` · `renderCategoriasMeta` · `renderCategTile` | mix de serviço contra o share oficial |
| `renderComparacaoSemana` | esta semana contra a anterior |

---

## 💰 Financeiro — *"sobrou quanto?"*

**Abas:** Financeiro, Stone

| Card | O que vigiar |
|---|---|
| `renderFinanceiro` | DRE, ponto de equilíbrio |
| `renderRentabilidade` | margem por linha |
| `renderStone` · `renderMeiosPagamento` · `renderParcelas` | recebível, taxa, prazo |
| `renderTicketMeta` | ticket médio — **fronteira com Operação**: o número é dos dois, a leitura de margem é sua |

---

## 📣 Marketing — *"o dinheiro virou cliente?"*

**Abas:** Mídias (inteira)

| Card | O que vigiar |
|---|---|
| `renderMidias` | gasto, CPA, CTR, frequência |
| `renderMidiasCanalAquisicao` | de onde a cliente veio |
| `renderMidiasGoogleDow` | busca por dia da semana |
| `renderMidiasPlanoAcao` | o que fazer com a verba |

---

## 💬 Relacionamento — *"o cliente volta?"*

**Abas:** Clientes (inteira)

| Card | O que vigiar |
|---|---|
| `renderChurn` | quem sumiu — **tem botão 📱 que abre a conversa** |
| `renderAniversariantes` | aniversário do dia, com mensagem sugerida e 📱 |
| `renderTopClientes` · `renderSegmentacao` | onde está o LTV |
| `renderNovosRecorr` | a base cresce ou só gira |
| `renderCrossSell` | quem só faz um serviço |
| `renderClientes` · `renderClientesSnapshot` · `renderClientesCadastro` | saúde do cadastro |

**O canal é o painel, não um robô.** Decidido em 14/09/2026: o botão 📱 abre a
conversa no WhatsApp de quem atende, com o número que a cliente conhece. Ver
`docs/decisoes/`.

---

## 👥 Pessoas — *"a equipe dá conta?"*

**Cards dentro das abas Painel e Auditoria**

| Card | O que vigiar |
|---|---|
| `renderRankingProf` · `renderProfExecutor` | produção por profissional |
| `renderComissoes` · `renderComissoesPer` · `renderProfComissoes` | comissão — **hoje sem regra no Trinks** |

---

## ⚖️ Conselho — o que ninguém deve ter sozinho

**Aba:** Auditoria

| Card | Por que é da mesa |
|---|---|
| `renderAuditoria` | cancelamento cruza Operação, Pessoas e Financeiro |
| `renderDesvioTabela` | preço fora da tabela: Operação vê, Financeiro sente, ninguém autoriza |
| `renderObsAlertas` · `renderInsights` | alertas que atravessam departamento |

---

## Infra — de ninguém

`renderTable` · `renderScaffoldingBanner` · `renderPlaceholderUnidade` ·
`renderAvisoBase` · `renderBarsDia` — componentes de desenho, não de negócio.

---

## Regra de fronteira

Card com dois interessados tem **um dono e um leitor**. O dono responde pelo
número; o leitor usa o número e devolve o que viu pelo campo `NÃO VEJO` do
`PROTOCOLO.md`. Ninguém corrige card dos outros por conta própria.
