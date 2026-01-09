#!/usr/bin/env python3
"""
이 채널의 history.json 초기화

사용법:
    python3 reset_history.py
"""

import json
from pathlib import Path
from datetime import datetime

CHANNEL_DIR = Path(__file__).parent
HISTORY_FILE = CHANNEL_DIR / "history.json"


def reset_history():
    """history.json 초기화"""
    
    channel_name = CHANNEL_DIR.name
    
    # 기존 데이터 확인
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
        old_count = len(old_data.get('used_recipes', []))
        print(f"📊 [{channel_name}] 현재 기록: {old_count}개 항목")
    else:
        old_count = 0
        print(f"📊 [{channel_name}] 기존 파일 없음")
    
    # 확인
    confirm = input(f"\n⚠️  정말 '{channel_name}' 채널의 기록을 초기화하시겠습니까? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ 초기화가 취소되었습니다.")
        return False
    
    # 초기화
    empty_data = {
        "used_recipes": [],
        "last_updated": datetime.now().isoformat()
    }
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(empty_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ [{channel_name}] history.json 초기화 완료!")
    print(f"   삭제된 항목: {old_count}개")
    
    return True


if __name__ == "__main__":
    reset_history()
