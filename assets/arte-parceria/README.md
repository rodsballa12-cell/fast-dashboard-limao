# Arte de parceria — Yázigi Limão + fastspa + fastescova

Redesenho da peça de parceria, nos três formatos de publicação. A mensagem é a
mesma da arte original; o que mudou foi a execução.

## Arquivos para publicar

| Formato | Arquivo | Onde usar |
|---|---|---|
| 1080 × 1350 (4:5) | `parceria-feed.*` | Feed do Instagram — ocupa mais tela |
| 1080 × 1080 (1:1) | `parceria-quad.*` | Facebook e grades de feed quadradas |
| 1080 × 1920 (9:16) | `parceria-story.*` | Stories e Reels |

PNG e JPG (qualidade 95, sem subamostragem de croma) de cada um. Para o Instagram,
o JPG basta e sobe mais rápido; o PNG serve se a peça for reeditada.

## O que mudou em relação à arte original

- **Logo `fastspa | LIMÃO` oficial**, do arquivo vetorial da marca, no lugar da versão
  rasterizada de baixa resolução — nítido em qualquer tamanho.
- **`fastescova` vetorizado** a partir da arte original (13 curvas no branco, 9 no
  amarelo), também livre de resolução.
- **Símbolo oficial de 4 pétalas do fastspa** usado como ícone do card e como marca
  d'água de fundo.
- **Fundo refeito**: gradiente roxo com glows direcionais no lugar dos blobs que
  disputavam atenção nos quatro cantos.
- **Hierarquia**: os dois cards ganharam altura igual e o `+` foi centralizado entre
  eles, virando o eixo da composição.
- **Ícones redesenhados em SVG** (pétalas, escova, globo, estrela, coração) — antes
  eram bitmap e borravam.
- **Tipografia** Poppins + Archivo Black + Permanent Marker, embutidas no gerador.

## Paleta

| Cor | HEX | Uso |
|---|---|---|
| Roxo profundo | `#1B0540` → `#2D0A63` | Fundo |
| Ciano | `#16E0F2` | Card fastspa, acentos |
| Magenta | `#FF2FD0` | Card fastescova, acentos |
| Verde-limão | `#D8FF2E` | Faixas de destaque e CTA |
| Amarelo | `#FBE007` | `escova` no logo |

## Pendência

O CTA diz "Vem com a gente!" mas **não há dado de contato na peça** — sem @, endereço
ou telefone, quem vê não sabe o que fazer. Não preenchi porque inventar um @ numa peça
publicada pode apontar para o perfil de outra pessoa. Mandando os dados reais, entram
no rodapé.

## Regerar

`fonte/` traz o gerador completo. `python3 gerar.py && node render.mjs r jobs_arte.json`
reconstrói os três formatos. Os textos e tamanhos ficam em `gerar.py`; os logos
extraídos da arte original estão em `fonte/yazigi.png` e `fonte/fastescova.svg`.

> O logo do Yázigi foi extraído da arte original (símbolo por máscara circular, wordmark
> por remoção de fundo) porque não temos o arquivo oficial. Para uso prolongado da marca,
> vale pedir o logo oficial ao Yázigi.
