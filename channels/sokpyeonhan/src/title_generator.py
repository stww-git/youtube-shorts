"""
레시피 제목 생성기 모듈

레시피 정보를 바탕으로 바이럴 제목을 생성합니다.
"""

import os
import sys
import time
import logging

# 채널 루트의 prompts.py 사용
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import genai
from google.genai import types
from config.model_config import TEXT_MODEL, MAX_RETRIES, RETRY_DELAY, TEMPERATURE
from prompts import TITLE_GENERATION_PROMPT

logger = logging.getLogger(__name__)


class RecipeTitleGenerator:
    """레시피 기반 바이럴 제목 생성기"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not found in environment variables.")
        
        self.client = None
        self.api_call_count = 0
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    def _increment_api_call(self, call_type: str = "generate_content"):
        """Increment and log API call count."""
        self.api_call_count += 1
        print(f"   📊 [API Call #{self.api_call_count}] {call_type}")

    def get_api_call_count(self):
        """Return total API calls made."""
        return self.api_call_count
    
    def generate_title(self, recipe: dict, scenes: list = None) -> str:
        """
        대본 내용을 바탕으로 바이럴 제목을 생성합니다.
        
        Args:
            recipe: 레시피 딕셔너리 {title, ingredients, steps, ...}
            scenes: 대본 scenes 리스트 (대본 기반 제목 생성)
            
        Returns:
            생성된 제목 문자열 (실패 시 원본 제목 반환)
        """
        original_title = recipe.get('title', '요리')
        
        # 대본 내용을 문자열로 변환
        if scenes:
            script_lines = []
            for scene in scenes:
                script_lines.append(f"{scene['scene_id']}번: {scene['audio_text']}")
            script_content = "\n".join(script_lines)
        else:
            # scenes가 없으면 빈 문자열 (fallback)
            script_content = "(대본 없음)"
        
        prompt = TITLE_GENERATION_PROMPT.format(
            title=original_title,
            script_content=script_content
        )
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Generating title for: {original_title}")
                if attempt == 1:
                    print(f"\n--- [DEBUG] Recipe Title Generation ---")
                    print(f"   원본 제목: {original_title}")
                    print(f"----------------------------------------")
                else:
                    print(f"   🔄 재시도 중... ({attempt}/{MAX_RETRIES})")
                
                self._increment_api_call("Recipe Title Generation")
                response = self.client.models.generate_content(
                    model=TEXT_MODEL,
                    contents=[prompt],
                    config=types.GenerateContentConfig(
                        temperature=TEMPERATURE,
                        max_output_tokens=1024,
                    )
                )
                
                # 제목 정리
                generated_title = response.text.strip()
                generated_title = generated_title.replace('**', '')
                generated_title = generated_title.strip('"\'')
                generated_title = generated_title.strip()
                
                # 여러 줄인 경우 첫 번째 줄만
                if '\n' in generated_title:
                    for line in generated_title.split('\n'):
                        line = line.strip()
                        if line and len(line) >= 5:
                            generated_title = line
                            break
                

                
                print(f"   ✅ 생성된 제목: {generated_title}")
                return generated_title
                
            except Exception as e:
                error_str = str(e)
                
                if attempt < MAX_RETRIES:
                    logger.warning(f"Title generation failed (attempt {attempt}/{MAX_RETRIES}): {e}")
                    print(f"\n   ⚠️  [에러 발생] 재시도 대기 중... ({RETRY_DELAY}초)")
                    print(f"   원인: {error_str[:80]}...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    logger.error(f"Title generation failed after {MAX_RETRIES} attempts: {e}")
                    print(f"\n   ⚠️ 제목 생성 실패, 원본 제목 사용: {original_title}")
                    return original_title


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    generator = RecipeTitleGenerator()
    # Test usage
    # test_recipe = {
    #     "title": "백선생 시금치무침 만드는법 초간단",
    #     "ingredients": [{"name": "시금치", "amount": "1단"}],
    #     "steps": [{"step": 1, "description": "시금치를 깨끗이 씻어주세요"}]
    # }
    # title = generator.generate_title(test_recipe)
    # print(title)
