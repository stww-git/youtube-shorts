"""
핵심 정보 카드 테스트 스크립트
summary_card_config.py 설정을 바로 확인할 수 있습니다.
"""

import sys
import os
from pathlib import Path

# 현재 디렉토리를 src로 설정 (config import를 위해)
os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

from motion_effects import MotionEffectsComposer

# 테스트용 체크리스트 (실제 영상에서 나올 법한 내용)
test_checklist = [
    "1. 미역 불린 물 버리지 않기",
    "2. 참기름 마지막에 넣기",
    "3. 간장2:설탕1 비율 기억",
    "4. 센불 1분 → 약불 10분",
]

composer = MotionEffectsComposer()
card_clip = composer._create_summary_card(test_checklist, duration=3.0)

if card_clip:
    # 첫 프레임을 이미지로 저장
    output_path = Path(__file__).parent.parent / "output" / "test_summary_card.png"
    output_path.parent.mkdir(exist_ok=True)
    
    frame = card_clip.get_frame(0)
    
    from PIL import Image
    img = Image.fromarray(frame)
    img.save(str(output_path))
    
    print(f"\n   ✅ 테스트 카드 저장 완료!")
    print(f"   📁 {output_path}")
    print(f"   💡 이 파일을 열어서 디자인을 확인하세요.")
    
    card_clip.close()
else:
    print("\n   ❌ 카드 생성 실패")
