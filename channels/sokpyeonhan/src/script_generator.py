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
from config.model_config import TEXT_MODEL, TEXT_FALLBACK_MODEL, MAX_RETRIES, RETRY_DELAY, TEMPERATURE
from prompts import SCRIPT_GENERATION_PROMPT, SUMMARY_GENERATION_PROMPT, KICK_ANALYSIS_PROMPT
from subtitle.prompts import get_subtitle_prompt
from subtitle.config import get_mode_setting
from core.utils import format_ingredients, format_steps
import re
import json

logger = logging.getLogger(__name__)


class RecipeScriptGenerator:
    """요리 레시피 기반 대본 생성기"""
    
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

    def analyze_kick(self, recipe: dict, min_confidence: int = 5) -> dict:
        """
        레시피에 Kick(핵심 비법)이 있는지 분석합니다.
        
        Args:
            recipe: 레시피 딕셔너리
            min_confidence: 최소 신뢰도 (이 이하면 Kick 없음으로 판단)
            
        Returns:
            {
                "has_kick": bool,
                "confidence": int,
                "kick_candidate": str,
                "reason": str
            }
        """
        title = recipe.get('title', '요리')
        steps = format_steps(recipe.get('steps', []))
        
        prompt = KICK_ANALYSIS_PROMPT.format(
            title=title,
            steps=steps
        )
        
        try:
            print(f"\n   🔍 [Kick 분석 중] {title}")
            self._increment_api_call("Kick Analysis")
            
            response = self.client.models.generate_content(
                model=TEXT_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    temperature=0.3  # 분석용이므로 낮은 temperature
                )
            )
            
            result_text = response.text
            
            # JSON 추출
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                result = json.loads(json_match.group(0))
                
                # confidence 기반으로 has_kick 재조정
                confidence = result.get("confidence", 0)
                if confidence <= min_confidence:
                    result["has_kick"] = False
                
                print(f"      Kick: {result.get('kick_candidate', 'N/A')}")
                print(f"      신뢰도: {confidence}/10")
                print(f"      판단: {'✅ 사용 가능' if result.get('has_kick') else '❌ 스킵'}")
                print(f"      이유: {result.get('reason', '')}")
                
                return result
            else:
                print(f"      ⚠️ JSON 파싱 실패")
                return {"has_kick": True, "confidence": 5, "kick_candidate": "", "reason": "파싱 실패, 기본값 사용"}
                
        except Exception as e:
            print(f"      ⚠️ Kick 분석 실패: {e}")
            return {"has_kick": True, "confidence": 5, "kick_candidate": "", "reason": f"분석 실패: {e}"}

    def generate_script(self, recipe: dict, kick: str = "") -> str:
        """
        레시피를 바탕으로 7줄 구조의 대본을 생성합니다.
        
        Args:
            recipe: 레시피 딕셔너리 {title, ingredients, steps, ...}
            kick: 이미 분석된 Kick (핵심 비법). 제공되면 재분석하지 않음.
            
        Returns:
            JSON 형식의 대본 문자열 (실패 시 None)
        """
        title = recipe.get('title', '요리')
        steps = format_steps(recipe.get('steps', []))
        
        prompt = SCRIPT_GENERATION_PROMPT.format(
            title=title,
            steps=steps,
            kick=kick if kick else "(분석된 Kick 없음 - 직접 찾아서 사용)"
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

    def generate_summary(self, article_content: str, kick: str = "") -> dict:
        """
        레시피에서 카드 제목과 핵심 체크리스트를 추출합니다.
        
        Args:
            article_content: 레시피 정보 (조리 단계 등)
            kick: 대본 Scene 7에서 강조한 핵심 비법
            
        Returns:
            dict: {"summary_title": "...", "checklist": [...]}
        """
        prompt = SUMMARY_GENERATION_PROMPT.format(
            article_content=article_content[:3000],  # 토큰 제한
            kick=kick if kick else "레시피의 핵심 포인트를 찾아주세요"
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
        # 대본 텍스트 생성
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
            
            # JSON 파싱
            json_match = re.search(r'\{[\s\S]*"scenes"[\s\S]*\}', result_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                effect_scenes = data.get('scenes', [])
                color_keywords = data.get('color_keywords', {})
                
                # scene_id 기반 딕셔너리로 변환
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
