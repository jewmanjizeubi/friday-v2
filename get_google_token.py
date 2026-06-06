"""
Script one-shot pour obtenir le refresh token Google OAuth.
À lancer UNE SEULE FOIS depuis ton PC (pas le Pi).

Usage :
  1. Crée un projet Google Cloud
  2. Active Gmail API + Calendar API
  3. Crée des credentials OAuth (Desktop App)
  4. Télécharge le client_secret.json
  5. Lance : python get_google_token.py
  6. Copie le refresh_token dans ton .env
"""

import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar"
]

CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "google_token.json"


def main():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    token_data = json.loads(creds.to_json())

    print("\n" + "="*60)
    print("✅ OAuth réussi ! Copie ces valeurs dans ton .env :")
    print("="*60)
    print(f"GOOGLE_CLIENT_ID={token_data.get('client_id', '')}")
    print(f"GOOGLE_CLIENT_SECRET={token_data.get('client_secret', '')}")
    print(f"GOOGLE_REFRESH_TOKEN={token_data.get('refresh_token', '')}")
    print("="*60 + "\n")
    print("⚠️  Ne commite JAMAIS ce fichier ni le client_secret.json sur GitHub.")


if __name__ == "__main__":
    main()
