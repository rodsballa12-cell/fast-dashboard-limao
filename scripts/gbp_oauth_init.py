"""Setup OAuth 2.0 pra Google Business Profile Performance API.

RODAR LOCALMENTE UMA VEZ. Vai:
  1. Abrir o navegador pedindo consentimento na sua conta Google
  2. Voce clica "Permitir" (aceita ler dados do seu Business Profile)
  3. Google redireciona pro localhost com um code
  4. Script troca code por refresh_token e mostra na tela
  5. Voce copia o refresh_token pros GH Secrets

PRE-REQUISITO: baixar client_secret.json do Google Cloud Console
  (Credentials > OAuth 2.0 Client ID > Desktop app > download JSON)

USO:
  pip install google-auth google-auth-oauthlib
  python scripts/gbp_oauth_init.py path/para/client_secret.json

Depois, no repo Github:
  - Settings > Secrets and variables > Actions > New repository secret
  - Adicionar 3 secrets: GBP_OAUTH_CLIENT_ID, GBP_OAUTH_CLIENT_SECRET,
    GBP_OAUTH_REFRESH_TOKEN (todos vem do output deste script)
"""

from __future__ import annotations

import json
import sys

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("ERRO: pacotes faltando. Rode:")
    print("  pip install google-auth google-auth-oauthlib")
    sys.exit(1)


# Scopes minimos pra ler Business Profile Performance + Business Information
SCOPES = [
    "https://www.googleapis.com/auth/business.manage",
]


def main() -> int:
    if len(sys.argv) < 2:
        print("USO: python scripts/gbp_oauth_init.py <path_client_secret.json>")
        return 1

    client_secret_path = sys.argv[1]
    with open(client_secret_path) as f:
        cs = json.load(f)

    # Chave 'installed' pra Desktop app, 'web' pra Web app
    if "installed" in cs:
        client_id = cs["installed"]["client_id"]
        client_secret = cs["installed"]["client_secret"]
    elif "web" in cs:
        client_id = cs["web"]["client_id"]
        client_secret = cs["web"]["client_secret"]
    else:
        print(f"ERRO: formato de client_secret.json inesperado (nem 'installed' nem 'web')")
        return 1

    print(f"Vou abrir seu browser pra consent. Se ja estiver logado em varias contas Google,")
    print(f"ESCOLHA a conta que e OWNER do Business Profile Fast Escova Limao.\n")

    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
    # run_local_server abre browser e captura o code no callback
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")

    if not creds.refresh_token:
        print("ERRO: Google nao devolveu refresh_token. Pode ser que ja tenha consentido antes;")
        print("nesse caso revogue em https://myaccount.google.com/permissions e rode de novo.")
        return 1

    print("\n" + "=" * 70)
    print("SUCESSO! Copie os 3 valores abaixo pros GitHub Secrets:")
    print("=" * 70)
    print(f"\nGBP_OAUTH_CLIENT_ID:")
    print(f"  {client_id}")
    print(f"\nGBP_OAUTH_CLIENT_SECRET:")
    print(f"  {client_secret}")
    print(f"\nGBP_OAUTH_REFRESH_TOKEN:")
    print(f"  {creds.refresh_token}")
    print("\n" + "=" * 70)
    print("Onde adicionar:")
    print("  https://github.com/rodsballa12-cell/fast-dashboard-limao/settings/secrets/actions")
    print("Depois avise o Claude no chat que ele testa o refresh.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
