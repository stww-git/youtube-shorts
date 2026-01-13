#!/usr/bin/env python3
"""
채널 삭제 스크립트

사용법:
    1. 아래 CHANNEL_ID 수정
    2. python3 remove_channel.py 실행

자동으로 처리되는 작업:
    1. channels/{채널ID}/ 폴더 삭제
    2. main.py CHANNELS에서 제거
    3. .github/schedule.yml에서 제거
    4. .github/workflows/auto_upload.yml에서 job 제거
"""

# ============================================
# 🎯 삭제할 채널 ID를 입력하세요
# ============================================
CHANNEL_ID = "tvtv"
# ============================================

import os
import sys
import shutil
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
CHANNELS_DIR = PROJECT_ROOT / "channels"
SCHEDULE_FILE = PROJECT_ROOT / ".github" / "schedule.yml"
WORKFLOW_FILE = PROJECT_ROOT / ".github" / "workflows" / "auto_upload.yml"
MAIN_PY_FILE = PROJECT_ROOT / "main.py"


def remove_channel_folder(channel_id: str) -> bool:
    """채널 폴더 삭제"""
    channel_dir = CHANNELS_DIR / channel_id
    
    if not channel_dir.exists():
        print(f"   ❌ 채널 폴더가 존재하지 않습니다: {channel_dir}")
        return False
    
    shutil.rmtree(channel_dir)
    print(f"   ✅ 폴더 삭제: {channel_dir}")
    return True


def remove_from_main_py(channel_id: str):
    """main.py CHANNELS에서 채널 제거"""
    with open(MAIN_PY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 채널 블록 패턴 매칭 및 제거
    # "channel-id": { ... }, 형태
    pattern = rf'\n\s*"{re.escape(channel_id)}":\s*\{{[^}}]+\}},?'
    new_content = re.sub(pattern, '', content)
    
    if content != new_content:
        with open(MAIN_PY_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"   ✅ main.py CHANNELS에서 제거")
    else:
        print(f"   ⚠️  main.py에서 채널을 찾을 수 없음")


def remove_from_schedule_yml(channel_id: str):
    """schedule.yml에서 채널 스케줄 제거"""
    if not SCHEDULE_FILE.exists():
        print(f"   ⚠️  schedule.yml 파일이 없습니다")
        return
    
    with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 채널 블록 제거
    pattern = rf'\n  {re.escape(channel_id)}:\n.*?(?=\n  \w+:|$)'
    new_content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    if content != new_content:
        with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"   ✅ schedule.yml에서 제거")
    else:
        print(f"   ⚠️  schedule.yml에서 채널을 찾을 수 없음")


def remove_from_workflow_yml(channel_id: str):
    """auto_upload.yml에서 job 제거"""
    if not WORKFLOW_FILE.exists():
        print(f"   ⚠️  auto_upload.yml 파일이 없습니다")
        return
    
    with open(WORKFLOW_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    skip_until_next_job = False
    removed_crons = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 1. cron 스케줄 주석과 해당 cron 줄들 제거
        if f'# {channel_id}:' in line:
            # 주석 줄 스킵
            i += 1
            # 이어지는 cron 줄들 스킵하고 기록
            while i < len(lines) and lines[i].strip().startswith('- cron:'):
                cron_match = re.search(r"'([^']+)'", lines[i])
                if cron_match:
                    removed_crons.append(cron_match.group(1))
                i += 1
            continue
        
        # 2. workflow_dispatch options에서 제거
        if line.strip() == f'- {channel_id}':
            i += 1
            continue
        
        # 3. jobs 섹션에서 해당 채널 job 제거
        # job 이름은 channel_id 그대로 또는 대시를 언더스코어로 변환
        job_pattern = rf'^  ({re.escape(channel_id)}|{re.escape(channel_id.replace("-", "_"))}):\s*$'
        if re.match(job_pattern, line):
            skip_until_next_job = True
            i += 1
            continue
        
        # 다음 job 시작 감지 (들여쓰기 2칸으로 시작하는 새 키)
        if skip_until_next_job:
            if re.match(r'^  [a-zA-Z0-9_-]+:\s*$', line) and not line.startswith('    '):
                skip_until_next_job = False
            else:
                i += 1
                continue
        
        new_lines.append(line)
        i += 1
    
    # if 조건에서 제거된 cron들 제거
    content = ''.join(new_lines)
    for cron in removed_crons:
        # github.event.schedule == 'cron' || 패턴 제거
        content = re.sub(rf"\s*github\.event\.schedule == '{re.escape(cron)}' \|\|\n", '', content)
        content = re.sub(rf"\s*github\.event\.schedule == '{re.escape(cron)}'\n", '', content)
    
    original = ''.join(lines)
    if original != content:
        with open(WORKFLOW_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   ✅ auto_upload.yml에서 제거")
    else:
        print(f"   ⚠️  auto_upload.yml에서 채널을 찾을 수 없음")


def get_existing_channels() -> list:
    """현재 존재하는 채널 목록"""
    channels = []
    for item in CHANNELS_DIR.iterdir():
        if item.is_dir() and not item.name.startswith('_'):
            channels.append(item.name)
    return sorted(channels)


def remove_channel(channel_id: str):
    """채널 삭제 메인 함수"""
    
    print(f"\n{'='*60}")
    print(f"🗑️  채널 삭제: {channel_id}")
    print(f"{'='*60}")
    
    existing = get_existing_channels()
    if channel_id not in existing:
        print(f"\n❌ 채널 '{channel_id}'가 존재하지 않습니다.")
        print(f"\n현재 채널 목록:")
        for ch in existing:
            print(f"   - {ch}")
        return False
    
    # 확인
    print(f"\n⚠️  다음 항목이 삭제됩니다:")
    print(f"   - channels/{channel_id}/ 폴더")
    print(f"   - main.py CHANNELS 항목")
    print(f"   - schedule.yml 스케줄")
    print(f"   - auto_upload.yml job")
    
    confirm = input(f"\n정말 삭제하시겠습니까? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ 삭제가 취소되었습니다.")
        return False
    
    print(f"\n[1/4] 📁 채널 폴더 삭제...")
    remove_channel_folder(channel_id)
    
    print(f"\n[2/4] 📄 main.py 수정...")
    remove_from_main_py(channel_id)
    
    print(f"\n[3/4] 📅 schedule.yml 수정...")
    remove_from_schedule_yml(channel_id)
    
    print(f"\n[4/4] ⚙️ auto_upload.yml 수정...")
    remove_from_workflow_yml(channel_id)
    
    print(f"\n{'='*60}")
    print(f"✅ 채널 '{channel_id}' 삭제 완료!")
    print(f"{'='*60}")
    print(f"\n📋 추가 작업:")
    print(f"   1. GitHub Secrets에서 토큰 삭제 (선택사항):")
    print(f"      REFRESH_TOKEN_{channel_id.upper().replace('-', '_')}")
    print(f"")
    print(f"   2. 변경사항 커밋 & 푸시:")
    print(f"      git add . && git commit -m 'Remove {channel_id}' && git push")
    
    return True


def main():
    if CHANNEL_ID == "삭제할채널ID":
        print("❌ remove_channel.py 파일을 열어 CHANNEL_ID를 수정해주세요.")
        print("\n현재 채널 목록:")
        for ch in get_existing_channels():
            print(f"   - {ch}")
        sys.exit(1)
    
    remove_channel(CHANNEL_ID)


if __name__ == "__main__":
    main()
