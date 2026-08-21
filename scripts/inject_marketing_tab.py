r"""Injeta a aba Marketing no index.html — de forma idempotente.

Por que existe: o index.html é regenerado inteiro pelo publish_pages.py (vault do
Rodrigo). Qualquer edição manual no arquivo seria perdida no próximo refresh. Este
script re-aplica a aba em cima do HTML gerado, quantas vezes for preciso, sempre
com o mesmo resultado.

Roda sozinho no GitHub Actions a cada push que toque o index.html, e pode ser
chamado no fim do publish_pages.py na máquina Windows.

Uso:
  python scripts/inject_marketing_tab.py            # aplica
  python scripts/inject_marketing_tab.py --check    # só verifica (exit 1 se faltar)
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX = REPO_ROOT / "index.html"

BLOCO_CSS = """<!-- MKT:CSS -->
<link rel="stylesheet" href="assets/marketing.css">
<!-- /MKT:CSS -->
"""

BLOCO_TAB = """<!-- MKT:TAB --><button class="tab-btn" role="tab" aria-selected="false" \
data-tab="marketing">📣 Marketing<span class="subn" id="tab-marketing-sub"></span></button>\
<!-- /MKT:TAB -->"""

BLOCO_PANEL = """    <!-- MKT:PANEL -->
    <div class="panel" id="tab-marketing">
      <div class="audit"><div>📣</div><div>Gestão de <strong>Instagram, Facebook e Google Meu \
Negócio</strong>. Calendário editorial, avaliações e pauta gerada a partir dos números reais do \
Trinks. Dados de <code>data/marketing_data.json</code>.</div></div>
      <div id="mk-app"><div class="card"><h2>Carregando marketing…</h2></div></div>
    </div>
    <!-- /MKT:PANEL -->
"""

BLOCO_JS = """<!-- MKT:JS -->
<script src="assets/marketing.js"></script>
<!-- /MKT:JS -->
"""


def limpar(html: str) -> str:
    """Remove blocos já injetados — deixa o HTML como o gerador o produziu.

    Duas formas: bloco em linha própria (leva a quebra de linha junto) e bloco
    inline, como o botão da aba, que vive no meio da linha das outras abas. A
    distinção é o que torna a injeção estável: rodar 1x ou 10x dá o mesmo arquivo.
    """
    for marca in ("CSS", "TAB", "PANEL", "JS"):
        for padrao in (
            rf"(?<=\n)[ \t]*<!-- MKT:{marca} -->.*?<!-- /MKT:{marca} -->[ \t]*\n",
            rf"<!-- MKT:{marca} -->.*?<!-- /MKT:{marca} -->",
        ):
            html = re.sub(padrao, "", html, flags=re.DOTALL)
    return html


def injetar(html: str) -> str:
    html = limpar(html)

    # 1. CSS antes do </head>
    if "</head>" not in html:
        raise RuntimeError("Âncora </head> não encontrada")
    html = html.replace("</head>", BLOCO_CSS + "</head>", 1)

    # 2. Botão da aba, depois do último .tab-btn existente
    botoes = list(re.finditer(r'<button class="tab-btn"[^>]*>.*?</button>', html, re.DOTALL))
    if not botoes:
        raise RuntimeError("Nenhum .tab-btn encontrado — estrutura de abas mudou")
    fim = botoes[-1].end()
    html = html[:fim] + BLOCO_TAB + html[fim:]

    # 3. Painel, imediatamente antes do <footer>
    m = re.search(r"\n(\s*)<footer>", html)
    if not m:
        raise RuntimeError("Âncora <footer> não encontrada")
    corte = m.start() + 1  # depois da quebra de linha, na coluna do <footer>
    html = html[:corte] + BLOCO_PANEL + html[corte:]

    # 4. Script antes do </body>
    if "</body>" not in html:
        raise RuntimeError("Âncora </body> não encontrada")
    html = html.replace("</body>", BLOCO_JS + "</body>", 1)

    return html


def main() -> int:
    ap = argparse.ArgumentParser(description="Injeta a aba Marketing no index.html")
    ap.add_argument("--check", action="store_true", help="apenas verifica, não escreve")
    args = ap.parse_args()

    if not INDEX.exists():
        print("index.html não encontrado", file=sys.stderr)
        return 1

    original = INDEX.read_text(encoding="utf-8")
    try:
        novo = injetar(original)
    except RuntimeError as e:
        print(f"Falha ao injetar: {e}", file=sys.stderr)
        return 1

    if novo == original:
        print("Aba Marketing já presente e atualizada — nada a fazer")
        return 0

    if args.check:
        print("Aba Marketing AUSENTE ou desatualizada no index.html", file=sys.stderr)
        return 1

    INDEX.write_text(novo, encoding="utf-8")
    print("Aba Marketing injetada no index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
