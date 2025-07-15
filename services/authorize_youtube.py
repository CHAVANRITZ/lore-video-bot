from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import json

# Path to your client secrets file
CLIENT_SECRETS_FILE = "credentials/youtube_client_secret.json"

# Path where credentials will be saved
CREDENTIALS_PATH = "credentials/youtube_credentials.json"

# Scope for YouTube upload access
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def run_youtube_oauth():
    # Initialize the OAuth flow with client secret and scope
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE,
                                                     SCOPES)

    # Use console-based flow (better for Replit/server environments)
    creds = flow.run_console()

    # Save credentials to JSON file
    with open(CREDENTIALS_PATH, "w") as token_file:
        token_file.write(creds.to_json())

    print(f"✅ YouTube OAuth complete. Credentials saved to {CREDENTIALS_PATH}")


if __name__ == "__main__":
    run_youtube_oauth()
