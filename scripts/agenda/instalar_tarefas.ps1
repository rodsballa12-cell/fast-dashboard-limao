<#
  Registra as sete tarefas agendadas dos cargos no Agendador do Windows — uma por cargo.

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

# As tarefas: nome, agente, hora, e por que esse horário.
$tarefas = @(
  @{ Nome="FAST\Memoria 07h30";      Agente="memoria";          Hora="07:30"
     Porque="lê o resultado da auditoria de coerência que roda às 07h no GitHub" }
  @{ Nome="FAST\Marketing 08h";      Agente="marketing";        Hora="08:00"
     Porque="o refresh de mídia tem seis fires entre 06h05 e 11h05; o cargo confere o gerado_em e diz a idade do dado" }
  @{ Nome="FAST\Financeiro 08h30";   Agente="financeiro";       Hora="08:30"
     Porque="caixa e margem antes do dia começar a gastar" }
  @{ Nome="FAST\Relacionamento 09h"; Agente="relacionamento";   Hora="09:00"
     Porque="chamar quem sumiu antes do movimento começar" }
  @{ Nome="FAST\Pessoas 09h30";      Agente="pessoas";          Hora="09:30"
     Porque="equipe e escala antes do turno da tarde, que é onde o movimento está" }
  @{ Nome="FAST\Operacao 11h30";     Agente="operacao-diaria";  Hora="11:30"
     Porque="o painel atualiza às 11h — ainda dá tempo de salvar o dia" }
  @{ Nome="FAST\Conselho 22h30";     Agente="conselho";         Hora="22:30"
     Porque="fecha o dia depois do último refresh, das 22h" }
)

if ($Remover) {
  foreach ($t in $tarefas) {
    if (Get-ScheduledTask -TaskName $t.Nome -ErrorAction SilentlyContinue) {
      Unregister-ScheduledTask -TaskName $t.Nome -Confirm:$false
      Ok "removida: $($t.Nome)"
    }
  }
  Write-Host "`nTarefas removidas. Os cargos continuam existindo — só não são chamados sozinhos."
  exit 0
}

# 'claude' pode não estar no PATH quando a tarefa roda sem sessão interativa.
# O rodar_agente.ps1 já procura em locais conhecidos, mas avisar aqui evita
# descobrir isso só amanhã de manhã, num briefing vazio.
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
  Aviso "O comando 'claude' não está no PATH desta sessão. O runner tenta caminhos conhecidos, mas se os briefings saírem com erro, rode 'where claude' e me diga o caminho."
}

Write-Host "`nRegistrando as sete tarefas — uma por cargo...`n"

foreach ($t in $tarefas) {
  $acao = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$runner`" -Agente $($t.Agente) -Projeto `"$Projeto`""
  $gatilho = New-ScheduledTaskTrigger -Daily -At $t.Hora
  # StartWhenAvailable: recupera a execução se o PC estava desligado.
  # DontStopIfGoingOnBatches / AllowStartIfOnBatteries: notebook não deve pular.
  $config = New-ScheduledTaskSettingsSet -StartWhenAvailable `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 20)

  Register-ScheduledTask -TaskName $t.Nome -Action $acao -Trigger $gatilho `
    -Settings $config -Description "Cargo $($t.Agente) — $($t.Porque)" -Force | Out-Null
  Ok "$($t.Nome.PadRight(24)) $($t.Hora)  ·  $($t.Porque)"
}

Write-Host "`nConferindo..."
Get-ScheduledTask -TaskPath "\FAST\" | Select-Object TaskName, State,
  @{n="Proxima"; e={ (Get-ScheduledTaskInfo $_.TaskName -TaskPath $_.TaskPath).NextRunTime }} |
  Format-Table -AutoSize

Write-Host "Os briefings aparecem em:" -ForegroundColor Cyan
Write-Host "  Obsidian Vault\Cerebro_Claude\Briefings\AAAA-MM-DD-<cargo>.md`n"
Write-Host "Para testar agora, sem esperar o horário:" -ForegroundColor Cyan
Write-Host "  Start-ScheduledTask -TaskName 'FAST\Operacao 11h30'`n"
