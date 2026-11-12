#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera a pagina da RECEPCAO (so a aba Clientes) e o cofre dela.

Cria, na raiz do repositorio:
  recepcao.html                     pagina (derivada do index.html, sem dado)
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


def recorte(d: dict) -> dict:
    anual = (d.get("abas") or {}).get("anual") or {}
    return {
        "gerado_em": d.get("gerado_em"), "hoje": d.get("hoje"),
        "unidade": d.get("unidade"), "_unidade_ativa": d.get("_unidade_ativa"),
        "dias_op_mes": d.get("dias_op_mes"),
        "abas": {"anual": {k: anual[k] for k in CHAVES_CLIENTES if k in anual}},
        "insights": {"clientes": (d.get("insights") or {}).get("clientes")},
    }


# Secao "Pacotes com sessao a consumir" no topo da aba Clientes. Os dados vem do
# cofre-recepcao.js (evento recepcao-pacotes). Pacote nao tem validade: a lista
# e de quem ainda tem sessao sobrando, para a recepcao oferecer o uso/renovacao.
RENDER_PACOTES = r"""
<script>
(function(){
  var DADOS=null;
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function unidade(){try{return localStorage.getItem('unidade_ativa_recepcao')==='spa'?'spa':'escova';}catch(e){return 'escova';}}
  function dataBR(iso){var p=String(iso||'').split('-');return p.length===3?p[2]+'/'+p[1]+'/'+p[0]:esc(iso||'');}
  function desenhar(){
    var raiz=document.getElementById('tab-clientes'); if(!raiz||!DADOS) return;
    var alvo=document.getElementById('recepcao-pacotes');
    if(!alvo){alvo=document.createElement('div');alvo.id='recepcao-pacotes';raiz.insertBefore(alvo,raiz.firstChild);}
    var u=unidade(), lista=DADOS[u]||[], nome=u==='spa'?'Spa':'Escova';
    var q=(document.getElementById('rp-busca')||{}).value||'';
    var qn=q.toLowerCase();
    var linhasP=lista.map(function(p){
      var total=p.itens.reduce(function(s,it){return s+it.restante;},0);
      return {cliente:p.cliente,pacote:p.pacote,itens:p.itens,total:total};
    }).filter(function(p){return !qn||p.cliente.toLowerCase().indexOf(qn)>=0;});
    linhasP.sort(function(a,b){var pa=a.total<=1?0:(a.total===2?1:2),pb=b.total<=1?0:(b.total===2?1:2);return pa-pb||a.cliente.localeCompare(b.cliente,'pt-BR')||a.pacote.localeCompare(b.pacote,'pt-BR');});
    var renovar=lista.filter(function(p){return p.itens.reduce(function(s,it){return s+it.restante;},0)<=1;}).length;
    var linhas=linhasP.map(function(p){
      var itens=p.itens.map(function(it){return '<strong>'+it.restante+'</strong> × '+esc(it.servico);}).join('<br>');
      var sit=p.total<=1?'<strong style="color:#c0392b">🔴 Renovar agora</strong>':(p.total===2?'<strong style="color:#b7791f">🟡 Falta pouco</strong>':'<span style="color:var(--ink-3)">em uso</span>');
      return '<tr><td><strong>'+esc(p.cliente)+'</strong></td><td>'+esc(p.pacote)+'</td><td>'+itens+'</td><td>'+sit+'</td></tr>';
    }).join('');
    alvo.innerHTML='<div class="card"><h2>🎁 Pacotes com sessão a consumir · '+nome+'</h2>'+
      '<div class="cap"><strong>'+renovar+'</strong> pacote(s) com 1 sessão restante: oferecer a renovação antes de acabar e não deixar a cliente sair com a comanda zerada. Pacote não tem validade. Posição do Trinks em '+dataBR(DADOS.posicao)+'.</div>'+
      '<input id="rp-busca" type="search" placeholder="Buscar cliente…" value="'+esc(q)+'" style="width:100%;box-sizing:border-box;margin:10px 0;padding:9px 12px;font-size:15px;border:1px solid var(--border);border-radius:8px;background:var(--surface);color:var(--ink)">'+
      (linhas?'<div style="overflow-x:auto"><table><thead><tr><th>Cliente</th><th>Pacote</th><th>Falta consumir</th><th>Situação</th></tr></thead><tbody>'+linhas+'</tbody></table></div>':'<div class="cap">Nenhum cliente encontrado.</div>')+'</div>';
    var b=document.getElementById('rp-busca'); b.addEventListener('input',function(){var pos=b.selectionStart;desenhar();var n=document.getElementById('rp-busca');n.focus();try{n.setSelectionRange(pos,pos);}catch(e){}});
  }
  document.addEventListener('recepcao-pacotes',function(ev){DADOS=ev.detail;desenhar();});
  document.addEventListener('click',function(ev){if(ev.target.closest&&ev.target.closest('.unid-btn')){setTimeout(desenhar,80);}});
})();
</script>
"""


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
    corpo = corpo.replace("</head>", extra + RENDER_PACOTES + "</head>", 1)
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
        saida[u] = recorte(json.loads(p.read_text(encoding="utf-8")))
        print(f"[recepcao] {u}: dado de {saida[u]['gerado_em']}")
    enc = REPO / "data" / "recepcao_clientes.json.enc"
    enc.write_bytes(cifrar(json.dumps(saida, ensure_ascii=False).encode("utf-8"), s))
    print(f"[recepcao] {enc.relative_to(REPO)} gravado")
    return 0


if __name__ == "__main__":
    gerar_html()
    sys.exit(0 if "--so-html" in sys.argv else gerar_cofre())
