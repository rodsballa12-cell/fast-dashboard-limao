#!/usr/bin/env python3
"""Cofre de dados do painel FAST — criptografa o que é dado pessoal ou financeiro.

Por que existe (21/10/2026): o repositório precisa ser PÚBLICO para o GitHub
Pages gratuito funcionar, e os caches de clientes (CPF, telefone, nascimento,
endereço) e o extrato Stone estavam legíveis por qualquer pessoa desde 12/08.
Apagar os caches quebraria o refresh e estouraria a cota do Trinks, porque o
repositório é o "banco de dados" das automações. Então eles continuam no repo,
mas CRIPTOGRAFADOS (arquivo .enc ao lado do nome original).

Duas chaves, de propósito:
  FAST_COFRE_CHAVE  -> caches com CPF/endereço. Só as automações e o PC do Rodrigo.
  FAST_PAINEL_SENHA -> arquivos que o painel lê. É a senha que o navegador pede.
Quem só vê o painel nunca consegue abrir os caches com CPF.

As chaves vêm de variáveis de ambiente (GitHub Secrets) ou de .cofre/chaves.env
(só no PC, fora do git).

Uso:
  python scripts/cofre.py abrir     # .enc -> arquivo normal (rode depois de git pull)
  python scripts/cofre.py fechar    # arquivo normal -> .enc (rode antes de commitar)
  python scripts/cofre.py status
  python scripts/cofre.py migrar    # migração única de 21/10/2026 (pull, cifra, commit, push)

Formato do .enc (JSON), compatível com WebCrypto no navegador:
  {"v":1,"alg":"AES-256-GCM","kdf":"PBKDF2-SHA256","iter":N,"salt":b64,"iv":b64,"ct":b64}
"""
import base64, json, os, subprocess, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ITER = 150_000

PAINEL = [
    "data/dashboard_data.json", "data/spa/dashboard_data.json", "data/consolidado/dashboard_data.json",
    "data/financeiro.json", "data/spa/financeiro.json", "data/consolidado/financeiro.json",
    "data/wa_fila.json",
]
CACHE = [f"data/{u}{n}" for u in ("", "spa/") for n in (
    "clientes_detalhes.json", "clientes_lista_cache.json", "agend_detail_cache.json",
    "agendamentos_ano_cache.json", "transacoes_ano_cache.json", "stone_extrato.csv")] + [
    "data/aniversarios_fila.json", "data/wa_historico.json",
]
TODOS = PAINEL + CACHE
REMOVER = ["data/hubspot_import_clientes.csv"]  # importação única; nenhum script usa


def _carregar_chaves():
    arq = RAIZ / ".cofre" / "chaves.env"
    if arq.exists():
        for linha in arq.read_text(encoding="utf-8").splitlines():
            if "=" in linha and not linha.strip().startswith("#"):
                k, v = linha.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def _chave(rel):
    nome = "FAST_PAINEL_SENHA" if rel in PAINEL else "FAST_COFRE_CHAVE"
    valor = os.environ.get(nome, "")
    if not valor:
        sys.exit(f"[cofre] ERRO: falta {nome} (GitHub Secret ou .cofre/chaves.env).")
    return valor


def _aes():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
    except ImportError:
        sys.exit("[cofre] ERRO: instale com  pip install cryptography")
    return AESGCM, PBKDF2HMAC, hashes


def _derivar(senha, salt, it):
    _, PBKDF2HMAC, hashes = _aes()
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=it).derive(senha.encode())


def cifrar(dados: bytes, senha: str) -> bytes:
    AESGCM, *_ = _aes()
    salt, iv = os.urandom(16), os.urandom(12)
    ct = AESGCM(_derivar(senha, salt, ITER)).encrypt(iv, dados, None)
    b = lambda x: base64.b64encode(x).decode()
    return json.dumps({"v": 1, "alg": "AES-256-GCM", "kdf": "PBKDF2-SHA256", "iter": ITER,
                       "salt": b(salt), "iv": b(iv), "ct": b(ct)}).encode()


def decifrar(envelope: bytes, senha: str) -> bytes:
    AESGCM, *_ = _aes()
    e = json.loads(envelope)
    d = base64.b64decode
    return AESGCM(_derivar(senha, d(e["salt"]), e["iter"])).decrypt(d(e["iv"]), d(e["ct"]), None)


def abrir():
    n = 0
    for rel in TODOS:
        enc = RAIZ / (rel + ".enc")
        if not enc.exists():
            continue
        try:
            (RAIZ / rel).write_bytes(decifrar(enc.read_bytes(), _chave(rel)))
            n += 1
        except Exception as exc:
            sys.exit(f"[cofre] ERRO ao abrir {rel}: chave errada ou arquivo corrompido ({type(exc).__name__}).")
    print(f"[cofre] {n} arquivo(s) aberto(s).")


def fechar():
    n = 0
    for rel in TODOS:
        claro, enc = RAIZ / rel, RAIZ / (rel + ".enc")
        if not claro.exists():
            continue
        dados, senha = claro.read_bytes(), _chave(rel)
        # Mesma informação -> mantém o .enc antigo. Sem isso, o IV aleatório
        # geraria um commit novo a cada execução mesmo sem dado novo.
        if enc.exists():
            try:
                if decifrar(enc.read_bytes(), senha) == dados:
                    continue
            except Exception:
                pass
        enc.write_bytes(cifrar(dados, senha))
        n += 1
    print(f"[cofre] {n} arquivo(s) fechado(s) (os demais não mudaram).")


def status():
    for rel in TODOS:
        claro, enc = (RAIZ / rel).exists(), (RAIZ / (rel + ".enc")).exists()
        print(f"{'enc' if enc else '---'} {'claro' if claro else '-----'}  {rel}")


def _git(*args, ok=False):
    print("  $ git " + " ".join(args))
    r = subprocess.run(["git", *args], cwd=RAIZ)
    if r.returncode and not ok:
        sys.exit(f"[cofre] git {args[0]} falhou — nada foi publicado. Me mostre a mensagem acima.")
    return r.returncode


def migrar():
    print("[cofre] Migração única: tirar dado pessoal do repositório público.")
    _chave("data/dashboard_data.json"); _chave("data/clientes_detalhes.json")  # falha cedo se faltar chave
    # 1) guarda alterações locais em data/ (recuperáveis com `git stash list`)
    _git("stash", "push", "-m", "pre-cofre-dados-locais", "--", "data/", ok=True)
    # 2) traz o que as automações publicaram
    _git("pull", "--rebase", "--autostash", "origin", "main")
    # 3) cifra a versão mais nova e tira o texto puro do git (fica no PC)
    fechar()
    for rel in TODOS + REMOVER:
        _git("rm", "--cached", "-q", "--ignore-unmatch", rel)
    for rel in REMOVER:
        (RAIZ / rel).unlink(missing_ok=True)
    _git("add", ".gitignore", *[r + ".enc" for r in TODOS if (RAIZ / (r + ".enc")).exists()])
    _git("commit", "-m", "seguranca: dados de clientes e financeiros passam a ser criptografados (cofre)")
    _git("push", "origin", "main")
    print("[cofre] Pronto. Abra o painel: ele vai pedir a senha uma vez neste aparelho.")


if __name__ == "__main__":
    _carregar_chaves()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    {"abrir": abrir, "fechar": fechar, "status": status, "migrar": migrar}.get(
        cmd, lambda: sys.exit(__doc__))()
