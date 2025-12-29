"""
Gemini API 모델 설정 파일

모든 AI 모델 이름을 한 곳에서 관리합니다.
모델을 변경하려면 이 파일만 수정하면 됩니다.
"""

# ============================================
# 텍스트 생성 모델 (Gemini)
# ============================================
# 옵션: gemini-3-pro-preview, gemini-3-flash-preview, gemini-2.5-pro, gemini-2.5-flash
TEXT_MODEL = "gemini-3-flash-preview"

# ============================================
# 이미지 생성 모델 (Imagen)
# ============================================
# 옵션: imagen-4.0-fast-generate-001, imagen-4.0-generate-001
IMAGE_MODEL = "imagen-4.0-fast-generate-001"

# 이미지 네거티브 프롬프트 (텍스트/글자 생성 방지)
IMAGE_NEGATIVE_PROMPT = ", no text, no letters, no words, no writing, no signs, no labels"

# ============================================
# 음성 생성 모델 (TTS)
# ============================================
# 옵션: gemini-2.5-flash-preview-tts
TTS_MODEL = "gemini-2.5-flash-preview-tts"

# TTS 음성 설정
# 옵션: Kore (여성), Aoede (여성), Charon (남성), Fenrir (남성), Puck (남성)
TTS_VOICE = "Kore"

# ============================================
# API 호출 설정
# ============================================
# 재시도 횟수
MAX_RETRIES = 3

# 재시도 대기 시간 (초)
RETRY_DELAY = 5

# temperature 설정 (0.0 ~ 2.0, 높을수록 다양한 출력)
TEMPERATURE = 1.0

# ============================================
# 영상 품질 설정 (Video Quality)
# ============================================
# 해상도 (9:16 세로 영상)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920

# 프레임 레이트
VIDEO_FPS = 24

# 인코딩 설정
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"
VIDEO_PRESET = "medium"  # ultrafast, fast, medium, slow, veryslow

# 렌더링 스레드 수
VIDEO_THREADS = 4

# ============================================
# 이미지 생성 설정 (Image Generation)
# ============================================
# 병렬 처리 worker 수
IMAGE_MAX_WORKERS = 3
