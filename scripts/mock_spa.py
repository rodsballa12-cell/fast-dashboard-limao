"""Mock temporário do payload SPA: clona Escova com valores escalados por FACTOR,
apenas pra visualização do consolidado antes de a SPA ter estabelecimentoId Trinks.
Quando SPA abrir de verdade, este script deixa de rodar e o refresh backend
gera data/spa/dashboard_data.json com dados reais."""

import json, os, sys, copy
from datetime import datetime, timezone, timedelta

FACTOR = 0.42  # SPA sendo unidade menor/nova: ~42% do volume da Escova
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


def main():
    src = os.path.join(ROOT, "data", "dashboard_data.json")
    dst_dir = os.path.join(ROOT, "data", "spa")
    dst = os.path.join(dst_dir, "dashboard_data.json")
    os.makedirs(dst_dir, exist_ok=True)

    with open(src, "r") as f:
        escova = json.load(f)

    spa = scale(escova)

    # Marca metadata como mock/spa
    spa["_mock"] = True
    spa["_mock_factor"] = FACTOR
    spa["_mock_origem"] = "clone escalado de data/dashboard_data.json (Escova) — pré-conexão Trinks SPA"

    with open(dst, "w") as f:
        json.dump(spa, f, indent=2, ensure_ascii=False)
    print(f"[mock_spa] gerado {dst} · factor={FACTOR}")


if __name__ == "__main__":
    main()
