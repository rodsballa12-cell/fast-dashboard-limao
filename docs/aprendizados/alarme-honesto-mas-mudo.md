---
titulo: "Consertei o alarme falso e criei o alarme mudo"
data: 2026-10-08
cargo: Memória
status: vigente
custo: "3 dias de mídia cega, sem um único e-mail"
---

## O que aconteceu

Em 17/09 o `alerta_entrega.py` gritou *"entrega despencou 85% — foi assim que
começou a parada de 27/08"* quando o token da Meta tinha morrido. O R$ 14,31
não era o gasto do dia: era o que a API alcançou antes de morrer.

Em 18/09 eu consertei: coleta com `_erro` passa a devolver `indef`, porque zero
por falta de dado e zero por falta de entrega pedem ações opostas. O conserto
estava certo.

Só que `indef` sai com **código 2**, e o workflow trata código 2 como *"não
falha, só avisa"*. Resultado, três semanas depois:

```
05/10 16h16  última coleta boa — escova R$ 701,63 / 7d
06/10 13h43  Meta recusa · grava zeros · carimba hoje · run VERDE
07/10 14h27  idem
08/10 14h25  idem
```

**Três dias de mídia cega, run verde todo dia, nenhum e-mail.** O detector
sabia exatamente o que estava errado — a mensagem da Meta estava gravada no
JSON, palavra por palavra — e disse para um log que ninguém lê.

Eu tinha calado o alarme falso e, sem perceber, calado o alarme.

## Por que era invisível

O arquivo é **reescrito todo dia com zeros**. `gerado_em` é sempre de hoje.
Qualquer verificação de frescor baseada na idade do arquivo passa: ele está
novíssimo, só está vazio.

A medida honesta não é a idade do arquivo. É **até quando a série diária
alcança** — ela só avança quando uma coleta dá certo. No dia 08/10 a série da
Escova parava em 04/10. Essa distância é a cegueira real.

## O que mudou

`alerta_entrega.py` agora separa dois casos dentro do mesmo erro:

| situação | nível | código | efeito |
|---|---|---|---|
| coleta falhou, série chega até ontem | `indef` | 2 | avisa, não falha — pode ser soluço |
| coleta falhou, série ≥ 2 dias atrás | `critico` | 1 | **run vermelho, e-mail sai** |

A mensagem crítica nomeia a credencial, não a conta de anúncio: *"Não olhe para
a conta de anúncio — olhe para a credencial"*. É o erro que o alerta de 17/09
cometeu, ao contrário.

## A regra

**Alarme que distingue bem e não acorda ninguém não é alarme, é anotação.**
Ao silenciar um falso positivo, pergunte sempre: *e o verdadeiro positivo, por
onde ele sai agora?* Toda exceção que você abre precisa de um caminho de volta
para o canal que acorda alguém.

Sétimo caso desta família: **"o passo rodou" não é "o passo funcionou"** — e
agora também **"o detector detectou" não é "alguém foi avisado"**.
