#!/usr/bin/env python3
"""Extrato Stone entra pelo PC (substitui o upload pelo github.com).

Desde 21/10/2026 o CSV bruto não pode passar pelo repositório público. Uso:

    python scripts/stone_local.py "C:/Users/rods_/Downloads/extrato.csv"

Faz: git pull -> abre o cofre -> soma o extrato ao histórico (stone_merge.py)
-> fecha o cofre -> commita só o .enc -> push. O painel pega no próximo refresh.
"""
import shutil, subprocess, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def rodar(*cmd):
    print("  $", " ".join(cmd))
    r = subprocess.run(cmd, cwd=RAIZ)
    if r.returncode:
        sys.exit(f"[stone] falhou em: {' '.join(cmd)} — nada foi publicado.")


def main():
    arquivos = [Path(a) for a in sys.argv[1:]]
    if not arquivos or not all(a.exists() for a in arquivos):
        sys.exit(__doc__)
    py = sys.executable
    rodar("git", "pull", "--rebase", "--autostash", "origin", "main")
    rodar(py, "scripts/cofre.py", "abrir")
    entrada = RAIZ / "data" / "stone_entrada"
    for a in arquivos:
        shutil.copy2(a, entrada / a.name)
    rodar(py, "scripts/stone_merge.py")
    rodar(py, "scripts/cofre.py", "fechar")
    rodar("git", "add", "data/stone_extrato.csv.enc")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=RAIZ).returncode == 0:
        print("[stone] Nada novo no extrato.")
        return
    rodar("git", "commit", "-m", "stone: extrato somado ao historico (local, cofre)")
    rodar("git", "push", "origin", "main")
    print("[stone] Pronto. O painel atualiza no próximo refresh agendado.")


if __name__ == "__main__":
    main()
