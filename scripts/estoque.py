# -*- coding: utf-8 -*-
"""Controle de estoque: lê a aba de estoque da planilha da Siibello e devolve o
bloco `estoque` de cada financeiro.json.

Por que existe: pedido do Rodrigo em 27/10/2026 - "coloque dentro do painel, ele
conecta com pagamentos que não foram CAPEX e nem despesas; garanta que a
auditoria valide isso sempre; definiremos a regra de amortização para o
resultado". Até ali, compra de material (Mercado Livre, Kione, Glossex, Tulipia)
ficava ora no CAPEX, ora como despesa, e o estoque de R$ 21 mil de 30/09 era o
valor de compra sem nenhum consumo descontado.

A REGRA
  Compra de estoque não é CAPEX nem despesa: é dinheiro parado na prateleira.
  Ela sai do caixa, mas só entra no resultado quando for consumida (ou pela
  regra de amortização, ainda a definir). Por isso um mesmo pagamento NUNCA
  pode estar no estoque e, ao mesmo tempo, numa categoria CAPEX/OPEX do razão:
  seria contado duas vezes.

A ABA (procurada pelo nome: "Estoque" ou "Contagem de estoque")
  - Resumo do CMV: linha cuja coluna B começa com "Estoque inicial", com o
    valor da Escova na C e o do Spa na D (data entre parênteses no rótulo).
  - Data da contagem: linha com "Data da contagem" na coluna A ou B e a data
    na célula seguinte. Sem data, a contagem é tratada como não feita.
  - Produtos: coluna A = "Escova" ou "Spa", B produto, D uso (Serviço /
    Revenda / Fora do CMV), F quantidade contada, G custo unitário, H valor.
  - Compras de estoque: coluna A = data do pagamento, B descrição, C loja
    (Escova / Spa / Rateio), D origem ("Conta XP" ou "Cartão ..."), E valor,
    F uso. É a ligação com os pagamentos.

A CONFERÊNCIA (feita aqui, porque só aqui a planilha está aberta; a auditoria
lê o resultado gravado no JSON e acusa)
  - toda compra com origem na conta XP precisa achar o seu pagamento no razão
    (aba Conta_XP) pela data e pelo valor;
  - esse pagamento tem de estar classificado como estoque (categoria que começa
    com "Estoque") e não como CAPEX ou OPEX;
  - o total do razão classificado como estoque tem de bater com o total das
    compras de origem XP. Pagamento classificado como estoque no razão e
    ausente da aba é estoque que o controle não vê.
  As linhas são achadas por data e valor, nunca pelo número da linha: o razão
  cresce e os números andam (já aconteceu com o Pix do Bruno, l.89 -> l.90).
"""
import datetime
import re
import unicodedata

USOS = ("Serviço", "Revenda", "Fora do CMV")


def _norm(s):
    if s is None:
        return ""
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(s.lower().split())


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _data(v):
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    m = re.match(r"^\s*(\d{1,2})/(\d{1,2})/(\d{2,4})\s*$", str(v or ""))
    if m:
        d, mo, a = (int(x) for x in m.groups())
        return datetime.date(a + 2000 if a < 100 else a, mo, d)
    return None


def _brl(v):
    return f"R$ {v:,.2f}".replace(",", "~").replace(".", ",").replace("~", ".")


def _uso(v):
    n = _norm(v)
    if n.startswith("serv"):
        return "Serviço"
    if n.startswith("reven"):
        return "Revenda"
    if n.startswith("fora"):
        return "Fora do CMV"
    return None


def _loja(v):
    n = _norm(v)
    if n.startswith("escova"):
        return {"escova": 1.0}
    if n.startswith("spa"):
        return {"spa": 1.0}
    if "rateio" in n or "50/50" in n or "ambas" in n:
        return {"escova": 0.5, "spa": 0.5}
    return None


def _origem(v):
    n = _norm(v)
    if "xp" in n:
        return "conta_xp"
    if "cart" in n:
        return "cartao"
    return "outra"


def achar_aba(wb):
    for nome in wb.sheetnames:
        n = _norm(nome)
        if n == "estoque" or "contagem de estoque" in n or n.startswith("estoque"):
            return wb[nome]
    return None


def _vazio(loja):
    return {
        "status": "aba_ausente",
        "loja": loja,
        "inicial": {"data": None, "valor": None},
        "compras": {"total": 0.0, "n": 0, "por_mes": {}, "por_uso": {}, "por_origem": {}},
        "contagem": {"data": None, "valor": None, "produtos": 0, "contados": 0,
                     "sem_uso": 0, "por_uso": {}},
        "consumo_estimado": None,
        "fora_do_resultado": 0.0,
        "amortizacao": {"regra": None,
                        "obs": "regra a definir pelo Rodrigo; até lá as compras de "
                               "estoque não entram no resultado"},
    }


def _soma(d, k, v):
    d[k] = round(d.get(k, 0.0) + v, 2)


def ler(wb, regra_amortizacao=None):
    """Devolve {"escova": bloco, "spa": bloco, "consolidado": bloco}."""
    ws = achar_aba(wb)
    blocos = {u: _vazio(u) for u in ("escova", "spa", "consolidado")}
    for b in blocos.values():
        b["amortizacao"]["regra"] = regra_amortizacao
    if ws is None:
        blocos["consolidado"]["conferencia"] = {"status": "aba_ausente"}
        return blocos
    for b in blocos.values():
        b["status"] = "ok"
        b["aba"] = ws.title

    data_contagem = None
    compras_xp = []      # (data, valor) das compras com origem na conta XP
    compras_cartao = 0
    n_pagamentos = 0
    sem_loja = []

    for r in range(1, ws.max_row + 1):
        a, b_, c, d, e, f, g, h = (ws.cell(r, k).value for k in range(1, 9))
        na, nb = _norm(a), _norm(b_)

        if nb.startswith("estoque inicial"):
            m = re.search(r"\((\d{1,2}/\d{1,2}(?:/\d{2,4})?)\)", str(b_))
            dt = None
            if m:
                txt = m.group(1)
                dt = _data(txt if txt.count("/") == 2 else f"{txt}/{datetime.date.today().year}")
            for u, v in (("escova", c), ("spa", d)):
                blocos[u]["inicial"] = {"data": dt.isoformat() if dt else None,
                                        "valor": round(_num(v), 2) if _num(v) is not None else None}
            continue

        if "data da contagem" in na or "data da contagem" in nb:
            alvo = b_ if "data da contagem" in na else c
            dt = _data(alvo)
            data_contagem = dt.isoformat() if dt else None
            continue

        if na in ("escova", "spa") and b_ not in (None, ""):
            ct = blocos[na]["contagem"]
            ct["produtos"] += 1
            uso = _uso(d)
            qt, cu = _num(f), _num(g)
            if qt is not None:
                ct["contados"] += 1
                if uso is None and qt > 0:
                    ct["sem_uso"] += 1
                val = _num(h)
                if val is None and cu is not None:
                    val = qt * cu
                if val:
                    ct["valor"] = round((ct["valor"] or 0.0) + val, 2)
                    _soma(ct["por_uso"], uso or "sem uso", val)
            continue

        dt = _data(a)
        val = _num(e)
        if dt and val:
            val = abs(val)
            n_pagamentos += 1
            rateio = _loja(c)
            if rateio is None:
                sem_loja.append(f"{dt.isoformat()} {b_} {_brl(val)}")
                rateio = {"escova": 0.5, "spa": 0.5}
            origem = _origem(d)
            if origem == "conta_xp":
                compras_xp.append((dt, val, str(b_ or "")))
            elif origem == "cartao":
                compras_cartao += 1
            uso = _uso(f) or "sem uso"
            mes = f"{dt.year}-{dt.month:02d}"
            for u, frac in rateio.items():
                cp = blocos[u]["compras"]
                cp["total"] = round(cp["total"] + val * frac, 2)
                cp["n"] += 1
                _soma(cp["por_mes"], mes, val * frac)
                _soma(cp["por_uso"], uso, val * frac)
                _soma(cp["por_origem"], origem, val * frac)

    for u in ("escova", "spa"):
        bl = blocos[u]
        bl["contagem"]["data"] = data_contagem
        # Sem data de contagem, o que estiver na coluna de quantidade é rascunho.
        if not data_contagem:
            bl["contagem"]["valor"] = None
            bl["contagem"]["por_uso"] = {}
        ini = bl["inicial"]["valor"]
        cont = bl["contagem"]["valor"]
        if ini is not None and cont is not None:
            bl["consumo_estimado"] = round(ini + bl["compras"]["total"] - cont, 2)
        bl["fora_do_resultado"] = bl["compras"]["total"] if not regra_amortizacao else 0.0

    # Consolidado: soma, não leitura.
    cons = blocos["consolidado"]
    e_, s_ = blocos["escova"], blocos["spa"]

    def _som(x, y):
        return None if x is None or y is None else round(x + y, 2)

    cons["inicial"] = {"data": e_["inicial"]["data"] or s_["inicial"]["data"],
                       "valor": _som(e_["inicial"]["valor"], s_["inicial"]["valor"])}
    cons["compras"]["total"] = round(e_["compras"]["total"] + s_["compras"]["total"], 2)
    # Por pagamento: na loja, uma compra rateada conta nas duas.
    cons["compras"]["n"] = n_pagamentos
    for campo in ("por_mes", "por_uso", "por_origem"):
        tot = {}
        for x in (e_, s_):
            for k, v in x["compras"][campo].items():
                _soma(tot, k, v)
        cons["compras"][campo] = tot
    cons["contagem"] = {
        "data": data_contagem,
        "valor": _som(e_["contagem"]["valor"], s_["contagem"]["valor"]),
        "produtos": e_["contagem"]["produtos"] + s_["contagem"]["produtos"],
        "contados": e_["contagem"]["contados"] + s_["contagem"]["contados"],
        "sem_uso": e_["contagem"]["sem_uso"] + s_["contagem"]["sem_uso"],
        "por_uso": {},
    }
    for x in (e_, s_):
        for k, v in x["contagem"]["por_uso"].items():
            _soma(cons["contagem"]["por_uso"], k, v)
    cons["consumo_estimado"] = _som(e_["consumo_estimado"], s_["consumo_estimado"])
    cons["fora_do_resultado"] = round(e_["fora_do_resultado"] + s_["fora_do_resultado"], 2)

    cons["conferencia"] = conferir_razao(wb, compras_xp)
    cons["conferencia"]["compras_cartao_nao_conferidas"] = compras_cartao
    cons["conferencia"]["compras_sem_loja"] = sem_loja
    return blocos


def conferir_razao(wb, compras_xp):
    """Cruza as compras de origem XP com a aba Conta_XP (A data, D valor, G categoria)."""
    if "Conta_XP" not in wb.sheetnames:
        return {"status": "sem_razao"}
    ws = wb["Conta_XP"]
    razao = []  # (data, valor absoluto, categoria, linha)
    for r in range(1, ws.max_row + 1):
        dt, v, cat = _data(ws.cell(r, 1).value), _num(ws.cell(r, 4).value), ws.cell(r, 7).value
        if dt and v is not None and v < 0:
            razao.append((dt, round(-v, 2), str(cat or ""), r))

    usados = set()
    conflitos, sem_par = [], []
    for dt, val, desc in compras_xp:
        par = next((x for x in razao if x[0] == dt and abs(x[1] - val) <= 0.01 and x[3] not in usados), None)
        if par is None:
            sem_par.append(f"{dt.strftime('%d/%m/%Y')} {desc} {_brl(val)}")
            continue
        usados.add(par[3])
        if not _norm(par[2]).startswith("estoque"):
            conflitos.append(f"{dt.strftime('%d/%m/%Y')} {desc} {_brl(val)} está no razão "
                             f"(linha {par[3]}) como '{par[2] or 'sem categoria'}'")

    no_razao = [x for x in razao if _norm(x[2]).startswith("estoque")]
    fora_do_controle = [f"{x[0].strftime('%d/%m/%Y')} {_brl(x[1])} (linha {x[3]})"
                        for x in no_razao if x[3] not in usados]
    total_razao = round(sum(x[1] for x in no_razao), 2)
    total_xp = round(sum(v for _, v, _ in compras_xp), 2)
    return {
        "status": "ok",
        "razao_estoque_total": total_razao,
        "compras_xp_total": total_xp,
        "diferenca": round(total_razao - total_xp, 2),
        "conflitos_capex_opex": conflitos,
        "compras_sem_par_no_razao": sem_par,
        "razao_fora_do_controle": fora_do_controle,
    }
