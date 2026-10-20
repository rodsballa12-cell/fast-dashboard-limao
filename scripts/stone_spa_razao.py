# -*- coding: utf-8 -*-
"""Bloco "STONE SPA" dentro do razão (aba Conta_XP) do Excel do PC — caixa único.

Por que existe: o Spa recebe e paga pela própria conta Stone (filial 0002-41, conta
70951239-6): comissões, salário da recepção e Beleza Boost do Spa saem dali. Decisão do
Rodrigo em 20/10/2026: manter a conta separada para gerir o caixa de cada negócio, mas
SEM aba nova — "caixa um só": os movimentos entram no mesmo razão (aba Conta_XP), num
bloco logo abaixo do rodapé, e o SALDO TOTAL da empresa lê o saldo do bloco.

Regras do bloco:
- Saldo corrido (coluna E) = saldo da conta Stone do Spa (bate com o extrato dela).
- Categoria (coluna G) sempre começa com "Stone Spa — …". De propósito NÃO usa
  "OPEX (…)": comissão, equipe e Beleza Boost do Spa já entram na DRE pela regra
  (receita × 25%, Premissas B138 e B121); com "OPEX (…)" as fórmulas SUMIFS da DRE e
  do pivô contariam de novo. Os totais por categoria do bloco servem para conferência.
- Fica fora das faixas da tabela de validação mensal da XP (linhas de cada mês).
- Pix para profissional do Spa no Trinks = "Stone Spa — Comissão"; exceções por nome
  em OneDrive\\Franquia - FAST\\Claude\\stone_spa_categorias.json (fora do repo, que é público).
- Boleto pago pela conta (débito "Transação" COM destino) é despesa, não varredura.

Mesmas travas dos outros passos de Excel: COM (nunca openpyxl), só grava se o extrato
mudou, pula se a planilha estiver aberta.

Uso: python scripts/stone_spa_razao.py [--forcar | --seco]
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CSV = RAIZ / "data" / "spa" / "stone_extrato.csv"
PASTA = Path(r"C:\Users\rods_\OneDrive\Franquia - FAST\Claude")
PAINEL = PASTA / "Painel_Gestao_Financeira_SIIBELLO.xlsx"
REGRAS = PASTA / "stone_spa_categorias.json"
ESTADO = PASTA / "stone_spa_estado.json"
INICIO_BLOCO = "— STONE SPA"
FIM_BLOCO = "FIM DO BLOCO STONE SPA"


def ascii_(s) -> str:
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()


def norm(s) -> str:
    s = ascii_(s).lower()
    s = re.sub(r"^\d{2}\.\d{3}\.\d{3}\s+", "", s.strip())
    return re.sub(r"\s+", " ", s).strip()


def num(s) -> float:
    s = str(s or "0").replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def profs_spa() -> set[str]:
    try:
        pm = json.loads((RAIZ / "data" / "spa" / "profissionais_cache.json").read_text(encoding="utf-8"))["payload"]["prof_map"]
        return {norm(n) for n in pm.values()}
    except (OSError, ValueError, KeyError):
        return set()


def casa(nome: str, profs: set[str]) -> bool:
    t = nome.split()
    return any(t and q.split() and t[0] == q.split()[0] and (t[-1] == q.split()[-1] or (len(t) > 1 and len(q.split()) > 1 and t[1] == q.split()[1]))
               for q in profs)


def ler():
    regras = {}
    try:
        regras = {norm(k): v for k, v in (json.loads(REGRAS.read_text(encoding="utf-8")).get("por_nome") or {}).items()}
    except (OSError, ValueError):
        pass
    rot = lambda c: "Stone Spa — " + c.replace("OPEX (", "").rstrip(")") if c.startswith("OPEX (") else c
    profs = profs_spa()
    L = []
    with CSV.open(encoding="utf-8") as fh:
        for idx, l in enumerate(csv.DictReader(fh)):
            quando = dt.datetime.strptime(l["Data"][:16], "%d/%m/%Y %H:%M")
            deb = l["Movimentação"].startswith("D")
            tipo = l.get("Tipo") or ""
            contra = (l.get("Destino") if deb else l.get("Origem")) or ""
            desconhecido = contra.lower().startswith("desconhecido")
            if deb and tipo == "Pix" and "SIIBELLO" in contra.upper():
                cat, desc = "Stone Spa — Transferência para a conta XP", "Transferência Stone Spa → XP"
            elif deb and tipo == "Pix":
                c = regras.get(norm(contra)) or ("OPEX (Comissão)" if casa(norm(contra), profs) else None)
                cat, desc = (rot(c), "Pix pago pela conta do Spa") if c else ("A classificar", "Pix — natureza a confirmar")
            elif deb and tipo == "Transação" and not desconhecido:
                c = regras.get(norm(contra))
                cat, desc = (rot(c), "Boleto pago pela conta do Spa") if c else ("A classificar", "Boleto — natureza a confirmar")
            elif deb and tipo == "Transação":
                cat, desc = "Stone Spa — Aplicação na Reserva", "Varredura automática para a Reserva Stone"
            elif not deb and tipo == "Transação" and desconhecido:
                cat, desc = "Stone Spa — Resgate da Reserva", "Resgate da Reserva Stone"
            elif not deb and "SIIBELLO" in contra.upper():
                cat, desc = "Stone Spa — Transferência da conta XP", "Transferência XP → Stone Spa"
            else:
                cat, desc = "Stone Spa — Recebimento de cliente", "Recebimento (cartão/Pix) — a receita vem do Trinks"
            L.append(dict(quando=quando, idx=idx, contra=("Clientes (Stone)" if desconhecido and not deb else contra),
                          desc=desc, saldo=round(num(l["Saldo depois"]), 2), cat=cat,
                          # líquido = o que mexeu no saldo (a Stone desconta tarifa de Pix recebido)
                          valor=round(num(l["Saldo depois"]) - num(l["Saldo antes"]), 2), tarifa=round(abs(num(l.get("Tarifa"))), 2)))
    L.sort(key=lambda x: (x["quando"], -x["idx"]))      # extrato vem do mais novo, sem segundos
    reserva = 0.0
    for x in L:
        if x["cat"].endswith("Aplicação na Reserva"):
            reserva -= x["valor"]
        elif x["cat"].endswith("Resgate da Reserva"):
            reserva -= x["valor"]
        x["reserva"] = round(reserva, 2)
    return L


PS = r"""
$ErrorActionPreference = 'Stop'
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false; $xl.DisplayAlerts = $false; $xl.AskToUpdateLinks = $false
try {
  $wb = $xl.Workbooks.Open($env:FAST_XLSX, 0, $false)
  if ($wb.ReadOnly) { throw 'planilha aberta' }
  try { $wb.AutoSaveOn = $false } catch { }
  $x = $wb.Worksheets.Item('Conta_XP')
  $tot = 0; $ini = 0; $fim = 0; $det = 0; $sp = 0
  for ($r = 500; $r -le 1500; $r++) {
    $a = [string]$x.Cells.Item($r, 1).Value2; $b = [string]$x.Cells.Item($r, 2).Value2
    if ($tot -eq 0 -and $b.StartsWith('SALDO TOTAL')) { $tot = $r }
    if ($b.StartsWith('Stone Spa — conta + Reserva')) { $sp = $r }
    if ($a.StartsWith($env:FAST_INI)) { $ini = $r }
    if ($a.StartsWith($env:FAST_FIMB)) { $fim = $r }
    if ($det -eq 0 -and $a.Contains('DESPESAS REALIZADAS')) { $det = $r }
  }
  if ($tot -eq 0 -or $sp -eq 0 -or $det -eq 0) { throw "ancoras: total=$tot spa=$sp detalhe=$det" }
  if ($ini -gt 0 -and $fim -gt $ini) { $x.Range("$($ini):$($fim)").EntireRow.Delete() | Out-Null; $det = $det - ($fim - $ini + 1) }
  $linhas = (Get-Content -Raw -Encoding UTF8 $env:FAST_TSV) -split "`n" | Where-Object { $_ -ne '' }
  $n = $linhas.Count
  $p0 = $tot + 2
  $x.Range("$($p0):$($p0 + $n - 1)").EntireRow.Insert() | Out-Null
  $x.Range("$($p0):$($p0 + $n - 1)").ClearFormats() | Out-Null
  $r = $p0 - 1
  foreach ($ln in $linhas) {
    $r++
    $cols = $ln.TrimEnd("`r") -split "`t"
    for ($c = 0; $c -lt $cols.Count; $c++) {
      $v = $cols[$c]; if ($v -eq '') { continue }
      $v = $v.Replace('{R}', [string]$r).Replace('{R-1}', [string]($r - 1)).Replace('{P0}', [string]$p0)
      $cel = $x.Cells.Item($r, $c + 1)
      if ($v.StartsWith('=')) { $cel.Formula = $v }
      elseif ($v -match '^-?\d+(\.\d+)?$') { $cel.Value2 = [double]$v }
      else { $cel.Value2 = $v }
    }
  }
  $ult = $p0 + $n - 1
  $x.Range("A$($p0):H$($p0)").Font.Bold = $true; $x.Range("A$($p0):H$($p0)").Interior.Color = 0xF2E1D9
  $x.Range("A$($p0 + 1):H$($p0 + 1)").Font.Bold = $true
  $x.Range("A$($ult - 2):H$($ult)").Font.Bold = $true
  try { $x.Range("A$($p0 + 2):A$($ult - 3)").NumberFormatLocal = 'dd/mm/aaaa hh:mm' } catch { }
  try { $x.Range("D$($p0 + 2):E$($ult)").NumberFormatLocal = '#.##0,00' } catch { }
  for ($i = $p0 + 2; $i -le $ult - 3; $i++) { if (([string]$x.Cells.Item($i, 7).Value2) -eq 'A classificar') { $x.Range("A$($i):H$($i)").Interior.Color = 0xCCF2FF } }
  # rodapé: caixa único lê o saldo da conta + a Reserva do bloco
  $x.Cells.Item($sp, 5).Formula = "=E$($ult - 2)+E$($ult - 1)"
  $x.Cells.Item($sp, 8).Value2 = [string]$env:FAST_OBS
  $xl.CalculateFull()
  $txt = $x.Cells.Item($sp, 5).Text
  $wb.Save(); $wb.Close($false)
  Write-Output ("GRAVADO linhas $p0-$ult · Stone Spa $txt")
} catch {
  Write-Output ('ERRO: ' + $_.Exception.Message + ' linha ' + $_.InvocationInfo.ScriptLineNumber + ': ' + $_.InvocationInfo.Line.Trim()); exit 1
} finally {
  $xl.Quit(); [Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null
}
"""


def montar(L):
    T = []
    fim_ext = L[-1]["quando"]
    T.append([f"{INICIO_BLOCO} conta 70951239-6 (filial 0002-41) · movimentos do Spa até {fim_ext:%d/%m/%Y %H:%M} — saldo corrido = saldo da conta Stone do Spa",
              "", "", "", "", "", "", "Bloco refeito por scripts/stone_spa_razao.py a cada extrato novo — não editar à mão. Categorias 'Stone Spa — …' ficam fora da DRE (comissão/equipe/Beleza Boost do Spa já entram pela regra)."])
    T.append(["Data", "Favorecido / origem", "Descrição", "Valor (R$)", "Saldo Stone Spa (R$)", "# CAPEX", "Categoria", "Obs"])
    br = lambda v: f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    for k, x in enumerate(L):
        serial = (x["quando"] - dt.datetime(1899, 12, 30)).total_seconds() / 86400
        # 1ª linha parte do saldo do extrato (a conta já tinha saldo antes do 1º movimento baixado)
        saldo = f"{x['saldo']:.2f}" if k == 0 else "=E{R-1}+D{R}"
        T.append([f"{serial:.6f}", x["contra"].replace("\t", " "), x["desc"], f"{x['valor']:.2f}", saldo, "STONE SPA", x["cat"],
                  f"Extrato Stone Spa {x['quando']:%d/%m %H:%M} · saldo no extrato R$ {br(x['saldo'])}"
                  + (f" · líquido de tarifa Stone R$ {br(x['tarifa'])}" if x["tarifa"] else "")])
    # 3 linhas finais: conta, Reserva e o marcador; o rodapé soma E das duas primeiras
    T.append(["Saldo da conta Stone Spa", f"em {fim_ext:%d/%m/%Y %H:%M}", "confere com o extrato", "", "=E{R-1}",
              "", "", f"saldo no extrato: R$ {br(L[-1]['saldo'])}"])
    T.append(["Reserva Stone do Spa (principal)", "aplicações − resgates", "rendimento não aparece no extrato", "", f"{L[-1]['reserva']:.2f}",
              "", "", "boleto pago pela conta (débito com destino) NÃO é Reserva"])
    T.append([FIM_BLOCO, "", "", "", "", "", "", ""])
    return T, fim_ext, L[-1]["saldo"], L[-1]["reserva"], sum(1 for x in L if x["cat"] == "A classificar")


def main():
    seco, forcar = "--seco" in sys.argv, "--forcar" in sys.argv
    L = ler()
    T, fim_ext, saldo, reserva, pend = montar(L)
    resumo = (f"Stone Spa no razao: extrato ate {fim_ext:%d/%m %H:%M} - conta R$ {saldo:.2f} + Reserva R$ {reserva:.2f} "
              f"= R$ {saldo + reserva:.2f} - {pend} a classificar")
    if seco:
        tot = {}
        for x in L:
            tot[x["cat"]] = round(tot.get(x["cat"], 0) + x["valor"], 2)
        print(ascii_(resumo))
        for c, v in sorted(tot.items(), key=lambda i: i[1]):
            print(ascii_(f"  {c}: {v:.2f}"))
        for x in L:
            if x["cat"] == "A classificar":
                print(ascii_(f"  ? {x['quando']:%d/%m %H:%M} {x['contra']} {x['valor']:.2f}"))
        return 0
    assin = hashlib.sha1(json.dumps(T, ensure_ascii=False).encode()).hexdigest()
    try:
        antes = json.loads(ESTADO.read_text(encoding="utf-8")).get("assinatura_razao")
    except (OSError, ValueError):
        antes = None
    if antes == assin and not forcar:
        print(ascii_(resumo + " - sem novidade"))
        return 0
    if (PASTA / ("~$" + PAINEL.name)).exists():
        print(ascii_(resumo + " - planilha aberta, gravo na proxima rodada"))
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        tsv = Path(tmp) / "bloco.tsv"
        tsv.write_text("\n".join("\t".join(map(str, r)) for r in T) + "\n", encoding="utf-8")
        ps1 = Path(tmp) / "grava.ps1"
        ps1.write_text(PS, encoding="utf-8-sig")
        env = dict(os.environ, FAST_XLSX=str(PAINEL), FAST_TSV=str(tsv), FAST_INI=INICIO_BLOCO, FAST_FIMB=FIM_BLOCO,
                   FAST_OBS=f"bloco STONE SPA abaixo (extrato até {fim_ext:%d/%m/%Y %H:%M}) · conta R$ {saldo:.2f} + Reserva R$ {reserva:.2f} · o Spa recebe e paga pela própria conta Stone (Rodrigo, 20/10/2026: caixa um só, no mesmo razão)")
        out = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1)], env=env,
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
    saida = ((out.stdout or "") + (out.stderr or "")).strip()
    if "GRAVADO" not in saida:
        print(ascii_(resumo + " - ERRO ao gravar: " + saida[-300:]))
        return 1
    try:
        est = json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        est = {}
    est.update(assinatura_razao=assin, gravado_em=dt.datetime.now().isoformat(timespec="seconds"))
    ESTADO.write_text(json.dumps(est, ensure_ascii=False), encoding="utf-8")
    print(ascii_(resumo + " - " + saida.splitlines()[-1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
