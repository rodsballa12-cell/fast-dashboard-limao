#!/usr/bin/env python3
"""Confere o painel contra os numeros extraidos do Trinks a mao.

POR QUE ISTO EXISTE
-------------------
Em 28/10/2026 o Rodrigo subiu um export do Trinks para a reuniao com a
agencia e pediu uma coisa simples: "garanta que batam". Ate entao ninguem
conferia — o painel calculava, o Trinks calculava, e os dois so se
encontravam na reuniao, na frente da agencia.

Este script e o encontro antecipado. Ele le os numeros que vieram do
Trinks (`data/trinks_conferencia.json`) e os compara, campo a campo, com o
que o painel gravou para o mesmo mes.

O QUE ELE DESCOBRE, E NAO SO CONFERE
------------------------------------
O painel tem DOIS numeros de receita, e eles nao sao o mesmo:

  caixa                  soma das formas de pagamento (dinheiro que entrou)
  total_recebido_trinks  servicos + produtos + pacotes + saldo - descontos

O bloco da aba Midias mostra um como "Faturamento" e usa o OUTRO como
numerador do ticket medio. Se os dois divergirem, quem na reuniao dividir
o faturamento pelos atendimentos vai achar um terceiro ticket medio — e a
conversa vira sobre o numero em vez de sobre a loja.

Entao este script compara o faturamento do Trinks com os DOIS, e diz qual
deles e o que o Trinks chama de faturamento. Essa resposta decide o que o
painel deve mostrar.

Mesma coisa no denominador do ticket: o export do Trinks de 28/10 divide o
faturamento pela "Qtd total de atendimentos", enquanto o painel divide por
"transacoes com pagamento". O script mostra os dois lado a lado.

COMO RODAR
----------
    python3 scripts/cofre.py abrir        # sem isto, nao ha o que ler
    python3 scripts/conferir_trinks.py            # todas as unidades e meses
    python3 scripts/conferir_trinks.py spa 2026-10

Sessao da nuvem nao roda: a chave do cofre so existe no PC e nos Secrets.

SAIDA
-----
    0  tudo dentro da tolerancia
    1  divergencia real (alguem precisa olhar antes da reuniao)
    2  nao deu para conferir (cofre fechado, mes ausente, etc)
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REF = RAIZ / "data" / "trinks_conferencia.json"

# Caminho do payload de cada unidade.
PAYLOAD = {
    "escova": RAIZ / "data" / "dashboard_data.json",
    "spa": RAIZ / "data" / "spa" / "dashboard_data.json",
    "consolidado": RAIZ / "data" / "consolidado" / "dashboard_data.json",
}

# Tolerancia por tipo de campo. Dinheiro aceita centavo de arredondamento;
# contagem nao aceita nada — 65 clientes novos e 66 sao fatos diferentes.
TOL_REAIS = 0.05
TOL_PCT_TICKET = 0.01   # o ticket e derivado: 1 centavo de folga


def _n(v):
    """Numero ou None. Campo ausente nunca vira zero (regra da casa)."""
    return v if isinstance(v, (int, float)) else None


def _fmt(v, dinheiro=False):
    if v is None:
        return "NAO VEJO"
    if dinheiro:
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{v:,.0f}".replace(",", ".") if float(v).is_integer() else f"{v:,.2f}"


def _linha(rot, trinks, painel, dinheiro=False, tol=0.0):
    """Uma linha do relatorio. Devolve ('ok'|'erro'|'indef', texto)."""
    t, p = _n(trinks), _n(painel)
    st = f"  {rot:26} Trinks {_fmt(t, dinheiro):>14}   painel {_fmt(p, dinheiro):>14}"
    if t is None or p is None:
        return "indef", st + "   ?  nao da para comparar"
    dif = p - t
    if abs(dif) <= tol:
        return "ok", st + "   OK"
    pct = (dif / t * 100) if t else float("inf")
    return "erro", st + f"   XX  diferenca {_fmt(dif, dinheiro)} ({pct:+.1f}%)"


def divergencias(ref, m):
    """Compara um mes do painel (`m`) com a referencia do Trinks (`ref`).

    Devolve lista de (campo, valor_trinks, valor_painel). Nao imprime nada —
    existe para que a auditoria de coerencia use a MESMA regra que o
    relatorio, em vez de ter uma segunda copia que envelhece sozinha.

    Campo ausente de um dos lados nao e divergencia: e coisa que nao deu
    para conferir, e quem chama decide o que fazer com isso.
    """
    fora = []
    pares = [
        ("meta", ref.get("meta"), m.get("meta"), TOL_REAIS),
        ("faturamento", ref.get("faturamento"), m.get("total_recebido_trinks"), TOL_REAIS),
        ("atendimentos", ref.get("atendimentos"), m.get("atend_fin"), 0),
        ("clientes_novos", ref.get("clientes_novos"), m.get("clientes_novos"), 0),
        ("pacotes_n", ref.get("pacotes_n"), m.get("pacotes_n"), 0),
        ("pacotes_v", ref.get("pacotes_v"), m.get("pacotes_v"), TOL_REAIS),
        ("ticket_medio", ref.get("ticket_medio"), m.get("ticket_medio"), TOL_PCT_TICKET),
    ]
    for campo, t, p_, tol in pares:
        t, p_ = _n(t), _n(p_)
        if t is None or p_ is None:
            continue
        if abs(p_ - t) > tol:
            fora.append((campo, t, p_))
    return fora


def conferir_mes(unidade, ym, ref, achados):
    """Compara um mes. Acrescenta linhas em `achados`."""
    arq = PAYLOAD.get(unidade)
    if arq is None:
        achados.append(("indef", f"{unidade}: unidade desconhecida"))
        return
    if not arq.exists():
        enc = arq.with_suffix(arq.suffix + ".enc")
        if enc.exists():
            # Um aviso por unidade, nao um por mes: a causa e a mesma e
            # repetir so faz o relatorio parecer ter mais problemas.
            msg = (f"{unidade}: o cofre esta FECHADO ({arq.name} so existe como "
                   ".enc). Rode `python3 scripts/cofre.py abrir` antes.")
            if ("indef", msg) not in achados:
                achados.append(("indef", msg))
        else:
            achados.append(("indef", f"{unidade}: {arq} nao existe."))
        return

    dash = json.loads(arq.read_text(encoding="utf-8"))
    meses = (((dash.get("abas") or {}).get("anual") or {}).get("meses")) or {}
    m = meses.get(ym)
    if not m:
        achados.append(("indef",
            f"{unidade} {ym}: o painel nao tem esse mes em abas.anual.meses. "
            "Rode o refresh do Trinks."))
        return

    print()
    print("=" * 78)
    print(f"  {unidade.upper()} · {ym}" + (f"  (Trinks parcial ate {ref['_parcial_ate']})"
                                           if ref.get("_parcial_ate") else ""))
    print(f"  fonte do lado Trinks: {ref.get('_fonte', 'nao informada')}")
    print(f"  painel gerado em:     {dash.get('gerado_em', '?')}")
    print("=" * 78)

    linhas = []

    # --- meta: vem do config, nao do Trinks; divergir aqui e cadastro errado
    linhas.append(_linha("Meta", ref.get("meta"), _n(m.get("meta")), dinheiro=True,
                         tol=TOL_REAIS))

    # --- A PERGUNTA: qual dos dois o Trinks chama de faturamento?
    caixa = _n(m.get("caixa"))
    recebido = _n(m.get("total_recebido_trinks"))
    fat_trinks = _n(ref.get("faturamento"))
    linhas.append(_linha("Faturamento (caixa)", fat_trinks, caixa, dinheiro=True,
                         tol=TOL_REAIS))
    linhas.append(_linha("Faturamento (recebido)", fat_trinks, recebido, dinheiro=True,
                         tol=TOL_REAIS))

    linhas.append(_linha("Atendimentos", ref.get("atendimentos"), _n(m.get("atend_fin"))))
    linhas.append(_linha("Clientes novos", ref.get("clientes_novos"),
                         _n(m.get("clientes_novos"))))
    linhas.append(_linha("Pacotes vendidos", ref.get("pacotes_n"), _n(m.get("pacotes_n"))))
    linhas.append(_linha("Valor dos pacotes", ref.get("pacotes_v"), _n(m.get("pacotes_v")),
                         dinheiro=True, tol=TOL_REAIS))

    # --- ticket medio: os dois caminhos, lado a lado
    linhas.append(_linha("Ticket medio", ref.get("ticket_medio"), _n(m.get("ticket_medio")),
                         dinheiro=True, tol=TOL_PCT_TICKET))

    for st, txt in linhas:
        print(txt)
        if st != "ok":
            achados.append((st, f"{unidade} {ym}: {txt.strip()}"))

    # --- o diagnostico que o relatorio existe para dar -------------------
    print()
    print("  Como cada lado chega no ticket medio:")
    n_pagto = _n(m.get("n_trans_com_pagto"))
    atend = _n(m.get("atend_fin"))
    if fat_trinks and ref.get("atendimentos"):
        print(f"    Trinks: {_fmt(fat_trinks, True)} / {ref['atendimentos']} atendimentos"
              f" = {_fmt(fat_trinks / ref['atendimentos'], True)}")
    if recebido is not None and n_pagto:
        print(f"    painel: {_fmt(recebido, True)} / {n_pagto} transacoes com pagamento"
              f" = {_fmt(recebido / n_pagto, True)}")
    if recebido is not None and atend:
        print(f"    painel, se dividisse por atendimentos ({atend})"
              f" = {_fmt(recebido / atend, True)}")

    if caixa is not None and recebido is not None:
        d = recebido - caixa
        if abs(d) > TOL_REAIS:
            print()
            print(f"  ATENCAO: os dois numeros de receita do painel diferem em"
                  f" {_fmt(d, True)}.")
            print("    `caixa` e o que entrou por forma de pagamento; "
                  "`total_recebido_trinks`")
            print("    soma servicos+produtos+pacotes+saldo-descontos. O bloco da aba")
            print("    Midias precisa mostrar o mesmo que serve de base ao ticket medio,")
            print("    senao quem dividir na reuniao acha um terceiro numero.")
            achados.append(("erro",
                f"{unidade} {ym}: caixa e total_recebido_trinks diferem em {_fmt(d, True)}"))
        else:
            print()
            print("  Os dois numeros de receita do painel coincidem — sem ambiguidade.")

    if n_pagto is not None and atend is not None and n_pagto != atend:
        print()
        print(f"  NOTA: o painel conta {n_pagto} transacoes com pagamento e {atend}")
        print(f"    atendimentos finalizados. O Trinks divide por atendimentos.")
        print("    Enquanto os dois diferirem, os tickets nao vao bater.")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not REF.exists():
        enc = REF.with_suffix(REF.suffix + ".enc")
        print("Nao achei data/trinks_conferencia.json.")
        if enc.exists():
            print("Ele esta no cofre: rode `python3 scripts/cofre.py abrir`.")
        else:
            print("Crie-o com os numeros do export do Trinks (veja o cabecalho "
                  "deste arquivo).")
        return 2

    ref_tudo = json.loads(REF.read_text(encoding="utf-8"))
    alvos = []
    if len(args) >= 1:
        unidades = [args[0]]
    else:
        unidades = [u for u in ref_tudo if not u.startswith("_")]
    for u in unidades:
        meses_ref = ref_tudo.get(u) or {}
        if not isinstance(meses_ref, dict):
            continue
        for ym, r in meses_ref.items():
            if ym.startswith("_") or not isinstance(r, dict):
                continue
            if len(args) >= 2 and ym != args[1]:
                continue
            alvos.append((u, ym, r))

    if not alvos:
        print("Nenhum mes a conferir com esses argumentos.")
        return 2

    achados = []
    for u, ym, r in sorted(alvos):
        conferir_mes(u, ym, r, achados)

    print()
    print("=" * 78)
    erros = [m for t, m in achados if t == "erro"]
    indef = [m for t, m in achados if t == "indef"]
    if erros:
        print(f"{len(erros)} divergencia(s) entre o painel e o Trinks:")
        for m in erros:
            print(f"  - {m}")
    if indef:
        print(f"{len(indef)} ponto(s) que nao deu para conferir:")
        for m in indef:
            print(f"  - {m}")
    if not achados:
        print("Tudo bate: o painel e o Trinks contam a mesma historia.")
    return 1 if erros else (2 if indef else 0)


if __name__ == "__main__":
    sys.exit(main())
