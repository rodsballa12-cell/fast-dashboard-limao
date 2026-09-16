# Plano de comissão da recepção entra no painel

**Data:** 16/09/2026 · **Fonte:** tabela da franqueadora, informada pelo Rodrigo
**Revisar em:** 01/11/2026 (depois de dois fechamentos de mês)

## A tabela

| Categoria | Faturamento | Comissão | Bônus | Total |
|---|---:|---:|---:|---:|
| Pacotes | R$ 8.000 | R$ 400 (5%) | R$ 250 | R$ 650 |
| Fast Retoque | R$ 5.800 | R$ 290 (5%) | R$ 200 | R$ 490 |
| Produtos | R$ 3.000 | R$ 300 (10%) | — | R$ 300 |
| **TOTAL** | **R$ 16.800** | **R$ 990** | **R$ 450** | **R$ 1.440** |

Bônus é **tudo-ou-nada** por categoria: sai ao bater a meta, não é proporcional.

## O que foi decidido

Gravar o plano em `data/config.json > plano_comissao_recepcao` e renderizar
`💰 Comissão da recepção` na aba Mês — só nela, porque comissão é de mês fechado
e mostrar "bônus proporcional da semana" inventaria uma regra que não existe.

## Os dois limites, ditos em vez de disfarçados

**1. Fast Retoque não é atribuível por pessoa.** É serviço: o Trinks grava
`idProfissionalQueRealizouServico` — quem executou, não quem vendeu. São
**R$ 490 dos R$ 1.440 (34%)** que ficam fora do cálculo individual. O card mostra
o retoque como linha da loja, marcada "sem dono". Ratear no chute seria pior que
não mostrar: pagaria alguém errado com aparência de precisão.

**2. O faturamento da tabela não bate com o config.**

| | pacotes | retoque | produtos | total |
|---|---:|---:|---:|---:|
| `por_recepcionista_mensal` (config) | 7.200 | 4.200 | 1.800 | **13.200** |
| Tabela da franqueadora | 8.000 | 5.800 | 3.000 | **16.800** |

Se a tabela for **por recepcionista**, o balcão da loja vira R$ 33.600 e sobram
R$ 26.400 para serviços gerais — **exatamente os dois números de hoje trocados de
lugar**, o que sugere transposição em algum momento. Se for **da loja**, o balcão
vira R$ 16.800 e serviços gerais R$ 43.200.

Até o Rodrigo confirmar: o painel usa `por_recepcionista_mensal` para a **meta** e
a tabela só para **calcular comissão** — que é percentual e não depende de qual
total está certo. O bônus, que depende, fica marcado como "se bater".

## Onde isso estava até hoje

Numa nota do Obsidian, que a sessão da nuvem não alcança. Os números vieram por
cópia e cola. **O plano de remuneração da equipe não pode viver só num vault que
só uma máquina enxerga** — agora está no repositório, versionado, e o painel
calcula sozinho.

## Como saber se deu certo

No fechamento de setembro, comparar o que o card calculou com o que foi pago de
fato. Se bater, a recepção passa a ter acompanhamento diário do próprio ganho —
que é o que transforma meta em alvo. Se não bater, a diferença aponta qual das
duas leituras da tabela é a certa.
