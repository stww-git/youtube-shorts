"""
채널 전용 프롬프트 파일

이 파일에 정의된 프롬프트가 기본 프롬프트(src/prompts.py) 대신 사용됩니다.
config.yaml에서 prompts.use_custom: true로 설정해야 적용됩니다.

사용하지 않을 프롬프트는 None으로 설정하면 기본 프롬프트가 사용됩니다.
"""

# 대본 생성 프롬프트 (None이면 기본 프롬프트 사용)
RECIPE_SCRIPT_GENERATION_PROMPT = None

# 제목 생성 프롬프트 (None이면 기본 프롬프트 사용)
RECIPE_TITLE_GENERATION_PROMPT = None

# 이미지 프롬프트 생성 프롬프트 (None이면 기본 프롬프트 사용)
IMAGE_PROMPT_GENERATION_PROMPT = None
