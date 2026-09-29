# Anúncio WhatsApp — Pacote Renove-se até 30/09

Data: **terça, 29/09/2026**. Prazo da promoção: **quarta, 30/09** ("até amanhã"),
que é também o último dia do mês.
Novidade a comunicar: **parcelamento em até 3x no cartão**.

## Artes geradas

| Arquivo | Formato | Quando usar |
|---|---|---|
| `artes-abertura/png/promo-renovese-ate-amanha.png` | 1080×1350 | **hoje**, no WhatsApp e no feed |
| `artes-abertura/png/promo-renovese-ate-amanha-story.png` | 1080×1920 | **hoje**, nos stories |
| `artes-abertura/png/promo-renovese-ultimo-dia.png` | 1080×1350 | **amanhã**, no WhatsApp e no feed |
| `artes-abertura/png/promo-renovese-ultimo-dia-story.png` | 1080×1920 | **amanhã**, nos stories |

Fonte editável: os `.html` de mesmo nome em `artes-abertura/`.

A arte de hoje diz **SÓ ATÉ AMANHÃ**; a de amanhã diz **HOJE É O ÚLTIMO DIA**.
São peças de uso datado — a de hoje não pode ser reenviada amanhã, porque
"amanhã" já seria 01/10 e a promoção teria acabado.

### Fundo (revisão de 29/09)

Rodrigo pediu a arte "mais com a cara do spa", com **foto de massagem ao fundo
em marca d'água**. O fundo passou a ter quatro camadas:

1. `fotos/textura-toalha.jpg` — textura real de toalha branca, extraída da
   própria peça oficial da franqueadora;
2. cáusticas de água (ruído fractal em teal, filtro SVG);
3. ondas horizontais deslocadas por ruído — o desenho de superfície de água;
4. anéis concêntricos, como gota caindo na água;
5. véu branco em diagonal, mais forte na coluna do texto, para o contraste de
   leitura não cair.

**A foto de massagem ainda não entrou.** O gerador de imagem do Canva devolveu
"Too many requests" em seis tentativas seguidas — é limite de uso da conta, não
falta de recurso. Duas saídas, em ordem de preferência:

- **Uma foto real do Spa do Limão** (maca, toalhas, uma sessão acontecendo, luz
  clara). É melhor que qualquer banco de imagem: é o espaço dela, não um spa
  genérico. Entra trocando uma linha em `fotos/`.
- Repetir a geração no Canva mais tarde, quando o limite liberar.

O arquivo está montado para a troca: basta substituir `fotos/textura-toalha.jpg`
mantendo o nome, ou apontar `.foto` para o novo arquivo. Nada mais muda.

### O que a arte mantém e o que acrescenta

Mantém a oferta oficial da franqueadora sem alterar nada: Pacote Renove-se,
10 sessões por R$ 1.490, +1 sessão Renove-se, +2 sessões à escolha, +1 escova
bônus na Fast Escova.

Acrescenta o que é do Limão: o prazo, o **3x no cartão**, o "sem hora marcada",
o endereço 358 e o estacionamento próprio.

---

## Mensagem 1 — grupo VIP (transmissão, ninguém responde no grupo)

```
Última chamada 🩵

O Pacote Renove-se vai até amanhã.

10 sessões por R$ 1.490 — ou 3x de R$ 496,67 no cartão.

Fechando o pacote, você ganha:
+ 1 sessão Renove-se
+ 2 sessões à sua escolha
+ 1 escova bônus na Fast Escova

É só passar no Spa até amanhã e fechar na recepção. Sem hora marcada.

📍 Av. Dep. Emílio Carlos, 358 · Limão
🅿️ Estacionamento próprio

Quer garantir antes de vir? Chama no (11) 99024-3927.
```

O grupo é só de transmissão — por isso a mensagem **não** pede "responde aqui".
Manda para o número do Spa, que é onde alguém atende.

## Mensagem 2 — envio individual (1 a 1)

```
Oi, [Nome]! 🩵

O Pacote Renove-se vai só até amanhã: 10 sessões por R$ 1.490,
ou 3x de R$ 496,67 no cartão.

E fechando o pacote você ganha +1 sessão Renove-se, +2 sessões à sua
escolha e +1 escova bônus na Fast Escova.

Quer que eu separe o seu? Me responde aqui que eu deixo pronto.
```

Curta de propósito: no 1 a 1 a arte já carrega o detalhe, e a mensagem só
precisa abrir a conversa.

## Mensagem 3 — status do WhatsApp

```
Pacote Renove-se só até amanhã.
10 sessões por R$ 1.490 ou 3x no cartão.
Fast Spa Limão · sem hora marcada 🩵
```

---

## Três coisas para confirmar antes de enviar

### 1. O parcelamento é sem juros?

A arte e as mensagens dizem **"3x no cartão"**, sem afirmar "sem juros" — porque
isso não foi confirmado. Se o Spa absorve a taxa da maquininha e a cliente paga
R$ 1.490 no total, **"3x sem juros" converte muito mais** e vale trocar em todas
as peças. Se quem parcela é a administradora do cartão e a cliente paga mais,
a redação atual está certa e não pode mudar.

### 2. O centavo

R$ 1.490 ÷ 3 = R$ 496,666…

A maquininha divide em **R$ 496,67 + R$ 496,67 + R$ 496,66**, fechando exatos
R$ 1.490,00. A arte mostra "3x de R$ 496,67", que é o arredondamento padrão.
Avisar a recepção para não estranhar a última parcela diferente.

### 3. O prazo é mesmo 30/09?

"Até amanhã" põe o fim em **quarta, 30/09** — último dia do mês. Se o prazo real
for outro, a arte precisa mudar antes de sair. Prazo errado em peça de urgência
queima a credibilidade da próxima.

---

## Como enviar (ordem que funciona)

1. **Arte primeiro, texto depois**, em duas mensagens separadas. A imagem abre
   no preview do WhatsApp e para o dedo; o texto legendado dentro da imagem não
   é lido.
2. **Grupo VIP agora** (hoje, terça) e **1 a 1 amanhã de manhã** para quem não
   respondeu. Duas ondas, não uma.
3. **Stories nas duas contas** — @fastspa.limao e @fastescova.limao. A base da
   Escova é maior e é ela que sustenta o Spa neste começo.
4. **Amanhã**, trocar para as peças `ultimo-dia`.

## Depois que acabar

Anotar quantos pacotes fecharam nestes dois dias e por qual caminho (grupo VIP,
1 a 1, stories, ou quem chegou sem ter visto nada). É o primeiro número real de
conversão do Spa — sem ele, a próxima promoção é chute de novo.
