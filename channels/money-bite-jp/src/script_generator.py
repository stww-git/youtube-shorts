"""
Money Bite 대본 생성기 모듈

금융 용어를 바탕으로 YouTube Shorts 대본을 생성합니다.
"""

import os
import sys
import re
import json
import time
import logging

# 채널 루트의 prompts.py 사용
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import genai
from google.genai import types
from shared.config.model_config import TEXT_MODEL, TEXT_FALLBACK_MODEL, MAX_RETRIES, RETRY_DELAY, TEMPERATURE
from prompts import SCRIPT_GENERATION_PROMPT, SUMMARY_GENERATION_PROMPT
from subtitle.prompts import get_subtitle_prompt
from subtitle.config import get_mode_setting

logger = logging.getLogger(__name__)


class ScriptGenerator:
    """금융 용어 기반 대본 생성기"""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "celestial-math-489909-f9")
        self.location = os.getenv("GCP_LOCATION", "global")
        
        self.api_call_count = 0
        self.client = genai.Client(vertexai=True, project=self.project_id, location=self.location)

    def _increment_api_call(self, call_type: str = "generate_content"):
        self.api_call_count += 1
        print(f"   📊 [API Call #{self.api_call_count}] {call_type}")

    def get_api_call_count(self):
        return self.api_call_count

    def generate_script(self, topic: dict) -> str:
        """
        금융 용어를 바탕으로 7줄 대본을 생성합니다.
        
        Args:
            topic: {"term": "PER 쉽게 설명"}
            
        Returns:
            JSON 형식의 대본 문자열 (실패 시 None)
        """
        term = topic.get('term', 'Finance Topic')
        
        prompt = SCRIPT_GENERATION_PROMPT.format(term=term)
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Generating script for: {term}")
                if attempt == 1:
                    print(f"\n--- [Script Generation] ---")
                    print(f"   용어: {term}")
                else:
                    print(f"   🔄 재시도 중... ({attempt}/{MAX_RETRIES})")
                
                self._increment_api_call("Script Generation")
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
                    logger.warning(f"Script generation failed (attempt {attempt}/{MAX_RETRIES}): {e}")
                    print(f"\n   ⚠️  [에러 발생] 재시도 대기 중... ({RETRY_DELAY}초)")
                    print(f"   원인: {error_str[:80]}...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
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
                    
                    logger.error(f"Script generation failed after {MAX_RETRIES} attempts: {e}")
                    print(f"\n{'❌'*25}")
                    print(f"  ❌ [치명적 에러] 대본 생성 실패")
                    print(f"{'❌'*25}")
                    return None

    def generate_summary(self, article_content: str) -> dict:
        """
        금융 용어 설명에서 카드 제목과 핵심 체크리스트를 추출합니다.
        
        Returns:
            dict: {"summary_title": "...", "checklist": [...]}
        """
        prompt = SUMMARY_GENERATION_PROMPT.format(
            article_content=article_content[:3000]
        )
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if attempt == 1:
                    print(f"\n   📝 [핵심 정보 카드] 제목 + 체크리스트 추출 중...")
                else:
                    print(f"   🔄 재시도 중... ({attempt}/{MAX_RETRIES})")
                
                self._increment_api_call("Summary Generation")
                response = self.client.models.generate_content(
                    model=TEXT_MODEL,
                    contents=[prompt],
                    config=types.GenerateContentConfig(
                        temperature=0.3
                    )
                )
                
                text = response.text
                json_match = re.search(r'\{[\s\S]*\}', text)
                if json_match:
                    data = json.loads(json_match.group())
                    summary_title = data.get('summary_title', '')
                    checklist = data.get('checklist', [])
                    print(f"   ✅ 카드 제목: {summary_title}")
                    print(f"   ✅ 체크리스트 {len(checklist)}개 추출 완료")
                    return {"summary_title": summary_title, "checklist": checklist}
                else:
                    print(f"   ⚠️ JSON 파싱 실패, 빈 데이터 반환")
                    return {"summary_title": "", "checklist": []}
                    
            except Exception as e:
                if attempt < MAX_RETRIES:
                    print(f"   ⚠️ 요약 생성 실패, 재시도 중...")
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"   ❌ 요약 생성 최종 실패: {e}")
                    return {"summary_title": "", "checklist": []}
        
        return {"summary_title": "", "checklist": []}

    def generate_subtitle_effects(self, scenes: list, single_font_size: int = 140, subtitle_mode: str = 'single') -> tuple:
        """
        AI가 대본을 분석하여 어절별 효과와 색상 키워드를 지정합니다.
        
        Args:
            scenes: 대본 scenes 리스트 [{scene_id, audio_text}, ...]
            single_font_size: 자막 폰트 크기 (글자 수 상한선 계산용)
            subtitle_mode: 자막 모드 (모드별 프롬프트 선택용)
            
        Returns:
            tuple: (effects_dict, color_keywords)
                - effects_dict: {scene_id: {"display": str, "words": [...]}}
                - color_keywords: {"#FFD700": ["keyword1", ...], ...}
        """
        script_lines = [f"{scene['scene_id']}. {scene['audio_text']}" for scene in scenes]
        script_text = "\n".join(script_lines)
        
        # 폰트 크기 기반 한 줄 최대 글자 수 계산 (화면 너비 1080px, 여백 감안 1000px)
        font_size = get_mode_setting(subtitle_mode, 'font_size', single_font_size)
        max_chunk_chars = int(1000 / font_size)
        
        # 모드별 프롬프트 선택
        prompt_template = get_subtitle_prompt(subtitle_mode)
        prompt = prompt_template.format(script_text=script_text, max_chunk_chars=max_chunk_chars)
        
        try:
            print(f"\n   🎨 [자막 효과 분석 중] AI가 어절별 효과를 판단합니다...")
            self._increment_api_call("Subtitle Effect Analysis")
            
            response = self.client.models.generate_content(
                model=TEXT_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    temperature=0.3
                )
            )
            
            result_text = response.text
            
            json_match = re.search(r'\{[\s\S]*"scenes"[\s\S]*\}', result_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                effect_scenes = data.get('scenes', [])
                color_keywords = data.get('color_keywords', {})
                
                result = {}
                for es in effect_scenes:
                    sid = es.get('scene_id')
                    result[sid] = {
                        'display': es.get('display', 'single'),
                        'words': es.get('words', [])
                    }
                
                total_effects = sum(
                    1 for es in effect_scenes 
                    for w in es.get('words', []) 
                    if w.get('effect')
                )
                color_count = sum(len(v) for v in color_keywords.values())
                print(f"   ✅ {len(effect_scenes)}개 장면, {total_effects}개 효과, {color_count}개 색상 키워드 지정 완료")
                return result, color_keywords
            else:
                print(f"   ⚠️ JSON 파싱 실패, 기본값 사용")
                return {}, {}
                
        except Exception as e:
            print(f"   ⚠️ 자막 효과 분석 실패: {e}")
            return {}, {}


# 파이프라인 호환을 위한 별칭 (제거 예정)
RecipeScriptGenerator = ScriptGenerator
