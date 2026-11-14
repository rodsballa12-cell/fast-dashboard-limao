#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera a pagina da RECEPCAO (so a aba Clientes) e o cofre dela.

Cria, na raiz do repositorio:
  recepcao.html                     pagina (derivada do index.html, sem dado)
  recepcao-app.js                   tela "Hoje na recepcao" (escrita a mao)
  data/recepcao_clientes.json.enc   recorte de clientes Escova + Spa, CIFRADO
                                    com FAST_RECEPCAO_SENHA

Por que uma senha propria: a senha do Ritmo Fast (FAST_PAINEL_SENHA) abre
financeiro e comissao no repositorio publico. A recepcao nao precisa disso.

Roda no PC e no GitHub Actions (depois do `cofre.py abrir`). Sem a senha, o
passo avisa e sai com 0 para nao derrubar o refresh; a pagina fica com o ultimo
cofre que existia.

Uso:  python scripts/recepcao_gerar.py            (gera html + cofre)
      python scripts/recepcao_gerar.py --so-html  (so a pagina, sem senha)
"""
import json
import os
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

UNIDADES = {"escova": "data/dashboard_data.json", "spa": "data/spa/dashboard_data.json"}
# Unica parte de abas.anual que a aba Clientes le (renderClientes).
CHAVES_CLIENTES = ["clientes_snapshot", "top_ltv", "novos_vs_recorr", "aniversariantes",
                   "churn_early", "clientes_cadastro"]


def senha() -> str:
    arq = REPO / ".cofre" / "chaves.env"
    if arq.exists():
        for linha in arq.read_text(encoding="utf-8-sig").splitlines():
            if "=" in linha and not linha.strip().startswith("#"):
                k, v = linha.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    return os.environ.get("FAST_RECEPCAO_SENHA", "").strip()


def _tel(det: dict) -> str:
    t = (det or {}).get("telefone")
    if isinstance(t, list):
        t = t[0] if t else ""
    return str(t or "")


def _ontem(d: dict, sub: str) -> list:
    """Clientes atendidas no dia anterior ao `hoje` do painel (para o pos-venda)."""
    import datetime
    base = REPO / "data" / sub
    frec, fcl = base / "recepcao_ontem.json", base / "clientes_detalhes.json"
    if not (frec.exists() and fcl.exists()):
        return []
    try:
        h = datetime.date.fromisoformat(str(d.get("hoje"))[:10])
        ini, fim = (h - datetime.timedelta(days=3)).isoformat(), (h - datetime.timedelta(days=1)).isoformat()
    except Exception:
        return []
    rec = json.loads(frec.read_text(encoding="utf-8"))
    cli = json.loads(fcl.read_text(encoding="utf-8"))
    cli = cli.get("payload", cli) if isinstance(cli, dict) else {}
    vistos, saida = set(), []
    for r in sorted(rec, key=lambda r: r.get("dia", ""), reverse=True):  # o dia mais recente de cada cliente
        if not (ini <= r.get("dia", "") <= fim) or str(r["id"]) in vistos:
            continue
        vistos.add(str(r["id"]))
        saida.append({"cliente": r["nome"].strip(), "dia": r["dia"], "telefone": _tel(cli.get(str(r["id"])))})
    return sorted(saida, key=lambda x: (x["dia"], x["cliente"].lower()), reverse=True)


def _base(sub: str) -> list:
    """Todos os clientes da unidade (so nome, telefone e dia/mes do aniversario) para consulta."""
    f = REPO / "data" / sub / "clientes_detalhes.json"
    if not f.exists():
        return []
    c = json.loads(f.read_text(encoding="utf-8"))
    c = c.get("payload", c) if isinstance(c, dict) else {}
    saida = []
    for v in c.values():
        if not v.get("nome"):
            continue
        nasc = str(v.get("dataNascimento") or "")
        a = nasc[8:10] + "/" + nasc[5:7] if len(nasc) >= 10 else ""
        saida.append({"n": " ".join(v["nome"].split()), "t": _tel(v), "a": a})
    return sorted(saida, key=lambda x: x["n"].lower())


def _resgate(sub: str) -> list:
    """Lista completa de clientes sumidas (o painel guarda so as 50 primeiras)."""
    f = REPO / "data" / sub / "recepcao_resgate.json"
    if not f.exists():
        return []
    return [{k: v for k, v in x.items() if k != "ltv"} for x in json.loads(f.read_text(encoding="utf-8"))]


def _aniv30(d: dict, base: list) -> list:
    """Aniversariantes dos proximos 30 dias, de toda a base (o painel so lista 14 dias)."""
    import datetime
    try:
        h = datetime.date.fromisoformat(str(d.get("hoje"))[:10])
    except Exception:
        return []
    visitas = {" ".join(x["cliente"].split()).casefold(): x.get("n_visitas")
               for x in ((d.get("abas") or {}).get("anual") or {}).get("aniversariantes", [])}
    saida = []
    for c in base:
        a = c.get("a") or ""
        if len(a) != 5:
            continue
        try:
            x = datetime.date(h.year, int(a[3:5]), int(a[0:2]))
        except ValueError:
            continue
        if x < h:
            x = x.replace(year=h.year + 1)
        dias = (x - h).days
        if dias <= 30:
            saida.append({"cliente": c["n"], "data_aniv": a, "dias": dias, "telefone": c.get("t", ""),
                          "n_visitas": visitas.get(" ".join(c["n"].split()).casefold())})
    return sorted(saida, key=lambda x: (x["dias"], x["cliente"].lower()))


def _sem_dinheiro(a: dict) -> dict:
    """Tira valores em reais do recorte da recepcao (receita, LTV, ticket), mantendo a forma
    dos dados para o index.html (que le essas chaves) nao quebrar."""
    snap = dict(a.get("clientes_snapshot") or {})
    for k in ("ltv_medio", "ticket_medio_visita"):
        snap.pop(k, None)
    if "clientes_snapshot" in a:
        a["clientes_snapshot"] = snap
    if "top_ltv" in a:
        tl = a["top_ltv"]
        a["top_ltv"] = {"total_clientes": tl.get("total_clientes"), "uma_vez": tl.get("uma_vez"),
                        "duas_mais": tl.get("duas_mais"), "top": []}
    if "novos_vs_recorr" in a:
        nr = a["novos_vs_recorr"]
        a["novos_vs_recorr"] = {k: {"clientes": (nr.get(k) or {}).get("clientes"), "atend": (nr.get(k) or {}).get("atend"),
                                    "receita": 0} for k in ("novos", "recorrentes")}
    ch = a.get("churn_early")
    if ch:
        a["churn_early"] = {"n_alerta": ch.get("n_alerta"), "ltv_em_risco": 0,
                            "top": [{k: v for k, v in x.items() if k != "ltv"} for x in ch.get("top", [])]}
    if "aniversariantes" in a:
        a["aniversariantes"] = [{k: v for k, v in x.items() if k != "ltv"} for x in a["aniversariantes"]]
    return a


def _retoque(d: dict, sub: str, base: list) -> dict:
    """Listas do bloco Fast Retoque. Escova apenas (o Spa nao tem o servico)."""
    import datetime
    f = REPO / "data" / sub / "recepcao_retoque.json"
    vazio = {"lembrar": [], "atrasadas": [], "pacote": [], "nunca": []}
    if not f.exists():
        return vazio
    try:
        h = datetime.date.fromisoformat(str(d.get("hoje"))[:10])
    except Exception:
        return vazio
    raw = json.loads(f.read_text(encoding="utf-8"))
    tel = {}
    c = REPO / "data" / sub / "clientes_detalhes.json"
    if c.exists():
        cj = json.loads(c.read_text(encoding="utf-8"))
        cj = cj.get("payload", cj) if isinstance(cj, dict) else {}
        tel = {str(k): _tel(v) for k, v in cj.items()}
    out = {"lembrar": [], "atrasadas": [], "pacote": [], "nunca": []}
    for r in raw.get("retoque", []):
        dias = (h - datetime.date.fromisoformat(r["ultimo"])).days
        item = {"cliente": r["nome"].strip(), "dias": dias, "n": r["n"], "telefone": tel.get(str(r["id"]), "")}
        if 15 <= dias <= 25:
            out["lembrar"].append(item)
        elif 26 <= dias <= 60:
            out["atrasadas"].append(item)
        if r["n"] >= 2:
            out["pacote"].append(item)
    for r in raw.get("escova_sem_retoque", []):
        dias = (h - datetime.date.fromisoformat(r["ultima"])).days
        out["nunca"].append({"cliente": r["nome"].strip(), "dias_escova": r["dias_escova"], "dias": dias, "telefone": tel.get(str(r["id"]), "")})
    for k in ("lembrar", "atrasadas"):
        out[k].sort(key=lambda x: -x["dias"])
    out["pacote"].sort(key=lambda x: (-x["n"], x["dias"]))
    out["nunca"].sort(key=lambda x: (-x["dias_escova"], x["cliente"].lower()))
    return out


def recorte(d: dict, sub: str = "") -> dict:
    anual = (d.get("abas") or {}).get("anual") or {}
    return {
        "gerado_em": d.get("gerado_em"), "hoje": d.get("hoje"),
        "unidade": d.get("unidade"), "_unidade_ativa": d.get("_unidade_ativa"),
        "dias_op_mes": d.get("dias_op_mes"),
        "abas": {"anual": _sem_dinheiro({k: anual[k] for k in CHAVES_CLIENTES if k in anual})},
        "insights": {"clientes": (d.get("insights") or {}).get("clientes")},
        "resgate": _resgate(sub),
        "ontem": _ontem(d, sub),
        "base": _base(sub),
        "aniv30": _aniv30(d, _base(sub)),
        "retoque": _retoque(d, sub, []),
    }


def gerar_html() -> None:
    corpo = (REPO / "index.html").read_text(encoding="utf-8")
    # Cofre da recepcao no lugar do cofre do painel.
    corpo, n = re.subn(r'<script src="cofre-painel\.js[^"]*"></script>',
                       '<script src="cofre-recepcao.js"></script>', corpo, count=1)
    if not n:
        sys.exit('[recepcao] ERRO: nao achei <script src="cofre-painel.js"> no index.html')
    # Mesma origem do painel: nao compartilhar memoria local com ele.
    corpo = corpo.replace("'unidade_ativa'", "'unidade_ativa_recepcao'")
    corpo = corpo.replace("'fast_build'", "'fast_build_recepcao'")
    corpo = corpo.replace("<title>", "<title>Atendimento Fast · ", 1)
    # So a aba Clientes: as outras renderizacoes viram no-op (nao ha dado para elas).
    for chamada in ("renderPeriodoAtivo(data);", "renderStone(data);", "renderAuditoria(data);",
                    "if(FIN) renderFinanceiro();", "if(MID) renderMidias();"):
        if chamada not in corpo:
            print(f"[recepcao] AVISO: nao achei '{chamada}' (o index.html mudou?)")
        corpo = corpo.replace(chamada, "")
    # Sem Consolidado.
    corpo, n = re.subn(r'<button class="unid-btn" data-unidade="consolidado".*?</button>', "",
                       corpo, count=1, flags=re.S)
    if not n:
        print("[recepcao] AVISO: botao Consolidado nao encontrado")
    extra = (
        "<style>\n#content > .tabs{display:none!important}\n#content > .panel{display:none!important}\n"
        "#content > #tab-clientes{display:block!important}\n"
        "#chip-cota,#chip-live,#btn-reload,#saude-faixa{display:none!important}\n</style>\n"
        "<script>document.addEventListener('DOMContentLoaded',function(){\n"
        "var h=document.getElementById('brand-title');"
        "if(h)h.innerHTML='Atendimento <span style=\"color:var(--accent-ink)\">Fast</span>';\n"
        "var s=document.getElementById('brand-sub');if(s)s.textContent='Clientes · recepção';});</script>\n"
    )
    import hashlib

    def _v(nome):  # versao pelo conteudo: o navegador nunca fica com o script antigo
        return hashlib.sha1((REPO / nome).read_bytes()).hexdigest()[:8]
    app = '<script src="recepcao-app.js?v=' + _v("recepcao-app.js") + '"></script>\n'
    corpo = corpo.replace('<script src="cofre-recepcao.js"></script>',
                          '<script src="cofre-recepcao.js?v=' + _v("cofre-recepcao.js") + '"></script>')
    corpo = corpo.replace("</head>", extra + app + "</head>", 1)
    (REPO / "recepcao.html").write_text(corpo, encoding="utf-8")
    print(f"[recepcao] recepcao.html gerado ({len(corpo):,} chars)")


def gerar_cofre() -> int:
    s = senha()
    if not s:
        print("[recepcao] AVISO: falta FAST_RECEPCAO_SENHA — cofre da recepcao NAO atualizado.")
        return 0
    from cofre import cifrar
    saida = {}
    for u, rel in UNIDADES.items():
        p = REPO / rel
        if not p.exists():
            print(f"[recepcao] AVISO: {rel} ausente (cofre fechado?) — cofre NAO atualizado.")
            return 0
        saida[u] = recorte(json.loads(p.read_text(encoding="utf-8")), "" if u == "escova" else "spa/")
        print(f"[recepcao] {u}: dado de {saida[u]['gerado_em']}")
    enc = REPO / "data" / "recepcao_clientes.json.enc"
    enc.write_bytes(cifrar(json.dumps(saida, ensure_ascii=False).encode("utf-8"), s))
    print(f"[recepcao] {enc.relative_to(REPO)} gravado")
    return 0


if __name__ == "__main__":
    gerar_html()
    sys.exit(0 if "--so-html" in sys.argv else gerar_cofre())
