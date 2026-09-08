# Uniforme fastspa | Limão — artes vetorizadas

Vetorização das 4 artes de uniforme entregues em PDF. Os PDFs originais **não eram
vetoriais**: cada um continha um único JPEG de 1240 px achatado sobre o fundo colorido.
Aqui as artes viraram curvas de Bézier reais — escalam para qualquer tamanho sem perda.

## O que mandar para a gráfica

Use os arquivos **`*-estampa.*`**: são só a arte, com **fundo transparente** e recortados
na caixa do desenho. O fundo colorido do arquivo original é a *cor da camiseta*, não faz
parte da estampa e não deve ser impresso.

| Formato | Arquivo | Observação |
|---|---|---|
| **Vetor (preferido)** | `*-estampa.svg` | Abre em Illustrator, CorelDRAW, Inkscape, Silhouette |
| **Vetor para impressão** | `*-estampa.pdf` | Já no tamanho físico final, em cm |
| Raster | `*-estampa-300dpi.png` | 300 dpi no tamanho final, fundo transparente |

Os arquivos `*-mockup.*` são só para visualização/aprovação — trazem o fundo colorido
simulando a camiseta. **Não enviar para impressão.**

## Peças e tamanhos

| Peça | Cor da camiseta | Tamanho da estampa | PNG @300dpi |
|---|---|---|---|
| `frente-verde-agua` | verde-água `#62B1AC` | 26,0 × 14,4 cm | 3071 × 1695 |
| `frente-bege`       | bege `#EADACB`       | 26,0 × 14,1 cm | 3071 × 1670 |
| `costas-verde-agua` | verde-água `#62B1AC` | 23,1 × 34,0 cm | 2729 × 4016 |
| `costas-bege`       | bege `#EADACB`       | 23,1 × 34,0 cm | 2727 × 4016 |

Os tamanhos são uma sugestão já aplicada aos PDFs (frentes encaixadas em 26 × 22 cm,
costas em 30 × 34 cm). Como é vetor, a gráfica redimensiona para qualquer medida sem
perda — basta pedir.

## Paleta de impressão (4 cores + branco)

| Cor | HEX | Onde aparece |
|---|---|---|
| Verde-água   | `#62B1AC` | Fundo das peças 1 e 3; símbolo e `spa` na frente bege |
| Bege         | `#EADACB` | Fundo das peças 2 e 4 |
| Verde-escuro | `#285A62` | Símbolo (pétalas), `Limão` |
| Grafite      | `#454140` | `fast` e textos nas peças bege |
| Branco       | `#FFFFFF` | Logo e textos nas peças verde-água |

As cores foram medidas nos arquivos originais e unificadas: variações de 1–3 níveis
entre as artes foram igualadas, para que as peças fiquem idênticas entre si na produção.
Cada camada do SVG tem `id` próprio (`simbolo`, `texto`, `limao`…), então dá para separar
por cor para fotolito de serigrafia direto no arquivo.

## Como foi feito

1. Extração do JPEG embutido em cada PDF (1240 px, com uma linha de artefato na borda
   da arte bege, aparada).
2. Filtro de mediana 3×3 para eliminar o blocking do JPEG.
3. Supersample 3× e classificação de cada pixel por **projeção cromática**: resolve
   `pixel = a·tinta + (1−a)·fundo` para cada tinta candidata e escolhe a de menor
   resíduo. É o que separa o grafite do verde-escuro na arte bege — as duas são escuras
   e a distância euclidiana simples as confundia.
4. Traçado com potrace por camada de cor, descartando manchas menores que 12 px²
   (sujeira de compressão).

## Limitação conhecida

O material de origem tinha só 1240 px e compressão JPEG forte. A vetorização é fiel ao
que existia, mas herda pequenas irregularidades nas bordas das letras — mais visíveis no
`spa` da frente bege, que já estava degradado no arquivo original. Para tipografia
perfeita, o caminho é pedir ao designer o arquivo vetorial de origem (`.ai`, `.eps`,
`.svg` ou PDF com fontes) e refazer a partir dele.
