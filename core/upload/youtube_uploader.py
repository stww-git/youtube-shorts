
import os
import time
import random
import http.client
import httplib2
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

# Constants
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
                        http.client.IncompleteRead, http.client.ImproperConnectionState,
                        http.client.CannotSendRequest, http.client.CannotSendHeader,
                        http.client.ResponseNotReady, http.client.BadStatusLine)
MAX_RETRIES = 10

class YouTubeUploader:
    def __init__(self, client_secrets_file, credentials_file=None, get_refresh_token_func=None):
        self.client_secrets_file = client_secrets_file
        self.credentials_file = credentials_file
        self.get_refresh_token_func = get_refresh_token_func
        self.youtube = self._get_authenticated_service()

    def _get_authenticated_service(self):
        """인증된 YouTube 서비스 객체를 반환합니다."""
        # 환경변수에서 로드하는 방식을 우선시함 (채널별 REFRESH_TOKEN)
        creds = None
        
        # 1. Refresh Token 함수가 있으면 그것을 사용하여 Credentials 생성
        if self.get_refresh_token_func:
            refresh_token = self.get_refresh_token_func()
            if refresh_token:
                import json
                
                client_id = None
                client_secret = None
                token_uri = "https://oauth2.googleapis.com/token"
                
                # client_secrets.json 파일에서 로드 시도
                try:
                    if self.client_secrets_file and os.path.exists(self.client_secrets_file):
                        with open(self.client_secrets_file, 'r', encoding='utf-8') as f:
                            client_secrets = json.load(f)
                            web_config = client_secrets.get('installed', client_secrets.get('web', {}))
                            client_id = web_config.get('client_id')
                            client_secret = web_config.get('client_secret')
                            token_uri = web_config.get('token_uri', token_uri)
                except Exception as e:
                    logger.warning(f"client_secrets.json 로드 실패: {e}")
                
                # 파일에서 못 읽었으면 환경변수에서 읽기
                if not client_id or not client_secret:
                    client_id = os.getenv('CLIENT_ID')
                    client_secret = os.getenv('CLIENT_SECRET')
                
                if client_id and client_secret:
                    creds = Credentials(
                        token=None,
                        refresh_token=refresh_token,
                        token_uri=token_uri,
                        client_id=client_id,
                        client_secret=client_secret
                    )
        
        # 2. Creds 파일이 있고 유효하면 사용 (fallback)
        if not creds and self.credentials_file and os.path.exists(self.credentials_file):
            creds = Credentials.from_authorized_user_file(self.credentials_file, ['https://www.googleapis.com/auth/youtube.upload'])

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Flow를 통한 인증은 서버 환경(GitHub Actions)에서 불가능하므로 에러 처리하거나 
                # 로컬 실행 시 로직 추가 (여기서는 생략)
                if not creds:
                    raise Exception("Valid credentials not found. Check REFRESH_TOKEN settings.")

        return build('youtube', 'v3', credentials=creds)

    def upload_video(self, file_path, title, description, category_id="22", keywords=[], privacy_status="private", made_for_kids=False):
        """비디오를 YouTube에 업로드합니다."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")

        tags = keywords if keywords else []
        
        body = {
            'snippet': {
                'title': title[:100],  # Title max 100 chars
                'description': description[:5000],  # Description max 5000 chars
                'tags': tags,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': made_for_kids
            }
        }

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

        logger.info(f"Uploading file: {file_path}")
        logger.info(f"Title: {title}")
        logger.info(f"Privacy Status: {privacy_status}")

        insert_request = self.youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )

        return self._resumable_upload(insert_request)

    def _resumable_upload(self, request):
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                print("   📤 Uploading file...")
                status, response = request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        print(f"   ✅ Upload Complete! Video ID: {response['id']}")
                        return response['id']
                    else:
                        raise Exception(f"Unexpected response: {response}")
            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    error = f"A retriable HTTP error {e.resp.status} occurred:\n{e.content}"
                else:
                    raise e
            except RETRIABLE_EXCEPTIONS as e:
                error = f"A retriable error occurred: {e}"

            if error is not None:
                print(error)
                retry += 1
                if retry > MAX_RETRIES:
                    raise Exception("No longer attempting to retry.")
                
                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                print(f"   Sleeping {sleep_seconds} seconds and then retrying...")
                time.sleep(sleep_seconds)

        return None
