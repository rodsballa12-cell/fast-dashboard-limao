---
name: caixa-de-entrada
description: Processa os extratos que o Rodrigo manda pelo celular. Use quando ele disser "chegou extrato", "mandei os extratos", "processa a caixa", "atualiza tudo" ou anexar um CSV/XLSX de banco no chat. Identifica cada arquivo (Stone Escova, Stone Spa, XP conta corrente, XP investimento), roda a rota certa de cada um, atualiza planilha, painel e relatórios, e devolve UMA tabela. Só funciona no PC (cofre + Excel); na nuvem, diz isso na primeira linha.
---

# Caixa de Entrada · extrato do celular → relatórios atualizados

## Como o Rodrigo usa

1. No celular, ele exporta o extrato no app do banco e salva no **OneDrive**, na pasta
   `Franquia - FAST\Claude\Extratos\_entrada` (ou anexa direto neste chat).
2. Escreve aqui: **"chegou extrato"**.
3. Recebe de volta uma tabela só, e responde "aprovado" quando houver algo para gravar na planilha.

Ele não é programador e está no celular: respostas curtas, em reais e dias, sem nome de
arquivo ou função sem dizer o que a coisa faz.

## Passo 0 · você está no PC?

```
python scripts/cofre.py abrir
```

Se falhar por falta de chave, você está na nuvem: diga na **primeira linha** que o PC precisa
estar ligado com a sessão "FAST · Caixa de Entrada" aberta, e pare. Não finja processar.

Antes de tudo: `git pull --rebase --autostash origin main` e depois `python scripts/cofre.py abrir`.

## Passo 1 · achar e identificar os arquivos

Pasta de entrada: `C:\Users\rods_\OneDrive\Franquia - FAST\Claude\Extratos\_entrada`
(se ele anexou no chat, use o anexo; se não achar nada, olhe também `C:\Users\rods_\Downloads`
pelos arquivos de hoje e pergunte antes de usar).

Identifique pelo **conteúdo**, não pelo nome:

| Arquivo | Como reconhecer | Rota |
|---|---|---|
| Stone **Escova** | CSV da Stone, conta 98432083-8 | `stone_merge.py --dry-run`, depois `stone_local.py "<csv>"` |
| Stone **Spa** | CSV da Stone, conta 70951239-6 | `stone_merge.py --destino data/spa/stone_extrato.csv` (cofre aberto), depois `stone_spa_razao.py` |
| XP **conta corrente** (Siibello) | CSV da XP com Pix/boletos | `extrato_xp.py` para classificar; lançamento na aba Conta_XP (Passo 3) |
| XP **investimento** (fundo BNP) | XLSX da XP com aplicação/resgate/cotas | Passo 3, só a posição e os movimentos |

Arquivo que não se encaixa em nenhuma linha: **não processe**. Liste como "não reconheci".
Regras da Stone (nunca mesclar à mão, nunca trocar o histórico, conta errada é recusada
de propósito): `.claude/skills/extrato-stone/SKILL.md`.

## Passo 2 · Stone

- Mostre o resultado do `--dry-run` (quantos lançamentos novos, período coberto).
- **Sangria** (crédito vindo da Reserva + Pix para a XP): informe o rendimento medido da
  Reserva. É a única medição real que existe.
- O período novo do extrato (`stone.periodo_fim`) vai na tabela final: ele é um dos dois
  relógios de atraso do Financeiro.

## Passo 3 · XP na planilha (pede "aprovado" antes de gravar)

Planilha: `C:\Users\rods_\OneDrive\Franquia - FAST\Claude\Painel_Gestao_Financeira_SIIBELLO.xlsx`, aba `Conta_XP`.

1. Compare o extrato com o razão **por data + valor**, nunca por número de linha.
2. Monte a lista do que ainda **não** está no razão, com a categoria proposta pelo `extrato_xp.py`.
3. Mostre ao Rodrigo (data, descrição curta, valor, categoria) e **espere "aprovado"**.
4. Grave pelo Excel (COM), com a planilha **fechada**, do mesmo jeito que `atualiza_painel.py`
   faz. Planilha aberta = pare e peça para ele fechar. Nunca use openpyxl na planilha.
5. Confira o saldo final do razão contra o saldo do extrato. Divergência vai para a tabela, não
   é corrigida sozinha.

**Nunca leia receita do extrato XP** (é conta de pagamento; aporte entre sócios passa por ela).

## Passo 4 · atualizar tudo

Na ordem, parando no primeiro erro:

```
python scripts/stone_reserva_excel.py
python scripts/atualiza_painel.py
python scripts/gerar_financeiro.py
python scripts/cofre.py fechar
python scripts/auditoria_coerencia.py
```

Commit **só dos `.enc`** e push (nunca o arquivo aberto). O painel do celular pega no
próximo refresh; publicar no Artifact é o cargo `/publicar`, ofereça em uma linha.

## Passo 5 · arrumar a caixa

Mova cada arquivo processado para `Extratos\_processados\AAAA-MM-DD\`. Os que não
foram processados ficam em `_entrada`.

## Resposta final (uma tabela só)

| Extrato | Período | Entrou | Mudou na planilha | Mudou no painel | Atenção |
|---|---|---|---|---|---|

Depois da tabela, no máximo 3 linhas: o que a auditoria acusou e o que espera aprovação dele.

## Nunca

- Alterar meta, `financeiro.json` ou a planilha além dos lançamentos aprovados.
- Corrigir divergência sem aprovação: mostre e espere.
- Commitar extrato bruto ou arquivo aberto do cofre (o repositório é público).
- Preencher número que não foi lido; o que faltar vira `NÃO VEJO`.
