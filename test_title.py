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
TITLE_TEXT = "오징어무국 오징어 처음부터 넣지 마세요"

# 폰트 설정
FONT_PATH = os.path.join(os.getcwd(), "fonts/Gungseouche.ttf")
FONT_SIZE = 100  # 글자 크기 (px)

# 자간 설정 (핵심!)
# -10: 아주 좁게
# -5: 좁게 (기본값)
# 0: 원래대로
# +5: 넓게
LETTER_SPACING = -30

# 색상 설정
TEXT_COLOR = 'white'       # 글자 색 (white, yellow, #FFD700 등)
STROKE_COLOR = 'black'     # 테두리 색
STROKE_WIDTH = 0           # 테두리 두께

# 최대 너비 (자동 줄바꿈)
MAX_WIDTH = 800

# 줄간격 설정
# 1.0: 빼곡하게
# 1.3: 기본
# 1.5: 약간 넓게
# 2.0: 아주 넓게
LINE_HEIGHT = 1.0

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
