"""
로컬 히스토리(history.local.json) 초기화 스크립트

이 스크립트는 로컬 환경에서만 사용되는 history.local.json을 초기화합니다.
원격(GitHub Actions)에서 사용하는 history.json은 건드리지 않습니다.
"""

from pathlib import Path
import json

# 채널 디렉토리
CHANNEL_DIR = Path(__file__).parent
LOCAL_HISTORY_FILE = CHANNEL_DIR / "history.local.json"

def reset_local_history():
    """로컬 히스토리 파일 초기화"""
    channel_name = CHANNEL_DIR.name
    
    if LOCAL_HISTORY_FILE.exists():
        # 기존 파일 백업
        backup_path = CHANNEL_DIR / "history.local.backup.json"
        LOCAL_HISTORY_FILE.rename(backup_path)
        print(f"   📦 기존 파일 백업: {backup_path.name}")
    
    # 빈 히스토리로 초기화
    empty_history = {
        "used_recipes": [],
        "last_updated": None
    }
    
    with open(LOCAL_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(empty_history, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ [{channel_name}] 로컬 히스토리 초기화 완료!")
    print(f"   📄 파일: {LOCAL_HISTORY_FILE}")
    print(f"   ⚠️  원격용 history.json은 변경되지 않았습니다.")

if __name__ == "__main__":
    reset_local_history()
