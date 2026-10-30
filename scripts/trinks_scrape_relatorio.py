#!/usr/bin/env python3
"""Scraper do painel web Trinks (sistema.trinks.com).

Rodrigo (29/10/2026): a API Trinks nao expoe o relatorio Movimentacoes
Financeiras (probe em 15 paths candidatos retornou 404 em todos). O
unico lugar onde os numeros existem agregados e no painel web. Este
script loga no painel, abre o relatorio do mes corrente, le os numeros
(Total Recebido, Qtde Atendimentos, Ticket Medio, Servicos, Produtos,
Pacotes, Credito Cliente, Pre-Pago, Descontos) e grava em
`data/trinks_conferencia.json` — mesma estrutura que o
`conferir_trinks.py` ja usa.

Credenciais via env:
  TRINKS_PAINEL_USUARIO_<UNIT>
  TRINKS_PAINEL_SENHA_<UNIT>

Uso:
  python3 scripts/trinks_scrape_relatorio.py --unidade escova
  python3 scripts/trinks_scrape_relatorio.py --unidade spa
  python3 scripts/trinks_scrape_relatorio.py --unidade escova --mes 2026-10
  python3 scripts/trinks_scrape_relatorio.py --unidade escova --debug

Com --debug, salva screenshot + HTML da pagina em /tmp pra inspecao
quando os seletores quebrarem (Trinks muda layout de vez em quando).

NAO DEPENDE DA API: usa Playwright com Chromium.
"""
import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Instale: pip install playwright && playwright install chromium")
    sys.exit(2)


BASE = "https://sistema.trinks.com"
RAIZ = Path(__file__).resolve().parent.parent
REF_FILE = RAIZ / "data" / "trinks_conferencia.json"


def _num_br(s):
    """Converte '25.900,02' / 'R$ 25.900,02' / '177,40' em float."""
    if s is None: return None
    s = str(s).strip()
    if not s: return None
    # tira R$, espacos, nbsp
    s = re.sub(r"[R\$\s ]", "", s)
    # 25.900,02 -> 25900.02
    s = s.replace(".", "").replace(",", ".")
    try: return float(s)
    except ValueError: return None


def _int_br(s):
    if s is None: return None
    s = str(s).strip()
    if not s: return None
    s = re.sub(r"[^\d-]", "", s)
    try: return int(s)
    except ValueError: return None


def _extrair_resumo(page, debug=False):
    """Varre o DOM procurando campos conhecidos do relatorio Movimentacoes
    Financeiras. Dois metodos: label text + sibling, ou tabela colunar.

    Retorna {faturamento, atendimentos, ticket_medio, servicos, produtos,
    pacotes, credito_cliente, pre_pago, descontos}, cada um None se nao achar.
    """
    # Pega todo o texto da pagina pra regex como fallback
    try:
        texto = page.locator("body").inner_text(timeout=5000)
    except Exception:
        texto = ""
    if debug:
        print(f"[debug] texto da pagina: {len(texto)} chars")

    def _re_num(padrao):
        m = re.search(padrao, texto, re.IGNORECASE)
        return _num_br(m.group(1)) if m else None

    def _re_int(padrao):
        m = re.search(padrao, texto, re.IGNORECASE)
        return _int_br(m.group(1)) if m else None

    # Padroes extraidos do screenshot do SPA out/26:
    #   "Total Recebido R$ 25.900,02"
    #   "Qtde Atendimentos com pagamento 146"
    #   "Ticket Medio R$ 177,40"
    #   "Servicos R$ 18.208,70"
    #   "Produtos R$ 948,00"
    #   "Pacotes R$ 6.081,00"
    #   "Credito Cliente R$ 7.135,00"
    #   "Pre-Pago -R$ 4.847,70"
    #   "Descontos R$ 23,02"
    return {
        "faturamento": _re_num(r"Total\s+Recebido[\s\S]{0,40}?R?\$?\s*([\d.,-]+)"),
        "atendimentos": _re_int(r"Qtde\s+Atendimentos[^\d]{0,30}?(\d[\d.]*)"),
        "ticket_medio": _re_num(r"Ticket\s+M[eé]dio[\s\S]{0,40}?R?\$?\s*([\d.,]+)"),
        "servicos": _re_num(r"Servi[cç]os[\s\S]{0,40}?R?\$?\s*([\d.,-]+)"),
        "produtos": _re_num(r"Produtos[\s\S]{0,40}?R?\$?\s*([\d.,-]+)"),
        "pacotes": _re_num(r"Pacotes[\s\S]{0,40}?R?\$?\s*([\d.,-]+)"),
        "credito_cliente": _re_num(r"Cr[eé]dito\s+(?:de\s+)?Cliente[\s\S]{0,40}?R?\$?\s*([\d.,-]+)"),
        "pre_pago": _re_num(r"Pr[eé][\s-]*Pago[\s\S]{0,40}?-?R?\$?\s*(-?[\d.,-]+)"),
        "descontos": _re_num(r"Descontos[\s\S]{0,40}?R?\$?\s*([\d.,-]+)"),
        "clientes_unicos": _re_int(r"N[ºo°]?\s*Clientes[^\d]{0,30}?(\d[\d.]*)"),
    }


def _login(page, usuario, senha, debug=False):
    """Faz login em sistema.trinks.com. Trinks parece usar email + senha
    simples; se a tela mudar, inspecionar com --debug."""
    page.goto(BASE, timeout=30000)
    if debug:
        print(f"[debug] url pos-goto: {page.url}")

    # Procura campos genericamente (type=email, type=password)
    try:
        page.locator("input[type='email'], input[name='email'], input[name='usuario'], input[name='login']").first.fill(usuario, timeout=15000)
    except Exception as e:
        if debug: _dump(page, "login_falhou_email", exc=e)
        raise
    try:
        page.locator("input[type='password']").first.fill(senha, timeout=5000)
    except Exception as e:
        if debug: _dump(page, "login_falhou_senha", exc=e)
        raise
    # botao de login — Entrar / Login / submit
    try:
        page.locator("button[type='submit'], button:has-text('Entrar'), button:has-text('Login')").first.click(timeout=5000)
    except Exception:
        page.keyboard.press("Enter")
    page.wait_for_load_state("networkidle", timeout=30000)
    if debug:
        print(f"[debug] url pos-login: {page.url}")


def _dump(page, nome, exc=None):
    out = Path("/tmp") / f"trinks_dump_{nome}"
    try:
        page.screenshot(path=str(out) + ".png", full_page=True)
        (out.with_suffix(".html")).write_text(page.content(), encoding="utf-8")
        print(f"[debug] dump salvo em {out}.png / .html")
    except Exception as e:
        print(f"[debug] falha ao dumpar: {e}")
    if exc:
        print(f"[debug] exc: {exc}")


def _ir_pro_relatorio(page, data_ini, data_fim, debug=False):
    """Navega ate o relatorio Movimentacoes Financeiras no periodo pedido.

    Como nao conheco a URL interna, tenta duas estrategias:
    1. URL direta /relatorios/movimentacoes-financeiras com query params
    2. Clicks: menu Relatorios > Financeiro > Movimentacoes
    """
    # Estrategia 1: URL direta (chute informado — ajustar se dumping mostrar
    # outra rota depois do primeiro run)
    candidatos = [
        f"{BASE}/relatorios/movimentacoes-financeiras?dataInicio={data_ini}&dataFim={data_fim}",
        f"{BASE}/relatorios/financeiro/movimentacoes?dataInicio={data_ini}&dataFim={data_fim}",
        f"{BASE}/#/relatorios/movimentacoes-financeiras",
        f"{BASE}/relatorios",
    ]
    for url in candidatos:
        try:
            page.goto(url, timeout=20000)
            page.wait_for_load_state("networkidle", timeout=15000)
            txt = page.locator("body").inner_text(timeout=3000)
            if "Movimenta" in txt and "Total Recebido" in txt:
                if debug: print(f"[debug] bateu em: {url}")
                return True
        except Exception as e:
            if debug: print(f"[debug] falhou {url}: {e}")
    # Estrategia 2: clicks via menu
    try:
        page.locator("a:has-text('Relat'), button:has-text('Relat')").first.click(timeout=5000)
        page.locator("a:has-text('Movimenta'), button:has-text('Movimenta')").first.click(timeout=5000)
        page.wait_for_load_state("networkidle", timeout=15000)
        return True
    except Exception as e:
        if debug: _dump(page, "nao_achou_menu", exc=e)
        return False


def coletar(unidade, mes_ym, debug=False, headless=True):
    usuario = os.environ.get(f"TRINKS_PAINEL_USUARIO_{unidade.upper()}")
    senha = os.environ.get(f"TRINKS_PAINEL_SENHA_{unidade.upper()}")
    if not usuario or not senha:
        print(f"[erro] faltam secrets TRINKS_PAINEL_USUARIO_{unidade.upper()} / SENHA_{unidade.upper()}")
        return None

    ano, mm = mes_ym.split("-")
    ini = f"{ano}-{mm}-01"
    # fim = hoje se mes atual; senao ultimo dia do mes
    hoje = date.today()
    if int(ano) == hoje.year and int(mm) == hoje.month:
        fim = hoje.isoformat()
    else:
        from calendar import monthrange
        fim = f"{ano}-{mm}-{monthrange(int(ano), int(mm))[1]:02d}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, executable_path="/opt/pw-browsers/chromium",
                                     args=["--no-sandbox"])
        try:
            ctx = browser.new_context(locale="pt-BR")
            page = ctx.new_page()
            _login(page, usuario, senha, debug=debug)
            ok = _ir_pro_relatorio(page, ini, fim, debug=debug)
            if not ok:
                _dump(page, f"{unidade}_sem_relatorio")
                return None
            if debug:
                _dump(page, f"{unidade}_relatorio")
            resumo = _extrair_resumo(page, debug=debug)
            resumo["_fonte"] = f"Trinks painel web · scraping · periodo {ini} a {fim}"
            resumo["_parcial_ate"] = fim
            return resumo
        finally:
            browser.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unidade", required=True, choices=["escova", "spa"])
    ap.add_argument("--mes", default=None, help="YYYY-MM, default = mes corrente")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--headful", action="store_true", help="browser visivel (debug local)")
    args = ap.parse_args()

    mes = args.mes or date.today().strftime("%Y-%m")
    print(f"[scrape] {args.unidade} {mes}")
    resumo = coletar(args.unidade, mes, debug=args.debug, headless=not args.headful)
    if not resumo:
        print("[erro] nao consegui coletar — rode com --debug e inspecione /tmp/trinks_dump_*")
        return 1
    print("[scrape] resumo bruto:")
    for k, v in resumo.items():
        print(f"  {k}: {v}")

    # Grava em trinks_conferencia.json com a chave da estrutura esperada
    ref = {}
    if REF_FILE.exists():
        ref = json.loads(REF_FILE.read_text(encoding="utf-8"))
    ref.setdefault(args.unidade, {})

    entry = {
        "_fonte": resumo.get("_fonte"),
        "_parcial_ate": resumo.get("_parcial_ate"),
        "faturamento": resumo.get("faturamento"),
        "atendimentos": resumo.get("atendimentos"),
        "ticket_medio": resumo.get("ticket_medio"),
        "pacotes_v": resumo.get("pacotes"),
        "_clientes_unicos": resumo.get("clientes_unicos"),
        "_servicos": resumo.get("servicos"),
        "_produtos": resumo.get("produtos"),
        "_credito_cliente": resumo.get("credito_cliente"),
        "_pre_pago": resumo.get("pre_pago"),
        "_descontos": resumo.get("descontos"),
    }
    # Nao sobrescreve pacotes_n/clientes_novos que podem ter vindo manual
    old = ref[args.unidade].get(mes, {})
    for k_old in ("pacotes_n", "clientes_novos"):
        if k_old in old and entry.get(k_old) is None:
            entry[k_old] = old[k_old]

    ref[args.unidade][mes] = entry
    REF_FILE.write_text(json.dumps(ref, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[scrape] gravado em {REF_FILE}: {args.unidade}.{mes}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
