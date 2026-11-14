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
                   "churn_early", "cross_sell", "clientes_cadastro", "seg_genero"]


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
        ontem = (datetime.date.fromisoformat(str(d.get("hoje"))[:10]) - datetime.timedelta(days=1)).isoformat()
    except Exception:
        return []
    rec = json.loads(frec.read_text(encoding="utf-8"))
    cli = json.loads(fcl.read_text(encoding="utf-8"))
    cli = cli.get("payload", cli) if isinstance(cli, dict) else {}
    vistos, saida = set(), []
    for r in rec:
        if r.get("dia") != ontem or str(r["id"]) in vistos:
            continue
        vistos.add(str(r["id"]))
        saida.append({"cliente": r["nome"].strip(), "telefone": _tel(cli.get(str(r["id"])))})
    return sorted(saida, key=lambda x: x["cliente"].lower())


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


def recorte(d: dict, sub: str = "") -> dict:
    anual = (d.get("abas") or {}).get("anual") or {}
    return {
        "gerado_em": d.get("gerado_em"), "hoje": d.get("hoje"),
        "unidade": d.get("unidade"), "_unidade_ativa": d.get("_unidade_ativa"),
        "dias_op_mes": d.get("dias_op_mes"),
        "abas": {"anual": {k: anual[k] for k in CHAVES_CLIENTES if k in anual}},
        "insights": {"clientes": (d.get("insights") or {}).get("clientes")},
        "ontem": _ontem(d, sub),
        "base": _base(sub),
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
    app = '<script src="recepcao-app.js"></script>\n'
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
