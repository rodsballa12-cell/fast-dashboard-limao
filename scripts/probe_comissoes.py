# -*- coding: utf-8 -*-
"""Probe v3: reprocessa endpoints comissão com sleep pra evitar 429 do run anterior."""
import json, os, sys, time, traceback
import requests

API_KEY = os.getenv("TRINKS_API_KEY", "").strip()
EID = os.getenv("TRINKS_ESTABELECIMENTO_ID", "").strip()
BASE = "https://api.trinks.com"
HEADERS = {
    "X-Api-Key": API_KEY,
    "estabelecimentoId": EID,
    "Content-Type": "application/json",
    "Accept": "application/json",
}
SLEEP = 1.2  # ~50 req/min


def hit(path, params=None, method="GET"):
    print(f"\n[{method}] {path} params={params or {}}")
    time.sleep(SLEEP)
    try:
        if method == "GET":
            r = requests.get(BASE + path, headers=HEADERS, params=params or {}, timeout=15)
        else:
            r = requests.post(BASE + path, headers=HEADERS, json=params or {}, timeout=15)
        print(f"  status={r.status_code}")
        try:
            body = r.json()
        except Exception:
            body = r.text[:400]
        if isinstance(body, dict):
            keys = list(body.keys())
            data = body.get("data")
            tr = body.get("totalRecords", body.get("total", "?"))
            print(f"  keys={keys[:15]} totalRecords={tr}")
            if isinstance(data, list) and data:
                print(f"  data[{len(data)}] amostra[0]:")
                print("  ", json.dumps(data[0], ensure_ascii=False, indent=2)[:1200])
            elif isinstance(data, list):
                print(f"  data=[] (vazio)")
            elif data is None and body.get("message"):
                print(f"  message: {body.get('message')}")
            else:
                print(f"  body:", json.dumps(body, ensure_ascii=False)[:500])
        elif isinstance(body, list):
            print(f"  list[{len(body)}]")
            if body:
                print("  ", json.dumps(body[0], ensure_ascii=False)[:600])
        else:
            print(f"  raw: {str(body)[:400]}")
        return r.status_code, body
    except Exception as e:
        print(f"  ERR {type(e).__name__}: {str(e)[:200]}")
        return None, None


def main():
    print(f"Estabelecimento: {EID[:6]}...")
    print("Sleep entre calls: %.1fs (~%d req/min)\n" % (SLEEP, 60/SLEEP))

    # IDs de amostra do probe anterior
    SID = 15450779
    PID = 930860

    # Bloco A — /profissionais/comissoes com filtros
    hit("/v1/profissionais/comissoes")
    hit("/v1/profissionais/comissoes", {"profissionalId": PID})
    hit("/v1/profissionais/comissoes", {"idProfissional": PID})
    hit("/v1/profissionais/comissoes", {"servicoId": SID})
    hit("/v1/profissionais/comissoes", {"pageSize": 500})

    # Bloco B — variações de rota (aguardado o cooldown do run 3)
    hit("/v1/comissoes")
    hit("/v1/comissoes", {"profissionalId": PID})
    hit("/v1/comissoes/regras")
    hit("/v1/regras-comissao")
    hit("/v1/servicos-profissionais")
    hit("/v1/servicos-profissionais", {"pageSize": 200})
    hit("/v1/profissionais-servicos")

    # Bloco C — recurso relação n:n (candidato principal)
    hit(f"/v1/servicos/{SID}/profissionais/{PID}")
    hit(f"/v1/profissionais/{PID}/servicos/{SID}")

    # Bloco D — variantes com include
    hit(f"/v1/servicos/{SID}", {"include": "comissoes"})
    hit(f"/v1/servicos/{SID}", {"include": "profissionais.comissao"})
    hit(f"/v1/profissionais/{PID}", {"include": "comissoes"})
    hit(f"/v1/profissionais/{PID}", {"include": "servicos.comissao"})

    # Bloco E — backoffice / configuracoes / cadastros
    hit("/v1/backoffice/comissoes")
    hit("/v1/cadastros/comissoes")
    hit("/v1/configuracoes/comissoes")

    # Bloco F — endpoints internos do backoffice (long shot)
    hit("/backoffice/api/comissoes")
    hit("/api/backoffice/comissoes")
    hit("/backoffice/comissoes")

    print("\n" + "=" * 70)
    print("FIM DO PROBE V3.")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
