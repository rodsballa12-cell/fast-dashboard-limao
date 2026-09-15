# Falha muda: o erro que o script engoliu e o console que não existia

**Descoberto em:** 15/09/2026 · **Custo:** a Operação das 11h30 rodou, nenhuma
ata apareceu em `docs/atas/`, e passou meio dia até alguém perceber.

## O sintoma

A tarefa agendada `FAST\Operacao 11h30` aparecia como concluída com sucesso no
Agendador de Tarefas do Windows. A única ata publicada no repositório continuava
sendo a das 09h09 — de antes das correções de encoding e de análise. Nada
indicava que algo tinha dado errado.

## Duas falhas empilhadas

### 1. Programa externo não dispara `try/catch` no PowerShell

O bloco que publicava a ata era assim:

```powershell
try {
  git -C $Projeto pull --rebase --quiet
  git -C $Projeto add -- "docs/atas/$data-$Agente.md"
  ...
} catch {
  Write-Output "AVISO: nao consegui publicar no repositorio..."
}
```

Isso parece defensivo e não é. **`git` é um programa externo: quando falha, ele
não levanta exceção — só seta `$LASTEXITCODE`.** O `catch` nunca dispara. Um
`pull` com conflito, um `push` rejeitado, um `add` num caminho errado: o script
seguia em frente como se tudo tivesse dado certo, e o próprio `AVISO` que eu
tinha escrito para esse caso era código morto.

O inverso também morde: com `$ErrorActionPreference = "Stop"`, a forma
`git ... 2>&1` transforma qualquer coisa que o git escreva em *stderr*
(progresso, aviso de rebase) em **erro terminante** — mesmo quando o comando
teve sucesso. As duas armadilhas são opostas e estavam no mesmo arquivo.

A checagem tem que ser explícita:

```powershell
function Git-Passo([string]$Desc, [string[]]$GitArgs) {
  $anterior = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $saidaGit = (& git -C $Projeto @GitArgs 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { Registrar "FALHOU: $Desc ($LASTEXITCODE). $saidaGit"; return $false }
    return $true
  } finally { $ErrorActionPreference = $anterior }
}
```

### 2. Tarefa agendada não tem console

E mesmo que o aviso tivesse disparado, ninguém o veria: **`Write-Output` numa
tarefa agendada escreve para lugar nenhum.** Não há janela, não há terminal, não
há arquivo. O diagnóstico que eu tinha preparado ia para o vazio.

Agora toda execução deixa rastro em `_execucoes.log`, ao lado dos briefings no
vault — que é onde o Rodrigo alcança do celular, e não num diretório de log que
ele nunca vai abrir.

## A armadilha de terceiro nível

`Registrar` usa **`Write-Host`**, não `Write-Output`. Dentro de `Git-Passo`, um
`Write-Output` entraria no fluxo de saída da função e o retorno `$true`/`$false`
viraria um array de duas posições — que o PowerShell avalia como verdadeiro
**sempre**. A função de checar erro passaria a dizer "deu certo" em todo caso.
Um bug de log criando um bug de lógica.

## A regra

**Sucesso silencioso é pior que falha barulhenta.** Um script que roda sozinho
tem que provar que funcionou, não presumir. Se a única evidência de que deu certo
é a ausência de erro, e o erro não tem para onde ir, você não tem evidência
nenhuma — tem esperança.

Três perguntas antes de agendar qualquer coisa:

1. Se o passo do meio falhar, o script **percebe**?
2. Se perceber, tem **onde escrever** isso?
3. Esse lugar é um que alguém **realmente abre**?
