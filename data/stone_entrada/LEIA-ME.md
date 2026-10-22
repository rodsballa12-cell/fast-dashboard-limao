# Extrato Stone — como subir agora (mudou em 21/10/2026)

**Não suba mais o CSV por esta pasta no github.com.** O repositório é público e o
extrato bruto (com documento, agência e conta de destino) ficava visível no
histórico. Esta pasta continua existindo só como área de trabalho local; CSVs
aqui são ignorados pelo git.

## Como fazer

No PC, na pasta do projeto:

```
python scripts/stone_local.py "C:/Users/rods_/Downloads/extrato.csv"
```

Ou peça ao Claude Code: "sobe o extrato Stone que está em Downloads".

O script soma o arquivo ao histórico (mantém julho, agosto…, descarta repetidos),
grava só a versão criptografada (`data/stone_extrato.csv.enc`) e publica. O
painel pega no próximo refresh.

As regras de recusa (arquivo de outra conta, colunas diferentes) continuam as
mesmas — estão em `scripts/stone_merge.py`.
