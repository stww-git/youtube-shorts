"""
레시피 대본 생성기 모듈

요리 레시피를 바탕으로 YouTube Shorts 대본을 생성합니다.
"""

import os
import sys
import time
import logging

# 채널 루트의 prompts.py 사용
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import genai
from google.genai import types
from shared.config.model_config import TEXT_MODEL, TEXT_FALLBACK_MODEL, MAX_RETRIES, RETRY_DELAY, TEMPERATURE
from prompts import SCRIPT_GENERATION_PROMPT, SUMMARY_GENERATION_PROMPT
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

    def generate_script(self, column: dict) -> str:
        """
        건강 칼럼을 바탕으로 8줄 구조의 대본을 생성합니다.
        
        Args:
            column: 칼럼 딕셔너리 {title, content, source, author, ...}
            
        Returns:
            JSON 형식의 대본 문자열 (실패 시 None)
        """
        title = column.get('title', '건강 정보')
        content = column.get('content', '')
        
        prompt = SCRIPT_GENERATION_PROMPT.format(
            title=title,
            content=content
        )
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Generating script for: {title}")
                if attempt == 1:
                    print(f"\n--- [DEBUG] Health Script Generation ---")
                    print(f"   칼럼 제목: {title}")
                    print(f"   본문 길이: {len(content)}자")
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
                    # 기본 모델 모두 실패 시 fallback 모델로 시도
                    if TEXT_FALLBACK_MODEL:
                        print(f"\n   🔄 기본 모델 실패, fallback 모델({TEXT_FALLBACK_MODEL})로 재시도...")
                        try:
                            self._increment_api_call(f"Script Generation (Fallback: {TEXT_FALLBACK_MODEL})")
                            response = self.client.models.generate_content(
                                model=TEXT_FALLBACK_MODEL,
                                contents=[prompt],
                                config=types.GenerateContentConfig(
                                    temperature=TEMPERATURE
                                )
                            )
                            print(f"   ✅ Fallback 성공!")
                            return response.text
                        except Exception as fallback_e:
                            print(f"   ❌ Fallback도 실패: {fallback_e}")
                    
                    logger.error(f"Recipe script generation failed after {MAX_RETRIES} attempts: {e}")
                    print(f"\n{'❌'*25}")
                    print(f"  ❌ [치명적 에러] 대본 생성 실패")
                    print(f"{'❌'*25}")
                    print(f"   {MAX_RETRIES}번 재시도 모두 실패")
                    print(f"   원인: {error_str}")
                    print(f"{'❌'*25}\n")
                    return None

    def generate_summary(self, article_content: str) -> list:
        """
        건강 칼럼에서 핵심 체크리스트를 추출합니다.
        
        Args:
            article_content: 크롤링된 칼럼 본문
            
        Returns:
            체크리스트 문자열 리스트 (예: ["✓ 아침에 물 한 잔", ...])
        """
        prompt = SUMMARY_GENERATION_PROMPT.format(
            article_content=article_content[:3000]  # 토큰 제한
        )
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if attempt == 1:
                    print(f"\n   📝 [핵심 정보 카드] 체크리스트 추출 중...")
                else:
                    print(f"   🔄 재시도 중... ({attempt}/{MAX_RETRIES})")
                
                self._increment_api_call("Summary Generation")
                response = self.client.models.generate_content(
                    model=TEXT_MODEL,
                    contents=[prompt],
                    config=types.GenerateContentConfig(
                        temperature=0.3  # 낮은 온도로 정확한 추출
                    )
                )
                
                # JSON 파싱
                import re
                import json
                text = response.text
                # JSON 블록 추출
                json_match = re.search(r'\{[\s\S]*\}', text)
                if json_match:
                    data = json.loads(json_match.group())
                    checklist = data.get('checklist', [])
                    print(f"   ✅ 체크리스트 {len(checklist)}개 추출 완료")
                    return checklist
                else:
                    print(f"   ⚠️ JSON 파싱 실패, 빈 리스트 반환")
                    return []
                    
            except Exception as e:
                if attempt < MAX_RETRIES:
                    print(f"   ⚠️ 요약 생성 실패, 재시도 중...")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"   ❌ 요약 생성 최종 실패: {e}")
                    return []
        
        return []


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
