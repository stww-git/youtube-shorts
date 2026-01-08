"""
자막 스타일 테스트 스크립트

채널의 motion_effects 설정을 사용하여 자막 스타일을 테스트합니다.
"""

import sys
from pathlib import Path

# 채널 src 디렉토리를 sys.path에 추가
CHANNEL_SRC_DIR = Path(__file__).parent
PROJECT_ROOT = CHANNEL_SRC_DIR.parent.parent.parent
sys.path.insert(0, str(CHANNEL_SRC_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from motion_effects import MotionEffectsComposer
from config.subtitle_config import get_subtitle_style
from PIL import Image

# 고정 샘플 문장들 (자막용)
SAMPLE_SUBTITLES = [
    "아주 긴 자막 문장을 사용했을 때 줄바꿈과 표시가 어떻게 되는지 확인하는 테스트입니다"
]


def run_test():
    """자막 스타일 테스트를 실행합니다."""
    print("🎬 자막 스타일 테스트 시작\n")
    
    composer = MotionEffectsComposer()
    style = get_subtitle_style(False)
    
    for idx, subtitle in enumerate(SAMPLE_SUBTITLES, 1):
        try:
            # 자막 이미지 생성 (임시 파일 경로 반환)
            img_path = composer._create_subtitle_image(subtitle, style)
            
            if img_path:
                img = Image.open(img_path)
                
                # 검은 배경에 합성하여 보여주기 (투명도 확인용)
                bg = Image.new('RGB', img.size, (50, 50, 50))
                bg.paste(img, (0, 0), img)
                bg.show()
                
                print(f"✅ 테스트 {idx}: '{subtitle[:25]}...' → 이미지 창 표시됨")
            else:
                print(f"❌ 테스트 {idx} 실패: 이미지 생성 안됨")
                
        except Exception as e:
            print(f"❌ 테스트 {idx} 실패: {e}")
    
    print("🎬 테스트 완료!")


if __name__ == "__main__":
    run_test()
