import os
import sys
import json
from dotenv import load_dotenv

# Add project root to path to allow importing src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.upload.auth import get_authenticated_service

def check_channel():
    """
    Checks which channel is authenticated using the credentials in .env
    """
    # Load environment variables
    load_dotenv()
    
    # Try to load secrets from .env or client_secrets.json
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    refresh_token = os.getenv("REFRESH_TOKEN")
    
    # Fallback to client_secrets.json if env vars missing (for convenience)
    if not client_id or not client_secret:
        if os.path.exists('client_secrets.json'):
            try:
                with open('client_secrets.json', 'r') as f:
                    data = json.load(f)
                    installed = data.get('installed', data.get('web', {}))
                    client_id = installed.get('client_id')
                    client_secret = installed.get('client_secret')
                    print("loaded client_id/secret from client_secrets.json")
            except:
                pass

    if not all([client_id, client_secret, refresh_token]):
        print("\n❌ Missing Credentials!")
        print("Please ensure you have set the following in your .env file:")
        print(f"- CLIENT_ID: {'✅ Found' if client_id else '❌ Missing'}")
        print(f"- CLIENT_SECRET: {'✅ Found' if client_secret else '❌ Missing'}")
        print(f"- REFRESH_TOKEN: {'✅ Found' if refresh_token else '❌ Missing'}")
        return

    try:
        print("\n🔍 Connecting to YouTube...")
        youtube = get_authenticated_service(client_id, client_secret, refresh_token)
        
        # Get Channel Info
        request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            mine=True
        )
        response = request.execute()
        
        if response['items']:
            channel = response['items'][0]
            title = channel['snippet']['title']
            custom_url = channel['snippet'].get('customUrl', 'N/A')
            subs = channel['statistics']['subscriberCount']
            
            print("\n" + "="*50)
            print(f"✅ Authenticated Channel: {title}")
            print(f"🔗 Handle: {custom_url}")
            print(f"👥 Subscribers: {subs}")
            print("="*50)
            print("Videos will be uploaded to THIS channel.")
        else:
            print("❌ No channel found for this user.")
            
    except Exception as e:
        print(f"\n❌ Authentication Failed: {e}")
        print("Check if your REFRESH_TOKEN is valid.")

if __name__ == "__main__":
    check_channel()
