# Gemini API 모델 설정
TEXT_MODEL = "gemini-2.0-flash"
IMAGE_MODEL = "imagen-4.0-fast-generate-001"
TTS_MODEL = "gemini-2.5-flash-preview-tts"

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
