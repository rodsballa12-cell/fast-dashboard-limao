"""Mock temporário do payload SPA: clona Escova com valores escalados por FACTOR,
apenas pra visualização do consolidado antes de a SPA ter estabelecimentoId Trinks.
Quando SPA abrir de verdade, este script deixa de rodar e o refresh backend
gera data/spa/dashboard_data.json com dados reais."""

import json, os, sys, copy
from datetime import datetime, timezone, timedelta

FACTOR = 0.42  # SPA sendo unidade menor/nova: ~42% do volume da Escova
KEEP_TOP_N = 3  # top-N de cada ranking mantém o nome original → cross-unit "ambas"
SUFFIX_SPA = " (SPA)"  # sufixo pra criar nomes SPA-exclusivos no mock
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Chaves cujos valores NÃO devem ser escalados (ids, datas, strings, flags, etc.)
KEEP = {
    "gerado_em", "ano", "mes", "semana", "dia", "dia_semana",
    "periodo_ini", "periodo_fim", "periodo_ini_ref", "periodo_fim_ref",
    "estabelecimento_id", "id", "cnpj", "razao_social", "nome",
    "cor", "tipo", "categoria", "descricao", "status", "url",
    "data", "dataHora", "dataHoraInicio", "dataHoraFim", "hora",
    "produto", "marca", "filial", "cidade", "data_inauguracao",
    "cor_accent", "emoji", "data_prefix", "trinks_estabelecimento_id",
    "plano", "cotaTotal", "totalUtilizado", "saldoRestante",  # cota API é da própria conta
}

# Chaves que representam PERCENTUAIS — não escalar (0-100 continua 0-100)
PCT_KEYS = {
    "pct", "pct_receita", "pct_uso", "pct_atingimento", "utilizacao_pct",
    "cor_bar", "cobertura_pct", "delta_pct", "caixa_delta_pct",
    "atend_delta_pct", "ticket_delta_pct", "cliente_dia_delta_pct",
    "caixa_delta_perdia_pct", "atend_delta_perdia_pct",
    "cliente_dia_delta_perdia_pct", "caixa_delta_bruto_pct",
    "pct_recorrentes", "pareto20_pct", "pct_faturamento",
    "estrelas_media",  # rating não escala
}

# Chaves que representam TICKET/MÉDIA/PREÇO — não escalar (média por visita, etc.)
AVG_KEYS = {
    "ticket_medio", "ticket_medio_serv", "ticket_medio_visita",
    "ltv_medio", "freq_media_visitas", "rs_hora", "rs_hora_salao",
    "media_dia", "rating", "reviews_total",
}


def scale(obj, path=""):
    if obj is None: return None
    if isinstance(obj, bool): return obj  # bool é subclasse de int em py, precisa antes
    if isinstance(obj, (int, float)):
        return type(obj)(obj)  # não escala aqui — só via dict com key
    if isinstance(obj, list):
        return [scale(x, path) for x in obj]
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            new_path = f"{path}.{k}" if path else k
            if k in KEEP:
                out[k] = copy.deepcopy(v)
            elif k in PCT_KEYS or k in AVG_KEYS:
                out[k] = copy.deepcopy(v)  # mantém valor original (%, ticket)
            elif isinstance(v, bool):
                out[k] = v
            elif isinstance(v, int):
                out[k] = max(0, int(round(v * FACTOR)))
            elif isinstance(v, float):
                out[k] = round(v * FACTOR, 2)
            elif isinstance(v, (list, dict)):
                out[k] = scale(v, new_path)
            else:
                out[k] = copy.deepcopy(v)
        return out
    return copy.deepcopy(obj)


# Arrays cujos itens carregam NOME DE PESSOA (prof ou cliente) — pra
# criar diversidade visual no consolidado, renomeamos os N+ itens (deixamos
# top-N intactos → viram "ambas" no consolidado).
NOME_KEYS = {
    "ranking_prof": "nome",
    "ranking_prof_executor": "nome",
    "ranking_serv": "nome",        # serviços — deixa como está (produto)
    "rentabilidade_hora": "nome",  # também serviço
    "clientes_top": "nome",
    "aniversariantes": "cliente",
    "cross_sell": "cliente",       # note: cross_sell.top é uma sublista tratada abaixo
    "obs_alertas": "cliente",
    "obs_agend_alertas": "cliente",
    "top": "nome_or_cliente",       # top_ltv.top / churn_early.top / cross_sell.top
}
# Serviços (não são pessoas) — pula
NOT_PESSOA = {"ranking_serv", "rentabilidade_hora"}


def renomear_pessoas(obj):
    """Walk recursivo: pra cada array em NOME_KEYS, mantém top KEEP_TOP_N
    intacto e adiciona SUFIXO ' (SPA)' aos demais → cria itens exclusivos."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in NOME_KEYS and k not in NOT_PESSOA and isinstance(v, list):
                field = NOME_KEYS[k]
                for i, item in enumerate(v):
                    if not isinstance(item, dict): continue
                    if i < KEEP_TOP_N: continue
                    # 'top' pode ter chave 'nome' (top_ltv) ou 'cliente' (churn/aniv/xsell)
                    used_field = field
                    if field == "nome_or_cliente":
                        used_field = "nome" if "nome" in item else ("cliente" if "cliente" in item else None)
                    if not used_field: continue
                    nome = item.get(used_field)
                    if isinstance(nome, str) and SUFFIX_SPA not in nome:
                        item[used_field] = nome + SUFFIX_SPA
            else:
                renomear_pessoas(v)
    elif isinstance(obj, list):
        for x in obj:
            renomear_pessoas(x)


def main():
    src = os.path.join(ROOT, "data", "dashboard_data.json")
    dst_dir = os.path.join(ROOT, "data", "spa")
    dst = os.path.join(dst_dir, "dashboard_data.json")
    os.makedirs(dst_dir, exist_ok=True)

    with open(src, "r") as f:
        escova = json.load(f)

    spa = scale(escova)
    renomear_pessoas(spa)

    # Marca metadata como mock/spa
    spa["_mock"] = True
    spa["_mock_factor"] = FACTOR
    spa["_mock_origem"] = f"clone escalado (factor={FACTOR}) + top-{KEEP_TOP_N} de cada ranking preservado como cross-unit + demais renomeados com sufixo '{SUFFIX_SPA}' pra criar diversidade escova/spa/ambas na visualização do consolidado"

    with open(dst, "w") as f:
        json.dump(spa, f, indent=2, ensure_ascii=False)
    print(f"[mock_spa] gerado {dst} · factor={FACTOR} · top-{KEEP_TOP_N} cross-unit, resto SPA-exclusivo")


if __name__ == "__main__":
    main()
