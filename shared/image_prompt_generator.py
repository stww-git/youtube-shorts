"""
이미지 프롬프트 생성기

제목과 대본을 바탕으로 영어 이미지 프롬프트를 생성합니다.
"""

import os
import sys
import time
import logging

# 채널 루트의 prompts.py 사용
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import genai
from google.genai import types
from shared.config.model_config import TEXT_MODEL, MAX_RETRIES, RETRY_DELAY, TEMPERATURE
from prompts import IMAGE_GENERATION_PROMPT

logger = logging.getLogger(__name__)


class ImagePromptGenerator:
    """제목과 대본을 바탕으로 영어 이미지 프롬프트를 생성하는 클래스"""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "celestial-math-489909-f9")
        self.location = os.getenv("GCP_LOCATION", "global")
        
        self.api_call_count = 0
        self.client = genai.Client(vertexai=True, project=self.project_id, location=self.location)

    def _increment_api_call(self, call_type: str = "generate_content"):
        """Increment and log API call count."""
        self.api_call_count += 1
        print(f"   📊 [API Call #{self.api_call_count}] {call_type}")

    def get_api_call_count(self):
        """Return total API calls made."""
        return self.api_call_count

    def generate_image_prompts(self, title: str, scenes: list) -> str:
        """
        제목과 대본(scenes)을 바탕으로 영어 이미지 프롬프트를 생성합니다.
        
        Args:
            title: 영상 제목
            scenes: 장면 목록 [{"scene_id": 1, "audio_text": "...", "duration": 7}, ...]
            
        Returns:
            JSON 형식의 이미지 프롬프트 문자열 (실패 시 None)
        """
        # 대본 텍스트 조합
        script_text = "\n".join([
            f"Scene {s['scene_id']}: {s['audio_text']}"
            for s in scenes
        ])
        
        prompt = IMAGE_GENERATION_PROMPT.format(
            title=title,
            script_text=script_text
        )
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Generating image prompts for title: {title}")
                if attempt == 1:
                    print(f"\n--- [DEBUG] Image Prompt Generation ---")
                    print(f"   제목: {title}")
                    print(f"   장면 수: {len(scenes)}")
                    print(f"----------------------------------------")
                else:
                    print(f"   🔄 재시도 중... ({attempt}/{MAX_RETRIES})")
                
                self._increment_api_call("Image Prompt Generation")
                response = self.client.models.generate_content(
                    model=TEXT_MODEL,
                    contents=[prompt],
                    config=types.GenerateContentConfig(
                        temperature=TEMPERATURE
                    )
                )
                return response.text
                
            except Exception as e:
                error_str = str(e)
                
                if attempt < MAX_RETRIES:
                    logger.warning(f"Image prompt generation failed (attempt {attempt}/{MAX_RETRIES}): {e}")
                    print(f"\n   ⚠️  [에러 발생] 재시도 대기 중... ({RETRY_DELAY}초)")
                    print(f"   원인: {error_str[:80]}...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    logger.error(f"Image prompt generation failed after {MAX_RETRIES} attempts: {e}")
                    print(f"\n{'❌'*25}")
                    print(f"  ❌ [치명적 에러] 이미지 프롬프트 생성 실패")
                    print(f"{'❌'*25}")
                    print(f"   {MAX_RETRIES}번 재시도 모두 실패")
                    print(f"   원인: {error_str}")
                    print(f"{'❌'*25}\n")
                    return None


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    generator = ImagePromptGenerator()
    # Test usage
    # prompts = generator.generate_image_prompts("테스트 제목", [{"scene_id": 1, "audio_text": "테스트", "duration": 3}])
    # print(prompts)
