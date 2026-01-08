import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# OAuth 2.0 Scope for YouTube Upload and Channel Verification
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

def get_refresh_token(client_secrets_file):
    """
    Opens a browser to authenticate the user and returns the refresh token.
    Authentication flow for Desktop App.
    """
    if not os.path.exists(client_secrets_file):
        print(f"Error: {client_secrets_file} not found.")
        print("Please download credentials from Google Console and rename to 'client_secrets.json'.")
        return

    # Run local server flow
    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n" + "="*50)
    print("✅ Authentication Successful!")
    print("="*50)
    print(f"Access Token: {creds.token[:10]}... (Expires in 1 hour)")
    
    if creds.refresh_token:
        print("\n🔑  YOUR REFRESH TOKEN (Save this to GitHub Secrets):")
        print("-" * 50)
        print(creds.refresh_token)
        print("-" * 50)
        print("Required for: REFRESH_TOKEN secret.\n")
    else:
        print("\n⚠️  No Refresh Token received!")
        print("Reason: You might have already authorized this app.")
        print("Fix: Go to https://myaccount.google.com/permissions, remove the app, and run this script again.")

    # Show other secrets for convenience
    with open(client_secrets_file, 'r') as f:
        data = json.load(f)
        installed = data.get('installed', data.get('web', {}))
        print(f"Also save these to GitHub Secrets:")
        print(f"CLIENT_ID: {installed.get('client_id')}")
        print(f"CLIENT_SECRET: {installed.get('client_secret')}")

if __name__ == "__main__":
    CLIENT_SECRETS_FILE = "client_secrets.json"
    print(f"Looking for {CLIENT_SECRETS_FILE}...")
    token = get_refresh_token(CLIENT_SECRETS_FILE)
