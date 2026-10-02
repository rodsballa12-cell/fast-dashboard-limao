# -*- coding: utf-8 -*-
"""Leva os dados frescos do Trinks e da Stone para a DRE e o Fluxo de Caixa do Excel.

Por que existe: pedido do Rodrigo em 30/09/2026 - "sinto falta de trazer os dados
frescos atualizados do painel para nossa DRE e fluxo de caixa". Antes disso a
receita do mes em curso e o saldo da Stone eram digitados a mao a cada conversa,
e por isso envelheciam: o painel mostrava projecao onde ja havia numero real.

O que faz, todo dia, na rotina do agente:

1. MES EM CURSO (nao e competencia fechada)
   - DRE, bloco "MES EM CURSO": receita apurada do Trinks por loja, com a data
     das fontes.
   - Fluxo, bloco "DADOS FRESCOS": a mesma receita na coluna do mes, mais a
     projecao de fechamento pelo ritmo dos dias corridos, o que a Stone liquidou
     no mes e o saldo da Stone (conta + Reserva).

1b. MES CORRENTE NA DRE = REAL (pedido do Rodrigo em 30/09/2026: "no mes
   corrente o realizado de fato de receitas e despesas, e nos proximos meses a
   projecao")
   - a coluna do mes corrente no P&L 2026 recebe a receita real do Trinks e as
     despesas por competencia estimada: caixa do razao da Conta_XP no mes + os
     ajustes (linhas azuis) do bloco "COMPETENCIA DO MES EM CURSO", rateados
     por m2; comissao, royalty, CMV e Simples por regra das Premissas.
   - a grade da DRE do mes corrente CONTINUA NA PROJECAO ate o mes fechar
     (Rodrigo 02/10/2026: com 2 dias de mes, o real puro zerava outubro e
     distorcia o ano 1 e o caixa). So a receita muda: passa a ser o maior entre
     a projecao (meta do mes x curva do Pack) e o real ja apurado no P&L.
   - quando o mes fecha (bloco 2), a grade inteira do mes - receita e custos -
     passa a ler o P&L, que tem o real e a competencia estimada.

2. FECHAMENTO DE MES (so depois que o mes termina)
   - grava a receita real do mes no P&L 2026 (linhas de Receita bruta das duas
     lojas), aponta a DRE do mes para o P&L e marca o status como
     "REAL (receita)" - os custos continuam vindo das premissas ate o extrato da
     conta XP ser carregado no razao, que e passo manual.
   - grava a receita recebida do mes no Fluxo, mas so quando o extrato da Stone
     cobre o mes inteiro.

3. CONFERENCIA
   - nos meses ja marcados como reais, compara o que esta no painel com o que as
     fontes dizem hoje e AVISA a divergencia. Nao reescreve: competencia fechada
     de mes auditado so muda por decisao do Rodrigo.

Regras herdadas do stone_reserva_excel.py (mesmo padrao de escrita):
- Nunca grava com a planilha aberta (arquivo de trava ~$). Fica para a proxima.
- Desliga o AutoSave do OneDrive ao abrir: erro no meio nao deixa meia gravacao.
- Grava pelo Excel (COM), nunca pelo openpyxl: salvar pelo openpyxl apaga o valor
  calculado de TODAS as formulas, e o gerar_financeiro.py le esses valores.
- Acha as linhas pelo rotulo, nunca pelo endereco, e confere o rotulo antes de
  escrever: os blocos andam quando o razao cresce.
- Nao abre o Excel quando nao ha novidade.

Fontes e o que cada uma vale:
- Receita: data[/spa]/transacoes_ano_cache.json (transacoes do ano, vale ate a
  data em que o cache foi gerado) + historico.dias do dashboard_data.json
  (fechamento de cada dia, para os dias depois do cache). A receita de um mes
  NUNCA sai do extrato da conta XP - isso e regra do projeto.
- Stone: data/stone_extrato.csv. "Liquidado no mes" e a soma dos creditos do
  extrato no mes (reproduz jul/26 R$ 5.096,09 e ago/26 R$ 21.178,67, que estao
  no painel). O saldo aplicado na Reserva vem do stone_processor, o mesmo numero
  que o stone_reserva_excel.py grava na Conta_XP.

Uso:
    python scripts/atualiza_painel.py              # grava so se houver novidade
    python scripts/atualiza_painel.py --simular    # mostra o que faria, sem gravar
    python scripts/atualiza_painel.py --forcar     # regrava mesmo sem novidade

Saida em ASCII de proposito: na tarefa agendada a saida passa pela codepage do
console e acento vira lixo no _execucoes.log.
"""
import calendar
import collections
import contextlib
import csv
import datetime
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter

RAIZ = Path(__file__).resolve().parents[1]
# FAST_PAINEL existe para testar em copia fora do OneDrive antes de tocar no original.
PAINEL = Path(os.environ.get("FAST_PAINEL")
              or r"C:\Users\rods_\OneDrive\Franquia - FAST\Claude\Painel_Gestao_Financeira_SIIBELLO.xlsx")
CSV_STONE = RAIZ / "data" / "stone_extrato.csv"

UNIDADES = [("escova", RAIZ / "data"), ("spa", RAIZ / "data" / "spa")]
MESES_PT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
TOL = 0.01

PS_GRAVAR = r"""
$ErrorActionPreference = 'Stop'
$ops = [IO.File]::ReadAllText($env:FAST_OPS, [Text.Encoding]::UTF8) | ConvertFrom-Json
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false; $xl.DisplayAlerts = $false; $xl.AskToUpdateLinks = $false
try {
  $wb = $xl.Workbooks.Open($env:FAST_XLSX, 0, $false)
  # A planilha esta no OneDrive: sem desligar o AutoSave, cada celula escrita vai
  # para o disco na hora e um erro no meio deixa gravacao pela metade.
  try { $wb.AutoSaveOn = $false } catch { }
  foreach ($op in $ops) {
    $ws = $wb.Worksheets.Item([string]$op.aba)
    $cel = $ws.Cells.Item([int]$op.linha, [int]$op.coluna)
    if ([string]$op.guarda -ne '') {
      $rot = [string]$ws.Cells.Item([int]$op.linha, 1).Text
      if ($rot -notlike ('*' + [string]$op.guarda + '*')) {
        throw ('linha ' + $op.linha + ' da ' + $op.aba + ' nao e "' + $op.guarda + '": ' + $rot)
      }
    }
    switch ([string]$op.tipo) {
      'num' { $cel.Value2 = [double]::Parse([string]$op.valor, [Globalization.CultureInfo]::InvariantCulture) }
      'txt' { $cel.Value2 = [string]$op.valor }
      'f'   { $cel.Formula = [string]$op.valor }
      default { throw ('tipo desconhecido: ' + $op.tipo) }
    }
  }
  $xl.CalculateFullRebuild()
  # "pronto" no Excel e xlDone (-4135), nao 0. Compara pelo nome e desiste em 2 min.
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


# ----------------------------------------------------------------- fontes
def _num(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def receita_trinks(base: Path) -> dict:
    """Receita apurada por dia, somada por mes, das duas fontes do Trinks.

    Dia a dia, vale o fechamento do dia (historico.dias) - o agente fecha o dia
    inteiro, depois que a loja fechou. Nos dias que o historico nao tem (ele so
    comeca em ago/26), vale o cache de transacoes do ano.

    Nao da para simplesmente cortar pela data do cache: ele e gerado no meio da
    noite e perde as vendas do proprio dia feitas depois da geracao - foi assim
    que a receita de 27/09 ficou R$ 294,00 curta no primeiro teste.
    """
    dias = {}

    cache = base / "transacoes_ano_cache.json"
    cache_ate = None
    if cache.exists():
        c = json.loads(cache.read_text(encoding="utf-8"))
        cache_ate = str(c.get("gerado_em") or "")[:10] or None
        for t in c.get("payload") or []:
            dia = str(t.get("dataHora") or t.get("dataReferencia") or "")[:10]
            if dia and (not cache_ate or dia <= cache_ate):
                dias[dia] = round(dias.get(dia, 0.0) + _num(t.get("totalPagar")), 2)

    dash = base / "dashboard_data.json"
    do_dia = 0
    if dash.exists():
        d = json.loads(dash.read_text(encoding="utf-8"))
        for dia, reg in (((d.get("historico") or {}).get("dias")) or {}).items():
            kp = reg.get("kpis") if isinstance(reg, dict) else None
            if isinstance(kp, dict):
                dias[dia] = round(_num(kp.get("faturamento_apurado")), 2)
                do_dia += 1

    meses = collections.Counter()
    for dia, v in dias.items():
        meses[dia[:7]] += v

    return {
        "meses": {m: round(v, 2) for m, v in meses.items() if round(v, 2)},
        "ate": max(dias) if dias else None,
        "dias_do_fechamento": do_dia,
        "cache_ate": cache_ate,
    }


def _pv(s):
    s = (s or "").replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def stone() -> dict | None:
    """Creditos do extrato por mes + saldo da Stone (conta + Reserva)."""
    if not CSV_STONE.exists():
        return None
    with CSV_STONE.open(encoding="utf-8") as fh:
        recs = list(csv.DictReader(fh))

    creditos = collections.Counter()
    ordem = []
    for r in recs:
        try:
            dt = datetime.datetime.strptime(r["Data"], "%d/%m/%Y %H:%M")
        except (KeyError, ValueError):
            continue
        ordem.append((dt, r))
        if (r.get("Movimenta\u00e7\u00e3o") or "").startswith("Cr"):
            creditos[dt.strftime("%Y-%m")] += _pv(r.get("Valor"))
    if not ordem:
        return None
    ordem.sort(key=lambda x: x[0])
    saldo_conta = _pv(ordem[-1][1].get("Saldo depois"))

    # O saldo aplicado sai do stone_processor: e o mesmo numero que o
    # stone_reserva_excel.py grava na Conta_XP, para os dois nao brigarem.
    sys.path.insert(0, str(RAIZ / "scripts"))
    import stone_processor
    with contextlib.redirect_stdout(io.StringIO()):
        res = stone_processor.processar_stone_csv(CSV_STONE, [])
    reserva = round(_num((res or {}).get("aplicacao_reserva", {}).get("saldo_aplicado")), 2)

    return {
        "ate": ordem[-1][0].date(),
        "creditos": {m: round(v, 2) for m, v in creditos.items()},
        "saldo_conta": round(saldo_conta, 2),
        "reserva": reserva,
        "saldo_total": round(saldo_conta + reserva, 2),
    }


# ----------------------------------------------------------------- planilha
def _ym(v):
    """Aceita o cabecalho como data (DRE) ou como texto mmm/aa (P&L e Fluxo)."""
    if isinstance(v, datetime.datetime):
        return v.strftime("%Y-%m")
    m = re.match(r"^([a-z]{3})/(\d{2})$", str(v or "").strip().lower())
    if m and m.group(1) in MESES_PT:
        return f"20{m.group(2)}-{MESES_PT.index(m.group(1)) + 1:02d}"
    return None


def _colunas(ws, linha) -> dict:
    fora = {}
    for c in range(2, ws.max_column + 1):
        ym = _ym(ws.cell(linha, c).value)
        if ym:
            fora[ym] = c
    return fora


def _linha(ws, fragmento, inicio=1, fim=None) -> int:
    alvo = fragmento.lower()
    achadas = [r for r in range(inicio, (fim or ws.max_row) + 1)
               if alvo in str(ws.cell(r, 1).value or "").lower()]
    if len(achadas) != 1:
        raise SystemExit(f"ERRO: esperava 1 linha com '{fragmento}' na {ws.title}, achei {achadas}")
    return achadas[0]


def mapa_painel() -> dict:
    """Endereco de tudo que o script le e escreve, sempre achado pelo rotulo."""
    # dois carregamentos: um com o valor calculado (numeros) e outro com a
    # formula escrita (para nao reescrever formula e rotulo que ja estao certos).
    wb = openpyxl.load_workbook(PAINEL, data_only=True)
    wbf = openpyxl.load_workbook(PAINEL)
    d, fx = wb["DRE"], wb["Fluxo_Caixa"]
    df, fxf = wbf["DRE"], wbf["Fluxo_Caixa"]

    curso = _linha(d, "M\u00caS EM CURSO")
    pl = _linha(d, "P&L OPERACIONAL 2026")
    esc = _linha(d, "FAST ESCOVA", inicio=pl)
    spa = _linha(d, "FAST SPA", inicio=pl)
    frescos = _linha(fx, "DADOS FRESCOS")
    st_dre = _linha(d, "Status do m\u00eas")
    st_fx = _linha(fx, "Status do m\u00eas")

    dre = {
        "grid_status": st_dre,
        "curso_barra": curso,
        "curso_fonte": _linha(d, "Fonte e data dos dados", inicio=curso),
        "curso_escova": _linha(d, "apurada no m\u00eas \u2014 Escova", inicio=curso),
        "curso_spa": _linha(d, "apurada no m\u00eas \u2014 Spa", inicio=curso),
        "curso_cons": _linha(d, "apurada no m\u00eas \u2014 consolidado", inicio=curso),
        "pl_status": pl + 2,
        "pl_escova": _linha(d, "(+) Receita bruta", inicio=esc, fim=esc + 4),
        "pl_spa": _linha(d, "(+) Receita bruta", inicio=spa, fim=spa + 4),
    }
    dre["grid_cols"] = _colunas(d, st_dre + 1)
    dre["pl_cols"] = _colunas(d, pl + 3)
    # as duas primeiras "Receita bruta" da aba sao as da DRE consolidada (Escova e Spa)
    dre["grid_receita"] = [r for r in range(1, st_dre + 60)
                           if str(d.cell(r, 1).value or "").startswith("(+) Receita bruta")][:2]

    flx = {
        "status": st_fx,
        "recebida": _linha(fx, "(+) Receita recebida"),
        "fr_barra": frescos,
        "fr_escova": _linha(fx, "apurada no m\u00eas \u2014 Escova", inicio=frescos),
        "fr_spa": _linha(fx, "apurada no m\u00eas \u2014 Spa", inicio=frescos),
        "fr_cons": _linha(fx, "apurada no m\u00eas \u2014 consolidado", inicio=frescos),
        "fr_ritmo": _linha(fx, "pelo ritmo", inicio=frescos),
        "fr_liquidado": _linha(fx, "Liquidado pela Stone", inicio=frescos),
        "fr_saldo": _linha(fx, "Saldo da Stone", inicio=frescos),
    }
    flx["cols"] = _colunas(fx, st_fx + 1)

    valores = {
        "curso": {k: d.cell(v, 2).value for k, v in dre.items() if k.startswith("curso")},
        "curso_nota": {k: d.cell(v, 3).value for k, v in dre.items() if k.startswith("curso")},
        "curso_barra_txt": df.cell(dre["curso_barra"], 1).value,
        "fr_cons_f": {ym: fxf.cell(flx["fr_cons"], c).value for ym, c in flx["cols"].items()},
        "pl_escova": {ym: d.cell(dre["pl_escova"], c).value for ym, c in dre["pl_cols"].items()},
        "pl_spa": {ym: d.cell(dre["pl_spa"], c).value for ym, c in dre["pl_cols"].items()},
        "pl_status": {ym: d.cell(dre["pl_status"], c).value for ym, c in dre["pl_cols"].items()},
        "fluxo_recebida": {ym: fx.cell(flx["recebida"], c).value for ym, c in flx["cols"].items()},
        "fluxo_status": {ym: fx.cell(flx["status"], c).value for ym, c in flx["cols"].items()},
        "frescos": {k: {ym: fx.cell(v, c).value for ym, c in flx["cols"].items()}
                    for k, v in flx.items() if k.startswith("fr_")},
    }
    # 1b. mes corrente real: linhas da grade (Escova e Spa), do P&L e do bloco
    # de competencia, todas achadas pelo rotulo dentro do proprio bloco.
    comp = _linha(d, "COMPETÊNCIA DO MÊS CORRENTE")
    blk = {k: _linha(d, frag, inicio=comp, fim=comp + 16) for k, frag in (
        ("alu", "Aluguel + IPTU — caixa"), ("alu_aj", "Aluguel + IPTU — ajuste"),
        ("out", "seguro e consumo — caixa"), ("out_aj", "Sistemas, utilidades e outros — ajuste"),
        ("pes", "encargos e rescisão (Escova) — caixa"), ("pes_aj", "Pessoal CLT — ajuste"),
        ("ger", "Gerente única — competência"), ("bb", "Beleza Boost — caixa"),
        ("bb_aj", "Beleza Boost Escova — ajuste"), ("bb_spa", "Beleza Boost Spa — competência"),
        ("mid", "impressos — caixa"), ("mid_aj", "Mídia — ajuste"))}
    g_esc = _linha(d, "FAST ESCOVA — DRE mensal")
    g_spa = _linha(d, "FAST SPA — DRE mensal")
    linhas_dre = ("Simples", "Comiss", "Royalty", "CMV", "Marketing local", "Aluguel",
                  "Sistemas", "Pessoal", "Beleza Boost", "Mídia")
    corrente = {
        "blk": blk,
        "grid": {u: {k: _linha(d, k, inicio=ini, fim=ini + 15) for k in linhas_dre}
                 for u, ini in (("escova", g_esc), ("spa", g_spa))},
        "pl": {u: {k: _linha(d, k, inicio=ini, fim=ini + 14) for k in linhas_dre}
               for u, ini in (("escova", esc), ("spa", spa))},
        "formula": lambda linha, col: df.cell(linha, col).value,
    }
    return {"dre": dre, "fluxo": flx, "valores": valores, "corrente": corrente}


def formulas_mes_corrente(c, blk, pl_rec):
    """Despesas do mes corrente no P&L: competencia estimada (ver bloco 1b)."""
    b = {k: f"{c}{v}" for k, v in blk.items()}
    P = "Premissas!$B$"
    out = {}
    for u, rec, rat, com, cmv in (("escova", pl_rec["escova"], "82", "90", "91"),
                                  ("spa", pl_rec["spa"], "83", "101", "102")):
        r = f"{c}{rec}"
        out[u] = {
            "Simples": f"=-{r}*{P}78",
            "Comiss": f"=-{r}*{P}{com}",
            "Royalty": f"=IF({r}>0,-MAX({P}80,{r}*{P}79),0)",
            "CMV": f"=-{r}*{P}{cmv}",
            "Marketing local": "=0",
            "Aluguel": f"=-({b['alu']}+{b['alu_aj']})*{P}{rat}",
            "Sistemas": f"=-({b['out']}+{b['out_aj']})*{P}{rat}",
            "Mídia": f"=-({b['mid']}+{b['mid_aj']})*{P}{rat}",
        }
    # CMV do mes corrente = compras de insumo no mes (Rodrigo 30/09/2026: sem
    # contagem de estoque, o % das Premissas lancava de novo o estoque inicial ja
    # pago). Tudo na Escova ate o Spa ter compra propria identificada.
    out["escova"]["CMV"] = (f'=-SUMIFS(Conta_XP!$D$15:$D$3000,Conta_XP!$G$15:$G$3000,'
                            f'"OPEX (Produtos e insumos)",Conta_XP!$A$15:$A$3000,">="&{c}$4,'
                            f'Conta_XP!$A$15:$A$3000,"<"&EDATE({c}$4,1))')
    out["spa"]["CMV"] = "=0"
    out["escova"]["Pessoal"] = f"=-({b['ger']}*{P}82+{b['pes']}+{b['pes_aj']})"
    out["escova"]["Beleza Boost"] = f"=-({b['bb']}+{b['bb_aj']})"
    # royalty do Spa so a partir do mes de inicio da cobranca (Premissas B120)
    r_spa = f"{c}{pl_rec['spa']}"
    out["spa"]["Royalty"] = f"=IF({c}$4<{P}120,0,IF({r_spa}>0,-MAX({P}80,{r_spa}*{P}79),0))"
    out["spa"]["Pessoal"] = f"=-{b['ger']}*{P}83"
    out["spa"]["Beleza Boost"] = f"=-{b['bb_spa']}"
    return out


def _fmt(v):
    return f"R$ {v:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _mes_pt(ym):
    a, m = ym.split("-")
    return f"{MESES_PT[int(m) - 1]}/{a[2:]}"


def main():
    simular = "--simular" in sys.argv
    forcar = "--forcar" in sys.argv

    if not PAINEL.exists():
        print("planilha nao encontrada neste computador - nada a fazer")
        return 0
    if (PAINEL.parent / ("~$" + PAINEL.name)).exists() and not simular:
        print("planilha aberta no Excel - fica para a proxima rodada")
        return 0

    hoje = datetime.date.today()
    # --hoje=AAAA-MM-DD so vale com --simular: ensaio da virada de mes sem gravar
    for a in sys.argv:
        if a.startswith("--hoje=") and simular:
            hoje = datetime.date.fromisoformat(a.split("=", 1)[1])
    mes = hoje.strftime("%Y-%m")
    dias_mes = calendar.monthrange(hoje.year, hoje.month)[1]

    rec = {u: receita_trinks(b) for u, b in UNIDADES}
    st = stone()
    m = mapa_painel()
    dre, flx, val = m["dre"], m["fluxo"], m["valores"]

    ops, mudou, avisos = [], [], []

    def op(aba, linha, coluna, tipo, valor, guarda="", atual=None, rotulo=""):
        igual = (atual is not None
                 and ((tipo == "num" and isinstance(atual, (int, float)) and abs(atual - float(valor)) < TOL)
                      or (tipo in ("txt", "f") and str(atual) == str(valor))))
        if igual and not forcar:
            return
        if rotulo:
            de = _fmt(atual) if isinstance(atual, (int, float)) else (str(atual)[:40] if atual else "vazio")
            para = _fmt(float(valor)) if tipo == "num" else str(valor)[:60]
            mudou.append(f"{rotulo}: {de} -> {para}")
        ops.append({"aba": aba, "linha": linha, "coluna": coluna, "tipo": tipo,
                    "valor": f"{float(valor):.2f}" if tipo == "num" else valor, "guarda": guarda})

    # ---------------- 1. mes em curso ----------------
    r_esc = rec["escova"]["meses"].get(mes, 0.0)
    r_spa = rec["spa"]["meses"].get(mes, 0.0)
    datas = [x["ate"] for x in rec.values() if x["ate"]]
    ate = max(datas) if datas else None
    corridos = min(int(ate[8:10]), dias_mes) if ate and ate[:7] == mes else 0
    ritmo = round((r_esc + r_spa) / corridos * dias_mes, 2) if corridos else 0.0
    ate_br = f"{ate[8:10]}/{ate[5:7]}" if ate else "\u2014"

    op("DRE", dre["curso_barra"], 1, "txt",
       f"\U0001F4E1 M\u00caS EM CURSO ({_mes_pt(mes)}) \u2014 dados frescos do Trinks e da Stone"
       f" (o agente atualiza sozinho todo dia)", "", val["curso_barra_txt"])
    op("DRE", dre["curso_escova"], 2, "num", r_esc, "apurada no m",
       val["curso"].get("curso_escova"), "DRE receita Escova do mes")
    op("DRE", dre["curso_spa"], 2, "num", r_spa, "apurada no m",
       val["curso"].get("curso_spa"), "DRE receita Spa do mes")
    op("DRE", dre["curso_escova"], 3, "txt", f"real at\u00e9 {ate_br}", "apurada no m",
       val["curso_nota"].get("curso_escova"))
    op("DRE", dre["curso_spa"], 3, "txt", f"real at\u00e9 {ate_br}", "apurada no m",
       val["curso_nota"].get("curso_spa"))
    op("DRE", dre["curso_cons"], 3, "txt",
       (f"no ritmo dos {corridos} dias corridos, o m\u00eas fecha em ~{_fmt(ritmo)}"
        if ritmo else "\u2014"), "apurada no m", val["curso_nota"].get("curso_cons"))

    col = flx["cols"].get(mes)
    if col:
        fr, letra = val["frescos"], get_column_letter(col)
        op("Fluxo_Caixa", flx["fr_escova"], col, "num", r_esc, "apurada no m", fr["fr_escova"].get(mes))
        op("Fluxo_Caixa", flx["fr_spa"], col, "num", r_spa, "apurada no m", fr["fr_spa"].get(mes))
        op("Fluxo_Caixa", flx["fr_cons"], col, "f",
           f"={letra}{flx['fr_escova']}+{letra}{flx['fr_spa']}", "apurada no m",
           val["fr_cons_f"].get(mes))
        op("Fluxo_Caixa", flx["fr_ritmo"], col, "num", ritmo, "pelo ritmo", fr["fr_ritmo"].get(mes))
        # Stone so entra na coluna do mes se o extrato for deste mes: um extrato
        # velho na coluna nova mostraria saldo de outro mes como se fosse de hoje.
        if st and st["ate"].strftime("%Y-%m") == mes:
            op("Fluxo_Caixa", flx["fr_liquidado"], col, "num", st["creditos"].get(mes, 0.0),
               "Liquidado pela Stone", fr["fr_liquidado"].get(mes), "Fluxo liquidado Stone no mes")
            op("Fluxo_Caixa", flx["fr_saldo"], col, "num", st["saldo_total"],
               "Saldo da Stone", fr["fr_saldo"].get(mes), "Fluxo saldo Stone")
        elif st:
            avisos.append(f"o extrato da Stone e de {st['ate']:%d/%m} - as linhas da Stone do "
                          f"bloco de dados frescos ficaram como estavam (carregue extrato novo)")
    else:
        avisos.append(f"o Fluxo nao tem coluna para {_mes_pt(mes)} - "
                      f"bloco de dados frescos nao foi atualizado")

    # ---------------- 1b. mes corrente real na DRE ----------------
    cor = m["corrente"]
    c_pl, c_gr = dre["pl_cols"].get(mes), dre["grid_cols"].get(mes)
    if c_pl and c_gr and not str(val["pl_status"].get(mes) or "").upper().startswith("REAL"):
        L_pl, L_gr = get_column_letter(c_pl), get_column_letter(c_gr)
        op("DRE", dre["pl_escova"], c_pl, "num", r_esc, "Receita bruta",
           val["pl_escova"].get(mes), f"P&L {_mes_pt(mes)} Escova (real ate {ate_br})")
        op("DRE", dre["pl_spa"], c_pl, "num", r_spa, "Receita bruta",
           val["pl_spa"].get(mes), f"P&L {_mes_pt(mes)} Spa (real ate {ate_br})")
        form = formulas_mes_corrente(L_pl, cor["blk"],
                                     {"escova": dre["pl_escova"], "spa": dre["pl_spa"]})
        n_antes = len(ops)
        for u, pl_rec in (("escova", dre["pl_escova"]), ("spa", dre["pl_spa"])):
            for k, f in form[u].items():
                linha = cor["pl"][u][k]
                op("DRE", linha, c_pl, "f", f, k, cor["formula"](linha, c_pl))
        # grade do mes corrente: custos ficam na projecao; receita = maior entre a
        # projecao e o real apurado. Se a celula ainda nao tem a projecao (ex.: ja
        # aponta so para o P&L), nao inventa formula - avisa.
        for linha_gr, linha_pl in zip(dre["grid_receita"], (dre["pl_escova"], dre["pl_spa"])):
            atual = str(cor["formula"](linha_gr, c_gr) or "")
            real = f"DRE!{L_pl}{linha_pl}"
            if real in atual:
                continue
            if atual.startswith("=") and "Premissas" in atual:
                op("DRE", linha_gr, c_gr, "f", f"=MAX({atual[1:]},{real})", "Receita bruta", atual)
            else:
                avisos.append(f"DRE {_mes_pt(mes)} linha {linha_gr}: receita da grade nao e "
                              f"projecao ({atual[:40]}) - nao mexi; restaurar a formula do Pack")
        op("DRE", dre["pl_status"], c_pl, "txt", "EM CURSO (real + competência estimada)", "",
           val["pl_status"].get(mes))
        op("DRE", dre["grid_status"], c_gr, "txt", "EM CURSO (proj.)", "Status do m",
           cor["formula"](dre["grid_status"], c_gr))
        if len(ops) > n_antes:
            mudou.append(f"DRE {_mes_pt(mes)}: P&L do mes corrente com real + competencia; "
                         f"grade segue na projecao ({len(ops) - n_antes} celulas)")
    elif not c_pl:
        avisos.append(f"o P&L 2026 nao tem coluna para {_mes_pt(mes)} - a DRE do mes corrente "
                      f"continua na projecao (precisa de bloco novo no P&L)")

    # ---------------- 2. fechamento de mes ----------------
    for ym in sorted(set(rec["escova"]["meses"]) | set(rec["spa"]["meses"])):
        if ym >= mes:
            continue
        v_esc = rec["escova"]["meses"].get(ym, 0.0)
        v_spa = rec["spa"]["meses"].get(ym, 0.0)
        c_pl = dre["pl_cols"].get(ym)
        if not c_pl:
            avisos.append(f"{_mes_pt(ym)} fechou e o P&L 2026 nao tem coluna para ele - "
                          f"receita real {_fmt(v_esc + v_spa)} precisa de bloco novo no P&L")
            continue
        if str(val["pl_status"].get(ym) or "").upper().startswith("REAL"):
            for rot, atual, novo in (("Escova", val["pl_escova"].get(ym), v_esc),
                                     ("Spa", val["pl_spa"].get(ym), v_spa)):
                if isinstance(atual, (int, float)) and abs(atual - novo) > 1:
                    avisos.append(f"DIVERGENCIA em {_mes_pt(ym)} {rot}: painel {_fmt(atual)} x "
                                  f"fontes hoje {_fmt(novo)} - mes ja fechado, nao mexi")
            continue

        op("DRE", dre["pl_escova"], c_pl, "num", v_esc, "Receita bruta",
           val["pl_escova"].get(ym), f"P&L {_mes_pt(ym)} Escova")
        op("DRE", dre["pl_spa"], c_pl, "num", v_spa, "Receita bruta",
           val["pl_spa"].get(ym), f"P&L {_mes_pt(ym)} Spa")
        op("DRE", dre["pl_status"], c_pl, "txt", "REAL (receita)", "",
           val["pl_status"].get(ym), f"P&L {_mes_pt(ym)} status")
        # a DRE do mes passa a puxar o P&L em vez da projecao do Pack
        c_gr = dre["grid_cols"].get(ym)
        if c_gr:
            letra = get_column_letter(c_pl)
            for linha_gr, linha_pl in zip(dre["grid_receita"], (dre["pl_escova"], dre["pl_spa"])):
                op("DRE", linha_gr, c_gr, "f", f"=DRE!{letra}{linha_pl}", "Receita bruta")
            # mes que passou pelo "EM CURSO": o P&L tem os custos por competencia
            # estimada; a grade, que ficou na projecao durante o mes, passa a le-los.
            if str(val["pl_status"].get(ym) or "").upper().startswith("EM CURSO"):
                for u in ("escova", "spa"):
                    for k, linha in cor["pl"][u].items():
                        op("DRE", cor["grid"][u][k], c_gr, "f", f"=DRE!{letra}{linha}", k)
            op("DRE", dre["grid_status"], c_gr, "txt", "REAL (receita)", "Status do m")

        # Fluxo: receita recebida real, so quando o extrato cobre o mes inteiro
        c_fx = flx["cols"].get(ym)
        fim_mes = datetime.date(int(ym[:4]), int(ym[5:7]),
                                calendar.monthrange(int(ym[:4]), int(ym[5:7]))[1])
        if c_fx and st and st["ate"] >= fim_mes:
            op("Fluxo_Caixa", flx["recebida"], c_fx, "num", st["creditos"].get(ym, 0.0),
               "Receita recebida", val["fluxo_recebida"].get(ym), f"Fluxo recebido {_mes_pt(ym)}")
            op("Fluxo_Caixa", flx["status"], c_fx, "txt", "REAL (receita)", "Status do m",
               val["fluxo_status"].get(ym))
        elif c_fx and st:
            avisos.append(f"{_mes_pt(ym)} fechou mas o extrato da Stone vai ate "
                          f"{st['ate']:%d/%m} - receita recebida do Fluxo continua projetada")

    # ---------------- 3. grava ----------------
    print(f"receita apurada em {_mes_pt(mes)}: Escova {_fmt(r_esc)} · Spa {_fmt(r_spa)} · "
          f"total {_fmt(r_esc + r_spa)}" + (f" · ritmo fecha em {_fmt(ritmo)}" if ritmo else ""))
    if st:
        print(f"Stone ate {st['ate']:%d/%m}: liquidou {_fmt(st['creditos'].get(mes, 0.0))} no mes · "
              f"saldo {_fmt(st['saldo_total'])} (conta {_fmt(st['saldo_conta'])} + "
              f"Reserva {_fmt(st['reserva'])})")
    for a in avisos:
        print(f"  ! {a}")
    for c in mudou:
        print(f"  ~ {c}")

    if not ops:
        print("sem novidade no painel - Excel nao foi aberto")
        return 0

    # O carimbo da hora entra so quando ja ha algo para gravar: se entrasse
    # sempre, o relogio sozinho abriria o Excel a cada rodada.
    ops.append({"aba": "DRE", "linha": dre["curso_fonte"], "coluna": 2, "tipo": "txt",
                "guarda": "Fonte e data",
                "valor": (f"Trinks até {ate_br} (transações do ano + fechamento do dia)"
                          + (f" · Stone até {st['ate']:%d/%m}" if st else "")
                          + f" · gravado em {datetime.datetime.now():%d/%m %H:%M}")})

    if simular:
        print(f"--simular: {len(ops)} celulas seriam gravadas, nada foi tocado")
        return 0

    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as fh:
        json.dump(ops, fh, ensure_ascii=False)
        caminho = fh.name
    try:
        env = dict(os.environ, FAST_XLSX=str(PAINEL), FAST_OPS=caminho)
        p = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", PS_GRAVAR],
                           env=env, capture_output=True, text=True, timeout=600)
        saida = (p.stdout or "").strip().splitlines()
        if p.returncode != 0 or not saida or saida[-1] != "GRAVADO":
            print(f"ERRO ao gravar no Excel (codigo {p.returncode}): "
                  f"{' | '.join(saida)[-400:]} {(p.stderr or '')[-200:]}")
            return 1
    finally:
        with contextlib.suppress(OSError):
            os.unlink(caminho)
    print(f"painel atualizado: {len(ops)} celulas gravadas na DRE e no Fluxo de Caixa")
    return 0


if __name__ == "__main__":
    sys.exit(main())
