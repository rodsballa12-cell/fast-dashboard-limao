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
  [switch]$Publicar,   # roda o cargo /publicar depois da ata (so o Conselho usa)
  [string]$Projeto = "C:\Users\rods_\dev\fast-dashboard-limao",
  [string]$Destino = "C:\Users\rods_\OneDrive\Documentos\Obsidian Vault\Cerebro_Claude\02-PROJETOS\Franquia_FAST_Limao\76_Briefings_Agentes"
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
# pull --rebase --autostash: guarda e devolve as mudancas locais numa operacao
# so. Antes eram tres passos (stash, pull, pop) e as rotinas das 09h disparam
# juntas quando o PC acorda: uma mexia na arvore entre o stash e o pull da
# outra e o pull falhava com "cannot pull with rebase: You have unstaged
# changes" (13/10, 15/10, 16/10, 18/10 e 20/10/2026). Se ainda assim falhar,
# espera um pouco e tenta de novo uma vez, que e o caso de outra rotina
# estar com o git ocupado.
$avisoGit = ""
$atualizou = Git-Passo "atualizar o repositorio antes de rodar" @("pull","--rebase","--autostash")
if (-not $atualizou) {
  Start-Sleep -Seconds (15 + (Get-Random -Maximum 20))
  $atualizou = Git-Passo "atualizar o repositorio antes de rodar (2a tentativa)" @("pull","--rebase","--autostash")
}
if (-not $atualizou) {
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

# --- Conta Stone do Spa no razao (Conta_XP) ----------------------------------
# O Spa recebe e paga pela propria conta Stone. Decisao do Rodrigo em 20/10/2026:
# caixa um so, sem aba nova - os movimentos entram num bloco "STONE SPA" dentro
# da aba Conta_XP (mesmo razao) e o rodape soma o saldo do bloco. So grava
# quando o extrato muda; pula se a planilha estiver aberta. Falha aqui nunca
# derruba o cargo.
function StoneSpa-Para-Razao {
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $py = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $py) { Registrar "Stone Spa no razao: python nao encontrado, pulei."; return }
    $envAntes = $env:PYTHONUTF8
    $env:PYTHONUTF8 = "1"
    try {
      $saidaPy = (& $py (Join-Path $Projeto "scripts\stone_spa_razao.py") 2>&1 | Out-String).Trim()
      if ($LASTEXITCODE -ne 0) { Registrar "FALHOU: Stone Spa no razao (codigo $LASTEXITCODE). $saidaPy" }
      else { Registrar $saidaPy }
    } finally { $env:PYTHONUTF8 = $envAntes }
  } catch {
    Registrar ("FALHOU: Stone Spa no razao. " + $_.Exception.Message)
  } finally { $ErrorActionPreference = $anterior }
}
StoneSpa-Para-Razao

# --- Dados frescos na DRE e no Fluxo ----------------------------------------
# Leva a receita apurada do Trinks e o que a Stone liquidou para o bloco
# MES EM CURSO da DRE e para o bloco DADOS FRESCOS do Fluxo de Caixa, e fecha
# no P&L o mes que ja terminou. Mesmas travas do script da Reserva: nao abre o
# Excel sem novidade e pula se a planilha estiver aberta. Falha aqui nunca
# derruba o cargo. Pedido do Rodrigo em 30/09/2026.
function Frescos-Para-Excel {
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $py = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $py) { Registrar "Dados frescos no Excel: python nao encontrado, pulei."; return }
    $saidaPy = (& $py (Join-Path $Projeto "scripts\atualiza_painel.py") 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { Registrar "FALHOU: dados frescos no Excel (codigo $LASTEXITCODE). $saidaPy" }
    else { Registrar "Dados frescos no Excel: $saidaPy" }
  } catch {
    Registrar ("FALHOU: dados frescos no Excel. " + $_.Exception.Message)
  } finally { $ErrorActionPreference = $anterior }
}
Frescos-Para-Excel

# --- DRE/financeiro.json atualizado a partir do Excel ---------------------
# atualiza_painel.py grava no Excel; gerar_financeiro.py le o Excel e produz
# data/financeiro.json + data/spa/financeiro.json + data/consolidado/financeiro.json
# que o painel online le na aba Financeiro. Sem este passo o DRE no painel so
# atualiza quando o Rodrigo roda manualmente — baseline fica dias defasada.
# Pedido do Rodrigo em 13/10/2026 apos o briefing dele mostrar baseline 11/10.
function DRE-Para-JSON {
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $py = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $py) { Registrar "DRE para JSON: python nao encontrado, pulei."; return }
    # PYTHONUTF8=1 evita UnicodeDecodeError cp1252 em open() sem encoding.
    $envAntes = $env:PYTHONUTF8
    $env:PYTHONUTF8 = "1"
    try {
      $saidaPy = (& $py (Join-Path $Projeto "scripts\gerar_financeiro.py") 2>&1 | Out-String).Trim()
      if ($LASTEXITCODE -ne 0) { Registrar "FALHOU: DRE para JSON (codigo $LASTEXITCODE). $saidaPy" }
      else {
        # Pegar so as 3 linhas-chave do gerar_financeiro (uma por unidade) pra nao poluir o log.
        $resumo = ($saidaPy -split "`r?`n" | Where-Object { $_ -match "gerado|principal" } | Select-Object -First 6) -join " | "
        if (-not $resumo) { $resumo = "ok" }
        Registrar "DRE para JSON: $resumo"
      }
    } finally { $env:PYTHONUTF8 = $envAntes }
  } catch {
    Registrar ("FALHOU: DRE para JSON. " + $_.Exception.Message)
  } finally { $ErrorActionPreference = $anterior }
}
DRE-Para-JSON

# --- Comissoes: Trinks x Pix pagos -----------------------------------------
# Confere a comissao devida (Trinks, taxa por categoria) contra os Pix de
# comissao do razao, por profissional e quinzena fechada, e grava a aba
# "11 Comissoes x Trinks" no arquivo de pendencias do OneDrive. So regrava
# quando o resultado muda; pula se o arquivo estiver aberto. O resultado NAO
# vai para o repositorio (publico). Pedido do Rodrigo em 16/10/2026.
function Comissoes-Trinks {
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $py = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $py) { Registrar "Comissoes x Trinks: python nao encontrado, pulei."; return }
    $envAntes = $env:PYTHONUTF8
    $env:PYTHONUTF8 = "1"
    try {
      $saidaPy = (& $py (Join-Path $Projeto "scripts\conciliacao_comissoes.py") 2>&1 | Out-String).Trim()
      if ($LASTEXITCODE -ne 0) { Registrar "FALHOU: Comissoes x Trinks (codigo $LASTEXITCODE). $saidaPy" }
      else { Registrar $saidaPy }
    } finally { $env:PYTHONUTF8 = $envAntes }
  } catch {
    Registrar ("FALHOU: Comissoes x Trinks. " + $_.Exception.Message)
  } finally { $ErrorActionPreference = $anterior }
}
Comissoes-Trinks

# --- SULTS (franqueadora): chamados, pedidos, comunicados, checklists --------
# So leitura (GET) e so das lojas Limao: o token enxerga a rede inteira, o
# script filtra e descarta o resto. O resultado NAO vai para o repositorio
# (publico): fica em OneDrive\Franquia - FAST\Claude\SULTS\sults_limao.json.
# --se-velho 180: as sete rodadas do dia nao precisam repetir a leitura (cada
# uma leva ~1 minuto pelo limite de 2 consultas/s). Codigo 3 = pulado, nao e
# falha. Pedido do Rodrigo em 21/10/2026.
function SULTS-Leitura {
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $py = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $py) { Registrar "SULTS: python nao encontrado, pulei."; return }
    $envAntes = $env:PYTHONUTF8
    $env:PYTHONUTF8 = "1"
    try {
      $saidaPy = (& $py (Join-Path $Projeto "scripts\sults_leitura.py") --se-velho 180 2>&1 | Out-String).Trim()
      if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 3) { Registrar "FALHOU: SULTS (codigo $LASTEXITCODE). $saidaPy" }
      else { Registrar $saidaPy }
    } finally { $env:PYTHONUTF8 = $envAntes }
  } catch {
    Registrar ("FALHOU: SULTS. " + $_.Exception.Message)
  } finally { $ErrorActionPreference = $anterior }
}
SULTS-Leitura

# 'claude' pode nao estar no PATH de uma tarefa agendada.
$claude = (Get-Command claude -ErrorAction SilentlyContinue).Source
if (-not $claude) {
  foreach ($p in @("$env:APPDATA\npm\claude.cmd",
                   "$env:LOCALAPPDATA\Programs\claude\claude.exe",
                   "$env:ProgramFiles\Claude\claude.exe")) {
    if (Test-Path $p) { $claude = $p; break }
  }
}
# Smoke test: valida que o claude CLI responde (sessao autenticada). Sem
# isso, se o login caiu, o /conselho e /publicar falham silenciosamente no
# fim do dia e Rodrigo so descobre no dia seguinte.
if ($claude) {
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $smokeJob = Start-Job -ScriptBlock { param($cli) & $cli -p "diga apenas: ok" 2>&1 } -ArgumentList $claude
    $pronto = Wait-Job $smokeJob -Timeout 20
    if ($pronto) {
      $smokeOut = (Receive-Job $smokeJob -ErrorAction SilentlyContinue | Out-String).Trim()
      if ($smokeOut -match "ok") {
        Registrar "Smoke test claude CLI: ok"
      } else {
        Registrar "ALERTA: smoke test claude CLI respondeu diferente de 'ok' (sessao pode ter caido): $($smokeOut.Substring(0, [Math]::Min(100, $smokeOut.Length)))"
      }
    } else {
      Stop-Job $smokeJob -ErrorAction SilentlyContinue
      Registrar "ALERTA: smoke test claude CLI timeout 20s — sessao pode ter caido"
    }
    Remove-Job $smokeJob -Force -ErrorAction SilentlyContinue
  } catch {
    Registrar ("Smoke test claude CLI falhou: " + $_.Exception.Message)
  } finally { $ErrorActionPreference = $anterior }
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

↑ [[76_Briefings_Agentes/00-INDEX|Briefings dos Agentes]]

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
# --autostash: DRE-Para-JSON reescreve os tres financeiro.json a cada rodada
# (o gerado_em muda mesmo sem novidade), entao a arvore chega suja neste pull
# e ele falhava com "unstaged changes" desde 13/10/2026.
$rel = "docs/atas/$data-$Agente.md"
if ((Git-Passo "pull antes de publicar" @("pull","--rebase","--autostash")) -and
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

# --- Leva o painel pro celular ----------------------------------------------
# So o Conselho passa -Publicar. Publicar a cada refresh seriam sete vezes por
# dia para mudar centavos, e sete notificacoes no celular do Rodrigo; as 22h30
# o dia ja fechou e o numero e o final.
#
# Chamada SEPARADA do claude, de proposito: se a publicacao falhar, o briefing
# ja esta salvo no vault e commitado. Um nao derruba o outro.
#
# O GitHub Actions nao consegue fazer isto: a ferramenta de Artifact so existe
# dentro de uma sessao do Claude. Por isso mora aqui, na maquina que roda a
# agenda, e nao no workflow.
if ($Publicar) {
  Registrar "Publicando o painel no artefato..."
  $encAnt2 = [Console]::OutputEncoding
  $eaAnt2  = $ErrorActionPreference
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  $ErrorActionPreference = "Continue"
  try   { $pub = & $claude -p "/publicar" 2>&1 | Out-String }
  finally {
    [Console]::OutputEncoding = $encAnt2
    $ErrorActionPreference = $eaAnt2
  }
  if ([string]::IsNullOrWhiteSpace($pub)) {
    Registrar "FALHOU: /publicar nao devolveu nada (codigo $LASTEXITCODE)."
  } else {
    Registrar ("/publicar: " + ($pub.Trim() -split "`r?`n" | Select-Object -Last 1))
  }
}

Registrar "Fim."
