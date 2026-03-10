# 이미지 생성 설정
IMAGE_NEGATIVE_PROMPT = "text, watermark, logo, blurry, low quality, realistic, 3D rendering, gradient, photographic, complex shading"
IMAGE_MAX_WORKERS = 1  # Rate limit 방지를 위해 순차 처리

# 해상도 설정 (gemini-3.1-flash-image-preview 전용, gemini-2.5-flash-image는 미지원)
# 옵션: "512", "1K", "2K", "4K" (대문자 K 필수, 512만 K 없음)
IMAGE_SIZE = "1K"

# 재시도 설정
IMAGE_MAX_RETRIES = 3           # 최대 재시도 횟수
IMAGE_RETRY_BASE_DELAY = 5     # 첫 재시도 대기 시간 (초)
IMAGE_REQUEST_DELAY = 2        # 이미지 요청 간 대기 시간 (초)
