"""
자막 테스트 스크립트

MoviePy TextClip의 잘림 문제를 해결하기 위해
Pillow(PIL)를 사용하여 직접 자막을 그리는 방식으로 변경했습니다.
이 방식이 훨씬 안정적이고 깔끔하게 나옵니다.

사용법:
    python test_subtitle.py
"""

import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

# ============================================
#   📐 화면 크기 설정
# ============================================
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920

# ============================================
#   📝 테스트할 자막 텍스트
# ============================================
SUBTITLE_TEXT = "작은 팬에 올리브오일을 끓여 마늘 페페론치노를"

# ============================================
#   📍 자막 설정
# ============================================
SUBTITLE_Y_RATIO = 0.55   # 위치 (0.55 = 55%)
FONT_SIZE = 80
FONT_PATH = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
TEXT_COLOR = 'white'
STROKE_COLOR = 'black'
STROKE_WIDTH = 10
MAX_WIDTH = 960          # 줄바꿈 기준 너비

# ============================================

def draw_text_with_stroke(draw, text, x, y, font, text_color, stroke_color, stroke_width):
    # 테두리(stroke) 그리기
    if stroke_width > 0:
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx == 0 and dy == 0:
                    continue
                # 원형에 가깝게 그리기 위한 거리 체크 (선택 사항)
                if dx*dx + dy*dy > stroke_width*stroke_width:
                     continue
                draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
    
    # 메인 텍스트 그리기
    draw.text((x, y), text, font=font, fill=text_color)

def wrap_text(text, font, max_width):
    """너비에 맞춰 텍스트 줄바꿈"""
    dummy_img = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(dummy_img)
    
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        line_str = ' '.join(current_line)
        bbox = draw.textbbox((0, 0), line_str, font=font)
        width = bbox[2] - bbox[0]
        
        if width > max_width:
            if len(current_line) == 1:
                # 단어 하나가 이미 너무 긴 경우 그냥 넣음
                lines.append(current_line[0])
                current_line = []
            else:
                # 마지막 단어 제외하고 줄바꿈
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
        
    return lines

def main():
    print("🎬 자막 테스트 미리보기 (Pillow 방식)")
    print("=" * 50)
    
    # 1. 배경 생성
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), (50, 50, 50))
    draw = ImageDraw.Draw(img)
    
    # 2. 폰트 로드
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except:
        print("⚠️ 폰트 로드 실패, 기본 폰트 사용")
        font = ImageFont.load_default()
    
    # 3. 줄바꿈 계산
    lines = wrap_text(SUBTITLE_TEXT, font, MAX_WIDTH)
    
    # 4. 전체 텍스트 높이 계산 (줄간격 포함)
    line_spacing = 10  # 줄간격 픽셀
    total_text_height = 0
    line_heights = []
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        h = bbox[3] - bbox[1]
        line_heights.append(h)
        total_text_height += h
        
    total_text_height += line_spacing * (len(lines) - 1)
    
    # 5. 그리기 시작 위치 (Y) 계산
    # 기준 위치(SUBTITLE_Y_RATIO)가 텍스트 박스의 "상단"이 되도록 할지, "중앙"이 되도록 할지 결정
    # 여기서는 "중앙" 정렬로 구현
    base_y = int(VIDEO_HEIGHT * SUBTITLE_Y_RATIO)
    start_y = base_y - (total_text_height // 2)
    
    print(f"📝 텍스트: {SUBTITLE_TEXT[:30]}...")
    print(f"📊 줄바꿈 결과: {len(lines)}줄")
    for i, l in enumerate(lines):
        print(f"   [{i+1}] {l}")
        
    # 6. 한 줄씩 그리기
    current_y = start_y
    for i, line in enumerate(lines):
        # 가로 중앙 정렬
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - w) // 2
        
        draw_text_with_stroke(draw, line, x, current_y, font, TEXT_COLOR, STROKE_COLOR, STROKE_WIDTH)
        
        current_y += line_heights[i] + line_spacing
        
    # 7. 가이드라인 (선택)
    draw.line([(0, base_y), (VIDEO_WIDTH, base_y)], fill=(255, 255, 0, 128), width=1)
    draw.text((10, base_y - 20), f"Center Y: {base_y}px", fill='yellow')
    
    # 영역 박스 표시
    box_top = start_y - 10
    box_bottom = current_y + 10
    box_left = (VIDEO_WIDTH - MAX_WIDTH) // 2
    box_right = (VIDEO_WIDTH + MAX_WIDTH) // 2
    
    draw.rectangle([box_left, box_top, box_right, box_bottom], outline=(100, 100, 255), width=2)
    
    # 저장
    os.makedirs("output", exist_ok=True)
    output_path = "output/test_subtitle_pillow.png"
    img.save(output_path)
    
    print(f"\n✅ 완료! → {output_path}")
    subprocess.run(["open", output_path])

if __name__ == "__main__":
    main()
