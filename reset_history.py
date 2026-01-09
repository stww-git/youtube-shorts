#!/usr/bin/env python3
"""
recipe_history.json 초기화 스크립트

사용법:
    python3 reset_history.py                  # 모든 채널 목록 표시
    python3 reset_history.py <channel_id>     # 특정 채널 초기화

각 채널의 recipe_history.json 파일을 빈 상태로 초기화합니다.
이미 사용한 레시피 기록이 모두 삭제되므로 주의하세요.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
CHANNELS_DIR = PROJECT_ROOT / "channels"


def get_channels():
    """채널 목록 반환"""
    channels = []
    for d in CHANNELS_DIR.iterdir():
        if d.is_dir() and not d.name.startswith('_'):
            channels.append(d.name)
    return sorted(channels)


def reset_history(channel_id: str):
    """특정 채널의 recipe_history.json 초기화"""
    
    channel_dir = CHANNELS_DIR / channel_id
    history_file = channel_dir / "history.json"
    
    if not channel_dir.exists():
        print(f"❌ 채널 '{channel_id}'이(가) 존재하지 않습니다.")
        print(f"\n사용 가능한 채널:")
        for ch in get_channels():
            print(f"   - {ch}")
        return False
    
    # 기존 데이터 백업 정보
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
        old_count = len(old_data.get('used_recipes', []))
        print(f"📊 [{channel_id}] 현재 기록: {old_count}개 레시피")
    else:
        old_count = 0
        print(f"📊 [{channel_id}] 기존 파일 없음")
    
    # 확인
    confirm = input(f"\n⚠️  정말 '{channel_id}' 채널의 기록을 초기화하시겠습니까? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ 초기화가 취소되었습니다.")
        return False
    
    # 초기화
    empty_data = {
        "used_recipes": [],
        "last_updated": datetime.now().isoformat()
    }
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(empty_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ [{channel_id}] recipe_history.json 초기화 완료!")
    print(f"   삭제된 레시피: {old_count}개")
    print(f"   파일 위치: {history_file}")
    
    return True


def main():
    if len(sys.argv) < 2:
        print("사용법: python3 reset_history.py <channel_id>")
        print("\n사용 가능한 채널:")
        for ch in get_channels():
            history_file = CHANNELS_DIR / ch / "recipe_history.json"
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                count = len(data.get('used_recipes', []))
            else:
                count = 0
            print(f"   - {ch} ({count}개 레시피)")
        sys.exit(0)
    
    channel_id = sys.argv[1]
    reset_history(channel_id)


if __name__ == "__main__":
    main()
