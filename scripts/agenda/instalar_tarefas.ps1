<#
  Registra a rodada da madrugada no Agendador do Windows: os sete cargos em fila, às 00h40.

  Use Register-ScheduledTask em vez de schtasks porque só ele expõe
  StartWhenAvailable: se o computador estiver desligado na hora, a tarefa roda
  assim que ligar, em vez de pular o dia inteiro em silêncio.

  COMO RODAR — PowerShell COMO ADMINISTRADOR:
    powershell -ExecutionPolicy Bypass -File "C:\Users\rods_\dev\fast-dashboard-limao\scripts\agenda\instalar_tarefas.ps1"

  É idempotente: rodar de novo substitui as tarefas em vez de duplicar.
  Para remover tudo:  .\instalar_tarefas.ps1 -Remover
#>
param(
  [string]$Projeto = "C:\Users\rods_\dev\fast-dashboard-limao",
  [switch]$Remover
)

$ErrorActionPreference = "Stop"

function Falhar($msg) { Write-Host "`n[X] $msg" -ForegroundColor Red; exit 1 }
function Ok($msg)     { Write-Host "[ok] $msg" -ForegroundColor Green }
function Aviso($msg)  { Write-Host "[!] $msg" -ForegroundColor Yellow }

# --- Conferências antes de mexer em qualquer coisa -------------------------
$admin = ([Security.Principal.WindowsPrincipal] `
  [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { Falhar "Rode este arquivo num PowerShell aberto COMO ADMINISTRADOR." }

$runner = Join-Path $Projeto "scripts\agenda\rodar_agente.ps1"
if (-not (Test-Path $runner)) { Falhar "Não achei $runner. Confira o caminho do projeto (-Projeto)." }

# Uma tarefa so, com os sete cargos EM FILA (desde 18/11/2026).
#
# Por que de madrugada: a assinatura do Claude tem uma cota que vale por 5 horas
# e e dividida com todas as outras rotinas do Rodrigo (painel de investimentos
# das 07h14 as 19h14, cotacoes de hora em hora no pregao, midias 08h e 18h,
# cerebro 19h). Em 11/11 o conselho das 22h30 caiu no "5-hour limit" aberto as
# 19h; em 14/11 memoria, marketing e financeiro cairam na janela das 03h40.
# Das 00h40 as ~03h nada mais roda, e a janela fica so para a FAST.
#
# Por que em fila e nao em sete horarios: o Agendador roda as acoes de uma
# tarefa uma depois da outra. Se o PC estava desligado, StartWhenAvailable
# dispara a fila inteira quando ele ligar, e mesmo assim um cargo nao atropela
# o outro (antes as sete tarefas atrasadas disparavam juntas).
#
# O conselho e o ultimo: le os seis pareceres que acabaram de sair. Todos falam
# do dia que fechou (antes do meio-dia o dia de referencia e ontem).
$Hora  = "00:40"
$Nome  = "FAST\Rodada da madrugada"
$fila  = @("memoria","marketing","financeiro","relacionamento","pessoas","operacao-diaria","conselho")

# Remove TODAS as tarefas antigas da pasta FAST (uma por cargo, horarios de dia):
# se ficassem, cada cargo rodaria duas vezes e gastaria cota em dobro.
foreach ($velha in @(Get-ScheduledTask -TaskPath "\FAST\" -ErrorAction SilentlyContinue)) {
  Unregister-ScheduledTask -TaskName $velha.TaskName -TaskPath $velha.TaskPath -Confirm:$false
  Ok "removida: $($velha.TaskName)"
}

if ($Remover) {
  Write-Host "`nTarefas removidas. Os cargos continuam existindo, so nao sao chamados sozinhos."
  exit 0
}

# 'claude' pode não estar no PATH quando a tarefa roda sem sessão interativa.
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
  Aviso "O comando 'claude' não está no PATH desta sessão. O runner tenta caminhos conhecidos, mas se os briefings saírem com erro, rode 'where claude' e me diga o caminho."
}

$acoes = foreach ($ag in $fila) {
  New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument ("-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$runner`" " +
               "-Agente $ag -Ontem -Projeto `"$Projeto`"" +
               $(if ($ag -eq "conselho") { " -Publicar" } else { "" }))
}
$gatilho = New-ScheduledTaskTrigger -Daily -At $Hora
# WakeToRun: acorda o PC da suspensao para rodar (desligado de vez, nao).
# StartWhenAvailable: se perdeu o horario, roda assim que o PC ligar.
# Sete cargos de ate ~20 min cada: limite de 3 horas para a fila inteira.
# RestartCount: se falhar, refaz; quem ja tem ata valida do dia e pulado em
# segundos pelo rodar_agente.ps1, entao refazer nao gasta cota de novo.
$config = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun `
  -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
  -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
  -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 10)

Register-ScheduledTask -TaskName $Nome -Action $acoes -Trigger $gatilho `
  -Settings $config -Force `
  -Description "Os sete cargos da FAST em fila, de madrugada, fora da hora das outras rotinas do Claude" | Out-Null
Ok "$Nome  $Hora  ·  $($fila -join ' > ')"

Write-Host "`nConferindo..."
Get-ScheduledTask -TaskPath "\FAST\" | Select-Object TaskName, State,
  @{n="Proxima"; e={ (Get-ScheduledTaskInfo $_.TaskName -TaskPath $_.TaskPath).NextRunTime }} |
  Format-Table -AutoSize

Write-Host "Os briefings aparecem em:" -ForegroundColor Cyan
Write-Host "  Obsidian Vault\Cerebro_Claude\Briefings\AAAA-MM-DD-<cargo>.md`n"
Write-Host "Para testar agora, sem esperar o horário:" -ForegroundColor Cyan
Write-Host "  Start-ScheduledTask -TaskName 'FAST\Rodada da madrugada'`n"
