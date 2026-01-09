#!/usr/bin/env python3
"""
채널 목록 조회 스크립트

사용법:
    python3 list_channels.py

현재 등록된 모든 채널의 상태를 한눈에 확인합니다.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
CHANNELS_DIR = PROJECT_ROOT / "channels"
SCHEDULE_FILE = PROJECT_ROOT / ".github" / "schedule.yml"
MAIN_PY_FILE = PROJECT_ROOT / "main.py"


def get_channel_folders() -> list:
    """채널 폴더 목록"""
    channels = []
    for item in CHANNELS_DIR.iterdir():
        if item.is_dir() and not item.name.startswith('_'):
            channels.append(item.name)
    return sorted(channels)


def get_main_py_settings() -> dict:
    """main.py에서 채널 설정 읽기"""
    settings = {}
    
    with open(MAIN_PY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # CHANNELS 딕셔너리 파싱
    # 각 채널의 enabled, test_mode, upload 값 추출
    pattern = r'"([^"]+)":\s*\{([^}]+)\}'
    matches = re.findall(pattern, content)
    
    for channel_id, block in matches:
        if channel_id == "channel-id":  # 주석 템플릿 건너뛰기
            continue
            
        enabled = re.search(r'"enabled":\s*(True|False)', block)
        test_mode = re.search(r'"test_mode":\s*(True|False)', block)
        upload = re.search(r'"upload":\s*(True|False)', block)
        
        settings[channel_id] = {
            'enabled': enabled.group(1) if enabled else 'N/A',
            'test_mode': test_mode.group(1) if test_mode else 'N/A',
            'upload': upload.group(1) if upload else 'N/A',
        }
    
    return settings


def get_schedule_times() -> dict:
    """schedule.yml에서 스케줄 시간 읽기"""
    schedules = {}
    
    if not SCHEDULE_FILE.exists():
        return schedules
    
    with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 각 채널의 times 추출
    pattern = r'(\S+):\s*\n\s*name:[^\n]*\n\s*enabled:\s*(\w+)\s*\n\s*times:\s*\n((?:\s*-\s*"[^"]+"\s*\n)+)'
    matches = re.findall(pattern, content)
    
    for channel_id, enabled, times_block in matches:
        times = re.findall(r'"([^"]+)"', times_block)
        schedules[channel_id] = {
            'enabled': enabled,
            'times': times
        }
    
    return schedules


def display_channels():
    """채널 목록 표시"""
    
    folders = get_channel_folders()
    settings = get_main_py_settings()
    schedules = get_schedule_times()
    
    print()
    print("=" * 80)
    print("📺 채널 목록")
    print("=" * 80)
    print()
    print(f"{'채널 ID':<25} {'활성화':<8} {'테스트':<8} {'업로드':<8} {'스케줄 (KST)'}")
    print("-" * 80)
    
    for channel in folders:
        # main.py 설정
        ch_settings = settings.get(channel, {})
        enabled = ch_settings.get('enabled', 'N/A')
        test_mode = ch_settings.get('test_mode', 'N/A')
        upload = ch_settings.get('upload', 'N/A')
        
        # 활성화 상태 표시
        enabled_icon = "✅" if enabled == "True" else "❌" if enabled == "False" else "❓"
        test_icon = "🧪" if test_mode == "True" else "🎬" if test_mode == "False" else "❓"
        upload_icon = "⬆️" if upload == "True" else "💾" if upload == "False" else "❓"
        
        # 스케줄
        sch = schedules.get(channel, {})
        times = sch.get('times', [])
        schedule_str = ", ".join(times) if times else "설정 없음"
        
        print(f"{channel:<25} {enabled_icon:<8} {test_icon:<8} {upload_icon:<8} {schedule_str}")
    
    print("-" * 80)
    print()
    print("범례:")
    print("  활성화: ✅ = GitHub Actions 스케줄 실행 / ❌ = 스케줄 비활성화")
    print("  테스트: 🧪 = 테스트 모드 / 🎬 = 실제 이미지 생성")
    print("  업로드: ⬆️ = YouTube 업로드 / 💾 = 로컬 저장만")
    print()
    print(f"총 {len(folders)}개 채널")
    print()


def main():
    display_channels()


if __name__ == "__main__":
    main()
