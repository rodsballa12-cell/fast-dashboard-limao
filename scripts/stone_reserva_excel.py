# -*- coding: utf-8 -*-
"""Leva o saldo da Reserva Stone para o Excel do PC.

O que faz: lê data/stone_extrato.csv com o mesmo processador do painel
(stone_processor.py) e grava o principal aplicado na Reserva na linha
"Stone — Reserva" do rodapé da aba Conta_XP. Essa linha entra no
SALDO TOTAL EMPRESA, que o Painel e a Integridade leem.

Por que existe: o extrato Stone chega pelo repositório, mas o Excel só existe
no PC. Pedido do Rodrigo em 16/09/2026: "puxe toda vez que eu carregar o
extrato da Stone". Roda sozinho em scripts/agenda/rodar_agente.ps1, logo
depois do git pull.

Regras:
- Só grava quando o extrato é mais novo ou o saldo mudou. Senão, não abre o Excel.
- Nunca grava com a planilha aberta (arquivo de trava ~$). Tenta na próxima rodada.
- Desliga o salvamento automático do OneDrive ao abrir, para um erro não deixar
  gravação pela metade.
- Grava pelo Excel (COM), nunca pelo openpyxl: salvar pelo openpyxl apaga o
  valor calculado de TODAS as fórmulas, e o gerar_financeiro.py lê esses valores.
- Acha a linha pelo rótulo, não pelo endereço: o rodapé anda quando o razão cresce.
- O rendimento da Reserva NÃO é gravado: o extrato não mostra, o painel só estima.

Uso:
    python scripts/stone_reserva_excel.py            # grava só se houver novidade
    python scripts/stone_reserva_excel.py --forcar   # regrava mesmo sem novidade

Saída em ASCII de propósito: na tarefa agendada a saída passa pela codepage do
console e acento vira lixo no _execucoes.log.
"""
import contextlib, datetime, io, os, re, subprocess, sys
from pathlib import Path

import openpyxl

RAIZ = Path(__file__).resolve().parents[1]
CSV = RAIZ / "data" / "stone_extrato.csv"
PAINEL = Path(r"C:\Users\rods_\OneDrive\Franquia - FAST\Claude\Painel_Gestao_Financeira_SIIBELLO.xlsx")
ABA = "Conta_XP"
ROTULO = "Stone — Reserva"
RE_DATA = re.compile(r"extrato Stone at[ée] (\d{2}/\d{2}/\d{4})")

OBS = ("extrato Stone até {data} · principal aplicado · rendimento NÃO VEJO (o extrato não mostra) · "
       "atualiza sozinho quando chega extrato Stone novo · gravado em {agora}")

PS_GRAVAR = r"""
$ErrorActionPreference = 'Stop'
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false; $xl.DisplayAlerts = $false; $xl.AskToUpdateLinks = $false
try {
  $wb = $xl.Workbooks.Open($env:FAST_XLSX, 0, $false)
  # A planilha está no OneDrive: o Excel liga o salvamento automático e cada
  # célula escrita vai para o disco na hora. Sem desligar, um erro no meio deixa
  # gravação pela metade e o Close sem salvar não desfaz nada (visto em 16/09).
  try { $wb.AutoSaveOn = $false } catch { }
  $ws = $wb.Worksheets.Item($env:FAST_ABA)
  $r = [int]$env:FAST_LINHA
  if (-not ($ws.Cells.Item($r, 2).Text).StartsWith('Stone')) { throw "linha $r nao e a da Reserva Stone" }
  $ws.Cells.Item($r, 5).Value2 = [double]::Parse($env:FAST_VALOR, [Globalization.CultureInfo]::InvariantCulture)
  # [string] explícito: $env: devolve um objeto do PowerShell com propriedades
  # extras, e o Excel recusa com "conversão especificada não é válida".
  $ws.Cells.Item($r, 8).Value2 = [string]$env:FAST_OBS
  $xl.CalculateFullRebuild()
  # "pronto" no Excel é xlDone (-4135), não 0. Compara pelo nome e desiste em 2 min.
  $n = 0
  while ([string]$xl.CalculationState -ne 'xlDone' -and $n -lt 240) { Start-Sleep -Milliseconds 500; $n++ }
  $wb.Save(); $wb.Close($false)
  Write-Output 'GRAVADO'
} catch {
  Write-Output ('ERRO: ' + $_.Exception.Message)
  exit 1
} finally {
  $xl.Quit()
  [Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null
}
"""


def ler_reserva():
    sys.path.insert(0, str(RAIZ / "scripts"))
    import stone_processor
    with contextlib.redirect_stdout(io.StringIO()):
        r = stone_processor.processar_stone_csv(CSV, [])
    if not r or not r.get("periodo_fim"):
        raise SystemExit("ERRO: extrato Stone sem periodo_fim")
    fim = datetime.date.fromisoformat(str(r["periodo_fim"])[:10])
    return fim, round(float(r["aplicacao_reserva"]["saldo_aplicado"]), 2)


def ler_planilha():
    wb = openpyxl.load_workbook(PAINEL, data_only=True)
    ws = wb[ABA]
    linhas = [r for r in range(1, ws.max_row + 1) if str(ws.cell(r, 2).value or "").startswith(ROTULO)]
    if len(linhas) != 1:
        raise SystemExit(f"ERRO: esperava 1 linha '{ROTULO}' na {ABA}, achei {len(linhas)}")
    r = linhas[0]
    m = RE_DATA.search(str(ws.cell(r, 8).value or ""))
    data = datetime.datetime.strptime(m.group(1), "%d/%m/%Y").date() if m else None
    valor = ws.cell(r, 5).value
    return r, data, (round(float(valor), 2) if isinstance(valor, (int, float)) else None)


def main():
    forcar = "--forcar" in sys.argv
    if not CSV.exists():
        print("sem extrato Stone no repositorio - nada a fazer"); return 0
    if not PAINEL.exists():
        print("planilha nao encontrada neste computador - nada a fazer"); return 0
    if (PAINEL.parent / ("~$" + PAINEL.name)).exists():
        print("planilha aberta no Excel - fica para a proxima rodada"); return 0

    fim, saldo = ler_reserva()
    linha, data_atual, valor_atual = ler_planilha()
    if not forcar and data_atual == fim and valor_atual == saldo:
        print(f"sem novidade: Reserva Stone ja em R$ {saldo:.2f} (extrato ate {fim:%d/%m/%Y})"); return 0

    env = dict(os.environ,
               FAST_XLSX=str(PAINEL), FAST_ABA=ABA, FAST_LINHA=str(linha), FAST_VALOR=f"{saldo:.2f}",
               FAST_OBS=OBS.format(data=fim.strftime("%d/%m/%Y"),
                                   agora=datetime.datetime.now().strftime("%d/%m/%Y %H:%M")))
    p = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", PS_GRAVAR],
                       env=env, capture_output=True, text=True, timeout=300)
    saida = (p.stdout or "").strip().splitlines()
    if p.returncode != 0 or not saida or saida[-1] != "GRAVADO":
        print(f"ERRO ao gravar no Excel (codigo {p.returncode}): {' | '.join(saida)[-300:]} {(p.stderr or '')[-200:]}")
        return 1
    antes = f"R$ {valor_atual:.2f} ({data_atual:%d/%m/%Y})" if valor_atual is not None and data_atual else "vazio"
    print(f"Reserva Stone gravada no Excel: R$ {saldo:.2f} (extrato ate {fim:%d/%m/%Y}); antes {antes}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
