#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Caca nome usado e nunca definido, sem rodar o script.

POR QUE ESTE SCRIPT EXISTE (18/10/2026)
Em 18/10 eu adicionei um detector de comissao ao github_refresh.py. O dict
nasceu dentro de `analisar()` e foi lido dentro de `main()` — duas funcoes
diferentes. `python -m py_compile` passou, a auditoria passou (ela le DADO,
nao codigo), e eu empurrei. O refresh das 10h43 morreu com

    NameError: name 'cats_sem_taxa' is not defined

depois de ja ter puxado 1.925 agendamentos e 1.126 transacoes do Trinks. Zero
dado gravado, e o painel ficou com o numero velho.

O erro nao foi o escopo — foi testar o consumidor e nao o produtor. Um
NameError assim e achavel sem API, sem segredo e sem rodar nada: basta olhar,
escopo por escopo, se todo nome lido tem onde nascer.

Nao substitui o pyflakes; substitui NAO TER pyflakes, que e o caso desta
maquina (sem rede para instalar).

Uso:  python scripts/checa_nomes.py [arquivo.py ...]      (sem argumento: scripts/*.py)
      exit 1 se achou algo
"""
import ast
import builtins
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
EMBUTIDOS = set(dir(builtins)) | {"__file__", "__name__", "__doc__", "__spec__"}


class Escopo:
    def __init__(self, pai=None, tipo="modulo", nome=""):
        self.pai, self.tipo, self.nome = pai, tipo, nome
        self.definidos: set[str] = set()
        self.lidos: list[tuple[str, int]] = []
        self.filhos: list["Escopo"] = []

    def alcance(self):
        """Nomes visiveis aqui: os meus, os dos pais (menos a classe, que nao
        entra no fechamento das funcoes de dentro) e os embutidos."""
        vis = set(self.definidos)
        p = self.pai
        while p is not None:
            if p.tipo != "classe":
                vis |= p.definidos
            p = p.pai
        return vis | EMBUTIDOS

    def caminho(self):
        partes, e = [], self
        while e is not None:
            if e.nome:
                partes.append(e.nome)
            e = e.pai
        return " → ".join(reversed(partes)) or "módulo"


class Visita(ast.NodeVisitor):
    def __init__(self, escopo):
        self.e = escopo

    # --- o que DEFINE um nome -------------------------------------------
    def visit_Name(self, no):
        if isinstance(no.ctx, (ast.Store, ast.Del)):
            self.e.definidos.add(no.id)
        else:
            self.e.lidos.append((no.id, no.lineno))

    def _novo(self, no, tipo, nome):
        filho = Escopo(self.e, tipo, nome)
        self.e.filhos.append(filho)
        return filho

    def visit_FunctionDef(self, no):
        self.e.definidos.add(no.name)
        for d in no.decorator_list:
            self.visit(d)
        for v in (no.args.defaults + [x for x in no.args.kw_defaults if x]):
            self.visit(v)
        f = self._novo(no, "funcao", no.name + "()")
        a = no.args
        for arg in (a.posonlyargs + a.args + a.kwonlyargs
                    + ([a.vararg] if a.vararg else []) + ([a.kwarg] if a.kwarg else [])):
            f.definidos.add(arg.arg)
        sub = Visita(f)
        for c in no.body:
            sub.visit(c)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, no):
        f = self._novo(no, "funcao", "<lambda>")
        a = no.args
        for arg in (a.posonlyargs + a.args + a.kwonlyargs
                    + ([a.vararg] if a.vararg else []) + ([a.kwarg] if a.kwarg else [])):
            f.definidos.add(arg.arg)
        Visita(f).visit(no.body)

    def visit_ClassDef(self, no):
        self.e.definidos.add(no.name)
        for b in no.bases:
            self.visit(b)
        c = self._novo(no, "classe", "class " + no.name)
        sub = Visita(c)
        for x in no.body:
            sub.visit(x)

    def visit_comprehension_generic(self, no, partes):
        f = self._novo(no, "funcao", "<comprehension>")
        sub = Visita(f)
        for g in no.generators:
            sub.visit(g.target)
            sub.visit(g.iter)
            for i in g.ifs:
                sub.visit(i)
        for pt in partes:
            sub.visit(pt)

    def visit_ListComp(self, no):
        self.visit_comprehension_generic(no, [no.elt])
    def visit_SetComp(self, no):
        self.visit_comprehension_generic(no, [no.elt])
    def visit_GeneratorExp(self, no):
        self.visit_comprehension_generic(no, [no.elt])
    def visit_DictComp(self, no):
        self.visit_comprehension_generic(no, [no.key, no.value])

    def visit_Import(self, no):
        for a in no.names:
            self.e.definidos.add((a.asname or a.name).split(".")[0])
    def visit_ImportFrom(self, no):
        for a in no.names:
            if a.name == "*":
                self.e.definidos.add("*")   # desliga a checagem deste escopo
            else:
                self.e.definidos.add(a.asname or a.name)

    def visit_Global(self, no):
        for n in no.names:
            self.e.definidos.add(n)
            r = self.e
            while r.pai is not None:
                r = r.pai
            r.definidos.add(n)
    visit_Nonlocal = visit_Global

    def visit_ExceptHandler(self, no):
        if no.name:
            self.e.definidos.add(no.name)
        self.generic_visit(no)


def achados_de(caminho: pathlib.Path):
    try:
        arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    except SyntaxError as e:
        return [(0, "ERRO DE SINTAXE", str(e))]
    raiz = Escopo()
    Visita(raiz).visit(arvore)
    # Segunda passada: `def` pode usar global definido depois dele.
    def coleta(e, saida):
        saida.append(e)
        for f in e.filhos:
            coleta(f, saida)
    todos = []
    coleta(raiz, todos)
    out = []
    for e in todos:
        vis = e.alcance()
        if "*" in vis:
            continue
        for nome, linha in e.lidos:
            if nome not in vis:
                out.append((linha, nome, e.caminho()))
    return sorted(set(out))


def main() -> int:
    alvos = [pathlib.Path(a) for a in sys.argv[1:]] or sorted((REPO / "scripts").glob("*.py"))
    ruim = 0
    for a in alvos:
        itens = achados_de(a)
        if not itens:
            continue
        ruim += len(itens)
        print(f"🛑 {a.relative_to(REPO) if a.is_absolute() else a}")
        for linha, nome, onde in itens:
            print(f"   linha {linha}: `{nome}` é lido em {onde} e não nasce em lugar nenhum")
    if not ruim:
        print(f"✅ {len(alvos)} arquivo(s) conferido(s): todo nome lido tem onde nascer.")
    return 1 if ruim else 0


if __name__ == "__main__":
    sys.exit(main())
