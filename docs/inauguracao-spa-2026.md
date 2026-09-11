---
titulo: Inauguração Fast SPA Limão · 24 a 27/09/2026
unidade: spa
tags: [fast-spa, inauguracao, convites, marketing]
criado: 2026-09-11
painel: https://claude.ai/code/artifact/d3d9ad76-e084-4218-9567-6514d4b0d4bb
---

# Inauguração Fast SPA Limão · 24 a 27 de setembro de 2026

**Endereço:** Av. Dep. Emílio Carlos, 358 · Limão · São Paulo (mesmo prédio da Fast Escova Limão)
**WhatsApp:** (11) 99024-3927 · **Instagram:** @fastspa.limao
**Data oficial de inauguração no `data/config.json`:** 2026-09-25

> Página interativa com o convite, as cotas e o quadro de convidados:
> https://claude.ai/code/artifact/d3d9ad76-e084-4218-9567-6514d4b0d4bb

---

## 1. Princípio da distribuição

**Dois públicos que competem pela mesma poltrona nunca caem no mesmo dia.**

- VIP não divide fila com visitante de porta aberta.
- Imprensa e influenciadora veem a casa cheia **antes** de qualquer cliente entrar.
- Convite é sempre **nominal**, com **dia e horário definidos**. Convite genérico
  ("venha entre 24 e 27") destrói a capacidade: todo mundo aparece no sábado às 11h.

---

## 2. Os quatro dias

| Dia | Formato | Público | Convites | Presença est. |
|---|---|---|---|---|
| **Qui 24/09** · 18h–22h | Coquetel, corte de fita 19h30, tour, 2 estações de demonstração (10 min) — **único dia com cortesia** | Franqueadora, sócios, fornecedores, imprensa e perfis do bairro, 10 influenciadoras, comércio vizinho, equipe e família | 70 | ~50 |
| **Sex 25/09** · 10h–20h | Hora marcada, tour, conversa com a equipe, welcome drink e oferta de combo | Top 20% da base da Escova + 10 lugares da franqueadora | 60 | ~30 |
| **Sáb 26/09** · 9h–19h | Blocos de 30 min, música, mini-bar, oferta de combo, mecânica "traga uma amiga" | Clientes ativas da Escova (visita ≤60d) + 1 acompanhante cada | 80 (40+40) | ~40 |
| **Dom 27/09** · 10h–17h | Sem hora marcada, senha por ordem de chegada, tour curto e oferta de combo | Base inativa (60–180d), lista do Instagram, vizinhança, quem passou na porta | 90 | ~45 |

**Total: 300 convites nominais → ~165 presenças.**
A quinta usa **70%** de comparecimento (convite institucional, com cortesia).
Sexta, sábado e domingo usam **50%**: nesses dias a convidada não ganha nada só por
comparecer — a garrafa está atrelada à compra de um combo. É a conta realista, não a
otimista. Para subir, ou aumenta o volume de convites (~25% a mais) ou entra um
mimo pequeno de chegada (uma água saborizada, uma amostra) que não custe margem.

### Por que cada dia é assim

- **Quinta** — quem vem por relação, não por serviço. Não ocupa cadeira e gera conteúdo
  para os três dias seguintes.
- **Sexta** — é o dia que vira receita recorrente. Sem cortesia, a venda acontece na
  conversa: tour, equipe apresentando os protocolos e o combo com a garrafa como
  fechamento. É também o dia da foto oficial: não pode estar vazio.
- **Sábado** — dia de maior fluxo natural. A acompanhante é lead novo com prova social
  embutida (chega já ouvindo elogio de quem confia na casa).
- **Domingo** — não canibaliza a agenda da Escova e absorve volume sem risco de frustrar VIP.

---

## 3. As sete listas (critérios objetivos, tirados do Trinks)

| Lista | Critério | Dia | Convites |
|---|---|---|---|
| **A · Institucional** | Franqueadora FAST, sócios, contador, fornecedores, locador do prédio | Qui 24 | 20 |
| **B · Imprensa e bairro** | Perfis e jornais do Limão/Zona Norte, associação comercial, síndicos vizinhos | Qui 24 | 15 |
| **C · Influenciadoras** | 5k–50k seguidores, Zona Norte, público feminino 25–50, engajamento >3% | Qui 24 (10) + Sáb 26 (4) | 14 |
| **D · Equipe e família** | Time das duas unidades + 1 acompanhante, **em escala** para não esvaziar o salão | Qui 24 | 21 |
| **E · VIPs da Escova** | Top 20% por ticket médio **ou** 3+ visitas nos últimos 90 dias | Sex 25 | 60 |
| **F · Ativas da Escova** | Última visita ≤60 dias e fora da lista E — convite com "+1" | Sáb 26 | 76 |
| **G · Resgate e bairro** | 60–180 dias sem visita, lista de espera do Instagram, cadastro de porta | Dom 27 | 90 |

> Monte a lista nominal **filtrando o Trinks por esses cortes**, não por memória.
> Tire duplicados entre listas antes de disparar — receber dois convites diferentes
> queima o convite.

---

## 4. As duas contas que importam

Com cortesia só na quinta e a garrafa atrelada ao combo, a restrição muda de dia para
dia: **na quinta o gargalo é a cadeira; de sexta a domingo o número que importa é
quantos combos a equipe fecha.**

```
QUI 24 · experiencias = estacoes × (horas × 60 ÷ duracao) × 0,8
SEX a DOM · garrafas  = presencas × taxa_de_conversao_em_combo
```

**Quinta (premissa: 4 estações, sessões de 10 min):**
4 × (4h × 60 ÷ 10) × 0,8 = **76 experiências possíveis** para ~50 presentes.
Cabe todo mundo com folga. O `0,8` é a folga de troca, atraso e limpeza.

**Garrafas:** 165 presenças × 15% de conversão ≈ **25 combos**.
Mande fazer **40 garrafas** — a margem cobre um sábado acima da média, e a sobra
continua valendo: como a garrafa está presa à compra, não vira encalhe, vira
gatilho de venda no mês seguinte.

**Onde a garrafa fica:** à vista, na recepção, com o preço do combo escrito ao lado.
Brinde que ninguém vê não vende combo.

### Combos da tabela oficial

| Combo | O que inclui | Valor |
|---|---|---|
| **Fast Spa Detox** | Limpeza de pele Super VIP + Máscara de LED + Fast Spa Detox + Drenagem Linfática Facial (15min) | R$ 457,00 |
| **Fast Spa Casual** | Limpeza de pele Super VIP + Máscara de LED + Fast Spa Casual + Quick Massage | R$ 437,00 |

---

## 5. Regras de realocação e contingência

| Situação | O que fazer |
|---|---|
| Convidado não pode no dia dele | Realoque **para frente**: sexta → sábado, sábado → domingo. Nunca puxe ninguém para quinta (lista fechada e aprovada). |
| Quinta lotou | Corte primeiro pela lista D (equipe/família), que conhece a casa no dia 27. Institucional e imprensa não saem. |
| Sexta com <30 confirmações até 21/09 | Puxe 15 nomes do topo da lista F para a sexta e reponha o sábado com a lista G. Sexta vazia é o pior cenário. |
| Domingo com fila na porta | Senha numerada + cadastro no WhatsApp na entrada. Quem não for atendido sai com **voucher datado** para a semana seguinte. |
| Sobra de capacidade em qualquer dia | Libere no Stories com 3h de antecedência: "10 lugares abertos hoje até 17h". Lugar vazio não volta. |
| **A oferta que converte** | De sexta a domingo a convidada não experimenta o serviço: quem converte é a equipe. Combo Fast Spa Detox (R$ 457) e Combo Fast Spa Casual (R$ 437), com a **garrafa personalizada** como fechamento. Todo mundo do time precisa saber os dois preços de cor e **mostrar a garrafa antes de falar o valor**. |

---

## 6. Texto do convite (base)

```
Fast SPA · Limão

QUATRO DIAS PARA ABRIR AS PORTAS
Inauguração do Fast SPA Limão

24 quinta · 25 sexta · 26 sábado · 27 domingo

Av. Dep. Emílio Carlos, 358 · Limão · São Paulo
(no mesmo prédio da Fast Escova Limão)

[NOME], seu convite é para [DIA], às [HORA] · código [SPA-24-000]

Confirme até segunda, 21/09, pelo WhatsApp (11) 99024-3927
```

Os campos entre colchetes são preenchidos **por convidado**. O código
(`SPA-24-000`) serve para conferir a entrada e medir quem veio de qual lista.

---

## 7. Os quatro convites de WhatsApp (um por dia)

Artes em 1080×1350 (serve para WhatsApp e Stories), em `docs/convites/`:

| Dia | Arte | Vai para |
|---|---|---|
| Qui 24 | `convite-24-qui.png` | Listas A, B, C, D |
| Sex 25 | `convite-25-sex.png` | Lista E |
| Sáb 26 | `convite-26-sab.png` | Lista F |
| Dom 27 | `convite-27-dom.png` | Lista G |

Manda a imagem e o texto abaixo dela, na mesma mensagem. A arte é igual para todo
mundo daquele dia — quem personaliza é o texto (nome, horário, código).
Todas pedem a mesma coisa: responder **1** ou **2**. Resposta de uma tecla é o que
faz a confirmação realmente acontecer.

**Identidade:** segue o padrão da **Tabela de Serviços oficial** (`arte_5.pdf`):

| Elemento | Cor |
|---|---|
| Verde-petróleo (cabeçalho, títulos) | `#005A65` |
| Turquesa (rodapé, barras) | `#00A6A4` |
| Pêssego (fundo) | `#F6E3D2` |
| Creme (linhas de serviço) | `#FEF4E9` |
| Oliva (barra do dia) | `#8BA229` |
| Verde claro (destaque/cortesia) | `#C9DC94` |
| Carvão | `#555350` |

Tipografia: **Playfair Display** nos títulos, **Montserrat** nos textos.
Logo e ornamentos foram recortados da própria arte, em 300 dpi, e vivem em
`docs/convites/marca/` (`logo_fastspa.png`, `ornamento_comma.png`, `ornamento_faixa.png`).
Assinatura de rodapé: *Este lugar é pra você!* — a mesma da tabela.

> Para peça grande ou impressa, pedir o **logo vetorial** (AI/SVG/EPS) à franqueadora:
> o recorte atual é raster e só aguenta bem até o tamanho usado aqui.

**Cortesia x garrafa:** só a **quinta 24/09** tem experiência-cortesia. De sexta a
domingo as peças anunciam a **garrafa personalizada Fast SPA para quem fechar um
combo** — nenhuma arte promete serviço gratuito nem brinde por comparecer.

Para regerar as artes (se mudar horário, texto ou logo): edite
`docs/convites/gerar_convites.py` e rode `python3 docs/convites/gerar_convites.py`
— precisa do Chromium do Playwright.

### Qui 24 · listas A, B, C e D
```
[Nome], o Fast SPA Limão abre dia 25.

Na véspera, quinta 24/09, das 18h às 22h, recebemos um grupo pequeno para o corte
de fita, o tour da casa e uma experiência-cortesia — e sua presença faz falta nessa noite.

Av. Dep. Emílio Carlos, 358 · Limão
(no mesmo prédio da Fast Escova)

Responda 1 para confirmar ou 2 se não conseguir vir.
Rodrigo Garcia · Fast Limão
```

### Qui 24 · variação para a lista C (influenciadoras)
```
Oi [Nome]! Aqui é o Fast SPA Limão 🧖‍♀️

Abrimos dia 25 e queremos você na noite de estreia, quinta 24/09, das 18h às 22h:
tour da casa, coquetel e um ritual de 10 min por nossa conta, com espaço e luz
reservados para você gravar.

Av. Dep. Emílio Carlos, 358 · Limão

Responda 1 para confirmar ou 2 se preferir vir no sábado 26.
```

### Sex 25 · lista E (VIPs da Escova)
```
[Nome], tem novidade no prédio da Fast Escova 💛

Abrimos o Fast SPA Limão e sexta, 25/09, é o dia reservado para as clientes de casa
— antes de abrir para o bairro.

Separei um horário no seu nome: [HORA], para você conhecer a casa, falar com a
equipe e tomar um café com a gente.

Quem fechar um combo na inauguração leva a garrafa personalizada do Fast SPA.

Responda 1 para confirmar esse horário ou 2 para escolher outro.
```

### Sáb 26 · lista F (ativas + acompanhante)
```
[Nome], sábado 26/09 o Fast SPA Limão abre para você e uma amiga 🧖‍♀️

Venham conhecer a casa nova no seu horário: [HORA]. Tem música, mini-bar e
condição de inauguração nos combos — quem fechar leva a garrafa personalizada
do Fast SPA.

Av. Dep. Emílio Carlos, 358 · Limão
(no mesmo prédio da Fast Escova)

Responda 1 com o nome da amiga ou 2 se preferir domingo.
```

### Dom 27 · lista G (resgate e bairro)
```
[Nome], domingo 27/09 o Fast SPA Limão abre para o bairro, das 10h às 17h.

Sem hora marcada: é chegar, pegar sua senha e conhecer a casa. Quem aproveitar a
condição de inauguração nos combos leva a garrafa personalizada do Fast SPA.

Av. Dep. Emílio Carlos, 358 · Limão
(no mesmo prédio da Fast Escova)

Responda 1 se vier — guardo uma senha para você.
```

---

## 8. Cronograma até a inauguração

| Quando | O quê | Detalhe |
|---|---|---|
| **Sex 11/09** | Fechar as listas nominais | Puxar os cortes A–G do Trinks, tirar duplicados, atribuir dia e horário a cada nome |
| **Seg 14/09** | Disparo 1 · convite nominal | Todas as listas, com dia e hora definidos. No mesmo dia: save the date no Instagram e no Google |
| **Qui 17/09** | Disparo 2 · só quem não respondeu | Mesma mensagem + "ainda tenho [N] lugares no seu dia". Quem recusou entra na realocação |
| **Seg 21/09** | **Fecha o RSVP** | Lista final por dia, escala da equipe, compra de insumos e brindes, impressão das senhas de domingo |
| **Qua 23/09** | Lembrete de véspera | "É amanhã/sexta, às [HORA]. Chegue 10 min antes." Corta boa parte das ausências |
| **24 a 27/09** | Os quatro dias | Lembrete 3h antes de cada horário. Cadastrar **todo mundo** que entra: nome, WhatsApp e aniversário |
| **Seg 28/09** | Agradecimento e retorno | Mensagem para quem veio + voucher válido por 7 dias. É aqui que a inauguração vira agenda de outubro |

---

## 9. Amarrações com o que já existe no painel

- **Cadastro de porta** (nome + WhatsApp + aniversário) alimenta os templates
  `aniversario_fast_v1` e `reativacao_fast_v1` — ver `data/spa/BRIEF_MARKETING.md`.
- **WhatsApp Cloud do SPA** ainda sem WABA criada (pendência 1 do brief). Se não sair
  até 21/09, os disparos das listas E/F/G saem do número pessoal/comercial manualmente —
  **não bloqueia a inauguração**, mas bloqueia o pós-evento automatizado.
- **Google Business Profile do SPA** ainda não criado (pendência 2). A verificação por
  cartão postal leva 5–14 dias: se for essa a via, já passou do prazo para estar no ar
  em 24/09 — usar verificação por vídeo/telefone.
- **Voucher de retorno (28/09)** é o que transforma presença em receita de outubro;
  lançar como serviço promocional no Trinks para o painel medir a conversão.

---

## 10. Premissas a confirmar

1. **Número de estações de atendimento no SPA** (a conta usa 4).
2. **Duração da sessão-degustação** (a conta usa 20 min; 15 min no domingo).
3. **Serviços oferecidos na degustação** (massagem? ritual facial? plástica dos pés?).
4. **Tamanho real da base da Escova** para calibrar as listas E, F e G.
5. **Orçamento de coquetel/brindes** dos quatro dias.
6. Se a **franqueadora FAST** exige algum protocolo de inauguração (foto, placa, presença de diretoria).

---

*Plano gerado em 11/09/2026 em conversa com Claude. Fonte de verdade dos IDs e
pendências de mídia: `data/config.json` e `data/spa/BRIEF_MARKETING.md`.*
