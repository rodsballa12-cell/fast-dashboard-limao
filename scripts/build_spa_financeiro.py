"""Zero-state do Spa ENQUANTO a loja não abre — estrutura
igual à Escova mas com todos os valores em 0 e flag _pre_abertura.

Executado quando o Excel real ainda não tem dados SPA preenchidos.
Assim que Rodrigo preencher o bloco DRE FAST SPA no Painel, rodar
scripts/gerar_financeiro.py sobrescreve este arquivo com o real.

Preserva:
- estrutura completa (meses, grupos, kpis)
- meta franqueadora mensal (60k)
- arrays estruturais

Zera:
- todos os numéricos
- provisões
"""
import json, os, copy
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "data", "config.json")
SRC = os.path.join(ROOT, "data", "financeiro.json")  # Escova como template
DST_DIR = os.path.join(ROOT, "data", "spa")
DST = os.path.join(DST_DIR, "financeiro.json")
CONS_DIR = os.path.join(ROOT, "data", "consolidado")
DST_CONS = os.path.join(CONS_DIR, "financeiro.json")
BRT = timezone(timedelta(hours=-3))

def _meta_mensal(unidade: str, padrao: float, ym: str = None) -> float:
    """Meta mensal vem do config.json — fonte única.

    Até 14/09/2026 este número estava fixo em DOIS scripts
    (gerar_financeiro.py e build_spa_financeiro.py), os dois com 60000. O SPA
    herdou a meta da Escova e ninguém zerou; a auditoria de coerência pegou
    quando o payload do SPA aparecia marcado _pre_abertura com meta cheia.
    Duas fontes da verdade sempre divergem — agora é uma.

    Mês a mês (30/09/2026): `meta_mensal_por_mes[YYYY-MM]` vence sobre
    `meta_mensal`. Sem isso o financeiro do Spa lia a provisória de R$ 50.000
    enquanto o painel de operação já lia R$ 20.000 (set) / R$ 25.000 (out), e o
    consolidado mostrava meta de R$ 110.000.
    """
    try:
        with open(os.path.join(ROOT, "data", "config.json"), encoding="utf-8") as fh:
            u = json.load(fh)["unidades"][unidade]
        ym = ym or datetime.now(timezone(timedelta(hours=-3))).strftime("%Y-%m")
        v = (u.get("meta_mensal_por_mes") or {}).get(ym)
        if not isinstance(v, (int, float)):
            v = u.get("meta_mensal")
        return float(v) if v is not None else padrao
    except Exception:
        return padrao

META_MES_SPA = _meta_mensal("spa", 20000.00)

PRESERVAR = {
    "gerado_em", "baseline", "custos_ate", "mes_corrente_chave",
    "mes_principal_chave", "mes_fechado_chave", "loja", "chave",
    "ano", "mes", "id", "titulo", "cat", "nota",
}


def zero_state(obj):
    if obj is None or isinstance(obj, bool): return obj
    if isinstance(obj, (int, float)): return type(obj)(0)
    if isinstance(obj, str): return obj
    if isinstance(obj, list): return [zero_state(x) for x in obj]
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in PRESERVAR:
                out[k] = copy.deepcopy(v)
            else:
                out[k] = zero_state(v)
        return out
    return copy.deepcopy(obj)


def main():
    if not os.path.exists(SRC):
        raise SystemExit(f"Escova financeiro não existe em {SRC}")
    with open(CONFIG, encoding="utf-8") as f: cfg = json.load(f)
    spa_cfg = cfg["unidades"]["spa"]

    # A loja abriu: o zero-state sai de cena e quem manda é o gerar_financeiro.py,
    # que lê o bloco DRE FAST SPA do painel. Sem esta guarda o script zerava a
    # unidade para sempre — em 30/09/2026 o Spa estava aberto desde 25/09 e
    # faturando R$ 9.819,47, e a aba financeira dele mostrava zero.
    abertura = (spa_cfg.get("data_inauguracao") or "")[:10]
    hoje = datetime.now(BRT).strftime("%Y-%m-%d")
    if abertura and hoje >= abertura:
        print(f"[build_spa_financeiro] Spa aberto desde {abertura} — nada a zerar; "
              f"o financeiro do Spa e o consolidado vêm de gerar_financeiro.py (painel).")
        return

    with open(SRC, encoding="utf-8") as f: escova = json.load(f)

    payload = zero_state(escova)

    now = datetime.now(BRT).isoformat(timespec="seconds")
    payload["gerado_em"] = now
    payload["loja"] = "FAST SPA LIMÃO"
    payload["_pre_abertura"] = True
    payload["_data_inauguracao"] = spa_cfg["data_inauguracao"]
    payload["_fonte_receita"] = (
        "Zero-state pré-abertura · projeções SPA no Excel ainda pendentes. "
        "Rodar scripts/gerar_financeiro.py quando bloco DRE FAST SPA estiver preenchido."
    )
    payload["_estado"] = "zero-state · SPA em pré-abertura · Excel SPA pendente"

    # Meta franqueadora preservada em todos os meses
    for k, m in (payload.get("meses") or {}).items():
        m["receita_meta"] = _meta_mensal("spa", META_MES_SPA, k[:7])  # set 20k · out 25k · nov 40k · dez 50k
    payload["kpis"]["meta_mes"] = META_MES_SPA
    payload["resultado"]["receita_meta"] = META_MES_SPA

    # Premissas herdadas (12% CMV, 7% Simples) — quando SPA rodar podem mudar. Sem inadimplência (Rodrigo, 16/09)
    payload["premissas"] = {
        "comissao": None,  # até termos categoria_native SPA real
        "insumos": 0.12,
        "simples": 0.07,
        "inadimplencia": 0.0,
    }

    os.makedirs(DST_DIR, exist_ok=True)
    with open(DST, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print(f"[build_spa_financeiro] gerado {DST}")
    print(f"  estado: zero-state (loja abre {spa_cfg['data_inauguracao']})")
    print(f"  meses: {len(payload.get('meses') or {})} · meta_mes: {META_MES_SPA}")

    # Consolidado enquanto SPA=0 é literalmente Escova. Gera cópia
    # de data/financeiro.json com loja="FAST LIMÃO CONSOLIDADO" pra
    # não cair no scaffolding banner (dado existe, é só um lado zerado).
    escova_cons = copy.deepcopy(escova)
    escova_cons["loja"] = "FAST LIMÃO CONSOLIDADO"
    escova_cons["_consolidado"] = True
    escova_cons["_composicao"] = (
        "Realizado: somente Fast Escova (SPA em pré-abertura · zero). "
        "Meta: soma das duas unidades — meta existe antes de a loja abrir."
    )
    # A META soma desde já, mesmo com o SPA zerado no realizado.
    # Corrigido em 14/09/2026: o consolidado copiava a meta da Escova e
    # ignorava a do SPA. Enquanto as duas eram 60000 o erro ficava invisível;
    # com metas diferentes (60000 e 15000) a holding apareceria com 60000 de
    # meta quando o alvo real é 75000 — e passaria a "bater meta" sem bater.
    escova_cons["kpis"]["meta_mes"] = round(
        float(escova["kpis"].get("meta_mes") or 0.0) + META_MES_SPA, 2)
    os.makedirs(CONS_DIR, exist_ok=True)
    with open(DST_CONS, "w", encoding="utf-8") as f:
        json.dump(escova_cons, f, ensure_ascii=False, indent=1)
    print(f"[build_spa_financeiro] gerado {DST_CONS}")
    print(f"  composição: Escova sozinho (SPA zero)")


if __name__ == "__main__":
    main()
