# -*- coding: utf-8 -*-
"""Sync Trinks → HubSpot (contatos).

Lê data/clientes_detalhes.json e faz batch upsert de contatos no HubSpot
usando `email` como chave natural quando disponível, ou `phone` como fallback.
Rodrigo cria uma Private App no HubSpot com escopos:
  - crm.objects.contacts.read
  - crm.objects.contacts.write
  - crm.schemas.contacts.write (pra criar custom props na primeira execução)
e cola o token como HUBSPOT_TOKEN nos Secrets do GitHub.

Sem o token roda em dry-run só imprimindo quantos entrariam.
"""
import json, os, sys, time
from datetime import datetime
from urllib import request, error, parse

TOKEN = (os.environ.get("HUBSPOT_TOKEN") or "").strip()
PORTAL_ID = os.environ.get("HUBSPOT_PORTAL_ID") or "51943728"
BASE = "https://api.hubapi.com"
CLIENTES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "clientes_detalhes.json")

CUSTOM_PROPS = [
    # nome interno, label, tipo, fieldType, groupName
    ("trinks_id", "Trinks ID", "string", "text", "contactinformation"),
    ("cpf", "CPF", "string", "text", "contactinformation"),
    ("data_cadastro_trinks", "Data cadastro Trinks", "date", "date", "contactinformation"),
    ("como_nos_conheceu", "Como nos conheceu (Trinks)", "string", "text", "contactinformation"),
]


def _req(method, path, body=None):
    """Chamada HTTP à API HubSpot. Retorna dict ou None."""
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    r = request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    })
    try:
        with request.urlopen(r, timeout=30) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except error.HTTPError as e:
        body_err = e.read().decode(errors="replace")
        print(f"  [http {e.code}] {path}: {body_err[:400]}")
        if e.code == 429:  # rate limit
            time.sleep(11)
            return _req(method, path, body)
        return None


def _ensure_custom_props():
    """Cria custom properties se não existirem. Idempotente."""
    existing = _req("GET", "/crm/v3/properties/contacts") or {}
    have = {p["name"] for p in existing.get("results", [])}
    for name, label, ptype, ftype, group in CUSTOM_PROPS:
        if name in have:
            continue
        print(f"  criando custom prop: {name}")
        _req("POST", "/crm/v3/properties/contacts", {
            "name": name, "label": label,
            "type": ptype, "fieldType": ftype,
            "groupName": group,
        })


def _normalize_phone(tel_raw):
    """Converte '11986119514' pra '+5511986119514' no padrão E.164."""
    if not tel_raw: return ""
    t = str(tel_raw).strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not t: return ""
    if t.startswith("+"): return t
    if t.startswith("55"): return "+" + t
    return "+55" + t.lstrip("0")


def _extract_contact(cid, c):
    """Converte cliente Trinks em properties HubSpot."""
    nome = (c.get("nome") or "").strip()
    if not nome: return None
    parts = nome.split()
    first = parts[0]
    last = " ".join(parts[1:]) if len(parts) > 1 else ""

    tel_list = c.get("telefone") or []
    tel = _normalize_phone(tel_list[0]) if tel_list else ""

    email = (c.get("email") or "").strip().lower() or None

    # aniversário só se válido (Trinks tem 1904 como placeholder)
    dob_ms = None
    dob_raw = c.get("dataNascimento") or ""
    if dob_raw:
        try:
            dt = datetime.fromisoformat(dob_raw.replace("Z", ""))
            if 1930 <= dt.year <= 2015:
                # HubSpot espera epoch ms à meia-noite UTC
                dob_ms = int(datetime(dt.year, dt.month, dt.day).timestamp() * 1000)
        except Exception: pass

    dcadastro_ms = None
    dcad_raw = (c.get("dataCadastro") or "").split("T")[0]
    if dcad_raw:
        try:
            dt = datetime.strptime(dcad_raw, "%Y-%m-%d")
            dcadastro_ms = int(dt.timestamp() * 1000)
        except Exception: pass

    genero_map = {"M": "Male", "F": "Female"}
    gen_raw = (c.get("genero") or c.get("sexo") or "").upper()
    gender = genero_map.get(gen_raw, "")

    fonte = ((c.get("comoNosConheceu") or {}).get("descricao") or "").strip()

    props = {
        "firstname": first,
        "lastname": last,
        "phone": tel,
        "mobilephone": tel,
        "country": "Brazil" if tel else "",
        "lifecyclestage": "customer",
        "hs_lead_status": "CONNECTED" if tel else "NEW",
        "trinks_id": str(c.get("id") or cid),
        "cpf": c.get("cpf") or "",
        "como_nos_conheceu": fonte,
    }
    if email: props["email"] = email
    if dob_ms is not None: props["date_of_birth"] = dob_ms
    if dcadastro_ms is not None: props["data_cadastro_trinks"] = dcadastro_ms
    if gender: props["gender"] = gender

    # remove chaves vazias (HubSpot aceita string vazia mas polui)
    return {k: v for k, v in props.items() if v not in ("", None)}


def _search_by_trinks_id(trinks_ids):
    """Busca no HubSpot contatos que já têm esses trinks_ids. Retorna dict
    {trinks_id: hs_contact_id}. HubSpot limita 100 valores por filtro IN."""
    encontrados = {}
    for i in range(0, len(trinks_ids), 100):
        batch = [str(t) for t in trinks_ids[i:i+100] if t]
        if not batch: continue
        body = {
            "filterGroups": [{"filters": [{
                "propertyName": "trinks_id",
                "operator": "IN",
                "values": batch,
            }]}],
            "properties": ["trinks_id"],
            "limit": 100,
        }
        r = _req("POST", "/crm/v3/objects/contacts/search", body)
        if r and "results" in r:
            for c in r["results"]:
                tid = (c.get("properties") or {}).get("trinks_id")
                if tid:
                    encontrados[str(tid)] = c["id"]
    return encontrados


def _upsert_batch(inputs):
    """Estratégia:
    1. Contatos COM email → batch upsert por email (dedup automático HubSpot)
    2. Contatos SEM email → busca existentes por trinks_id, atualiza se
       encontrado, cria se novo. Sem depender de trinks_id ser unique.
    """
    com_email = [i for i in inputs if i.get("email")]
    sem_email = [i for i in inputs if not i.get("email")]

    ok_upsert_email = 0
    if com_email:
        body = {"inputs": [{"idProperty": "email", "id": i["email"], "properties": i} for i in com_email]}
        r = _req("POST", "/crm/v3/objects/contacts/batch/upsert", body)
        if r and "results" in r:
            ok_upsert_email = len(r["results"])

    ok_update, ok_create = 0, 0
    if sem_email:
        trinks_ids = [str(i.get("trinks_id")) for i in sem_email if i.get("trinks_id")]
        existentes = _search_by_trinks_id(trinks_ids)  # {trinks_id: hs_id}

        para_atualizar, para_criar = [], []
        for c in sem_email:
            tid = str(c.get("trinks_id") or "")
            if tid and tid in existentes:
                para_atualizar.append({"id": existentes[tid], "properties": c})
            else:
                para_criar.append({"properties": c})

        if para_atualizar:
            body = {"inputs": para_atualizar}
            r = _req("POST", "/crm/v3/objects/contacts/batch/update", body)
            if r and "results" in r:
                ok_update = len(r["results"])

        if para_criar:
            body = {"inputs": para_criar}
            r = _req("POST", "/crm/v3/objects/contacts/batch/create", body)
            if r and "results" in r:
                ok_create = len(r["results"])

    return ok_upsert_email, ok_update, ok_create


def main():
    if not TOKEN:
        print("⚠ HUBSPOT_TOKEN não configurado — rodando em dry-run")

    with open(CLIENTES, encoding="utf-8") as f:
        raw = json.load(f)

    contacts = []
    for cid, c in raw.items():
        if cid == "gerado_em" or not isinstance(c, dict): continue
        p = _extract_contact(cid, c)
        if p: contacts.append(p)

    print(f"[hubspot] {len(contacts)} contatos preparados de {CLIENTES}")

    if not TOKEN:
        print("[dry-run] Amostra do primeiro:")
        print(json.dumps(contacts[0], indent=2, ensure_ascii=False))
        return

    print("[hubspot] garantindo custom properties...")
    _ensure_custom_props()

    print(f"[hubspot] enviando em batches de 100...")
    total_email, total_upd, total_new = 0, 0, 0
    for i in range(0, len(contacts), 100):
        batch = contacts[i:i+100]
        em, up, cr = _upsert_batch(batch)
        total_email += em
        total_upd += up
        total_new += cr
        print(f"  batch {i//100 + 1}: upsert_email={em} update={up} create={cr}")
        time.sleep(0.5)  # respeita rate limit HubSpot (100 req/10s)

    print(f"\n✓ {total_email + total_upd + total_new} contatos sincronizados "
          f"(upsert por email={total_email}, atualizados por trinks_id={total_upd}, "
          f"novos criados={total_new})")


if __name__ == "__main__":
    main()
