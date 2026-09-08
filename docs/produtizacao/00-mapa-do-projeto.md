---
titulo: "FAST Insights — Mapa do projeto de produtização"
projeto: Franquia_FAST_Limao
tipo: indice
status: rascunho-v1
criado: 2026-09-08
tags: [fast, produtizacao, saas, franquia, trinks]
---

# FAST Insights — Mapa do projeto

> Transformar o painel da FAST Limão (1 loja) em produto para a rede FAST (~431 lojas
> em operação hoje, ~600 previstas no horizonte de 2027).

## Os quatro documentos

| # | Documento | Para quê | Para quem |
|---|---|---|---|
| 01 | [[01-plano-tecnico-multiloja]] | O que existe hoje, o que trava, e a arquitetura para rodar 600 lojas | Você + quem for programar |
| 02 | [[02-business-plan]] | Modelo de negócio, preço, custos, cenários, riscos | Você + franqueadora + eventual sócio/investidor |
| 03 | [[03-conversa-com-a-franqueadora]] | O roteiro e os números da reunião | Você |
| 04 | [[04-metodo-de-prompts]] | Como me pedir isso com menos idas e voltas | Você |
| 05 | [[05-analise-contratual]] | **Leia primeiro.** O que o contrato FAST e os termos da Trinks permitem, proíbem e exigem | Você + seu advogado |

## Versão publicada (para compartilhar)

O business plan também está publicado como página web, pronta para mandar por link:
**https://claude.ai/code/artifact/cd35b2ac-8e6d-4697-a217-4c667227596d**
(privada por padrão — só abre para quem você compartilhar pelo menu da página).

## Resumo em cinco linhas

> **Atualização de 08/09/2026, após a leitura do contrato:** a cláusula 13.13 cede à
> franqueadora a propriedade de toda "invenção, aperfeiçoamento ou inovação" resultante
> da operação da unidade. A titularidade do painel é disputável, e a primeira ação do
> projeto passou a ser jurídica, não técnica. Ver [[05-analise-contratual]].

1. O motor de análise **já é multi-loja** — a identidade da loja vem de variável de
   ambiente, não está escrita no código. Isso encurta muito o caminho.
2. O que **não** escala é a embalagem: 1 repositório GitHub por loja, painel publicado
   numa URL pública, financeiro dependente de um Excel no seu OneDrive.
3. Existe **um bloqueador de privacidade** para resolver antes da loja nº 2: hoje DRE,
   caixa e telefones de clientes estão numa URL aberta na internet.
4. O caminho recomendado é **híbrido**: a franqueadora homologa e paga o painel da rede;
   o franqueado paga o plano da loja, cobrado junto do royalty.
5. Cenário-base modelado: **300 lojas pagando → ~R$ 1,3 milhão de receita anual**, com
   ponto de equilíbrio em torno de **120 lojas**.

## Estado atual do ativo (08/09/2026)

- Painel com 6 abas: painel operacional, clientes, financeiro, Stone, mídias, auditoria
- Atualização automática 5x/dia com controle de cota da API Trinks
- Motor de insights automáticos por aba
- Campanhas de WhatsApp (aniversário + reativação) com trava de segurança, em dry-run
- Sincronismo com HubSpot (369 contatos importados)
- ~5.500 linhas de Python + 1 HTML de 280 KB
