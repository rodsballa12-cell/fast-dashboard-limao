# SULTS · o que a franqueadora sabe sobre as lojas Limão

O SULTS é o sistema da franqueadora: chamados, compras, comunicados e
checklists. A leitura diária (`scripts/sults_leitura.py`, chamada pelas rotinas
do PC) grava **só os dados do Limão** em:

`C:\Users\rods_\OneDrive\Franquia - FAST\Claude\SULTS\sults_limao.json`

**Só a sessão do PC alcança esse arquivo.** Ele não vai para o repositório,
porque o repositório é público e os chamados trazem assunto de contrato e
jurídico. Sessão da nuvem que precisar dele: `NÃO VEJO` endereçado ao PC.

## Antes de ler

1. **`gerado_em`.** A leitura roda no máximo a cada 3 horas, e só quando o PC
   está ligado. Mais de 24 h = diga de quando é.
2. **`lojas.<loja>.erro`.** Se existir, aquela loja não atualizou e o resto do
   bloco é da leitura anterior.

## O que tem, por loja (`lojas.escova`, `lojas.spa`)

| Campo | O que é | Quem usa |
|---|---|---|
| `chamados_urgentes` | chamados em que **a franqueadora falou por último** (ou pediu retorno) há até 30 dias: a vez é da loja | Operação, Conselho |
| `chamados[]` | todos, com `ultima_fala` (quem, quando, texto), `dias_sem_resposta`, `sentido` | Operação, Pessoas |
| `pedidos[]` | compras dos últimos 120 dias + todas ainda abertas, com itens e preço | Financeiro |
| `pedidos_por_mes`, `pedidos_por_fornecedor` | soma em reais, sem os cancelados | Financeiro |
| `comunicados[]` | os 15 mais recentes; `novo` = apareceu desde a última leitura; `nao_abriram` = quem da loja ainda não abriu | Marketing, Financeiro |
| `checklists[]`, `planos_de_acao[]` | avaliações da franqueadora sobre a loja | Operação |

## Como não errar

- **Chamado com a vez da loja há mais de 30 dias não é alarme.** Costuma ser
  assunto morto que ninguém fechou (ex.: "Processo de Projeto", de fevereiro).
  Cite só se ele mudar.
- **Pedido "Aguardando" de abril não quer dizer dinheiro devido.** Os móveis e a
  fachada das duas lojas foram entregues, porque as lojas abriram. O SULTS só não
  foi atualizado. Se foi pago, isso está no Excel, não aqui: `NÃO VEJO` para o Financeiro.
- **Comunicado de boleto, royalty ou preço que ninguém abriu** é item de ação
  do Financeiro. Os de campanha, estoque e lançamento são do Marketing.
- **Nunca** responder, aceitar, abrir ou fechar nada no SULTS. Se a resposta for
  da loja, o parecer diz **o que responder e a quem**, e o Rodrigo (ou o Lucas) responde.
- **Nunca citar outra unidade da rede.** O arquivo não traz nenhuma; se um
  texto de chamado mencionar outra loja, não é assunto nosso.
