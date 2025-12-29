"""
제목 생성 테스트 스크립트

이 스크립트로 다양한 자간, 폰트 크기, 색상 등을 미리 확인할 수 있습니다.
수정 후 실행하면 바로 이미지로 결과를 볼 수 있습니다.

사용법:
    python test_title.py
"""

import os
import subprocess
from src.title_generator import create_title_image

# ========================================
#   👇 여기를 수정해서 테스트하세요! 👇
# ========================================

# 제목 텍스트
TITLE_TEXT = "카레 돼지고기 바로 볶기 절대 이렇게 하지마세요"

# 폰트 설정
# 폰트 설정
from src.config.title_config import (
    TITLE_FONT_PATH,
    TITLE_TEXT_COLOR,
    TITLE_STROKE_COLOR,
    TITLE_STROKE_WIDTH,
    TITLE_LETTER_SPACING,
    TITLE_MAX_WIDTH,
    TITLE_LINE_HEIGHT,
    get_adaptive_title_style
)

FONT_PATH = TITLE_FONT_PATH
FONT_SIZE = 100  # 기본값 (테스트용)

# 자간 설정
LETTER_SPACING = TITLE_LETTER_SPACING

# 색상 설정
TEXT_COLOR = TITLE_TEXT_COLOR
STROKE_COLOR = TITLE_STROKE_COLOR
STROKE_WIDTH = TITLE_STROKE_WIDTH

# 최대 너비
MAX_WIDTH = TITLE_MAX_WIDTH

# 줄간격 설정
LINE_HEIGHT = TITLE_LINE_HEIGHT

# ========================================


def main():
    print("🎨 제목 이미지 생성 중...")
    print(f"   텍스트: {TITLE_TEXT}")
    print(f"   자간: {LETTER_SPACING}px")
    print(f"   폰트 크기: {FONT_SIZE}px")
    
    # 제목 이미지 생성
    image_path = create_title_image(
        text=TITLE_TEXT,
        font_size=FONT_SIZE,
        letter_spacing=LETTER_SPACING,
        text_color=TEXT_COLOR,
        stroke_color=STROKE_COLOR,
        stroke_width=STROKE_WIDTH,
        max_width=MAX_WIDTH,
        line_height=LINE_HEIGHT,
        font_path=FONT_PATH
    )
    
    # 결과 파일을 output 폴더에 복사
    output_path = "output/test_title.png"
    os.makedirs("output", exist_ok=True)
    
    import shutil
    shutil.copy(image_path, output_path)
    
    print(f"\n✅ 생성 완료!")
    print(f"   저장 위치: {output_path}")
    
    # Mac에서 미리보기로 열기
    print("\n🖼️  이미지 열기...")
    subprocess.run(["open", output_path])


if __name__ == "__main__":
    main()
