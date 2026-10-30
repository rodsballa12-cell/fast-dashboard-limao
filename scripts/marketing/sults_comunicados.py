#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lê os COMUNICADOS do SULTS (franqueadora) e baixa o manual de marketing do mês.

Só leitura: usa apenas os 3 endpoints GET do módulo Comunicados da API v2
(https://developers.sults.com.br). Não chama Compras, Chamados nem Checklist.

O token v2 vale para TODOS os endpoints da v2 (a SULTS ainda não tem escopo por
token), por isso:
  · ele fica só na variável de ambiente SULTS_TOKEN_V2 do PC, nunca no repositório
    (o repositório é público) e nunca impresso;
  · este script só faz GET em /api/v2/comunicado/...;
  · o token só é enviado a hosts *.sults.com.br.

Uso:
  python sults_comunicados.py listar [--loja escova|spa] [--categoria ID] [--paginas 3]
  python sults_comunicados.py manual [--loja escova|spa] [--palavra marketing] [--saida PASTA]
O comando `manual` baixa os anexos dos comunicados ativos cujo título ou categoria
contém a palavra, para PASTA/AAAA-MM/, sem sobrescrever o que já existe.
Código de saída: 0 achou e baixou algo novo · 3 nada novo · 2 sem token ou erro.
"""
import argparse, datetime, json, os, re, sys, time, urllib.parse, urllib.request, urllib.error

BASE = "https://api.sults.com.br/api/v2/comunicado/announcement"
SAIDA_PADRAO = "C:/Users/rods_/OneDrive/Franquia - FAST/Claude/Marketing/Manuais_Franqueadora"


LOJAS = {"escova": "SULTS_TOKEN_V2", "spa": "SULTS_TOKEN_V2_SPA"}   # cada loja é uma empresa no SULTS, com token próprio


def _token(loja="escova"):
    var = LOJAS[loja]
    t = os.environ.get(var, "").strip()
    if not t:
        # sessões do Claude abertas antes do token ser salvo não o enxergam; o Windows guarda no perfil do usuário
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                t = str(winreg.QueryValueEx(k, var)[0]).strip()
        except Exception:
            t = ""
    if not t:
        print(f"SEM TOKEN da loja {loja}: defina a variável de ambiente {var} (Segurança > API > Gestão de Tokens v2, só administrador).", file=sys.stderr)
        sys.exit(2)
    return t


def _get(url, token, params=None, binario=False):
    url = urllib.parse.quote(url, safe=":/?&=%#+,;@!$'()*[]~")   # anexo com acento no nome quebrava a requisição
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    host = urllib.parse.urlparse(url).hostname or ""
    headers = {"Accept": "application/json"}
    if host.endswith("sults.com.br"):
        headers["Authorization"] = token          # token puro, sem 'Bearer'
    time.sleep(0.6)                               # limite da API: 2 requisições por segundo
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
            dados = r.read()
            return dados if binario else json.loads(dados.decode("utf-8"))
    except urllib.error.HTTPError as e:
        corpo = ""
        try:
            corpo = e.read().decode("utf-8", "replace")[:300]       # mensagem da SULTS (não contém o token)
        except Exception:
            pass
        print(f"ERRO {e.code} em {urllib.parse.urlparse(url).path} · {corpo}", file=sys.stderr)
        sys.exit(2)


def listar_comunicados(token, categoria=None, paginas=3):
    out = []
    for pg in range(paginas):
        lote = _get(BASE + "/list", token, {"categoryId": categoria, "active": "true", "page": pg})
        if not lote:
            break
        out += lote
    return out


def conteudo(token, anuncio_id):
    return _get(BASE + "/content/list", token, {"announcementId": anuncio_id})


def nome_seguro(n):
    return re.sub(r'[\\/:*?"<>|]+', "_", n).strip() or "arquivo"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("listar"); a.add_argument("--loja", choices=list(LOJAS), default="escova"); a.add_argument("--categoria", type=int); a.add_argument("--paginas", type=int, default=3)
    b = sub.add_parser("manual"); b.add_argument("--loja", choices=list(LOJAS), default="escova"); b.add_argument("--palavra", default="marketing"); b.add_argument("--saida", default=SAIDA_PADRAO); b.add_argument("--paginas", type=int, default=3)
    args = ap.parse_args()
    token = _token(args.loja)

    if args.cmd == "listar":
        for c in listar_comunicados(token, args.categoria, args.paginas):
            cat = (c.get("category") or {}).get("name", "")
            print(f'{c["id"]:>6} | {c.get("createdAt","")[:10]} | {cat:<20} | {c.get("title","")}')
        return

    palavra = args.palavra.lower()
    novos = 0
    pasta = os.path.join(args.saida, datetime.date.today().strftime("%Y-%m"), args.loja)
    for c in listar_comunicados(token, None, args.paginas):
        alvo = f'{c.get("title","")} {(c.get("category") or {}).get("name","")}'.lower()
        if palavra not in alvo and "manual" not in alvo:
            continue
        cont = conteudo(token, c["id"])
        for ax in (cont.get("attachment") or []):
            os.makedirs(pasta, exist_ok=True)
            dest = os.path.join(pasta, f'{c["id"]}_{nome_seguro(ax.get("name", "anexo"))}')
            if os.path.exists(dest) and os.path.getsize(dest) > 0:   # arquivo vazio = download que quebrou antes; baixa de novo
                continue
            dados = _get(ax["url"], token, binario=True)           # baixa antes de abrir, para não deixar arquivo vazio se falhar
            open(dest, "wb").write(dados)
            print(f'BAIXADO: {dest} ({ax.get("fileLength", 0)} bytes) · comunicado {c["id"]}: {c.get("title","")}')
            novos += 1
        # corpo do comunicado também vale: texto do manual pode estar no HTML
        html = cont.get("htmlText") or ""
        if html:
            corpo = os.path.join(pasta, f'{c["id"]}_corpo.html')
            if not os.path.exists(corpo):
                os.makedirs(pasta, exist_ok=True); open(corpo, "w", encoding="utf-8").write(html)
                print(f'SALVO corpo: {corpo}'); novos += 1
    print("NADA NOVO" if not novos else f"{novos} arquivo(s) novo(s)")
    sys.exit(0 if novos else 3)


if __name__ == "__main__":
    main()
