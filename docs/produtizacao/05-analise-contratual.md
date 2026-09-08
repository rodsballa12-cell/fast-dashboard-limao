---
titulo: "Análise contratual — o que o contrato FAST e os termos da Trinks permitem"
projeto: Franquia_FAST_Limao
tipo: analise-juridica
status: rascunho-v1 · NÃO é parecer jurídico
criado: 2026-09-08
fontes:
  - Contrato de Franquia FAST ESCOVA · São Paulo/SP · Limão · assinado 27/01/2026 (D4Sign 6f75256b)
  - Termos de Uso Trinks · sistema.trinks.com/termos-de-uso
tags: [fast, contrato, juridico, trinks, lgpd, produtizacao]
---

# Análise contratual

> **Aviso.** Isto é leitura atenta de dois documentos, não parecer jurídico. Eu não sou
> advogado. As cláusulas abaixo estão citadas literalmente para que um advogado de
> franquias consiga avaliar em 30 minutos. **Nada aqui deve ser executado sem essa
> validação** — o valor em risco é alto e está quantificado na seção 5.

## 1. O veredito em uma frase

**O produto pode existir, mas provavelmente não é seu para vender** — e o caminho
viável deixa de ser "vender para a franqueadora" e passa a ser "negociar com a
franqueadora antes de construir mais qualquer coisa".

## 2. A cláusula que decide tudo — 13.13

> **13.13.** As Partes estabelecem que no caso de a execução deste CONTRATO e a operação
> da UNIDADE FRANQUEADA resultar em **invenção, descoberta, aperfeiçoamento ou inovação,
> os respectivos direitos de propriedade pertencerão à FRANQUEADORA**, ainda que decorram
> de ato ou fato direta ou indiretamente praticado pelo FRANQUEADO que, portanto, concorda
> em ceder tais direitos à FRANQUEADORA.

Leia devagar, porque cada pedaço aperta:

- "aperfeiçoamento ou inovação" — não exige patente nem invenção formal. Um painel de
  gestão cabe confortavelmente.
- "resultar da execução deste CONTRATO **e** da operação da UNIDADE FRANQUEADA" — o
  painel nasceu para operar a Limão, lê os dados da Limão e usa as metas que a
  franqueadora forneceu. É difícil argumentar que nasceu fora disso.
- "**ainda que** decorram de ato ... praticado pelo FRANQUEADO" — a cláusula foi escrita
  justamente para o caso em que quem cria é o franqueado.
- "**concorda em ceder**" — a cessão já está dada no contrato assinado. Não é algo que
  ainda vá acontecer.

**Consequência prática:** numa leitura literal, o FAST Insights já pertence à
FE FRANCHISING. Vender, licenciar ou até doar para outros franqueados sem autorização
escrita seria dispor de um bem alheio.

**Há contra-argumentos** — e eles não são frívolos: contrato de franquia é de adesão, e
uma cessão universal e gratuita de tudo que o franqueado criar pode ser atacada como
cláusula abusiva; o código foi escrito com trabalho e ferramentas próprios, fora do
SISTEMA; e o Trinks não é software da franqueadora. Mas isso é tese para advogado
defender, não premissa para montar plano de negócio.

## 3. As outras quatro que importam

### 13.11 — a base de clientes não é sua

> O FRANQUEADO reconhece e concorda que o Mailing se origina em razão da utilização das
> Marcas ... **constituindo desta forma propriedade exclusiva da FRANQUEADORA**, devendo
> ser-lhe automaticamente transferido em caso de rescisão.

Mata qualquer plano de CRM independente. E torna o sync com o HubSpot uma exposição
presente, não hipotética (seção 6).

### 21.1 — confidencialidade, R$ 200.000

> Os documentos e informações fornecidos, em razão da relação de franquia ... deverão ser
> considerados confidenciais, logo, nenhum dos contratantes poderá divulgá-los sem o prévio
> e expresso consenso da outra parte, na vigência **e mesmo após a rescisão ... por mais
> dois anos**.

O painel embute material que veio da franqueadora: as metas oficiais por recepcionista
(`metas_franqueadora` no `config.json`), a tabela de preços, o modelo de DRE, a
classificação de serviços. Entregar isso a outro franqueado é divulgação. Multa do item
10.4: **R$ 200.000**.

### 19.3.3 (ix) — a mais perigosa das causas de rescisão

> ... **uso indevido, ilegal ou fraudulento dos dados dos clientes e/ou qualquer tipo de
> atuação visando a obtenção de vantagem para si ou para terceiros valendo-se do SISTEMA
> sob qualquer forma**.

"Obter vantagem para si valendo-se do SISTEMA sob qualquer forma" é redação larga o
bastante para alcançar exatamente o que o business plan propunha. E rescisão com justo
motivo aciona a multa do item 10.1: mais **R$ 200.000**, cumulável.

### 12.8, 7.6 e 14.2 — e aqui está a boa notícia comercial

> **7.6. Taxa de Software:** Atualmente os softwares que devem ser utilizados pelo
> FRANQUEADO são: **Trinks (ERP) e Sults (CRM)**, sendo que haverá um custo de implantação
> e mensalidade dos Softwares **a ser pago aos fornecedores homologados**.
>
> **12.8.** o FRANQUEADO deverá utilizar obrigatoriamente os SOFTWARES ... indicados pela
> FRANQUEADORA ... deverá obter a licença, bem como se utilizar do **FORNECEDOR
> HOMOLOGADO**.

Três coisas que valem ouro para o plano:

1. **O Trinks é obrigatório em toda a rede.** O item nº 3 da lista de validação está
   respondido: o mercado endereçável não é "quantas lojas usam o Trinks" — é 100% delas.
2. **O trilho de cobrança já existe.** Já há uma Taxa de Software paga **diretamente ao
   fornecedor homologado**, não dentro do royalty. Isso é melhor do que eu havia proposto:
   relação comercial direta com a loja, sem depender do faturamento da franqueadora.
3. **Ser Fornecedor Homologado é a única porta legítima** — e ela é uma porta, não um muro.

### 21.2 — o que **não** bloqueia

A não concorrência define atividade concorrente de forma fechada:

> **21.2.1.** Considera-se como atividade concorrente ... **estabelecimentos comerciais que
> tenham como negócio central a comercialização de Produtos e Serviços destinados a
> procedimentos estéticos, cuidados capilares, manicures, pedicures, e outros serviços de
> beleza.**

Uma empresa de software **não** é atividade concorrente por essa definição. Abrir uma
software house não viola 21.2. O impedimento é de propriedade (13.13) e de
confidencialidade (21.1), não de concorrência — e essa distinção é a base da negociação.

## 4. A Trinks aperta do outro lado

Dos Termos de Uso ([sistema.trinks.com/termos-de-uso](https://sistema.trinks.com/termos-de-uso)):

- **Os dados são deles:** "O banco de dados e as informações criadas a partir do uso da
  Trinks é e permanecerá de nossa propriedade, à qual será única titular de todos os
  direitos de propriedade dele decorrentes."
- **Licença fechada:** "limitada, não exclusiva, **não passível de sublicença**, revogável
  e não transferível".
- **Uso não comercial:** "O acesso é exclusivamente para uso pessoal dos usuários, **nunca
  comercial**, exceto nas hipóteses previamente e expressamente autorizadas."
- **Sem obras derivadas:** não podem "reproduzir, modificar, **preparar obras derivadas**,
  distribuir, licenciar, vender, revender, transferir, exibir ou explorar a Trinks de
  qualquer outro modo".
- **IP só por contrato específico:** "Nenhum direito de propriedade intelectual ... será
  transferido ou licenciado aos Usuários, a não ser através de **contratos específicos**,
  que deverão ser escritos e assinados por ambas as partes."

**Tradução:** um produto comercial construído sobre a API da Trinks exige contrato
específico e escrito com a Trinks. Isso deixa de ser o item nº 2 da lista de validação
("seria bom ter uma parceria") e vira **pré-requisito**. A boa notícia é que a própria
Trinks prevê esse caminho e tem programa de integração.

## 5. Os três donos de pedaços do mesmo produto

| Peça | Quem tem argumento de propriedade | Base |
|---|---|---|
| O código Python e o HTML | Você — e a franqueadora, por 13.13 | 13.13 vs. autoria e Lei de Software |
| As regras de negócio (metas, tabela, DRE, categorias) | Franqueadora | 12.3, 12.6, 21.1 |
| A base de clientes | Franqueadora | 13.11 |
| Os dados dentro do Trinks | Trinks | Termos de Uso |
| O direito de explorar comercialmente | Ninguém, hoje | 13.13 + ToS Trinks |

Nenhuma das três partes sozinha consegue lançar isso. Você tem o produto funcionando, a
franqueadora tem a rede e a titularidade, a Trinks tem o dado. **Isso não é um beco sem
saída — é a definição de uma negociação de três pontas, e você entra nela com a única
peça que não se compra pronta: um produto rodando em loja real.**

## 6. Três exposições no setup de HOJE

Estas existem independentemente de produtizar ou não, e a primeira é urgente.

| # | Exposição | Cláusula tocada | Ação |
|---|---|---|---|
| 1 | Painel público no GitHub Pages com DRE e telefones de clientes | 24.5 (i) e (ii) · 13.11 · 19.3.3 (ix) | **Fechar esta semana.** Já era prioridade por LGPD; agora também é risco contratual |
| 2 | Sync de 369 contatos para o HubSpot | xlii ("utilizar somente os softwares indicados") · 24.5 (iii) · 13.11 — o CRM homologado é o **Sults** | Suspender o workflow até resolver com a franqueadora |
| 3 | Campanhas de WhatsApp | 24.5 (iii): dados só para as finalidades do contrato e dos MANUAIS; nova finalidade exige base legal | Manter desligado (`ativo: false`) até autorização escrita |

O item 2 me passou despercebido na análise anterior — eu tinha lido `hubspot_sync.py`
como integração técnica e não como envio da base de clientes a um terceiro não
homologado. Com o contrato em mãos, é o segundo ponto a resolver.

## 7. O que muda no business plan

| Antes | Agora |
|---|---|
| Você é dono do produto e vende | A titularidade é disputável (13.13); negocie **antes** de construir |
| Modelo híbrido, cobrado no boleto do royalty | Modelo de **Fornecedor Homologado**, cobrado direto pela Taxa de Software (7.6) — precedente já existe |
| "Quantas lojas usam Trinks?" a validar | Respondido: **100%**, é obrigatório (7.6) |
| "A franqueadora cobra taxa de tecnologia?" a validar | Respondido: **sim**, paga direto ao fornecedor homologado |
| Parceria com a Trinks seria desejável | É **pré-requisito** — os ToS proíbem uso comercial e obra derivada sem contrato escrito |
| Risco "franqueadora constrói internamente" | Somado ao risco maior: ela pode simplesmente **reivindicar o que já existe** |
| Piloto com 5 lojas na semana 3 | **Não faça** antes da autorização escrita: cada loja adicional multiplica 21.1 e 19.3.3 (ix) |

## 8. Os três caminhos viáveis

### A · Homologação — recomendado
Levar à franqueadora **antes** de qualquer expansão, propondo virar Fornecedor
Homologado com contrato específico que trate de 13.13 expressamente. Você aceita que a
franqueadora tenha direitos sobre o produto e negocia a contrapartida: remuneração por
loja ativa, participação, ou um contrato de desenvolvimento. Precedente pronto: 7.6 já
prevê fornecedor homologado de software cobrando mensalidade de cada loja.
**Sua alavanca:** o produto existe, funciona e a alternativa dela é gastar 6 a 9 meses.
**O erro fatal:** entregar o código ou a demo detalhada antes de ter algo assinado —
13.13 permite que ela simplesmente fique com tudo.

### B · Produto genérico, fora do SISTEMA
Um produto para salões em geral, sem nada da FAST: sem as metas da franqueadora, sem a
tabela de preços, sem o modelo de DRE, sem material dos MANUAIS. Vendido a salões que
usam Trinks, incluindo — mas não só — franqueados FAST. 21.2 não impede (software não é
atividade concorrente). Mas 13.13 continua a assombrar a origem do código, e o caminho é
muito mais lento.

### C · Uso interno apenas
Manter o painel só na Limão, resolver as três exposições da seção 6, e usá-lo como
demonstração de gestão — inclusive no Conselho de Franqueados (cláusula 1.4, participação
exigida) e nos encontros de "ideias, críticas e sugestões sobre o SISTEMA" (6.1 ix).
Risco quase zero. É a posição de partida enquanto A é negociado.

**Recomendação: começar em C, negociar A, guardar B como alternativa** caso a
franqueadora diga não sem oferecer contrapartida.

## 9. Perguntas para o advogado de franquias

Uma hora de consulta com estas cinco perguntas resolve o projeto inteiro:

1. **13.13 alcança um software que eu escrevi?** Cessão universal e gratuita de tudo que o
   franqueado criar é exigível, ou é abusiva num contrato de adesão? A Lei de Software
   (9.609/98) muda algo, já que o autor é pessoa física fora de vínculo empregatício?
2. Se eu construir do zero, **fora do horário e sem material dos MANUAIS**, um produto
   genérico para salões, 13.13 ainda alcança? Que provas de segregação eu preciso produzir
   desde já?
3. **Como estruturar a conversa com a franqueadora sem entregar o ativo?** Existe NDA ou
   memorando de entendimento que preserve minha posição antes da demonstração?
4. Qual o **risco real** das três exposições da seção 6, e qual a ordem de correção?
5. Sendo eu franqueado **e** fornecedor homologado ao mesmo tempo, há conflito que precise
   ser tratado no contrato de fornecimento?

## 10. Os números do risco

| Item | Valor | Cláusula |
|---|---|---|
| Multa de confidencialidade / não concorrência | R$ 200.000 | 10.4 · XXI |
| Multa rescisória | R$ 200.000 | 10.1 · 19.4 |
| Multa por infração pontual | R$ 3.000 por infração | 10.2 · 6.2.1 |
| Multa diária | R$ 1.000/dia | 10.3 |
| Taxa inicial já paga | R$ 60.000 | 7.1 · item 13 |
| Royalty mensal | 7% do bruto, mínimo R$ 3.000 a partir do 13º mês | 7.2 |
| Vigência | 27/01/2026 a 27/01/2031 | item 6 |

As duas multas de R$ 200 mil são **cumuláveis entre si e com a rescisória** (21.3). O
cenário ruim não é perder o projeto de software: é perder a loja e sair devendo.

Isso não é argumento para desistir — é argumento para fazer na ordem certa. O ativo é
real, o mercado é cativo por contrato, e o trilho comercial já existe. O que muda é que
a primeira ação deixa de ser "configurar 2 lojas piloto" e passa a ser "sentar com um
advogado e depois com a franqueadora".
