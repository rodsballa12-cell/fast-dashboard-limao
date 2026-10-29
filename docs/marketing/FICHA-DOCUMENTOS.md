# Ficha de documentos · FAST Limão

**Versão 1 · 29/10/2026.** Montada na nuvem com os **logos oficiais** e as **peças aprovadas** da
abertura (ramo `claude/focused-keller-0bcwlw`, pasta `artes-abertura/`). **Aguarda o aval do Rodrigo**
e a conferência do Marketing no PC com o vault (`14_` e `15_`).

## Como usar

O código está em `modelos/kit.js`. Os modelos vazios ficam em `modelos/modelo-<pele>.docx` e são
gerados por `node docs/marketing/modelos/gerar_modelos.js`.

```js
const K = require('./docs/marketing/modelos/kit');
K.salvar(K.documento({ pele: 'escova' | 'spa' | 'consolidado', rotulo, titulo, blocos: [
  K.secao('1 · Seção', pele), K.p('texto', pele), K.lista([...], pele),
  K.sub('FAST Escova', 'escova'), K.tabela(larguras, linhas, { pele: 'escova', total: true }),
]}), 'saida.docx');
```

**Escova → `escova` · Spa → `spa` · as duas lojas → `consolidado`.** No documento consolidado, cada
bloco que é de uma loja usa a pele dela (`K.sub(..., 'escova')`, `K.tabela(..., {pele:'spa'})`).

Documento com salário ou dado de pessoa **não vai para o repositório**. Só o modelo vai.

## Cores (lidas dos arquivos de logo, pixel a pixel)

| | Hex | Onde |
|---|---|---|
| Amarelo FAST | `#FBD300` | logo Escova, acento, filete, barra |
| Amarelo claro | `#FFF6C2` | linha de total na Escova |
| Preto | `#000000` | faixa e cabeçalho de tabela da Escova |
| Verde-água | `#00A6A4` | logo Spa, faixa, cabeçalho de tabela do Spa |
| Verde-água escuro | `#006C6B` | títulos do Spa |
| Verde-água claro | `#DFF5F4` | linha de total no Spa |
| Grafite | `#2B3133` | "fast" do logo do Spa, texto e cabeçalho do consolidado |
| Cinza | `#5B6568` | legendas e rótulos |

> `identidade-visual.md` trazia `#FFD50C` e `#3FB1AF`. Os arquivos de logo dizem `#FBD300` e `#00A6A4`.
> **Vale o arquivo de logo.**

## Tipografia

Montserrat em todo o documento (regra do vault). As peças da abertura usavam fonte do sistema e
Georgia, porque foram feitas sem a fonte instalada. **A conferir no PC.**

| Uso | Tamanho | Peso | Detalhe |
|---|---|---|---|
| Título do documento | 24 pt | Bold | CAIXA ALTA |
| Rótulo acima do título | 8,5 pt | Bold | CAIXA ALTA, espaçado |
| Título de seção | 13 pt | Bold | CAIXA ALTA, espaçado, filete na cor da pele |
| Subtítulo de bloco | 11 pt | Bold | barra lateral na cor da loja |
| Corpo | 10,5 pt | Regular | entrelinha 1,2 |
| Tabela | 9,5 pt | Regular, cabeçalho Bold | cabeçalho CAIXA ALTA |
| Legenda | 9 pt | Itálico | cinza |
| Rodapé | 8 pt | Bold + Regular | SEM HORA MARCADA · @perfil |

## Página

- A4 com margens de 2,5 cm nas laterais, 1,8 cm no topo e 1,9 cm embaixo.
- **Faixa de logo no topo:**
  - Escova: faixa preta com o logo `fastescova-claro`;
  - Spa: faixa verde-água com o logo `fastspa-branco`;
  - Consolidado: as duas lado a lado, metade preta e metade verde-água.
- **Rodapé:** SEM HORA MARCADA mais o perfil do Instagram, com filete na cor da pele. **Sem endereço
  até o número ser confirmado** (as peças dizem 358, outras peças 362 e o Google 382).

## Logos (`marca/`)

| Arquivo | Fundo |
|---|---|
| `fastescova-claro.png` | escuro (fast branco + escova amarelo) |
| `fastescova-escuro.png` | claro (fast grafite + escova amarelo) |
| `fastescova-preto.png` | claro, uma cor |
| `fastspa-branco.png` | verde-água ou escuro, uma cor |
| `fastspa-claro.png` | escuro (fast branco + spa verde-água) |
| `fastspa-escuro.png` | claro (fast grafite + spa verde-água) |

Nunca redesenhar nem recolorir logo.

## Pendências para o Marketing no PC

1. Conferir com o vault `14_Marca_Logos_Oficiais.md` e `15_Sistema_Combo_Duas_Marcas.md`, e corrigir esta ficha.
2. Confirmar a tipografia oficial (Montserrat?) e os tamanhos.
3. Copiar os SVG da folha do `OneDrive\...\Marketing\Marca\` para `marca/`.
4. Confirmar o número do endereço.
