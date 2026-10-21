#!/usr/bin/env python3
"""Sonda de leitura da API do SULTS — descobre o que esta credencial alcança.

Por que existe: o Rodrigo disse "já tenho os tokens cadastrados" e nem a sessão
da nuvem nem a do PC conseguem conferir isso. Secret do GitHub não se lê, só se
usa; e `api.sults.com.br` não resolve do contêiner da nuvem. A única verificação
honesta é uma chamada de verdade, de dentro do Actions.

Esta sonda NÃO escreve nada no SULTS e NÃO grava nada no repositório. Só faz GET
e descreve o que voltou.

REGRA DE LOG — o log do Actions fica guardado no GitHub, público para quem tem
acesso ao repo. Então esta sonda imprime:

  - o NOME do secret que carregou (nunca o valor, nunca um pedaço dele)
  - código HTTP, contagem de registros e os NOMES dos campos que voltaram
  - NUNCA o conteúdo de um registro: chamado, checklist e empresa carregam nome
    de pessoa, e-mail, CNPJ e texto livre

Mesma regra dos scripts de diagnóstico por cliente, que não imprimem CPF nem
telefone completo pelo mesmo motivo.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

# O Rodrigo não disse com que nome cadastrou. Em vez de perguntar e esperar,
# a sonda procura os nomes plausíveis e diz qual achou.
NOMES_TOKEN = [
    "SULTS_API_TOKEN", "SULTS_TOKEN", "SULTS_API_KEY", "SULTS_KEY",
    "SULTS_AUTH_TOKEN", "SULTS_BEARER", "SULTS_ACCESS_TOKEN", "SULTS",
]

# A documentação pública aparece com as duas bases. Em vez de escolher uma e
# errar, a sonda testa as duas e diz qual responde.
BASES = ["https://api.sults.com.br/api/v1", "https://api.sults.com.br/v1"]

# Só leitura. Um endpoint por módulo que o portal de developers descreve.
ALVOS = [
    ("empresas",             "unidades da rede"),
    ("checklist/avaliacao",  "avaliações de checklist"),
    ("chamado",              "chamados (helpdesk com SLA)"),
    ("chamados",             "chamados (plural, caso o anterior 404)"),
]

TIMEOUT = 25


def achar_token() -> tuple[str | None, str | None]:
    for nome in NOMES_TOKEN:
        v = (os.environ.get(nome) or "").strip()
        if v:
            return nome, v
    return None, None


def get(url: str, token: str, esquema: str) -> tuple[int, dict | list | str]:
    """Um GET. Devolve (status, corpo). Nunca levanta por status."""
    cab = {
        "Authorization": f"Bearer {token}" if esquema == "bearer" else token,
        "Accept": "application/json",
        "User-Agent": "fast-dashboard-limao/sults-probe",
    }
    req = urllib.request.Request(url, headers=cab, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            bruto = r.read().decode("utf-8", "replace")
            try:
                return r.status, json.loads(bruto)
            except ValueError:
                return r.status, bruto[:200]
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8", "replace")[:200] if e.fp else ""
        return e.code, corpo
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        return 0, f"{type(e).__name__}: {e}"


def descrever(corpo) -> str:
    """Conta registros e nomeia campos — nunca mostra conteúdo."""
    if isinstance(corpo, str):
        return f"resposta não-JSON: {corpo[:120]!r}"
    if isinstance(corpo, list):
        itens = corpo
        envelope = "lista na raiz"
    elif isinstance(corpo, dict):
        chave = next((k for k in ("data", "content", "items", "result", "results",
                                  "registros", "list") if isinstance(corpo.get(k), list)), None)
        if chave:
            itens, envelope = corpo[chave], f"envelope dict, lista em '{chave}'"
            extras = [k for k in corpo if k != chave]
            if extras:
                envelope += f" · metadados: {sorted(extras)}"
        else:
            return f"dict sem lista · chaves: {sorted(corpo)[:14]}"
    else:
        return f"tipo inesperado: {type(corpo).__name__}"

    campos = sorted({k for it in itens[:5] if isinstance(it, dict) for k in it})
    return f"{envelope} · {len(itens)} registro(s) · campos: {campos[:22]}"


def main() -> int:
    print("=" * 72)
    print("SONDA SULTS · só leitura · nenhum valor de token é impresso")
    print("=" * 72)

    nome, token = achar_token()
    if not token:
        print("\n🛑 NENHUM TOKEN NO AMBIENTE.")
        print("   Procurei por: " + ", ".join(NOMES_TOKEN))
        print("\n   Se o secret existe com OUTRO nome, ele não chega aqui: o")
        print("   workflow precisa repassar cada secret explicitamente. Me diga")
        print("   o nome que você usou e eu acrescento — ou renomeie para")
        print("   SULTS_API_TOKEN, que é o nome que o cano vai usar.")
        return 2

    print(f"\n✅ Token carregado do secret `{nome}` · {len(token)} caracteres")
    print("   (o valor não é impresso em nenhuma circunstância)")

    combinacoes = [(b, e) for b in BASES for e in ("bearer", "cru")]
    vencedora = None

    print("\n--- Passo 1: qual base e qual esquema de Authorization respondem? ---")
    for base, esq in combinacoes:
        st, corpo = get(f"{base}/empresas?start=0&limit=1", token, esq)
        rot = "Bearer <token>" if esq == "bearer" else "<token> cru"
        marca = "✅" if st == 200 else ("🔑" if st in (401, 403) else "·")
        print(f"  {marca} HTTP {st or 'sem resposta'} · {base}/empresas · {rot}")
        if st != 200 and corpo:
            print(f"       {str(corpo)[:140]}")
        if st == 200 and vencedora is None:
            vencedora = (base, esq)

    if not vencedora:
        print("\n🛑 Nenhuma combinação devolveu 200.")
        print("   401/403 = token chegou e foi recusado (vencido, escopo, ou revogado).")
        print("   404     = base errada.")
        print("   0       = rede/DNS bloqueados até do Actions.")
        return 3

    base, esq = vencedora
    print(f"\n✅ Funciona: base `{base}` · Authorization `{esq}`")

    print("\n--- Passo 2: que módulos esta credencial alcança? ---")
    alcanca = []
    for caminho, rotulo in ALVOS:
        st, corpo = get(f"{base}/{caminho}?start=0&limit=5", token, esq)
        if st == 200:
            alcanca.append(caminho)
            print(f"  ✅ {caminho:22s} {rotulo}")
            print(f"       {descrever(corpo)}")
        else:
            print(f"  ❌ {caminho:22s} HTTP {st or 'sem resposta'} · {str(corpo)[:100]}")

    print("\n" + "=" * 72)
    print(f"RESUMO · secret `{nome}` · base `{base}` · auth `{esq}`")
    print(f"         {len(alcanca)} de {len(ALVOS)} endpoint(s) alcançados: {alcanca or '—'}")
    print("=" * 72)
    return 0 if alcanca else 4


if __name__ == "__main__":
    sys.exit(main())
