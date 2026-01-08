#!/usr/bin/env python3
"""
테스트 모드용 플레이스홀더 이미지 생성 스크립트.
실행 후 assets/test_images/test_placeholder.png 파일이 생성됩니다.
"""
from PIL import Image, ImageDraw
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
WIDTH, HEIGHT = 1080, 1920
COLOR = (30, 30, 60)  # 진한 네이비

def create_test_image(width, height, color):
    """단순한 테스트용 이미지 생성 (대본 텍스트 없음)"""
    img = Image.new('RGB', (width, height), color)
    d = ImageDraw.Draw(img)
    
    # 중앙에 원 그리기 (시각적 구분)
    center_x, center_y = width // 2, height // 2
    radius = 200
    lighter_color = tuple(min(c + 40, 255) for c in color)
    d.ellipse(
        [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
        fill=lighter_color,
        outline=None
    )
    
    return img

def main():
    print(f"🖼️  테스트용 이미지 생성 중...")
    
    img = create_test_image(WIDTH, HEIGHT, COLOR)
    output_path = os.path.join(OUTPUT_DIR, "test_placeholder.png")
    img.save(output_path)
    
    print(f"   ✅ test_placeholder.png 생성 완료")
    print(f"\n✅ 테스트 이미지 생성 완료: {output_path}")

if __name__ == "__main__":
    main()
