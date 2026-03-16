#!/usr/bin/env python3
"""
YouTube OAuth2 Refresh Token 발급 스크립트

이 스크립트를 실행하면:
1. 브라우저가 열리고 Google 계정 로그인을 요청합니다.
2. 원하는 YouTube 채널에 연결된 계정으로 로그인합니다.
3. 권한을 승인하면 Refresh Token이 출력됩니다.
4. 이 토큰을 .env 파일이나 GitHub Secrets에 저장하세요.

사전 설정:
1. Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성합니다.
2. client_secrets.json 파일을 프로젝트 루트에 저장합니다.
   (또는 아래 CLIENT_ID, CLIENT_SECRET을 직접 입력)
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# YouTube 업로드에 필요한 스코프
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly',
]

def get_refresh_token():
    """OAuth2 인증을 수행하고 Refresh Token을 반환합니다."""
    
    # 방법 1: client_secrets.json 파일 사용
    if os.path.exists('client_secrets.json'):
        print("🔐 client_secrets.json 파일을 사용합니다.")
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secrets.json',
            scopes=SCOPES
        )
    else:
        # 방법 2: 환경 변수에서 직접 읽기
        client_id = os.getenv('CLIENT_ID')
        client_secret = os.getenv('CLIENT_SECRET')
        
        if not client_id or not client_secret:
            print("❌ client_secrets.json 파일이 없고, 환경 변수도 설정되지 않았습니다.")
            print("\n다음 중 하나를 수행하세요:")
            print("1. client_secrets.json 파일을 프로젝트 루트에 저장")
            print("2. CLIENT_ID와 CLIENT_SECRET 환경 변수 설정")
            return None
        
        print("🔐 환경 변수에서 인증 정보를 사용합니다.")
        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"]
            }
        }
        flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
    
    print("\n🌐 브라우저가 열립니다. Google 계정으로 로그인하세요.")
    print("💡 팁: 원하는 YouTube 채널에 연결된 계정으로 로그인하세요!\n")
    
    # 로컬 서버를 통해 인증 (브라우저 자동 열림)
    # prompt='consent': 캐시 없이 계정 목록 최신화
    credentials = flow.run_local_server(
        port=8080,
        prompt='consent',
        access_type='offline',
    )
    
    refresh_token = credentials.refresh_token
    
    # 채널 정보 확인
    channel_name = "알 수 없음"
    channel_id = ""
    try:
        from googleapiclient.discovery import build
        youtube = build('youtube', 'v3', credentials=credentials)
        response = youtube.channels().list(part='snippet', mine=True).execute()
        if response.get('items'):
            channel_name = response['items'][0]['snippet']['title']
            channel_id = response['items'][0]['id']
    except Exception as e:
        print(f"   ⚠️  채널 정보 조회 실패: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Refresh Token 발급 성공!")
    print("=" * 60)
    print(f"\n📺 채널: {channel_name}")
    if channel_id:
        print(f"   ID: {channel_id}")
    print(f"\n🔑 REFRESH_TOKEN:\n{refresh_token}\n")
    print("=" * 60)
    print("\n📋 이 토큰을 복사하여 다음 위치에 저장하세요:")
    print("   - .env 파일: REFRESH_TOKEN_채널명=토큰값")
    print("   - GitHub Secrets: REFRESH_TOKEN_채널명")
    print("\n예시:")
    print(f"   REFRESH_TOKEN_{channel_name.upper().replace('-','_')}={refresh_token}")
    
    return refresh_token

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    print("=" * 60)
    print("🎬 YouTube OAuth2 Refresh Token 발급")
    print("=" * 60)
    
    get_refresh_token()
