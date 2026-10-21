#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Leitura diária do SULTS (franqueadora) para os agentes, SÓ das lojas Limão.

O que traz, por loja (Escova e Spa):
  · chamados abertos, com a última fala e de quem é a vez de responder;
  · pedidos de compra (últimos 120 dias + todos ainda abertos), com itens;
  · comunicados recentes e quais ninguém da loja abriu ainda;
  · checklists e planos de ação da franqueadora sobre a loja.

Regras (decisão do Rodrigo em 21/10/2026):
  · SÓ GET. Nada é criado, respondido, editado ou concluído no SULTS.
  · O token enxerga a REDE INTEIRA (centenas de unidades). Tudo que dá para
    pedir já filtrado pela empresa vai com companyId; o que não dá (checklists)
    é filtrado em memória e o resto da rede é descartado — nada de outra
    unidade é gravado.
  · O resultado NÃO vai para o repositório (é público): grava em
    OneDrive\\Franquia - FAST\\Claude\\SULTS\\sults_limao.json.
  · Os tokens ficam nas variáveis de ambiente do Windows SULTS_TOKEN_V2
    (Escova) e SULTS_TOKEN_V2_SPA (Spa), nunca impressos.

Uso:
  python scripts/sults_leitura.py                 # lê e grava
  python scripts/sults_leitura.py --se-velho 180  # só lê se o arquivo tiver mais de 180 min
Código de saída: 0 ok · 3 pulado (arquivo recente) · 2 erro/sem token.
"""
import argparse, datetime, html, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

API = "https://api.sults.com.br"
SAIDA = os.environ.get("SULTS_SAIDA", r"C:\Users\rods_\OneDrive\Franquia - FAST\Claude\SULTS\sults_limao.json")
# código da empresa Limão dentro de cada SULTS (achado na varredura de 21/10/2026)
LOJAS = {
    "escova": {"token": "SULTS_TOKEN_V2", "empresa": 683},
    "spa":    {"token": "SULTS_TOKEN_V2_SPA", "empresa": 95},
}
DIAS_PEDIDOS = 120
FECHADOS = {"RESOLVED", "CLOSED", "CONCLUDED", "CANCELED", "CANCELLED"}


def token(var):
    t = os.environ.get(var, "").strip()
    if not t and os.name == "nt":
        # o app do Claude e o terminal só enxergam variável criada depois que abriram
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                t = str(winreg.QueryValueEx(k, var)[0]).strip()
        except OSError:
            pass
    return t


def get(tok, path, params=None):
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    time.sleep(0.6)  # limite da API: 2 requisições por segundo
    req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json", "Authorization": tok})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8") or "null")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"SULTS respondeu {e.code} em {path}")


def lista(tok, path, params=None, max_pag=30):
    tudo = []
    for pg in range(max_pag):
        d = get(tok, path, dict(params or {}, page=pg))
        if not isinstance(d, list) or not d:
            break
        tudo += d
        if len(d) < 10:
            break
    return tudo


def texto(comentario, limite=400):
    m = comentario.get("messageHtml", "") if isinstance(comentario, dict) else (comentario or "")
    t = re.sub(r"<[^>]+>", " ", html.unescape(m)).replace("\xa0", " ")
    return re.sub(r"\s+", " ", t).strip()[:limite]


def ler_loja(tok, empresa, anterior):
    hoje = datetime.datetime.now(datetime.timezone.utc)

    # --- chamados (já filtrados pela empresa no servidor) ---
    chamados = lista(tok, "/api/v2/chamados/ticket/list", {"companyId": empresa})
    # quem fala pela loja: quem abriu chamado da loja para a franqueadora
    nossos = {c["requesterUser"]["id"] for c in chamados if c.get("direction") == "COMPANY_TO_ADMIN" and c.get("requesterUser")}
    out_ch = []
    for c in sorted(chamados, key=lambda x: x.get("lastUpdatedAt") or "", reverse=True):
        aberto = c.get("status") not in FECHADOS
        item = {
            "id": c["id"], "assunto": (c.get("subject") or "").strip(), "status": c.get("status"),
            "sentido": "loja_pediu" if c.get("direction") == "COMPANY_TO_ADMIN" else "franqueadora_pediu",
            "departamento": (c.get("inboundDepartment") or c.get("outboundDepartment") or {}).get("name"),
            "aberto_em": c.get("openedAt"), "prazo": c.get("dueDate"), "ultima_mudanca": c.get("lastUpdatedAt"),
            "aberto": aberto,
        }
        if aberto:
            falas = [e for e in lista(tok, "/api/v2/chamados/ticket/timeline-event/list", {"ticketId": c["id"]}, 10)
                     if e.get("type", "").startswith("COMMENT")]
            if falas:
                u = falas[-1]
                quem = (u.get("user") or {})
                item["ultima_fala"] = {"em": u.get("createdAt"), "quem": quem.get("name"),
                                       "lado": "loja" if quem.get("id") in nossos else "franqueadora",
                                       "texto": texto(u.get("comment"))}
                # a vez é da loja quando a franqueadora falou por último, ou quando ela marcou "aguardando solicitante"
                item["vez_da_loja"] = item["ultima_fala"]["lado"] == "franqueadora" or c.get("status") == "AWAITING_REQUESTER"
                d = item["ultima_fala"]["em"]
                if d:
                    item["dias_sem_resposta"] = (hoje - datetime.datetime.fromisoformat(d.replace("Z", "+00:00"))).days
                # chamado parado há mais de 30 dias costuma ser assunto morto que ninguém fechou; não é alarme
                item["urgente"] = item["vez_da_loja"] and item.get("dias_sem_resposta", 999) <= 30
        out_ch.append(item)

    # --- pedidos de compra ---
    corte = (hoje - datetime.timedelta(days=DIAS_PEDIDOS)).isoformat()
    pedidos = [p for p in lista(tok, "/api/v2/compras/order/list", {"companyId": empresa})
               if p.get("createdAt", "") >= corte or p.get("status") == "OPEN"]
    out_ped = []
    for p in sorted(pedidos, key=lambda x: x["createdAt"], reverse=True):
        itens = lista(tok, "/api/v2/compras/order/product/list", {"orderId": p["id"]}, 3)
        out_ped.append({
            "id": p["id"], "criado_em": p["createdAt"], "concluido_em": p.get("concludedAt"),
            "valor": float(p.get("amount") or 0), "desconto": float(p.get("productDiscount") or 0),
            "etapa": (p.get("stage") or {}).get("name"), "status": p.get("status"), "cancelado": bool(p.get("canceled")),
            "fornecedor": (p.get("supplier") or {}).get("name", "").strip(),
            "pagamento": (p.get("paymentMethod") or {}).get("name", "").strip(),
            "itens": [{"produto": (i.get("product") or {}).get("name", "").strip(), "qtd": i.get("quantity"),
                       "preco": i.get("price"), "preco_tabela": i.get("regularPrice")} for i in itens],
        })
    por_mes, por_forn = {}, {}
    for p in out_ped:
        if p["cancelado"]:
            continue
        m = p["criado_em"][:7]
        por_mes[m] = round(por_mes.get(m, 0) + p["valor"], 2)
        por_forn[p["fornecedor"]] = round(por_forn.get(p["fornecedor"], 0) + p["valor"], 2)

    # --- comunicados (são da rede toda por natureza; leitura só das pessoas da loja) ---
    comunicados = lista(tok, "/api/v2/comunicado/announcement/list", {"active": "true"}, 2)
    vistos_antes = set((anterior or {}).get("comunicados_ids", []))
    out_com = []
    for a in sorted(comunicados, key=lambda x: x.get("createdAt") or "", reverse=True)[:15]:
        leitura = []
        for u in nossos:
            leitura += lista(tok, "/api/v2/comunicado/announcement/user/list", {"announcementId": a["id"], "userId": u}, 1)
        out_com.append({
            "id": a["id"], "titulo": (a.get("title") or "").strip(), "criado_em": a.get("createdAt"),
            # na primeira leitura nada é "novo": senão os agentes anunciariam 15 comunicados antigos de uma vez
            "categoria": (a.get("category") or {}).get("name"), "novo": bool(vistos_antes) and a["id"] not in vistos_antes,
            "ninguem_da_loja_abriu": bool(leitura) and not any(x.get("viewed") for x in leitura),
            "nao_abriram": [((x.get("user") or {}).get("name") or "").strip() for x in leitura if not x.get("viewed")],
        })

    # --- checklists: a API não filtra por empresa, então filtra aqui e descarta o resto da rede ---
    avs = [a for a in lista(tok, "/api/v2/checklist/assessment/list", None, 50)
           if (a.get("company") or {}).get("id") == empresa]
    planos = [x for x in lista(tok, "/api/v2/checklist/action-plan/list", None, 50)
              if (((x.get("assessment") or {}).get("company")) or {}).get("id") == empresa]
    out_ck = [{"id": a["id"], "modelo": (a.get("template") or {}).get("name"), "status": a.get("status"),
               "agendado_para": a.get("scheduledDate"), "iniciado_em": a.get("startedAt"), "fechado_em": a.get("closedAt"),
               "nota": a.get("score"), "nota_max": a.get("maxScore")} for a in avs]
    out_pl = [{"id": x["id"], "status": x.get("status"), "o_que": x.get("what"), "prazo": x.get("whenDeadlineDate"),
               "pergunta": ((x.get("assessmentAnswer") or {}).get("question") or {}).get("title")} for x in planos]

    return {
        "chamados": out_ch,
        "chamados_vez_da_loja": [c["id"] for c in out_ch if c.get("vez_da_loja")],
        "chamados_urgentes": [c["id"] for c in out_ch if c.get("urgente")],
        "pedidos": out_ped,
        "pedidos_por_mes": por_mes, "pedidos_por_fornecedor": por_forn,
        "pedidos_abertos_valor": round(sum(p["valor"] for p in out_ped if p["status"] == "OPEN" and not p["cancelado"]), 2),
        "comunicados": out_com,
        "comunicados_ids": sorted({a["id"] for a in comunicados} | vistos_antes),
        "checklists": out_ck, "planos_de_acao": out_pl,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--se-velho", type=int, default=0, help="minutos; pula se o arquivo for mais novo que isso")
    args = ap.parse_args()

    anterior = {}
    if os.path.exists(SAIDA):
        idade = (time.time() - os.path.getmtime(SAIDA)) / 60
        if args.se_velho and idade < args.se_velho:
            print(f"SULTS: leitura de {int(idade)} min atrás ainda vale, pulei.")
            sys.exit(3)
        try:
            anterior = json.load(open(SAIDA, encoding="utf-8"))
        except Exception:
            anterior = {}

    res = {"gerado_em": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "fonte": "SULTS API v2 (só leitura), filtrado para as lojas Limão", "lojas": {}}
    resumo, erro = [], False
    for loja, cfg in LOJAS.items():
        tok = token(cfg["token"])
        if not tok:
            res["lojas"][loja] = {"erro": f"sem token ({cfg['token']})"}
            resumo.append(f"{loja}: SEM TOKEN"); erro = True
            continue
        try:
            r = ler_loja(tok, cfg["empresa"], (anterior.get("lojas") or {}).get(loja))
            res["lojas"][loja] = r
            novos = sum(1 for c in r["comunicados"] if c["novo"])
            resumo.append(f"{loja}: {len(r['chamados_urgentes'])} chamado(s) esperando a loja há até 30 dias, "
                          f"{len(r['pedidos'])} pedido(s), {novos} comunicado(s) novo(s)")
        except Exception as e:
            res["lojas"][loja] = (anterior.get("lojas") or {}).get(loja) or {}
            res["lojas"][loja]["erro"] = str(e)[:200]
            resumo.append(f"{loja}: FALHOU ({str(e)[:80]})"); erro = True

    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    tmp = SAIDA + ".tmp"
    json.dump(res, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, SAIDA)
    print("SULTS: " + " | ".join(resumo))
    sys.exit(2 if erro else 0)


if __name__ == "__main__":
    main()
