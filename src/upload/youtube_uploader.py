import os
import logging
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from .auth import get_authenticated_service
from src.config.upload_config import DEFAULT_TAGS, MADE_FOR_KIDS

logger = logging.getLogger(__name__)

class YouTubeUploader:
    def __init__(self, client_id, client_secret, refresh_token):
        self.youtube = get_authenticated_service(client_id, client_secret, refresh_token)

    def upload_video(self, file_path, title, description, privacy_status="private", tags=None, made_for_kids=None):
        """
        Uploads a video to YouTube.
        
        Args:
            file_path: Absolute path to the video file
            title: Video title (max 100 chars)
            description: Video description (max 5000 chars)
            privacy_status: "private", "public", or "unlisted"
            tags: List of tags (optional, uses config default if None)
            made_for_kids: Boolean COPPA setting (optional, uses config default if None)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")

        # Use defaults from config if not provided
        if tags is None:
            tags = DEFAULT_TAGS
        
        if made_for_kids is None:
            made_for_kids = MADE_FOR_KIDS

        body = {
            "snippet": {
                "title": title[:100],  # Max 100 chars
                "description": description[:5000],
                "tags": tags,
                "categoryId": "22"  # People & Blogs (or 26 for Howto & Style)
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": made_for_kids
            }
        }

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

        try:
            print(f"🚀 Uploading {title} to YouTube ({privacy_status})...")
            request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"   Uploaded {int(status.progress() * 100)}%")

            print(f"✅ Upload Complete! Video ID: {response['id']}")
            return response['id']

        except HttpError as e:
            error_content = e.content.decode("utf-8")
            logger.error(f"An HTTP error %d occurred:\n%s", e.resp.status, error_content)
            print(f"❌ Upload Failed: {e}")
            return None
