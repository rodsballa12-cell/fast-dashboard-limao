# Agenda dos cargos — rodando sozinhos

Os cargos não disparam sozinhos: alguém precisa chamar. Esta pasta transforma
isso em tarefa agendada do Windows, usando a assinatura Max que já está logada
no Claude Code do PC. **Não gera custo adicional.**

## Onde o resultado aparece

`Obsidian Vault / Cerebro_Claude / Briefings / AAAA-MM-DD-<cargo>.md`

O da noite — `AAAA-MM-DD-conselho.md` — é o mais importante: é o fechamento do
dia nas quatro janelas (dia, semana, mês, ano), com as decisões que sobraram
para você.

O vault sincroniza pelo OneDrive, então o briefing chega no celular sozinho.
O repositório guarda o que a **empresa** sabe; o vault guarda o que o **dono**
leu — por isso o briefing vai para lá.

## Registrar as tarefas

**Um comando.** PowerShell **como administrador**:

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\rods_\dev\fast-dashboard-limao\scripts\agenda\instalar_tarefas.ps1"
```

Ou, mais simples ainda, peça ao Claude Code aberto no projeto:

```
registre as 4 tarefas agendadas rodando scripts/agenda/instalar_tarefas.ps1
```

O instalador confere antes de mexer: se você não estiver como administrador,
ele para e avisa; se o caminho do projeto estiver errado, também. É idempotente
— rodar de novo substitui em vez de duplicar.

Ele usa `Register-ScheduledTask` em vez de `schtasks` por um motivo prático:
só esse caminho expõe **`StartWhenAvailable`**. Com ele, se o computador
estiver desligado na hora, a tarefa roda assim que ligar — em vez de pular o
dia inteiro em silêncio, que é o tipo de falha que ninguém percebe.

Para desfazer tudo:

```powershell
powershell -ExecutionPolicy Bypass -File "...\instalar_tarefas.ps1" -Remover
```

## Conferir e testar

```powershell
schtasks /Query /TN "FAST\*" /FO LIST          # ver as quatro
schtasks /Run   /TN "FAST\Operacao 11h30"      # rodar agora, sem esperar
```

Depois de rodar à mão, abra a pasta `Briefings` — o arquivo do dia deve estar lá.

## Se o computador estiver desligado na hora

A tarefa não roda. Para recuperar a execução perdida ao ligar:

```powershell
schtasks /Change /TN "FAST\Operacao 11h30" /ENABLE
```

e marque **"Executar assim que possível após perder um início agendado"** nas
propriedades da tarefa (Agendador de Tarefas → a tarefa → Configurações).

## Desligar uma tarefa

```powershell
schtasks /Change /TN "FAST\Marketing sexta" /DISABLE   # pausa
schtasks /Delete /TN "FAST\Marketing sexta" /F         # remove
```

## Por que quatro tarefas cobrem os sete cargos

Os três da manhã e do meio-dia são os **acionáveis**: dá tempo de fazer algo
com o que eles dizem.

O **Conselho das 22h30 convoca os seis departamentos** — inclusive `/financeiro`
e `/pessoas`, que não têm tarefa própria. Eles não ganham briefing individual
de propósito: dependem de dado que entra à mão (DRE, extrato Stone, regra de
comissão), e relatório diário sobre dado parado mostra o mesmo número todo dia
e ensina a ignorar o aviso. Dentro do conselho eles falam quando têm o que
dizer, e declaram o atraso do dado quando não têm.

`/memoria` roda sozinho por outro caminho: a auditoria de coerência executa
todo dia às 07h no GitHub Actions e falha o workflow quando os números não
batem entre unidades, períodos e consolidado.

## O risco que isso carrega

Entre 24/08 e 04/09 um fluxo criava uma tarefa de aprovação por dia: **9
criadas, 7 nunca respondidas**. Relatório automático que ninguém lê é pior que
nenhum — ensina a ignorar.

**Se em duas semanas você não estiver abrindo os briefings, desligue.** O
problema não terá sido a automação, e sim o ritual que ela tentou substituir.
