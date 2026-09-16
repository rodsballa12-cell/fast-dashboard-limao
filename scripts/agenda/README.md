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

## As sete tarefas

| Hora | Cargo | Por que esse horário |
|---|---|---|
| 07h30 | `/memoria` | lê a auditoria de coerência que roda às 07h no GitHub |
| 08h00 | `/marketing` | o refresh de mídia sai às 07h |
| 08h30 | `/financeiro` | caixa e margem antes de o dia começar a gastar |
| 09h00 | `/relacionamento` | chamar quem sumiu antes do movimento começar |
| 09h30 | `/pessoas` | equipe e escala antes do turno da tarde |
| 11h30 | `/operacao-diaria` | o painel atualiza às 11h — ainda dá tempo de salvar o dia |
| 22h30 | `/conselho` | fecha o dia nas quatro janelas, com os seis departamentos |

Um cargo, uma tarefa. O Conselho continua convocando todo mundo à noite — o
briefing individual da manhã é para agir, a reunião da noite é para decidir.

### A trava contra ruído

`/financeiro`, `/pessoas` e `/memoria` dependem de dado que entra à mão e fica
parado por dias. Os três têm instrução explícita na ficha: **dia sem novidade,
uma linha e pronto.**

Isso importa mais do que parece. Entre 24/08 e 04/09 um fluxo criava uma tarefa
de aprovação por dia: 9 criadas, **7 nunca respondidas**. Não falhou por estar
errado — falhou por ser repetitivo. Briefing que repete o mesmo número toda
manhã treina quem lê a não abrir.

## O risco que isso carrega

Entre 24/08 e 04/09 um fluxo criava uma tarefa de aprovação por dia: **9
criadas, 7 nunca respondidas**. Relatório automático que ninguém lê é pior que
nenhum — ensina a ignorar.

**Se em duas semanas você não estiver abrindo os briefings, desligue.** O
problema não terá sido a automação, e sim o ritual que ela tentou substituir.

## O que mais roda junto: Reserva Stone no Excel

Logo depois do `git pull`, toda rodada chama `scripts/stone_reserva_excel.py`.
Ele lê `data/stone_extrato.csv` com o mesmo processador do painel e grava o
**principal aplicado na Reserva Stone** no rodapé da aba `Conta_XP` do Excel —
linha que entra no saldo total da empresa.

- Só abre o Excel quando chegou extrato Stone novo; senão registra "sem novidade".
- Se a planilha estiver aberta, pula e tenta na próxima rodada.
- Grava pelo próprio Excel, nunca pelo openpyxl (que apagaria o valor
  calculado das fórmulas que o `gerar_financeiro.py` lê).
- Falha nunca derruba o cargo: vai para o `_execucoes.log` e a rodada segue.

Para rodar na hora, sem esperar a agenda: `python scripts/stone_reserva_excel.py`.

