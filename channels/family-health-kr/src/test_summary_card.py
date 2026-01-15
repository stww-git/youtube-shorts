"""
핵심 정보 카드 테스트 스크립트
실행: cd src && python3 test_summary_card.py
결과: test_summary_card.png 이미지 생성
"""

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# 설정 파일에서 불러오기
from config.summary_card_config import (
    CARD_DURATION, MAX_ITEMS, FONT_SIZE, LINE_SPACING,
    TEXT_COLOR, TEXT_ALIGN, BG_IMAGE, BG_COLOR, FONT_FILE
)

# 비디오 크기
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920

# 테스트용 체크리스트
sample_checklist = [
    "1. 아침에 물 한 잔 마시기",
    "2. 발가락 스트레칭 10초",
    "3. 짠 음식 줄이기",
    "4. 하루 30분 걷기",
    "5. 잠들기 전 스마트폰 끄기"
]

def create_test_card():
    card_text = "\n".join(sample_checklist[:MAX_ITEMS])
    
    # 폰트 로드
    font = None
    if FONT_FILE:
        font_path = Path(__file__).resolve().parent.parent / "fonts" / FONT_FILE
        print(f"   📁 폰트 경로: {font_path}")
        print(f"   📁 존재 여부: {font_path.exists()}")
        
        if font_path.exists():
            font = ImageFont.truetype(str(font_path), FONT_SIZE)
            print(f"   ✅ 폰트 로드 성공: {FONT_FILE}")
        else:
            print(f"   ⚠️ 폰트 없음, 시스템 폰트 사용")
    
    if font is None:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/AppleGothic.ttf", FONT_SIZE)
        print(f"   📝 시스템 폰트 사용: AppleGothic")
    
    # 배경 이미지 로드
    if BG_IMAGE:
        bg_path = Path(__file__).parent.parent / "assets" / BG_IMAGE
        if bg_path.exists():
            img = Image.open(str(bg_path)).convert('RGB')
        else:
            img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), BG_COLOR)
    else:
        img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), BG_COLOR)
    
    draw = ImageDraw.Draw(img)
    
    # 텍스트 크기 계산
    bbox = draw.textbbox((0, 0), card_text, font=font, spacing=LINE_SPACING)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # 중앙 정렬
    x = (VIDEO_WIDTH - text_width) / 2
    y = (VIDEO_HEIGHT - text_height) / 2
    
    # 텍스트 그리기
    draw.multiline_text((x, y), card_text, font=font, fill=TEXT_COLOR, 
                        spacing=LINE_SPACING, align=TEXT_ALIGN)
    
    # 저장
    output_path = Path(__file__).parent / "test_summary_card.png"
    img.save(str(output_path))
    
    print(f"✅ 테스트 카드 생성: {output_path}")
    print(f"   크기: {VIDEO_WIDTH}x{VIDEO_HEIGHT}")
    print(f"   글자 크기: {FONT_SIZE}px")
    print(f"   줄 간격: {LINE_SPACING}px")
    print(f"   항목 수: {MAX_ITEMS}개")
    print(f"\n📝 설정 변경: src/config/summary_card_config.py")
    
    # 미리보기 열기 (macOS)
    os.system(f"open '{output_path}'")

if __name__ == "__main__":
    create_test_card()
