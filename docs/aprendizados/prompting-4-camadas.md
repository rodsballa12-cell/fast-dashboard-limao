# Prompting em 4 camadas — regras destiladas

Origem: sessões claude.ai de ago/2026, capturadas em
`Cerebro_Claude/05-RECURSOS/Prompts-Claude-Inteligentes.md`.

---

## As 4 camadas (na ordem)

| # | Camada | O que responde | Exemplo FAST |
|---|---|---|---|
| 1 | **Contexto** | quem sou + qual o problema | "Sou o dono; conciliando Stone da Escova contra extrato de agosto" |
| 2 | **Tarefa** | exatamente o que fazer | "Consolide por tipo de transação e por dia" |
| 3 | **Restrições** | formato, limites, regras | "Saída em markdown, discrepâncias em negrito, sem narrativa" |
| 4 | **Fallback** | o que fazer se faltar informação | "Se o arquivo Stone não estiver disponível, avise e use o último disponível; se 'Desconhecido' passar de R$ 1.000, marque e siga" |

A camada 4 é a que mais economiza. As três primeiras evitam prompt vago.
A quarta evita a **pergunta de volta** — o ponto onde o agente já processou
tudo e trava esperando um dado que você poderia ter antecipado.

---

## Regra de 28/08 — registre o critério junto com o dado

Ao gravar qualquer número que dispara uma ação, grave a ação na mesma linha.

```
❌  alvo IBIT: $40
✅  alvo IBIT: $40 → ao superar, realizar 25–30% e subir o stop para o alvo antigo
```

Sem o critério, o agente sabe *qual é o número* mas não sabe *o que fazer
quando ele chegar* — e a pergunta repetida é exatamente a interação que a
camada 4 existe para eliminar.

Mesma família que o Fallback: a camada 4 responde "o que fazer se faltar
informação"; esta regra responde "o que fazer quando a informação chegar".
Juntas eliminam os dois pontos onde o agente para e espera.

---

## Métrica de autoavaliação

> Teve follow-up? O prompt foi ruim. Saiu pronto para encaminhar? Ganhou.
