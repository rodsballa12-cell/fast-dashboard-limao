#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lê as respostas do Forms "Envio de notas — Profissionais" e grava o lado NOTA
da conferência de comissões em data/notas_profissionais.json.

POR QUE EXISTE (17/11/2026)
Desde a 2ª quinzena de novembro as profissionais mandam a nota fiscal por um
Microsoft Forms, até o dia do pagamento (15 e 30). A aba "Comissões" do painel
põe cada nota ao lado do que o Trinks diz (scripts/comissao_quinzena.py). Este
script faz três coisas que o Forms não faz:

  1. casa o nome digitado com o nome do cadastro do Trinks
     ("Carol" -> "Carollina Rezende De Oliveira");
  2. descobre a quinzena (pelo campo Período; se não der, pela data de envio,
     e marca que foi deduzida);
  3. junta reenvio: a mesma pessoa mandando a MESMA nota (mesmo número) duas
     vezes vale a última; números diferentes são notas diferentes e somam.

ONDE ESTÃO AS RESPOSTAS
O Forms guarda as respostas numa planilha do OneDrive (no Forms: Respostas ->
Abrir no Excel / Baixar). Só o PC alcança. Padrão: o .xlsx mais novo em
    C:\\Users\\rods_\\OneDrive\\Franquia - FAST\\Claude\\Notas profissionais\\
ou o caminho passado na linha de comando.

APELIDOS: nomes que o casamento automático não resolve vão em
comissoes_aliases.json (o mesmo arquivo da conciliação, ao lado do Excel),
chave "forms_para_trinks": {"Carol": "Carollina Rezende De Oliveira"}.

PRIVACIDADE: o arquivo de saída tem nome e valor por pessoa -> entra no cofre
(lista PAINEL do scripts/cofre.py). CPF/CNPJ do Forms NÃO é copiado.

USO
    python scripts/notas_forms.py                  # pasta padrão do OneDrive
    python scripts/notas_forms.py respostas.xlsx   # arquivo específico (.xlsx ou .csv)
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comissao_quinzena import qid, quinzena  # noqa: E402  (uma regra de quinzena só)

RAIZ = Path(__file__).resolve().parent.parent
PASTA_FORMS = Path(r"C:\Users\rods_\OneDrive\Franquia - FAST\Claude\Notas profissionais")
ALIASES = Path(r"C:\Users\rods_\OneDrive\Franquia - FAST\Claude\comissoes_aliases.json")
SAIDA = RAIZ / "data" / "notas_profissionais.json"
BRT = dt.timezone(dt.timedelta(hours=-3))


def norm(s) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\(.*?\)", " ", s)
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", s).split())


# ------------------------------------------------------------------ entrada
def ler_planilha(p: Path) -> list[dict]:
    if p.suffix.lower() == ".csv":
        txt = p.read_text(encoding="utf-8-sig")
        dial = csv.Sniffer().sniff(txt.splitlines()[0], delimiters=",;\t")
        return list(csv.DictReader(txt.splitlines(), dialect=dial))
    import openpyxl
    ws = openpyxl.load_workbook(p, data_only=True, read_only=True).worksheets[0]
    linhas = list(ws.iter_rows(values_only=True))
    if not linhas:
        return []
    cab = [str(c or "").strip() for c in linhas[0]]
    return [dict(zip(cab, l)) for l in linhas[1:] if any(v not in (None, "") for v in l)]


def coluna(cabecalhos, *chaves, exato=None):
    for h in cabecalhos:
        n = norm(h)
        if exato and n in exato:
            return h
    for k in chaves:                    # a ordem das chaves é a prioridade
        for h in cabecalhos:
            if k in norm(h):
                return h
    return None


def data_hora(v) -> dt.datetime | None:
    if isinstance(v, dt.datetime):
        return v
    if isinstance(v, dt.date):
        return dt.datetime(v.year, v.month, v.day)
    s = str(v or "").strip()
    for f in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%m/%d/%Y %H:%M:%S", "%m/%d/%y %H:%M:%S",
              "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(s[:19], f)
        except ValueError:
            pass
    return None


def valor(v) -> float | None:
    if isinstance(v, (int, float)):
        return round(float(v), 2)
    s = re.sub(r"[^\d,.\-]", "", str(v or ""))
    if not s:
        return None
    if "," in s:                         # 1.234,56
        s = s.replace(".", "").replace(",", ".")
    elif s.count(".") > 1 or re.search(r"\.\d{3}$", s):   # 1.234 / 1.234.567
        s = s.replace(".", "")
    try:
        return round(float(s), 2)
    except ValueError:
        return None


def quinzena_do_periodo(txt: str, enviado: dt.datetime | None):
    """Primeiro dia citado no campo Período -> quinzena. None se não achar data."""
    t = str(txt or "")
    ano_ref = (enviado or dt.datetime.now()).year
    # "01 a 14/11", "15-30/11/2026", "1 até 14/11"
    m = re.search(r"\b(\d{1,2})\s*(?:a|à|ate|até|-|–|—)\s*\d{1,2}\s*/\s*(\d{1,2})(?:\s*/\s*(\d{2,4}))?", t, re.I)
    if m:
        d, mes, ano = int(m.group(1)), int(m.group(2)), m.group(3)
    else:
        m = re.search(r"\b(\d{1,2})\s*/\s*(\d{1,2})(?:\s*/\s*(\d{2,4}))?", t)
        if not m:
            # "1ª quinzena", "primeira quinzena", "2a quinzena": o mês sai do envio
            n = norm(t)
            h = 1 if re.search(r"\b(1|1a|primeira)\b.*quinzena", n) else \
                2 if re.search(r"\b(2|2a|segunda)\b.*quinzena", n) else None
            if h and enviado:
                y, mes = enviado.year, enviado.month
                if h == 2 and enviado.day <= 5:      # 2ª quinzena mandada no início do mês seguinte
                    y, mes = (y - 1, 12) if mes == 1 else (y, mes - 1)
                return (y, mes, h)
            return None
        d, mes, ano = int(m.group(1)), int(m.group(2)), m.group(3)
    a = int(ano) + (2000 if ano and len(ano) == 2 else 0) if ano else ano_ref
    if not ano and enviado and mes > enviado.month + 1:     # dezembro citado em janeiro
        a -= 1
    try:
        return quinzena(dt.date(a, mes, d))
    except ValueError:
        return None


def quinzena_do_envio(enviado: dt.datetime):
    # A nota chega até o dia do pagamento: o que foi enviado do dia 1 ao 15 é da
    # 1ª quinzena; do 16 em diante, da 2ª.
    return (enviado.year, enviado.month, 1 if enviado.day <= 15 else 2)


# ------------------------------------------------------------------ nomes
def nomes_trinks() -> dict[str, set[str]]:
    out = {"escova": set(), "spa": set()}
    for u, pasta in (("escova", RAIZ / "data"), ("spa", RAIZ / "data" / "spa")):
        try:
            pm = json.loads((pasta / "profissionais_cache.json").read_text(encoding="utf-8"))["payload"]["prof_map"]
            out[u] = {n for n in pm.values() if n}
        except (OSError, ValueError, KeyError):
            pass
    return out


def casar(nome: str, candidatos: set[str], aliases: dict[str, str]) -> tuple[str | None, str]:
    n = norm(nome)
    if not n:
        return None, "sem nome"
    if n in aliases:
        return aliases[n], "apelido"
    por_norm = {norm(c): c for c in candidatos}
    if n in por_norm:
        return por_norm[n], "exato"
    t = n.split()
    achados = [c for k, c in por_norm.items() if k.split()[0] == t[0] and len(t) > 1 and k.split()[-1] == t[-1]]
    if len(achados) == 1:
        return achados[0], "nome e sobrenome"
    achados = [c for k, c in por_norm.items() if k.split()[0] == t[0]]
    if len(achados) == 1:
        return achados[0], "primeiro nome"
    # apelido contido no primeiro nome ("carol" em "carollina")
    achados = [c for k, c in por_norm.items() if len(t[0]) >= 4 and k.split()[0].startswith(t[0])]
    if len(achados) == 1:
        return achados[0], "início do nome"
    return None, "não casou"


# ------------------------------------------------------------------ principal
def processar(linhas: list[dict], aliases: dict[str, str], cand: dict[str, set[str]]) -> list[dict]:
    if not linhas:
        return []
    cab = list(linhas[0].keys())
    c_env = coluna(cab, "hora de conclusao", "completion time", "hora de inicio", "start time")
    c_nome = coluna(cab, "nome", exato={"nome", "nome completo", "seu nome"})
    c_per = coluna(cab, "periodo", "quinzena")
    c_uni = coluna(cab, "unidade", "loja")
    c_val = coluna(cab, "valor")
    c_num = coluna(cab, "numero da n", "numero")
    c_cha = coluna(cab, "chave")
    c_arq = coluna(cab, "arquivo", "pdf", "anexo")
    c_id = coluna(cab, "id", exato={"id"})
    todos = cand["escova"] | cand["spa"]
    notas = []
    for i, l in enumerate(linhas, 1):
        env = data_hora(l.get(c_env)) if c_env else None
        uni_txt = norm(l.get(c_uni)) if c_uni else ""
        unidade = "spa" if "spa" in uni_txt else ("escova" if "escova" in uni_txt else None)
        nome_forms = str(l.get(c_nome) or "").strip() if c_nome else ""
        nome_trinks, como = casar(nome_forms, cand.get(unidade) or todos, aliases)
        if not nome_trinks and unidade:   # trabalha nas duas lojas?
            nome_trinks, como = casar(nome_forms, todos, aliases)
        q = quinzena_do_periodo(l.get(c_per), env) if c_per else None
        q_origem = "periodo"
        if not q and env:
            q, q_origem = quinzena_do_envio(env), "data_envio"
        num = re.sub(r"\D", "", str(l.get(c_num) or "")) if c_num and c_num != c_val else ""
        chave = re.sub(r"\D", "", str(l.get(c_cha) or "")) if c_cha else ""
        notas.append({
            "id": str(l.get(c_id) or i) if c_id else str(i),
            "enviado_em": env.isoformat(timespec="minutes") if env else None,
            "unidade": unidade,
            "nome_forms": nome_forms,
            "nome_trinks": nome_trinks,
            "casamento": como,
            "quinzena": qid(q) if q else None,
            "quinzena_origem": q_origem if q else None,
            "periodo_texto": str(l.get(c_per) or "").strip() if c_per else "",
            "valor": valor(l.get(c_val)) if c_val else None,
            "numero": num or None,
            "chave": chave if len(chave) >= 40 else None,
            "arquivo": str(l.get(c_arq) or "").strip()[:300] if c_arq else "",
        })
    # Reenvio da MESMA nota (mesmo número) pela mesma pessoa na mesma quinzena:
    # vale a última, a anterior fica marcada como substituída.
    ult = {}
    for n in sorted(notas, key=lambda x: x["enviado_em"] or ""):
        if n["numero"]:
            k = (n["nome_trinks"] or norm(n["nome_forms"]), n["unidade"], n["quinzena"], n["numero"])
            if k in ult:
                ult[k]["substituida"] = True
            ult[k] = n
    return notas


def main() -> int:
    if len(sys.argv) > 1:
        arq = Path(sys.argv[1])
    else:
        cands = sorted([*PASTA_FORMS.glob("*.xlsx"), *PASTA_FORMS.glob("*.csv")],
                       key=lambda p: p.stat().st_mtime) if PASTA_FORMS.exists() else []
        if not cands:
            print(f"Notas: nenhuma planilha do Forms em {PASTA_FORMS}. Baixe as respostas para lá.")
            return 3
        arq = cands[-1]
    try:
        al = json.loads(ALIASES.read_text(encoding="utf-8")) if ALIASES.exists() else {}
    except ValueError:
        al = {}
    aliases = {norm(k): v for k, v in (al.get("forms_para_trinks") or {}).items()}
    notas = processar(ler_planilha(arq), aliases, nomes_trinks())
    SAIDA.write_text(json.dumps({
        "gerado_em": dt.datetime.now(BRT).isoformat(timespec="seconds"),
        "fonte": arq.name,
        "notas": notas,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    sem_nome = [n["nome_forms"] for n in notas if not n["nome_trinks"]]
    sem_q = sum(1 for n in notas if not n["quinzena"])
    print(f"Notas: {len(notas)} respostas lidas de {arq.name}"
          + (f"; {len(sem_nome)} nome(s) sem par no Trinks: {', '.join(sorted(set(sem_nome)))}" if sem_nome else "")
          + (f"; {sem_q} sem quinzena" if sem_q else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
