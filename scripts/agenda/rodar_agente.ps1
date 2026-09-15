# ATENCAO AO SALVAR: este arquivo precisa de BOM UTF-8.
# O Windows PowerShell 5.1 - o unico instalado na maquina do Rodrigo - le
# arquivo sem BOM usando a codepage do sistema, e isso quebra acento e
# travessao. Em 15/09/2026 o instalar_tarefas.ps1 foi gravado sem BOM de um
# Linux e nao rodou; este aqui rodaria, mas escreveria o cabecalho de todo
# briefing com caractere corrompido. Editor que salva "UTF-8 sem BOM" reintroduz
# o problema em silencio.
#
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
  [System.IO.File]::WriteAllText($arquivo,
    "# ERRO - $Agente - $data $hora`n`nNao encontrei o comando 'claude'. Rode 'where claude' no terminal e me diga o caminho.",
    (New-Object System.Text.UTF8Encoding($false)))
  exit 1
}

# O PowerShell 5.1 decodifica a saida de programa externo usando
# [Console]::OutputEncoding, que por padrao e a codepage OEM (850 no Brasil).
# O claude devolve UTF-8, entao sem esta linha todo acento e emoji chegam como
# lixo: "ESCOVA ·" virou "ESCOVA ┬À" no briefing de 15/09/2026 as 09h09.
# Mesmo problema do BOM de ontem, do outro lado do cano - la era leitura de
# arquivo, aqui e leitura de saida de processo.
$encAnterior = [Console]::OutputEncoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
try   { $saida = & $claude -p "/$Agente" 2>&1 | Out-String }
finally { [Console]::OutputEncoding = $encAnterior }

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

# UTF-8 SEM BOM aqui, ao contrario do proprio .ps1: um BOM antes do '---'
# quebra o frontmatter YAML que o Obsidian le. Set-Content -Encoding UTF8 no
# PS 5.1 sempre poe BOM, por isso vai pelo .NET.
$semBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($arquivo, ($cabecalho + $saida), $semBom)
Write-Output "Gravado em $arquivo"

# --- Copia pro repositorio ------------------------------------------------
# O briefing no vault so existe nesta maquina. Uma copia em docs/atas/ da a
# ele tres coisas que o vault nao da: historico versionado, leitura por
# qualquer sessao (inclusive as que rodam na nuvem) e consulta pela Memoria.
#
# Escopo estreito de proposito: so docs/atas/, so um markdown que este script
# acabou de gerar. Nao toca em mais nada do repositorio.
$atasDir = Join-Path $Projeto "docs\atas"
if (-not (Test-Path $atasDir)) { New-Item -ItemType Directory -Path $atasDir -Force | Out-Null }
$ata = Join-Path $atasDir "$data-$Agente.md"
Copy-Item -Path $arquivo -Destination $ata -Force

try {
  git -C $Projeto pull --rebase --quiet 2>&1 | Out-Null
  git -C $Projeto add -- "docs/atas/$data-$Agente.md"
  # Sem mudanca no conteudo, nao gera commit vazio.
  git -C $Projeto diff --cached --quiet
  if ($LASTEXITCODE -ne 0) {
    git -C $Projeto -c user.name="FAST Agenda" -c user.email="noreply@anthropic.com" `
      commit --quiet -m "ata: $Agente $data $hora"
    git -C $Projeto push --quiet 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Output "Publicado em docs/atas/$data-$Agente.md" }
    else { Write-Output "AVISO: commit feito, push falhou. A ata sobe no proximo briefing." }
  }
} catch {
  # Falha aqui nunca pode derrubar o briefing: ele ja esta salvo no vault.
  Write-Output "AVISO: nao consegui publicar no repositorio ($($_.Exception.Message)). A ata esta no vault."
}
