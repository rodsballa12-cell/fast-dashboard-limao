---
titulo: "Como me pedir isso com menos idas e voltas"
projeto: Franquia_FAST_Limao
tipo: metodo
status: rascunho-v1
criado: 2026-09-08
tags: [prompts, metodo, claude]
---

# Como me pedir isso com menos idas e voltas

## O que aconteceu neste pedido

Você escreveu: *"Quero produtizar esse artefato para todos os franqueados do grupo
fast, aprox. 600, me ajude a entender como fazer isso e a montar um business plan."*

Foi um bom prompt, e vale entender por quê — tinha as três coisas que economizam idas
e voltas:

| Peça | O que você escreveu | Por que importa |
|---|---|---|
| **Contexto** | "esse artefato" + o repositório aberto | Eu li o código antes de opinar, em vez de perguntar o que ele faz |
| **Escala** | "aprox. 600" | Muda tudo. 6 lojas é copiar o repositório; 600 é banco de dados e BSP |
| **Entrega** | "entender como fazer" + "business plan" | Dois documentos, não uma conversa aberta |

**O que faltou** (e me custou algumas suposições): quem paga, qual seu papel no
negócio, e qual decisão isso precisa destravar. Eu assumi — modelo híbrido, você como
dono do produto, decisão = ir ou não à franqueadora. Se alguma dessas estiver errada,
me diga e eu refaço só a parte afetada.

## A fórmula das quatro linhas

Para pedidos grandes como este, quatro linhas resolvem quase sempre:

```
CONTEXTO:  onde estamos e o que já existe
OBJETIVO:  a decisão que isso precisa destravar (não a tarefa)
RESTRIÇÕES: orçamento, prazo, o que não pode mudar
ENTREGA:   formato, tamanho, para quem vai ler
```

Aplicada ao que você pediu:

> **Contexto:** painel da FAST Limão rodando em produção, li o repositório.
> **Objetivo:** decidir se levo isso para a franqueadora nos próximos 30 dias.
> **Restrições:** não sou programador, sem equipe, investimento até R$ 100 mil.
> **Entrega:** um plano técnico e um business plan, em markdown para o Obsidian.

Com isso eu teria pulado direto para os documentos, sem inferir nada.

## Três prompts prontos para este projeto

**Para refinar uma parte específica:**
> "Refaça só a seção 7 do 02-business-plan com estas premissas novas: [X]. Não mexa
> no resto do documento."

*Por que funciona:* delimita o alvo. "Melhore o business plan" me faz reescrever tudo,
inclusive o que já estava bom.

**Para decidir entre caminhos:**
> "Tenho duas opções: [A] e [B]. Critérios de decisão, nesta ordem: custo, prazo,
> risco. Me dê uma recomendação e o principal argumento contra ela."

*Por que funciona:* pedir o argumento contrário força análise em vez de concordância.

**Para tarefa técnica com Claude Code:**
> "Objetivo: [o resultado que quero ver funcionando]. Antes de escrever código, leia
> [arquivos] e me diga o que você entendeu e o que vai mudar. Espere eu confirmar."

*Por que funciona:* o checkpoint antes do código evita a situação cara — 300 linhas
escritas em cima de um mal-entendido.

## Cinco hábitos que economizam interações

1. **Peça a decisão, não a tarefa.** "Me ajude a decidir se vale produtizar" rende
   mais que "faça um business plan" — a segunda me faz preencher um formulário.
2. **Diga para quem é.** Um plano para você e um para a franqueadora são documentos
   diferentes. Sem isso, eu escrevo o do meio, que não serve para nenhum dos dois.
3. **Marque o que é chute.** Peça: "marque toda estimativa e liste o que preciso
   validar." Foi o que gerou a seção 9 do business plan — provavelmente a mais útil.
4. **Corrija sem recomeçar.** "A premissa X está errada, é Y — atualize as seções
   afetadas" é mais rápido e mais barato que refazer o pedido inteiro.
5. **Feche a sessão gravando.** "Salve o que decidimos hoje em [arquivo], no formato
   do vault." É o que mantém o cérebro do Obsidian utilizável.

## Sobre o Obsidian

Nesta sessão eu **não alcanço** o `C:\Users\rods_\OneDrive\Documentos\Obsidian Vault\
Cerebro_Claude` — ela roda num servidor na nuvem, isolado do seu PC. Só o Claude Code
rodando no seu computador chega lá.

O que dá para fazer:

- **Agora:** copiar a pasta `docs/produtizacao/` do repositório para o vault. Os
  arquivos já estão com frontmatter e links `[[wiki]]` prontos.
- **Melhor, uma vez só:** clonar o repositório dentro do vault. Aí `git pull` atualiza
  o cérebro sozinho, sem copiar nada à mão.
- **Sempre:** quando o assunto for o vault, abra o Claude Code no seu PC. Quando for o
  código, esta sessão na nuvem é melhor — ela tem o repositório na mão.
