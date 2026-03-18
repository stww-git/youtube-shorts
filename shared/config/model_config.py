# Vertex AI 모델 설정 (GA 모델 - API 호출 가능 확인됨)
TEXT_MODEL = "gemini-2.5-pro"                            # 텍스트 최상위: 2.5 Pro (GA)
TEXT_FALLBACK_MODEL = "gemini-2.5-flash"                 # 텍스트 2순위: 2.5 Flash (GA)
IMAGE_MODEL = "gemini-2.5-flash-image"                   # 이미지 최상위: Gemini 2.5 Flash Image (GA)
IMAGE_FALLBACK_MODEL = "gemini-2.5-flash-image-preview"  # 이미지 2순위: Gemini 2.5 Flash Image Preview
TTS_MODEL = "gemini-2.5-pro-preview-tts"                 # TTS 최상위: 2.5 Pro TTS
TTS_FALLBACK_MODEL = "gemini-2.5-flash-preview-tts"      # TTS 2순위: 2.5 Flash TTS

# API 재시도 설정
MAX_RETRIES = 3
RETRY_DELAY = 2
TEMPERATURE = 0.7

# 비디오 설정
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
VIDEO_CODEC = 'libx264'
AUDIO_CODEC = 'aac'
VIDEO_PRESET = 'medium'
VIDEO_THREADS = 4
