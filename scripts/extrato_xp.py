#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Classifica o extrato da conta XP e devolve o custo REAL, mês a mês.

POR QUE ESTE SCRIPT EXISTE (16/09/2026)

O `financeiro.json` é um DRE de PREMISSAS: comissão a 37,4% da receita, CMV a
12%, aluguel por rateio, mídia num valor fixo. Nenhuma dessas linhas nasce de
um pagamento; nascem de uma conta de padaria que alguém escreveu uma vez.

O extrato da conta corrente é a única fonte que diz o que de fato SAIU. Este
script o classifica e devolve, por mês, quanto foi pago em cada grupo do DRE —
para comparar premissa com realizado e corrigir a planilha.

O QUE ELE NÃO FAZ

Não mexe no `financeiro.json` nem na planilha (alçada do cargo Financeiro).
Imprime e, com --json, grava um resumo para o Rodrigo levar ao Excel.

RECEITA NÃO SAI DAQUI. A conta XP é conta de PAGAMENTO: o dinheiro de venda
chega por transferência, em lotes que não batem com dia nenhum de caixa. A
receita continua vindo do Trinks e a conciliação, da Stone.

APORTE NÃO É RECEITA E INVESTIMENTO NÃO É CUSTO. Transferência entre os sócios
e para a conta investimento soma R$ 1,2 milhão nos 90 dias — trinta vezes o
movimento da loja. Misturar isso com operação destrói qualquer leitura.

Uso:
    python3 scripts/extrato_xp.py <extrato.csv>
    python3 scripts/extrato_xp.py <extrato.csv> --json saida.json
"""
from __future__ import annotations
import argparse, csv, json, re, sys, unicodedata
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


# Ordem importa: a primeira regra que casar vence. Regras mais específicas em cima.
REGRAS = [
    # --- fora da operação -------------------------------------------------
    ("NAO_OPERACIONAL", "Sócios e conta investimento", [
        "conta investimento", "rodrigo de pinho garcia", "rosangela siqueira",
        "lucas de pinho garcia", "opiniao advisory",
    ]),
    ("A_CLASSIFICAR", "Transferências Siibello", ["siibello"]),

    # --- custo variável ---------------------------------------------------
    ("CMV", "Produtos e insumos", [
        "videlli", "cosmeticos", "belamax", "a.t. comercio",
    ]),

    # --- pessoal ----------------------------------------------------------
    ("PESSOAL_FIXO", "Gerente, recepção e limpeza", [
        "gabriela cristina da silva", "mirian fabiano", "adriana de souza angelico",
        "alice ferrari",
    ]),

    # --- ocupação ---------------------------------------------------------
    ("OCUPACAO", "Aluguel e IPTU", ["selo imoveis", "pref mun sao paulo"]),
    ("OCUPACAO", "Energia, água e gás", [
        "eletropaulo", "sabesp", "saneamento basico", "hiagas", "andrade distribuidora de aguas",
    ]),
    ("OCUPACAO", "Telefone, internet e seguro", ["claro s a", "porto s comp", "porto seguro"]),

    # --- comercial e franquia --------------------------------------------
    ("COMERCIAL", "Mídia paga", ["facebook servicos online", "pix marketplace"]),
    ("COMERCIAL", "Agência e gestão", [
        "xml marketing digital", "tem no limao producoes", "sunbrindes", "unifapris",
    ]),
    ("FRANQUIA", "Royalty e sistemas da rede", [
        "fast escova franchising", "fast escova on line", "safe2pay",
    ]),

    # --- obra, montagem e pré-operacional (CAPEX) -------------------------
    ("CAPEX", "Obra, montagem e mobiliário", [
        "derik presenca", "construcoes e reformas", "varotti", "lc produtos",
        "fastcril", "spazzio", "nova exaustores", "frm instalacoes", "master acrilico",
        "itaberaba comercio de tintas", "ferrassa e silva", "fast obras",
        "polo industria brasileira de uniformes", "l goldberg", "luxor - locacao",
        "amazon servicos", "ninja som", "magalupay",
    ]),
    ("CAPEX", "Serviços profissionais e abertura", [
        "roberto fontana", "id certificacao", "reynal comercio de papeis",
    ]),
]

# Quem é da equipe sai do dashboard, não de uma lista escrita à mão: assim
# entra gente nova sem ninguém lembrar de editar este arquivo. Inclui quem já
# saiu (aparece na auditoria de cancelados mas não no cadastro ativo) — senão
# a comissão de quem foi desligada no meio do mês vira "não classificado".
def nomes_equipe() -> set:
    try:
        d = json.loads((REPO / "data" / "dashboard_data.json").read_text(encoding="utf-8"))
    except Exception:
        return set()
    fora = {"franqueada"}
    nomes = {norm(v["nome"]) for v in (d.get("prof_meta") or {}).values()
             if v.get("nome") and (v.get("funcao") or "").lower() not in fora}
    for p in ((d.get("auditoria_cancelados") or {}).get("por_profissional") or []):
        n = norm(p.get("nome") or "")
        if n and n != "—" and len(n.split()) >= 2:
            nomes.add(n)
    return nomes


# Vale-transporte: a passagem de ônibus em SP custa R$ 5,30, e o extrato está
# cheio de PIX de R$ 10,60 (ida e volta), R$ 21,20 (dois dias) e R$ 31,80 (três)
# pingados para a equipe quase todo dia — 68 lançamentos no trimestre. Sem esta
# regra cada um vira "não classificado" e some; juntos são uma linha de custo
# que o DRE não tem.
PASSAGEM = 5.30


def eh_vale_transporte(valor: float) -> bool:
    v = abs(valor)
    if v <= 0 or v > 12 * PASSAGEM:
        return False
    return abs(round(v / PASSAGEM) * PASSAGEM - v) < 0.01


def parte(desc: str) -> str:
    for pre in ("Pix recebido de ", "Pix enviado para ", "Pix devolvido de ",
                "Pix XP enviado para ", "TED recebida de ", "Pagamento para ",
                "Transferência enviada para "):
        if desc.startswith(pre):
            return desc[len(pre):].strip()
    return desc.strip()


def classificar(desc: str, valor: float, equipe: set):
    d = norm(desc)
    for grupo, linha, chaves in REGRAS:
        if any(k in d for k in chaves):
            return grupo, linha
    # Equipe entra depois das regras fixas: a Gabriela é gerente (pessoal fixo),
    # não comissão, mesmo estando no prof_meta.
    p = norm(parte(desc))
    for nome in equipe:
        # sobrenome basta: o extrato traz "64.083.705 Erika Thais Pereira Melim Dona"
        if nome and (nome in p or all(t in p for t in nome.split()[:2])):
            return "COMISSAO", "Comissão sobre produção"
    if eh_vale_transporte(valor) and valor < 0:
        return "PESSOAL_FIXO", "Vale-transporte"
    return "OUTROS", "Não classificado"


def ler(csv_path: Path):
    def val(s):
        s = s.replace("R$", "").replace("\xa0", " ").strip()
        neg = s.startswith("-")
        return (-1 if neg else 1) * float(s.lstrip("-").strip().replace(".", "").replace(",", "."))
    linhas = []
    with open(csv_path, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if not r.get("Data"):
                continue
            dd, mm, aa = r["Data"].split("/")
            linhas.append({"data": f"20{aa}-{mm}-{dd}",
                           "desc": " ".join(r["Descricao"].split()),
                           "valor": val(r["Valor"])})
    return linhas


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--json", help="grava o resumo neste arquivo")
    args = ap.parse_args()

    linhas = ler(Path(args.csv))
    equipe = nomes_equipe()
    meses = defaultdict(lambda: defaultdict(float))
    detalhe = defaultdict(lambda: defaultdict(list))
    for x in linhas:
        g, sub = classificar(x["desc"], x["valor"], equipe)
        mes = x["data"][:7]
        meses[mes][(g, sub)] += x["valor"]
        detalhe[(g, sub)][mes].append(x)

    ordem = ["COMISSAO", "CMV", "PESSOAL_FIXO", "OCUPACAO", "COMERCIAL", "FRANQUIA",
             "CAPEX", "NAO_OPERACIONAL", "A_CLASSIFICAR", "OUTROS"]
    mlist = sorted(meses)
    chaves = sorted({k for m in meses.values() for k in m},
                    key=lambda k: (ordem.index(k[0]) if k[0] in ordem else 99, k[1]))

    larg = 13
    print(f"\n{'grupo · linha':<44}" + "".join(f"{m:>{larg}}" for m in mlist) + f"{'TOTAL':>{larg}}")
    print("-" * (44 + larg * (len(mlist) + 1)))
    grupo_ant = None
    for g, sub in chaves:
        if g != grupo_ant:
            print(f"\n{g}")
            grupo_ant = g
        vals = [meses[m].get((g, sub), 0.0) for m in mlist]
        print(f"  {sub[:41]:<42}" + "".join(f"{v:>{larg},.0f}" for v in vals)
              + f"{sum(vals):>{larg},.0f}")

    print()
    op = [k for k in chaves if k[0] in ("COMISSAO", "CMV", "PESSOAL_FIXO", "OCUPACAO",
                                        "COMERCIAL", "FRANQUIA")]
    tot_op = [sum(meses[m].get(k, 0.0) for k in op) for m in mlist]
    print(f"  {'CUSTO OPERACIONAL (sem CAPEX, sem sócios)':<42}"
          + "".join(f"{v:>{larg},.0f}" for v in tot_op) + f"{sum(tot_op):>{larg},.0f}")

    naoclass = detalhe.get(("OUTROS", "Não classificado"), {})
    if naoclass:
        itens = [x for m in naoclass.values() for x in m]
        print(f"\n⚠ {len(itens)} lançamentos não classificados · "
              f"R$ {sum(x['valor'] for x in itens):,.2f}")
        for x in sorted(itens, key=lambda x: x["valor"])[:15]:
            print(f"    {x['data']}  {x['valor']:>11,.2f}  {x['desc'][:58]}")

    if args.json:
        saida = {"periodo": [min(x["data"] for x in linhas), max(x["data"] for x in linhas)],
                 "meses": {m: {f"{g}|{s}": round(v, 2) for (g, s), v in meses[m].items()}
                           for m in mlist}}
        Path(args.json).write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n✍️  resumo em {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
