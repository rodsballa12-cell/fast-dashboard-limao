#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera o HTML do painel para publicar como Claude Artifact.

Por que existe: a CSP do Artifact bloqueia fetch externo, então todo JSON que o
index.html busca em runtime precisa ir embutido. O painel busca QUATRO arquivos
(dashboard_data, financeiro, midias_sociais, quota_status) — embutir só o
primeiro deixa as abas Financeiro e Mídias permanentemente vazias no Artifact,
sem erro visível, porque os loaders engolem a falha num catch.

Em vez de reescrever cada call site com regex (frágil: quebra quando o
index.html muda), instala um shim de fetch que serve os arquivos embutidos e
repassa o resto. O index.html não é modificado.

Uso:  python scripts/build_artifact.py [saida.html]
      (default: /tmp/artifact-updated.html)
"""
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
DATA = REPO / "data"
SAIDA_PADRAO = pathlib.Path("/tmp/artifact-updated.html")

# Arquivos que o index.html busca em runtime. `obrigatorio=False` = a ausência
# é um estado legítimo (quota_status.json só existe quando a cota estourou);
# o shim devolve 404 para esses, que é o que o loader do painel já trata.
ARQUIVOS = [
    ("data/dashboard_data.json", True),
    ("data/financeiro.json", True),
    ("data/midias_sociais.json", True),
    ("data/quota_status.json", False),
]


def js_seguro(texto: str) -> str:
    """Escapa o que pode quebrar um literal dentro de <script>."""
    return (
        texto.replace("</", "<\\/")
        .replace(" ", "\\u2028")
        .replace(" ", "\\u2029")
    )


def main() -> int:
    saida = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else SAIDA_PADRAO
    src = (REPO / "index.html").read_text(encoding="utf-8")

    embutidos: dict[str, object] = {}
    faltando: list[str] = []
    for rel, obrigatorio in ARQUIVOS:
        caminho = REPO / rel
        if not caminho.exists():
            if obrigatorio:
                faltando.append(rel)
            else:
                embutidos[rel] = None
                print(f"[build] {rel}: ausente (ok — opcional)")
            continue
        embutidos[rel] = json.loads(caminho.read_text(encoding="utf-8"))
        print(f"[build] {rel}: {caminho.stat().st_size:,} bytes embutidos")

    if faltando:
        print(f"[build] ERRO: arquivos obrigatórios ausentes: {', '.join(faltando)}")
        return 1

    title = re.search(r"<title>.*?</title>", src, re.S)
    style = re.search(r"<style>.*?</style>", src, re.S)
    body = re.search(r"<body>(.*)</body>", src, re.S)
    if not (title and style and body):
        print("[build] ERRO: não achei <title>/<style>/<body> no index.html")
        return 1
    corpo = body.group(1)

    # Desliga o auto-reload: num artifact estático ele só re-renderiza o mesmo
    # dado a cada 5 min. Casa qualquer setInterval que chame load() — a forma
    # exata já mudou uma vez (passou a recarregar financeiro e mídias junto), e
    # prender o build a um literal exato foi o que quebrou a versão anterior.
    corpo, n = re.subn(
        r"setInterval\(\s*\(\)\s*=>\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*,\s*5\s*\*\s*60\s*\*\s*1000\s*\);",
        "",
        corpo,
    )
    if n:
        print(f"[build] auto-reload de 5 min removido ({n}x)")
    else:
        print("[build] aviso: setInterval do auto-reload não encontrado — segue sem remover")

    dados_js = js_seguro(json.dumps(embutidos, ensure_ascii=False))
    shim = (
        "<script>\n"
        "// Dados embutidos: a CSP do Artifact bloqueia fetch externo.\n"
        f"window.__INLINE_DATA__ = {dados_js};\n"
        "(function(){\n"
        "  var orig = window.fetch ? window.fetch.bind(window) : null;\n"
        "  window.fetch = function(entrada, init){\n"
        "    var url = String(typeof entrada === 'string' ? entrada : (entrada && entrada.url) || '');\n"
        "    var chave = url.split('?')[0].replace(/^\\.?\\//, '');\n"
        "    if (Object.prototype.hasOwnProperty.call(window.__INLINE_DATA__, chave)) {\n"
        "      var valor = window.__INLINE_DATA__[chave];\n"
        "      if (valor === null) {\n"
        "        return Promise.resolve(new Response('', {status: 404, statusText: 'Not Found'}));\n"
        "      }\n"
        "      return Promise.resolve(new Response(JSON.stringify(valor), {\n"
        "        status: 200, headers: {'Content-Type': 'application/json'}\n"
        "      }));\n"
        "    }\n"
        "    if (!orig) return Promise.reject(new Error('fetch indisponível: ' + url));\n"
        "    return orig(entrada, init);\n"
        "  };\n"
        "})();\n"
        "</script>\n"
    )

    # O shim precisa existir antes de qualquer script do painel rodar.
    corpo = shim + corpo

    out = f"{title.group(0)}\n{style.group(0)}\n{corpo.strip()}"
    saida.write_text(out, encoding="utf-8")

    dash = embutidos["data/dashboard_data.json"]
    mid = embutidos["data/midias_sociais.json"]
    print(f"[build] OK · {saida} · {len(out):,} chars")
    print(f"  dashboard gerado_em: {dash.get('gerado_em')}")
    print(f"  midias    gerado_em: {mid.get('gerado_em')}")
    if embutidos.get("data/quota_status.json"):
        print("  ⚠️  cota Trinks marcada como esgotada — dashboard congelado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
