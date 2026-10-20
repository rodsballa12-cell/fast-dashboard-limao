# -*- coding: utf-8 -*-
"""Livro-caixa da conta Stone do Spa no Excel do PC (aba "Conta_Stone_Spa").

Por que existe: o Spa recebe e paga pela própria conta Stone (filial 0002-41, conta
70951239-6) — comissões e salário saem dali, sem passar pela XP. Decisão do Rodrigo em
20/10/2026: manter a conta separada para a gestão do caixa de cada negócio e colocar
essa conta nos controles. Antes disso o painel só via o saldo dela no rodapé da Conta_XP.

O que faz: lê data/spa/stone_extrato.csv, classifica cada movimento e (re)escreve a aba
"Conta_Stone_Spa" do Excel com: resumo (saldo da conta, Reserva, total), quadro mensal
por categoria e o livro lançamento a lançamento. O rodapé da Conta_XP ("Stone Spa —
conta + Reserva") passa a ler o total desta aba.

Classificação:
- Crédito de cartão/Pix de cliente ............ Recebimento de cliente
- Débito "Transação" sem destino ............... Aplicação na Reserva Stone (varredura)
- Crédito "Transação" sem origem ............... Resgate da Reserva Stone
- Pix para a SIIBELLO (XP) ..................... Transferência para a conta XP
- Pix para profissional do Spa (Trinks) ........ OPEX (Comissão)
- Pix para outra pessoa/empresa ................ A classificar
Exceções por nome (ex.: recepcionista CLT cadastrada no Trinks) em
OneDrive\\Franquia - FAST\\Claude\\stone_spa_categorias.json — fora do repositório (público).

Mesmas travas do stone_reserva_excel.py: grava pelo Excel (COM), nunca pelo openpyxl;
não abre o Excel sem novidade; pula se a planilha estiver aberta.

Uso:
    python scripts/stone_spa_excel.py            # grava só se o extrato mudou
    python scripts/stone_spa_excel.py --forcar   # regrava mesmo sem mudança
    python scripts/stone_spa_excel.py --seco     # só imprime o resumo
Saída em ASCII (log da tarefa agendada).
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
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CSV = RAIZ / "data" / "spa" / "stone_extrato.csv"
PASTA = Path(r"C:\Users\rods_\OneDrive\Franquia - FAST\Claude")
PAINEL = PASTA / "Painel_Gestao_Financeira_SIIBELLO.xlsx"
REGRAS = PASTA / "stone_spa_categorias.json"
ESTADO = PASTA / "stone_spa_estado.json"
ABA = "Conta_Stone_Spa"


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


def profissionais_spa() -> set[str]:
    try:
        pm = json.loads((RAIZ / "data" / "spa" / "profissionais_cache.json").read_text(encoding="utf-8"))["payload"]["prof_map"]
        return {norm(n) for n in pm.values()}
    except (OSError, ValueError, KeyError):
        return set()


def casa_prof(nome: str, profs: set[str]) -> bool:
    t = nome.split()
    for p in profs:
        q = p.split()
        if t and q and t[0] == q[0] and (t[-1] == q[-1] or (len(t) > 1 and len(q) > 1 and t[1] == q[1])):
            return True
    return False


def classificar():
    regras = {}
    try:
        regras = {norm(k): v for k, v in (json.loads(REGRAS.read_text(encoding="utf-8")).get("por_nome") or {}).items()}
    except (OSError, ValueError):
        pass
    profs = profissionais_spa()
    linhas = []
    with CSV.open(encoding="utf-8") as fh:
        for idx, l in enumerate(csv.DictReader(fh)):
            quando = dt.datetime.strptime(l["Data"][:16], "%d/%m/%Y %H:%M")
            v = num(l["Valor"]); tarifa = num(l.get("Tarifa")) if "R$" in str(l.get("Tarifa")) else 0.0
            deb = l["Movimentação"].startswith("D")
            contra = (l.get("Destino") if deb else l.get("Origem")) or ""
            tipo = l.get("Tipo") or ""
            if deb and tipo == "Pix":
                if "SIIBELLO" in contra.upper():
                    cat = "Transferência para a conta XP"
                elif norm(contra) in regras:
                    cat = regras[norm(contra)]
                elif casa_prof(norm(contra), profs):
                    cat = "OPEX (Comissão)"
                else:
                    cat = "A classificar"
            elif deb and tipo == "Transação" and not contra.lower().startswith("desconhecido"):
                # boleto/pagamento saindo da conta (ex.: XML Marketing em 05/10) — NÃO é varredura
                cat = regras.get(norm(contra), "A classificar")
            elif deb and tipo == "Transação" and contra.lower().startswith("desconhecido"):
                cat = "Aplicação na Reserva Stone"
            elif not deb and tipo == "Transação" and contra.lower().startswith("desconhecido"):
                cat = "Resgate da Reserva Stone"
            elif not deb and "SIIBELLO" in contra.upper() and tipo == "Pix":
                cat = "Transferência da conta XP"
            elif not deb:
                cat = "Recebimento de cliente"
            else:
                cat = "A classificar"
            linhas.append(dict(quando=quando, tipo=tipo, contra=("Cliente / cartão" if contra.lower().startswith("desconhecido") and not deb else contra),
                               valor=round(v, 2), tarifa=round(tarifa, 2), saldo=round(num(l["Saldo depois"]), 2), cat=cat, idx=idx))
    # o extrato vem do mais novo para o mais antigo e sem segundos: no mesmo minuto vale a ordem do arquivo
    linhas.sort(key=lambda x: (x["quando"], -x["idx"]))
    reserva = 0.0
    for x in linhas:
        if x["cat"] == "Aplicação na Reserva Stone":
            reserva += -x["valor"]
        elif x["cat"] == "Resgate da Reserva Stone":
            reserva -= x["valor"]
        x["reserva"] = round(reserva, 2)
    return linhas


PS = r"""
$ErrorActionPreference = 'Stop'
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false; $xl.DisplayAlerts = $false; $xl.AskToUpdateLinks = $false
try {
  $wb = $xl.Workbooks.Open($env:FAST_XLSX, 0, $false)
  if ($wb.ReadOnly) { throw 'planilha aberta' }
  try { $wb.AutoSaveOn = $false } catch { }
  $existe = $false; foreach ($s in $wb.Worksheets) { if ($s.Name -eq 'Conta_Stone_Spa') { $existe = $true } }
  if ($existe) { $ws = $wb.Worksheets.Item('Conta_Stone_Spa'); $ws.Cells.Clear() | Out-Null }
  else { $ws = $wb.Worksheets.Add([Type]::Missing, $wb.Worksheets.Item('Conta_XP')); $ws.Name = 'Conta_Stone_Spa' }
  $dados = Get-Content -Raw -Encoding UTF8 $env:FAST_TSV
  $linhas = $dados -split "`n" | Where-Object { $_ -ne '' }
  $r = 0
  foreach ($ln in $linhas) {
    $r++
    $cols = $ln.TrimEnd("`r") -split "`t"
    for ($c = 0; $c -lt $cols.Count; $c++) {
      $v = $cols[$c]
      if ($v -eq '') { continue }
      $cel = $ws.Cells.Item($r, $c + 1)
      if ($v.StartsWith('=')) { $cel.Formula = [string]$v }
      elseif ($v -match '^-?\d+(\.\d+)?$') { $cel.Value2 = [double]::Parse($v, [Globalization.CultureInfo]::InvariantCulture) }
      else { $cel.Value2 = [string]$v }
    }
  }
  $ws.Range('A1').Font.Bold = $true; $ws.Range('A1').Font.Size = 14
  $ws.Range("A$($env:FAST_HDR):I$($env:FAST_HDR)").Font.Bold = $true
  $ws.Range("A$($env:FAST_HDR):I$($env:FAST_HDR)").Interior.Color = 0xF2E1D9
  $ws.Range("A$($env:FAST_MHDR):J$($env:FAST_MHDR)").Font.Bold = $true
  $ws.Range("A$($env:FAST_MHDR):J$($env:FAST_MHDR)").Interior.Color = 0xF2E1D9
  $ws.Range('A4:A7').Font.Bold = $true
  try { $ws.Range("A$([int]$env:FAST_HDR + 1):A$($env:FAST_FIM)").NumberFormatLocal = 'dd/mm/aaaa hh:mm' } catch { }
  try { $ws.Range("D$([int]$env:FAST_HDR + 1):F$($env:FAST_FIM)").NumberFormatLocal = '#.##0,00' } catch { }
  try { $ws.Range("H$([int]$env:FAST_HDR + 1):H$($env:FAST_FIM)").NumberFormatLocal = '#.##0,00' } catch { }
  try { $ws.Range("B4:B7").NumberFormatLocal = '#.##0,00' } catch { }
  try { $ws.Range("B$([int]$env:FAST_MHDR + 1):J$([int]$env:FAST_MHDR + 20)").NumberFormatLocal = '#.##0,00' } catch { }
  $ws.Columns.Item(1).ColumnWidth = 34; $ws.Columns.Item(2).ColumnWidth = 40; $ws.Columns.Item(3).ColumnWidth = 20
  foreach ($c in 4,5,6,8,9,10) { $ws.Columns.Item($c).ColumnWidth = 14 }; $ws.Columns.Item(7).ColumnWidth = 34
  # rodapé da Conta_XP passa a ler o total desta aba
  $x = $wb.Worksheets.Item('Conta_XP'); $sp = 0
  for ($i = 500; $i -le 800; $i++) { if (([string]$x.Cells.Item($i, 2).Value2).StartsWith('Stone Spa')) { $sp = $i } }
  if ($sp -gt 0) {
    $x.Cells.Item($sp, 5).Formula = '=Conta_Stone_Spa!B6'
    $x.Cells.Item($sp, 8).Value2 = [string]$env:FAST_OBS
  }
  $xl.CalculateFull()
  $wb.Save(); $wb.Close($false)
  Write-Output 'GRAVADO'
} catch {
  Write-Output ('ERRO: ' + $_.Exception.Message); exit 1
} finally {
  $xl.Quit(); [Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null
}
"""


def montar(linhas):
    fim_ext = linhas[-1]["quando"]
    saldo_conta = linhas[-1]["saldo"]
    reserva = linhas[-1]["reserva"]
    T = []  # linhas da planilha (lista de colunas)
    T.append(["CONTA STONE DO SPA — livro-caixa (filial 0002-41 · conta 70951239-6)"])
    T.append([f"Gerado por scripts/stone_spa_excel.py a partir do extrato Stone do Spa (até {fim_ext:%d/%m/%Y %H:%M}). O Spa recebe e paga por esta conta — decisão do Rodrigo em 20/10/2026 (caixa de cada negócio separado). Não editar à mão: a aba é refeita a cada extrato novo; exceções de categoria em stone_spa_categorias.json."])
    T.append([])
    T.append(["Saldo da conta Stone Spa", f"{saldo_conta:.2f}", f"último saldo do extrato ({fim_ext:%d/%m %H:%M})"])
    T.append(["Reserva Stone do Spa (principal)", f"{reserva:.2f}", "varreduras para a Reserva − resgates (rendimento não aparece no extrato)"])
    T.append(["TOTAL — caixa do Spa na Stone", "=B4+B5", "entra no SALDO TOTAL da empresa (rodapé da Conta_XP)"])
    pend = [x for x in linhas if x["cat"] == "A classificar"]
    T.append(["Pagamentos a classificar", str(len(pend)), "ver categoria 'A classificar' no livro abaixo"])
    T.append([])
    meses = sorted({(x["quando"].year, x["quando"].month) for x in linhas})
    cats = ["Recebimento de cliente", "Aplicação na Reserva Stone", "Resgate da Reserva Stone", "Transferência para a conta XP",
            "Transferência da conta XP", "OPEX (Comissão)", "OPEX (Folha CLT)", "A classificar"]
    cats += sorted({x["cat"] for x in linhas} - set(cats))
    mhdr = len(T) + 1
    T.append(["Quadro mensal por categoria (R$)"] + [f"Mês {m:02d}/{y}" for y, m in meses] + ["Total"])
    n_l = len(linhas)
    hdr = mhdr + len(cats) + 3
    ini, fim = hdr + 1, hdr + n_l
    for ci, cat in enumerate(cats):
        row = [cat]
        for y, m in meses:
            d0 = (dt.date(y, m, 1) - dt.date(1899, 12, 30)).days
            d1 = (dt.date(y + (m == 12), m % 12 + 1, 1) - dt.date(1899, 12, 30)).days
            row.append(f'=SUMIFS($D${ini}:$D${fim},$G${ini}:$G${fim},$A{mhdr + 1 + ci},$A${ini}:$A${fim},">="&{d0},$A${ini}:$A${fim},"<"&{d1})')
        col_fim = chr(ord("A") + len(meses))
        row.append(f"=SUM(B{mhdr + 1 + ci}:{col_fim}{mhdr + 1 + ci})")
        T.append(row)
    T.append([])
    T.append([])
    assert len(T) + 1 == hdr, (len(T), hdr)
    T.append(["Data e hora", "Contraparte", "Tipo", "Valor (R$)", "Tarifa (R$)", "Saldo da conta (R$)", "Categoria", "Reserva acumulada (R$)", "Observação"])
    for x in linhas:
        serial = (x["quando"] - dt.datetime(1899, 12, 30)).total_seconds() / 86400
        T.append([f"{serial:.6f}", x["contra"].replace("\t", " "), x["tipo"], f"{x['valor']:.2f}", f"{x['tarifa']:.2f}" if x["tarifa"] else "",
                  f"{x['saldo']:.2f}", x["cat"], f"{x['reserva']:.2f}", "⚠️ classificar" if x["cat"] == "A classificar" else ""])
    return T, dict(hdr=hdr, mhdr=mhdr, fim=fim, saldo=saldo_conta, reserva=reserva, fim_ext=fim_ext, pend=len(pend), n=n_l)


def main():
    seco, forcar = "--seco" in sys.argv, "--forcar" in sys.argv
    linhas = classificar()
    T, info = montar(linhas)
    por_cat = defaultdict(float)
    for x in linhas:
        por_cat[x["cat"]] += x["valor"]
    resumo = (f"Stone Spa: extrato ate {info['fim_ext']:%d/%m %H:%M} - conta R$ {info['saldo']:.2f} + Reserva R$ {info['reserva']:.2f} "
              f"= R$ {info['saldo'] + info['reserva']:.2f} - {info['pend']} pagamento(s) a classificar")
    if seco:
        print(ascii_(resumo))
        for k, v in sorted(por_cat.items(), key=lambda t: t[1]):
            print(ascii_(f"  {k:32} {v:>12.2f}"))
        return 0
    assin = hashlib.sha1(json.dumps(T, ensure_ascii=False).encode()).hexdigest()
    try:
        antes = json.loads(ESTADO.read_text(encoding="utf-8")).get("assinatura")
    except (OSError, ValueError):
        antes = None
    if antes == assin and not forcar:
        print(ascii_(resumo + " - sem novidade"))
        return 0
    if (PASTA / ("~$" + PAINEL.name)).exists():
        print(ascii_(resumo + " - planilha aberta, gravo na proxima rodada"))
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        tsv = Path(tmp) / "stone_spa.tsv"
        tsv.write_text("\n".join("\t".join(map(str, r)) for r in T) + "\n", encoding="utf-8")
        ps1 = Path(tmp) / "grava.ps1"
        ps1.write_text(PS, encoding="utf-8-sig")
        env = dict(os.environ, FAST_XLSX=str(PAINEL), FAST_TSV=str(tsv), FAST_HDR=str(info["hdr"]), FAST_MHDR=str(info["mhdr"]),
                   FAST_FIM=str(info["fim"]),
                   FAST_OBS=f"aba Conta_Stone_Spa (extrato Stone do Spa até {info['fim_ext']:%d/%m/%Y %H:%M}) · conta R$ {info['saldo']:.2f} + Reserva R$ {info['reserva']:.2f} · o Spa recebe e paga por esta conta (decisão do Rodrigo, 20/10/2026)")
        out = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1)], env=env,
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
    saida = (out.stdout or "").strip() + (out.stderr or "").strip()
    if "GRAVADO" not in saida:
        print(ascii_(resumo + " - ERRO ao gravar: " + saida[-300:]))
        return 1
    ESTADO.write_text(json.dumps(dict(assinatura=assin, gravado_em=dt.datetime.now().isoformat(timespec="seconds")), ensure_ascii=False), encoding="utf-8")
    print(ascii_(resumo + " - aba Conta_Stone_Spa atualizada"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
