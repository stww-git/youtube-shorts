import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build

def get_authenticated_service(client_id, client_secret, refresh_token):
    """
    Builds the YouTube Data API service using stored secrets.
    Does NOT require browser interaction (suitable for GitHub Actions).
    """
    credentials = google.oauth2.credentials.Credentials(
        None,  # Access token (will be refreshed)
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=[
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.readonly"
        ]
    )

    return build("youtube", "v3", credentials=credentials)
