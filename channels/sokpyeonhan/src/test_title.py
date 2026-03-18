"""
제목 스타일 테스트 스크립트

채널의 motion_effects 설정을 사용하여 제목 스타일을 테스트합니다.
"""

import sys
from pathlib import Path

# 채널 src 디렉토리를 sys.path에 추가
CHANNEL_SRC_DIR = Path(__file__).parent
PROJECT_ROOT = CHANNEL_SRC_DIR.parent.parent.parent
sys.path.insert(0, str(CHANNEL_SRC_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from shared.title_image_generator import create_title_image

# 고정 샘플 문장들
SAMPLE_TITLES = [
    "안동찜닭 당면 넣을 때 절대 이렇게 하지 마세요"
]


def run_test():
    """제목 스타일 테스트를 실행합니다."""
    print("🎬 제목 스타일 테스트 시작\n")
    

    
    for idx, title in enumerate(SAMPLE_TITLES, 1):
        try:
            # create_title_image는 임시 파일 경로를 반환함
            temp_path = create_title_image(title)
            
            # 저장하지 않고 바로 표시
            from PIL import Image
            img = Image.open(temp_path)
            img.show()
            
            print(f"✅ 테스트 {idx}: '{title[:25]}...' → 이미지 창 표시됨")
        except Exception as e:
            print(f"❌ 테스트 {idx} 실패: {e}")
    
    print("🎬 테스트 완료!")


if __name__ == "__main__":
    run_test()
