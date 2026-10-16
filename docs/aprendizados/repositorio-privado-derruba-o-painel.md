# Tornar o repositório privado derruba o painel e não protege nenhum dado

**Destilado em:** 2026-10-16 · **Origem:** incidente de 28/08/2026, registrado
no Obsidian e migrado para cá em 16/10/2026.

## Regra

**Não tornar este repositório privado.** O painel só funciona com ele público, e
torná-lo privado não esconde nada do que o painel mostra.

## O que aconteceu

Em 28/08/2026, para proteger os dados, o repositório foi tornado privado. Na
conta GitHub gratuita isso despublica o GitHub Pages: o painel saiu do ar na
hora, por cerca de 4 horas.

Voltar o repositório a público **não religou o site**. Foi preciso recriar a
configuração do Pages, apontando para a branch `main` na raiz. Restaurado em
28/08 às 19:53, com build de 36 segundos e sem erro. Conferido abrindo o
endereço: dado de 19:33 BRT.

## A causa que importa

Repositório privado **não** protege os dados do painel. Mesmo numa conta paga
(GitHub Pro), que reativaria o Pages em repositório privado, **o site publicado
continua público**: controle de acesso no Pages só existe no plano Enterprise.
Proteger o repositório e proteger o site são coisas diferentes.

## O que fazer se um dia for preciso proteger o painel

Só há duas saídas que funcionam:

- **anonimizar o conteúdo** que vai para o painel (tirar nome e telefone de
  cliente, por exemplo), ou
- **mudar para um host com autenticação** (Cloudflare Access, Netlify com senha).

## Consequência prática hoje

Tudo o que entra neste repositório é público, inclusive nas pastas `data/` e
`docs/`. Antes de gravar qualquer coisa aqui, a pergunta é: *isso pode ser
lido por qualquer pessoa na internet?*
