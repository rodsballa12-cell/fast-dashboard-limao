---
name: extrato-stone
description: Entrada do extrato da Stone no histórico. Use quando o Rodrigo mandar um CSV exportado do app da Stone, disser "sobe o extrato", "atualiza o extrato da Stone", ou quando o painel estiver acusando venda sem pagamento e a suspeita for extrato atrasado. Sabe que sessão da nuvem NÃO faz isso (a chave do cofre está só no PC), que mesclar à mão quebra o arquivo, e que toda sangria no arquivo é a única medição de rendimento da Reserva que existe.
---

# Extrato Stone · como entra

## Cargo

Você põe o extrato novo dentro do histórico sem perder o que já estava lá e sem
vazar dado de cliente. São duas coisas fáceis de errar e caras de descobrir
depois.

## Antes de qualquer coisa: você consegue fazer isso?

**Sessão da nuvem não sobe extrato.** Desde 21/10/2026 o histórico vive
criptografado (`data/stone_extrato.csv.enc`) e a chave está no PC
(`.cofre/chaves.env`) e nos GitHub Secrets. Sem ela não dá para abrir o
histórico, somar nem fechar de novo.

Teste em um comando:

```bash
python3 scripts/cofre.py abrir
```

Se responder `falta FAST_PAINEL_SENHA`, você está na nuvem. **Diga isso na
primeira mensagem, não no fim**, passe o comando do PC (abaixo) e ofereça o que
dá para fazer daqui: ler o CSV numa pasta temporária e adiantar o que vem nele
— período, nº de lançamentos, total de entradas, se há sangria. Ler é seguro;
o que não pode é o arquivo entrar no repositório.

## A rotina, no PC

```
python scripts/stone_local.py "C:\Users\rods_\Downloads\extrato.csv"
```

Faz tudo: `git pull` → abre o cofre → soma (`stone_merge.py`) → fecha o cofre →
commita **só o `.enc`** → push. O painel pega no próximo refresh agendado.

Antes de rodar de verdade, vale ver o que vai entrar:

```
python scripts/stone_merge.py --dry-run
```

Ele imprime quantos lançamentos leu, quantos são novos e quantos já tinha.

## Três coisas que você nunca faz

**Nunca mesclar à mão.** Parece um merge de CSV trivial e não é. O
`stone_merge.py` preserva o CRLF que a Stone entrega (reescrever em LF suja o
diff do arquivo inteiro) e recusa extrato de **outra conta Stone** — a trava
existe porque misturar as duas contas transformou o dinheiro de uma loja em
"não conciliado" da outra no painel do Spa, em 25/09/2026. Em 10/10 eu comecei
uma mesclagem manual por hábito e só não publiquei porque fui ler o repositório
antes.

**Nunca subir o CSV pelo github.com.** O repositório é público e o extrato traz
nome, documento, agência e conta. Era a rota antiga; hoje
`data/stone_entrada/*.csv` está no `.gitignore` justamente para isso não
acontecer por acidente.

**Nunca substituir o histórico pelo arquivo novo.** A exportação da Stone traz
só uma janela, normalmente o mês corrente. Trocar apaga julho, agosto e, com
eles, a visão do ano, o histórico da Reserva e a base de recebíveis em D+30.

## Se houver sangria no arquivo, pare e meça

Sangria é o par: um **crédito "Transação" vindo da própria Stone** (o resgate
voltando da Reserva) seguido de um **débito Pix** para o banco principal.

Isso é mais que um lançamento. O rendimento da Reserva é invisível no dia a dia
— o extrato que chega é o da *conta*, e quando a varredura sai ele perde a
pista do dinheiro. **A sangria é o único momento em que o rendimento aparece**,
porque o resgate volta maior que o principal que foi varrido.

Em 10/10/2026: resgate de R$ 49.591,42 contra R$ 49.510,06 de principal —
**R$ 81,36 de rendimento real**. A estimativa do painel, que usava CDI cheio,
dizia R$ 339,87: errava por 4×. Parte é imposto (IOF morde rendimento resgatado
antes de 30 dias; o dinheiro tinha 17 dias médios), parte não dá para separar,
porque o extrato traz um número só.

O `stone_processor.py` já faz essa conta sozinho e recalibra a projeção. O que
cabe a você é **não** deixar passar em branco: diga o valor medido ao Rodrigo e
registre em `docs/aprendizados/` se a taxa mudar de patamar.

## Depois de subir

1. `python3 scripts/auditoria_coerencia.py` — exit 0 é o esperado.
2. O painel atualiza no próximo refresh. Se for urgente, o refresh pode ser
   disparado à mão, mas custa ~27 chamadas da cota do Trinks — não faça por
   hábito.
3. Publicar no Artifact do celular é outro cargo (`/publicar`), e o encaixe
   natural dele é o Conselho das 22h30.

## O Spa é outro arquivo

O `stone_local.py` atende só a Escova (`data/stone_extrato.csv.enc`). O Spa tem
conta e histórico próprios (`data/spa/stone_extrato.csv.enc`). Se um extrato do
Spa for passado para a rota da Escova, a checagem de conta **recusa** e o
arquivo fica intacto na pasta — é o comportamento certo, não um erro para
contornar. O caminho do Spa é o `stone_merge.py` com
`--destino data/spa/stone_extrato.csv`, com o cofre aberto.

## Por que isso importa mesmo quando ninguém reclamou

Extrato atrasado não fica quieto: ele vira alarme falso. Em 15/09 o briefing
abriu com *"15 PIX sem confirmação, R$ 1.599, ligue para cada cliente hoje"* —
catorze eram posteriores ao último dia do extrato. Não era dinheiro sumido, era
foto velha. Antes de repetir qualquer alarme de conciliação, olhe até quando vai
`stone.periodo_fim`.

## Alçada

**Decide sozinho:** rodar o `--dry-run`, ler o CSV para adiantar os números,
apontar sobreposição e dias sem cobertura, calcular o rendimento de uma sangria.

**Nunca:** mesclar à mão · subir CSV pelo repositório público · substituir o
histórico · commitar o CSV em claro · publicar o Artifact por conta própria.
