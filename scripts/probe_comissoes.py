# -*- coding: utf-8 -*-
"""Probe: descobre qual endpoint Trinks retorna as comissões por serviço/profissional.

Rodrigo confirmou que /BackOffice/ManterCadastro/Servicos na UI mostra comissão
por profissional × serviço. O endpoint /v1/profissionais/comissoes retorna 0.
Testa 8 alternativas e loga qual devolve o dado.

Roda via workflow probe_comissoes.yml. Não modifica nenhum JSON — só imprime.
"""
import json, os, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trinks_common import TrinksClient  # já autentica com secrets


def dump(label, resp, limit=3):
    print(f"\n===== {label} =====")
    if resp is None:
        print("  (None)")
        return
    if isinstance(resp, dict):
        keys = list(resp.keys())
        print(f"  dict keys: {keys[:20]}")
        # Se tem items/data/etc, dumpa amostra
        for k in ("items", "data", "results", "servicos", "profissionais"):
            v = resp.get(k)
            if isinstance(v, list) and v:
                print(f"  {k}: {len(v)} items · sample:")
                print("  ", json.dumps(v[0], ensure_ascii=False, indent=2)[:1500])
                return
        print(f"  content: {json.dumps(resp, ensure_ascii=False, indent=2)[:1500]}")
    elif isinstance(resp, list):
        print(f"  list: {len(resp)} items")
        for i in range(min(limit, len(resp))):
            print(f"  [{i}]:", json.dumps(resp[i], ensure_ascii=False, indent=2)[:800])
    else:
        print(f"  raw: {str(resp)[:800]}")


def try_endpoint(t, path, params=None):
    print(f"\n[try] GET {path} params={params}")
    try:
        r = t.get(path, params or {})
        return r
    except Exception as e:
        print(f"  ERRO: {type(e).__name__}: {str(e)[:200]}")
        return None


def main():
    t = TrinksClient()
    print("=" * 70)
    print("PROBE: descobrindo endpoint de comissões Trinks")
    print("=" * 70)

    # 1) Baseline — endpoint atual do refresh
    r1 = try_endpoint(t, "/v1/profissionais/comissoes", {"pageSize": 200})
    dump("1. /v1/profissionais/comissoes", r1)

    # 2) Serviços — checar se tem campo comissão que passamos batido
    r2 = try_endpoint(t, "/v1/servicos", {"pageSize": 5})
    dump("2. /v1/servicos (busca campo comissão)", r2)
    if isinstance(r2, dict) and "items" in r2 and r2["items"]:
        print("  CAMPOS do primeiro serviço:", list(r2["items"][0].keys()))
    elif isinstance(r2, list) and r2:
        print("  CAMPOS do primeiro serviço:", list(r2[0].keys()))

    # 3) Serviço específico + profissionais (endpoint aninhado)
    #    Trinks às vezes expõe /servicos/{id}/profissionais com comissão
    servs = r2.get("items") if isinstance(r2, dict) else r2 if isinstance(r2, list) else []
    if servs:
        sid = servs[0].get("id")
        r3 = try_endpoint(t, f"/v1/servicos/{sid}/profissionais")
        dump(f"3. /v1/servicos/{sid}/profissionais", r3)

    # 4) Profissional + serviços (variante inversa)
    r4a = try_endpoint(t, "/v1/profissionais", {"pageSize": 5})
    profs = r4a.get("items") if isinstance(r4a, dict) else r4a if isinstance(r4a, list) else []
    if profs:
        pid = profs[0].get("id")
        r4 = try_endpoint(t, f"/v1/profissionais/{pid}/servicos")
        dump(f"4. /v1/profissionais/{pid}/servicos", r4)

    # 5) Endpoint direto do BackOffice (pode ser exposto no v1)
    r5 = try_endpoint(t, "/v1/servicos/comissoes")
    dump("5. /v1/servicos/comissoes", r5)

    # 6) Endpoint que agrupa
    r6 = try_endpoint(t, "/v1/comissoes")
    dump("6. /v1/comissoes", r6)

    # 7) Serviço específico com include
    if servs:
        sid = servs[0].get("id")
        r7 = try_endpoint(t, f"/v1/servicos/{sid}", {"include": "profissionais,comissoes"})
        dump(f"7. /v1/servicos/{sid}?include=...", r7)

    # 8) Profissional específico com include
    if profs:
        pid = profs[0].get("id")
        r8 = try_endpoint(t, f"/v1/profissionais/{pid}", {"include": "comissoes,servicos"})
        dump(f"8. /v1/profissionais/{pid}?include=...", r8)

    print("\n" + "=" * 70)
    print("Probe concluído. Envie o output completo pra análise.")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
