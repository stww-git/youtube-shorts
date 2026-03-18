"""
레시피 대본 생성기 모듈

요리 레시피를 바탕으로 YouTube Shorts 대본을 생성합니다.
"""

import os
import time
import logging
from google import genai
from google.genai import types
from config.model_config import TEXT_MODEL, MAX_RETRIES, RETRY_DELAY, TEMPERATURE
from prompts import SCRIPT_GENERATION_PROMPT
from core.utils import format_ingredients, format_steps

logger = logging.getLogger(__name__)


class RecipeScriptGenerator:
    """요리 레시피 기반 대본 생성기"""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "celestial-math-489909-f9")
        self.location = os.getenv("GCP_LOCATION", "us-central1")
        
        self.api_call_count = 0
        self.client = genai.Client(vertexai=True, project=self.project_id, location=self.location)

    def _increment_api_call(self, call_type: str = "generate_content"):
        """Increment and log API call count."""
        self.api_call_count += 1
        print(f"   📊 [API Call #{self.api_call_count}] {call_type}")

    def get_api_call_count(self):
        """Return total API calls made."""
        return self.api_call_count

    def generate_script(self, recipe: dict) -> str:
        """
        레시피를 바탕으로 8줄 구조의 대본을 생성합니다.
        
        Args:
            recipe: 레시피 딕셔너리 {title, ingredients, steps, ...}
            
        Returns:
            JSON 형식의 대본 문자열 (실패 시 None)
        """
        title = recipe.get('title', '요리')
        steps = format_steps(recipe.get('steps', []))
        
        prompt = SCRIPT_GENERATION_PROMPT.format(
            title=title,
            steps=steps
        )
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Generating recipe script for: {title}")
                if attempt == 1:
                    print(f"\n--- [DEBUG] Recipe Script Generation ---")
                    print(f"   레시피: {title}")
                    print(f"   조리단계: {len(recipe.get('steps', []))}개")
                    print(f"----------------------------------------")
                else:
                    print(f"   🔄 재시도 중... ({attempt}/{MAX_RETRIES})")
                
                self._increment_api_call("Recipe Script Generation")
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
                    logger.warning(f"Recipe script generation failed (attempt {attempt}/{MAX_RETRIES}): {e}")
                    print(f"\n   ⚠️  [에러 발생] 재시도 대기 중... ({RETRY_DELAY}초)")
                    print(f"   원인: {error_str[:80]}...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    logger.error(f"Recipe script generation failed after {MAX_RETRIES} attempts: {e}")
                    print(f"\n{'❌'*25}")
                    print(f"  ❌ [치명적 에러] 대본 생성 실패")
                    print(f"{'❌'*25}")
                    print(f"   {MAX_RETRIES}번 재시도 모두 실패")
                    print(f"   원인: {error_str}")
                    print(f"{'❌'*25}\n")
                    return None


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    generator = RecipeScriptGenerator()
    # Test usage
    # test_recipe = {
    #     "title": "시금치무침",
    #     "ingredients": [{"name": "시금치", "amount": "1단"}, {"name": "소금", "amount": "1/2스푼"}],
    #     "steps": [{"step": 1, "description": "시금치를 깨끗이 씻어주세요"}]
    # }
    # script = generator.generate_script(test_recipe)
    # print(script)
