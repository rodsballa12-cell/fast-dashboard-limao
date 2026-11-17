#!/usr/bin/env python3
"""WhatsApp de cada profissional, sem ninguém digitar (17/11/2026).

Para que serve: o botão "Abrir no WhatsApp" da aba Comissões abre direto a
conversa da profissional que deve a nota. Antes ele abria o WhatsApp sem
destinatário e o Lucas tinha de procurar a pessoa.

Por que não vem direto do Trinks: a API pública do Trinks NÃO entrega o
celular do cadastro de profissional (/v1/profissionais traz nome, CPF, função
e situação; o detalhe vem vazio; não há rota de contatos). Testado em
17/11/2026. O número aparece na tela do Trinks, mas não sai pela API.

De onde o número vem, em ordem de confiança:
  1. Formulário de notas: o WhatsApp que a própria profissional informou na
     nota mais recente (data/notas_profissionais.json, gerado por
     notas_forms.py). Ela sabe o próprio número.
  2. Cadastro de CLIENTE no Trinks com o MESMO CPF da profissional
     (data/clientes_detalhes.json). Casamento só por CPF exato: pelo nome,
     uma homônima receberia a cobrança de outra pessoa.
  Sem nenhuma das duas, a pessoa fica sem número e a aba diz isso.

Saída: data/profissionais_contato.json -- {nome no Trinks: {telefone, fonte}}.
É dado pessoal: está no .gitignore e NÃO vai para o repositório público. É
regerado a cada refresh; o número chega ao painel dentro do dashboard_data,
que o cofre criptografa. Se o Trinks falhar, o arquivo anterior é mantido.

Uso:  python scripts/profissionais_contato.py
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "data" / "profissionais_contato.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _ler(p: Path, padrao=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _so_digitos(s) -> str:
    return re.sub(r"\D", "", str(s or ""))


def _telefone_ok(d: str) -> bool:
    # 10-11 dígitos (DDD + número) ou 12-13 com o 55 na frente
    return len(d) in (10, 11) or (len(d) in (12, 13) and d.startswith("55"))


def _nome(s: str) -> str:
    # Mesmo formato que o github_refresh grava no prof_map (é a chave da aba)
    return (s or "").strip().title()


def profissionais_trinks() -> tuple[dict[str, str], list[str]]:
    """{nome: cpf} das duas lojas, ativas e inativas (quem saiu ainda pode dever nota)."""
    from trinks_common import TrinksClient
    cpfs, falhas = {}, []
    for unidade in ("escova", "spa"):
        try:
            t = TrinksClient(unidade)
        except ValueError:
            falhas.append(f"{unidade}: sem credencial")
            continue
        try:
            for ativo in ("true", "false"):
                for p in t.paginate("/v1/profissionais", {"ativo": ativo}):
                    nome, cpf = _nome(p.get("nome")), _so_digitos(p.get("cpf"))
                    if nome and len(cpf) == 11:
                        cpfs.setdefault(nome, cpf)
        except Exception as e:  # noqa: BLE001 -- uma loja fora não derruba a outra
            falhas.append(f"{unidade}: {type(e).__name__}")
    return cpfs, falhas


def telefones_por_cpf() -> dict[str, str]:
    out = {}
    for rel in ("data/clientes_detalhes.json", "data/spa/clientes_detalhes.json"):
        for c in (_ler(RAIZ / rel, {}) or {}).values():
            if not isinstance(c, dict):
                continue
            cpf = _so_digitos(c.get("cpf"))
            tels = c.get("telefone") or []
            tels = tels if isinstance(tels, list) else [tels]
            tel = next((d for d in map(_so_digitos, tels) if _telefone_ok(d)), None)
            if len(cpf) == 11 and tel:
                out.setdefault(cpf, tel)
    return out


def telefones_do_forms() -> dict[str, str]:
    """WhatsApp informado no Forms; vale o da nota mais recente de cada pessoa."""
    notas = (_ler(RAIZ / "data" / "notas_profissionais.json", {}) or {}).get("notas") or []
    out = {}
    for n in sorted(notas, key=lambda x: x.get("enviado_em") or ""):
        d = _so_digitos(n.get("whatsapp"))
        if n.get("nome_trinks") and _telefone_ok(d):
            out[_nome(n["nome_trinks"])] = d
    return out


def main() -> int:
    cpfs, falhas = profissionais_trinks()
    anterior = (_ler(SAIDA, {}) or {}).get("contatos") or {}
    if not cpfs:
        print(f"[contato] Trinks não respondeu ({'; '.join(falhas) or 'sem dados'}) -- mantive o arquivo anterior "
              f"({len(anterior)} contato(s))")
        return 0
    por_cpf, forms = telefones_por_cpf(), telefones_do_forms()
    contatos = {}
    for nome, cpf in sorted(cpfs.items()):
        if nome in forms:
            contatos[nome] = {"telefone": forms[nome], "fonte": "forms"}
        elif cpf in por_cpf:
            contatos[nome] = {"telefone": por_cpf[cpf], "fonte": "cadastro_cliente_cpf"}
    # Quem informou no Forms mas não veio na lista do Trinks (nome por apelido) também vale
    for nome, tel in forms.items():
        contatos.setdefault(nome, {"telefone": tel, "fonte": "forms"})
    SAIDA.write_text(json.dumps({
        "gerado_em": dt.datetime.now(dt.timezone(dt.timedelta(hours=-3))).isoformat(timespec="seconds"),
        "fontes": "1) WhatsApp informado no Forms de notas; 2) cadastro de cliente do Trinks com o mesmo CPF",
        "profissionais_no_trinks": len(cpfs),
        "contatos": contatos,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    via_forms = sum(1 for c in contatos.values() if c["fonte"] == "forms")
    print(f"[contato] {len(contatos)} de {len(cpfs)} profissionais com WhatsApp "
          f"({via_forms} pelo Forms, {len(contatos) - via_forms} pelo cadastro de cliente)"
          + (f" · falhas: {'; '.join(falhas)}" if falhas else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
