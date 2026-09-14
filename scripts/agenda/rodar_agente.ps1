# Roda um cargo da empresa digital sem ninguem na frente do computador e
# grava o resultado no Obsidian, que sincroniza pro celular via OneDrive.
#
# Uso:  powershell -File rodar_agente.ps1 -Agente operacao-diaria
#
# Por que grava no vault e nao no repositorio: o briefing e leitura do
# Rodrigo, nao dado da empresa. Repositorio guarda o que a empresa sabe;
# vault guarda o que o dono leu.

param(
  [Parameter(Mandatory=$true)][string]$Agente,
  [string]$Projeto = "C:\Users\rods_\dev\fast-dashboard-limao",
  [string]$Destino = "C:\Users\rods_\OneDrive\Documentos\Obsidian Vault\Cerebro_Claude\Briefings"
)

$ErrorActionPreference = "Stop"
$data = Get-Date -Format "yyyy-MM-dd"
$hora = Get-Date -Format "HH:mm"

if (-not (Test-Path $Destino)) { New-Item -ItemType Directory -Path $Destino -Force | Out-Null }
$arquivo = Join-Path $Destino "$data-$Agente.md"

Set-Location $Projeto

# Traz o que as rotinas da nuvem publicaram desde a ultima execucao.
# Se falhar (sem rede, conflito), segue com o dado local e avisa no briefing.
$avisoGit = ""
try { git pull --quiet 2>&1 | Out-Null }
catch { $avisoGit = "> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.`n" }

# 'claude' pode nao estar no PATH de uma tarefa agendada.
$claude = (Get-Command claude -ErrorAction SilentlyContinue).Source
if (-not $claude) {
  foreach ($p in @("$env:APPDATA\npm\claude.cmd",
                   "$env:LOCALAPPDATA\Programs\claude\claude.exe",
                   "$env:ProgramFiles\Claude\claude.exe")) {
    if (Test-Path $p) { $claude = $p; break }
  }
}
if (-not $claude) {
  "# ERRO - $Agente - $data $hora`n`nNao encontrei o comando 'claude'. Rode 'where claude' no terminal e me diga o caminho." |
    Set-Content -Path $arquivo -Encoding UTF8
  exit 1
}

$saida = & $claude -p "/$Agente" 2>&1 | Out-String

$cabecalho = @"
---
agente: $Agente
data: $data
hora: $hora
gerado_por: tarefa agendada
---

# $Agente · $data às $hora

$avisoGit
"@

($cabecalho + $saida) | Set-Content -Path $arquivo -Encoding UTF8
Write-Output "Gravado em $arquivo"
