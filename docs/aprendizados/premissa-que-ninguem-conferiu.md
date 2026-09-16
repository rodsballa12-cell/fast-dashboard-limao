# Construí uma conclusão grave sobre premissas que ninguém tinha conferido

**Descoberto em:** 16/09/2026 · **Custo:** disse ao Rodrigo que o negócio dele
não fechava no zero nem batendo a meta. Estava errado, e por larga margem.

## O que eu afirmei

Em 16/09 de manhã, depois de classificar o extrato da XP:

> *"A loja não fecha no zero nem cravando a meta. Precisa de R$ 74 a 89 mil
> para empatar, e a meta é R$ 60.000."*

Era uma frase para mudar a vida de alguém. Sugeria que o negócio tinha um
buraco estrutural, que a franqueadora tinha dimensionado errado, e que nada do
que se fizesse no dia a dia resolveria.

## O que era verdade

Naquela mesma tarde o Excel foi atualizado com os números reais:

| | eu usei | era |
|---|---:|---:|
| Comissão | 37,4% / 43,6% | **35,1%** |
| Insumos (CMV) | 12% | **6,0%** |
| Inadimplência | 2% | **0%** |
| Margem de contribuição | 41,6% / 35,4% | **51,9%** |
| **Ponto de equilíbrio** | R$ 74.128 / R$ 89.208 | **R$ 58.729** |

A meta de R$ 60.000 **é** o ponto de equilíbrio — resultado de +R$ 660. A
franqueadora dimensionou certo; eu é que estava somando custo que não existia.

## De onde vieram os números errados

**Nenhum deles era invenção minha. Todos estavam no `financeiro.json`** — e
eram premissas que alguém escreveu uma vez e ninguém revisitou:

- CMV a 12% era "padrão Fast Escova", escrito como nota na própria linha. O
  realizado do mês estava a 5,2% e eu tinha esse número na mão.
- Inadimplência de 2% aplicada em 60 meses de projeção, numa loja que **não
  tem inadimplência** — é sem hora marcada, o cliente paga e sai.
- A comissão de 43,6% foi erro meu de conta: dividi pagamentos até 15/09 por
  produção até 31/08. O lote de 15/09 já cobria setembro.

## A parte que dói

Eu *tinha* o dado que contradizia a premissa. O CMV realizado aparecia no
mesmo arquivo, na linha de baixo. Não olhei porque a premissa vinha rotulada
como oficial, e o que vem rotulado como oficial parece conferido.

**Errei na direção mais cara possível**: uma conclusão pessimista sobre a
viabilidade do negócio, entregue com tabela e três casas decimais.

## As regras

1. **Premissa não é dado.** Toda linha com um percentual redondo — 12%, 2%,
   37,4% — é uma escolha de alguém, não uma medição. Antes de construir
   conclusão sobre ela, procure o realizado ao lado.
2. **Conclusão estrutural exige dado estrutural.** "Este negócio não fecha no
   zero" não se diz com premissa herdada. Ou se confere cada componente, ou se
   diz "com as premissas atuais, que não conferi".
3. **Erro pessimista não é mais seguro que erro otimista.** Parece prudente e
   não é: quase levou a discutir o tamanho da meta em vez de trabalhar para
   alcançá-la — que era o que cabia o tempo todo.
4. **Quando a correção vier, corrija com o mesmo tamanho do erro.** Se a
   afirmação foi uma tabela, a correção é uma tabela. Não se conserta manchete
   com nota de rodapé.
