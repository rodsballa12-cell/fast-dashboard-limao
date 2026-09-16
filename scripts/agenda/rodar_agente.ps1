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

# --- Onde a execucao deixa rastro -----------------------------------------
# Tarefa agendada nao tem console: tudo que este script escreve com
# Write-Output se perde no ar. Em 15/09/2026 a Operacao das 11h30 rodou, a ata
# nao apareceu em docs/atas/ e nao havia um unico lugar onde olhar por que.
# O log fica ao lado dos briefings, no vault, onde o Rodrigo alcanca do celular.
$log = Join-Path $Destino "_execucoes.log"
function Registrar([string]$linha) {
  $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  Add-Content -Path $log -Value "$stamp [$Agente] $linha" -Encoding UTF8
  # Write-Host, nao Write-Output: dentro de Git-Passo o Write-Output entraria
  # no valor de retorno da funcao e o $true/$false viraria um array.
  Write-Host $linha
}

# --- Por que git nao pode ficar dentro de try/catch ------------------------
# Programa externo nao dispara try/catch no PowerShell: ele so seta
# $LASTEXITCODE. Todo o bloco de publicacao daqui vivia dentro de um catch que
# nunca disparava - pull, commit e push podiam falhar e o script seguia como se
# tivesse dado certo, sem escrever uma linha sequer.
#
# E o oposto tambem morde: com $ErrorActionPreference = "Stop", a forma
# "git ... 2>&1" transforma qualquer coisa que o git escreva em stderr
# (progresso, aviso de rebase) em erro terminante, mesmo com o comando tendo
# tido sucesso. Por isso o Continue local, so durante a chamada.
function Git-Passo([string]$Desc, [string[]]$GitArgs) {
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $saidaGit = (& git -C $Projeto @GitArgs 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
      Registrar "FALHOU: $Desc (codigo $LASTEXITCODE). $saidaGit"
      return $false
    }
    return $true
  } finally { $ErrorActionPreference = $anterior }
}

Registrar "Inicio."

# Traz o que as rotinas da nuvem publicaram desde a ultima execucao.
# Se falhar (sem rede, conflito), segue com o dado local e avisa no briefing.
$avisoGit = ""
if (-not (Git-Passo "atualizar o repositorio antes de rodar" @("pull","--rebase"))) {
  $avisoGit = "> [!warning] Nao consegui atualizar o repositorio. Os numeros podem estar atrasados.`n"
}

# --- Reserva Stone no Excel -------------------------------------------------
# O extrato Stone chega pelo repositorio; o Excel so existe neste PC. Depois
# do pull, leva o saldo da Reserva Stone para o rodape da aba Conta_XP, que
# entra no saldo total da empresa. O script so abre o Excel quando o extrato
# e novo e pula se a planilha estiver aberta. Falha aqui nunca derruba o
# cargo: fica no log e a rodada segue. Pedido do Rodrigo em 16/09/2026.
function Stone-Para-Excel {
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $py = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $py) { Registrar "Reserva Stone no Excel: python nao encontrado, pulei."; return }
    $saidaPy = (& $py (Join-Path $Projeto "scripts\stone_reserva_excel.py") 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { Registrar "FALHOU: Reserva Stone no Excel (codigo $LASTEXITCODE). $saidaPy" }
    else { Registrar "Reserva Stone no Excel: $saidaPy" }
  } catch {
    Registrar ("FALHOU: Reserva Stone no Excel. " + $_.Exception.Message)
  } finally { $ErrorActionPreference = $anterior }
}
Stone-Para-Excel

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
  Registrar "FALHOU: nao encontrei o comando 'claude' no PATH nem nos caminhos conhecidos."
  [System.IO.File]::WriteAllText($arquivo,
    "# ERRO - $Agente - $data $hora`n`nNao encontrei o comando 'claude'. Rode 'where claude' no terminal e me diga o caminho.",
    (New-Object System.Text.UTF8Encoding($false)))
  exit 1
}

# O PowerShell 5.1 decodifica a saida de programa externo usando
# [Console]::OutputEncoding, que por padrao e a codepage OEM (850 no Brasil).
# O claude devolve UTF-8, entao sem esta linha todo acento e emoji chegam como
# lixo: "ESCOVA ·" virou "ESCOVA ┬À" no briefing de 15/09/2026 as 09h09.
# Mesmo problema do BOM, do outro lado do cano - la era leitura de arquivo,
# aqui e leitura de saida de processo.
$encAnterior = [Console]::OutputEncoding
$eaAnterior  = $ErrorActionPreference
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Continue"   # mesma armadilha do 2>&1 explicada acima
try   { $saida = & $claude -p "/$Agente" 2>&1 | Out-String }
finally {
  [Console]::OutputEncoding = $encAnterior
  $ErrorActionPreference = $eaAnterior
}

# Briefing vazio e uma falha, nao um dia sem noticia. Sem esta checagem ele
# viraria um arquivo so com cabecalho, indistinguivel de um parecer curto.
if ([string]::IsNullOrWhiteSpace($saida)) {
  Registrar "FALHOU: o claude terminou sem devolver texto (codigo $LASTEXITCODE)."
  $saida = "O comando ``claude -p /$Agente`` terminou sem devolver nenhum texto (codigo $LASTEXITCODE). Nao ha parecer hoje - veja _execucoes.log."
}

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
Registrar "Gravado em $arquivo"

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

# Falha aqui nunca derruba o briefing: ele ja esta salvo no vault. Mas agora
# cada passo diz em qual ponto parou, no log.
$rel = "docs/atas/$data-$Agente.md"
if ((Git-Passo "pull antes de publicar" @("pull","--rebase")) -and
    (Git-Passo "add da ata" @("add","--",$rel))) {

  $ErrorActionPreference = "Continue"
  & git -C $Projeto diff --cached --quiet
  $temMudanca = ($LASTEXITCODE -ne 0)   # 1 = ha algo staged
  $ErrorActionPreference = "Stop"

  if (-not $temMudanca) {
    Registrar "Nada novo para publicar em $rel (conteudo identico ao que ja esta no repositorio)."
  }
  elseif (Git-Passo "commit da ata" @("-c","user.name=FAST Agenda","-c","user.email=noreply@anthropic.com",
                                      "commit","-m","ata: $Agente $data $hora")) {
    if (Git-Passo "push da ata" @("push")) { Registrar "Publicado em $rel" }
    else { Registrar "Commit feito, push falhou. A ata sobe no proximo briefing." }
  }
}

Registrar "Fim."
