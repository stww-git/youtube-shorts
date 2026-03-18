"""
금융 영상 제목 생성기 모듈

금융 용어를 바탕으로 클릭 유도 제목을 생성합니다.
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
from prompts import TITLE_GENERATION_PROMPT

logger = logging.getLogger(__name__)


class TitleGenerator:
    """금융 용어 기반 영상 제목 생성기"""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "celestial-math-489909-f9")
        self.location = os.getenv("GCP_LOCATION", "us-central1")
        
        self.api_call_count = 0
        self.client = genai.Client(vertexai=True, project=self.project_id, location=self.location)

    def _increment_api_call(self, call_type: str = "generate_content"):
        self.api_call_count += 1
        print(f"   📊 [API Call #{self.api_call_count}] {call_type}")

    def get_api_call_count(self):
        return self.api_call_count
    
    def generate_title(self, topic: dict, scenes: list = None) -> str:
        """
        금융 용어와 대본을 바탕으로 클릭 유도 제목을 생성합니다.
        
        Args:
            topic: {"term": "PER 쉽게 설명"}
            scenes: 대본 scenes 리스트 [{scene_id, audio_text}, ...]
            
        Returns:
            생성된 제목 문자열 (실패 시 용어 그대로 반환)
        """
        term = topic.get('term', '금융 용어')
        
        # 대본 내용 구성
        script_content = ""
        if scenes:
            script_lines = [f"{scene['scene_id']}번: {scene['audio_text']}" for scene in scenes]
            script_content = "\n".join(script_lines)
        
        prompt = TITLE_GENERATION_PROMPT.format(term=term, script_content=script_content)
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Generating title for: {term}")
                if attempt == 1:
                    print(f"\n--- [Title Generation] ---")
                    print(f"   용어: {term}")
                else:
                    print(f"   🔄 재시도 중... ({attempt}/{MAX_RETRIES})")
                
                self._increment_api_call("Title Generation")
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
                    if TEXT_FALLBACK_MODEL:
                        print(f"\n   🔄 기본 모델 실패, fallback 모델({TEXT_FALLBACK_MODEL})로 재시도...")
                        try:
                            self._increment_api_call(f"Title Generation (Fallback: {TEXT_FALLBACK_MODEL})")
                            response = self.client.models.generate_content(
                                model=TEXT_FALLBACK_MODEL,
                                contents=[prompt],
                                config=types.GenerateContentConfig(
                                    temperature=TEMPERATURE,
                                    max_output_tokens=1024,
                                )
                            )
                            generated_title = response.text.strip()
                            generated_title = generated_title.replace('**', '')
                            generated_title = generated_title.strip('"\'')
                            generated_title = generated_title.strip()
                            if '\n' in generated_title:
                                for line in generated_title.split('\n'):
                                    line = line.strip()
                                    if line and len(line) >= 5:
                                        generated_title = line
                                        break
                            print(f"   ✅ Fallback 성공: {generated_title}")
                            return generated_title
                        except Exception as fallback_e:
                            print(f"   ❌ Fallback도 실패: {fallback_e}")
                    
                    logger.error(f"Title generation failed after {MAX_RETRIES} attempts: {e}")
                    print(f"\n   ⚠️ 제목 생성 실패, 원본 용어 사용: {term}")
                    return term


# 파이프라인 호환을 위한 별칭 (제거 예정)
RecipeTitleGenerator = TitleGenerator
