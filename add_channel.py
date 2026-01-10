#!/usr/bin/env python3
"""
새 YouTube 채널 추가 스크립트

사용법:
    1. 아래 CHANNEL_NAME 수정
    2. python3 add_channel.py 실행

자동으로 처리되는 작업:
    1. channels/__template__ 폴더를 복사하여 새 채널 폴더 생성
    2. config.yaml 자동 수정
    3. 업로드 시간 자동 계산 (기존 채널과 30분 이상 간격)
    4. .github/schedule.yml에 스케줄 추가
    5. .github/workflows/auto_upload.yml에 job 추가
    6. get_refresh_token.py 실행하여 토큰 얻기
"""

# ============================================
# 🎯 여기에 새 채널 이름만 입력하세요
# ============================================
CHANNEL_NAME = "새채널이름"

# 업로드 시간 설정 (선택사항)
# - "AUTO": 기존 채널과 겹치지 않게 자동 계산 (권장)
# - ["08:00", "13:00", "19:00"]: 직접 지정
SCHEDULE = "AUTO"
# ============================================

import os
import sys
import shutil
import re
import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
CHANNELS_DIR = PROJECT_ROOT / "channels"
TEMPLATE_DIR = CHANNELS_DIR / "__template__"
SCHEDULE_FILE = PROJECT_ROOT / ".github" / "schedule.yml"
WORKFLOW_FILE = PROJECT_ROOT / ".github" / "workflows" / "auto_upload.yml"

# 최적 업로드 시간대 (한국 시간)
OPTIMAL_BASE_TIMES = ["07:00", "12:00", "18:00"]  # 아침, 점심, 저녁


def sanitize_channel_id(name: str) -> str:
    """채널명을 폴더명/ID로 변환"""
    channel_id = name.lower()
    channel_id = re.sub(r'[^a-z0-9\s-]', '', channel_id)
    channel_id = re.sub(r'\s+', '-', channel_id)
    channel_id = re.sub(r'-+', '-', channel_id)
    return channel_id.strip('-')


def get_token_key(channel_id: str) -> str:
    """채널 ID를 토큰 환경변수 키로 변환"""
    return f"REFRESH_TOKEN_{channel_id.upper().replace('-', '_')}"


def time_to_minutes(time_str: str) -> int:
    """시간 문자열을 분으로 변환"""
    h, m = map(int, time_str.split(':'))
    return h * 60 + m


def minutes_to_time(minutes: int) -> str:
    """분을 시간 문자열로 변환"""
    minutes = minutes % (24 * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def get_existing_schedules() -> list:
    """기존 채널들의 스케줄 시간 목록 반환"""
    if not SCHEDULE_FILE.exists():
        return []
    
    with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 모든 시간 추출 (예: "07:00", "12:30")
    times = re.findall(r'"(\d{2}:\d{2})"', content)
    return times


def calculate_auto_schedule() -> list:
    """기존 채널과 겹치지 않는 시간 자동 계산"""
    existing_times = get_existing_schedules()
    existing_minutes = set(time_to_minutes(t) for t in existing_times)
    
    result = []
    for base_time in OPTIMAL_BASE_TIMES:
        base_min = time_to_minutes(base_time)
        
        # 30분 단위로 빈 슬롯 찾기 (앞뒤 2시간 범위)
        for offset in range(0, 121, 30):  # 0, 30, 60, 90, 120분
            for direction in [1, -1]:  # 앞/뒤 탐색
                candidate_min = base_min + (offset * direction)
                
                # 겹치는지 확인 (30분 이내 겹침 방지)
                is_conflict = any(abs(candidate_min - existing) < 30 
                                 for existing in existing_minutes)
                
                if not is_conflict:
                    result.append(minutes_to_time(candidate_min))
                    existing_minutes.add(candidate_min)  # 새 시간 추가
                    break
            else:
                continue
            break
    
    return result if result else ["08:00", "13:00", "19:00"]


def kst_to_utc_cron(time_str: str) -> str:
    """한국 시간을 UTC cron 형식으로 변환"""
    hour, minute = map(int, time_str.split(':'))
    utc_hour = (hour - 9) % 24
    return f"{minute} {utc_hour} * * *"


def update_config(config_path: Path, channel_name: str, channel_id: str):
    """config.yaml 파일 수정"""
    print(f"   📝 config.yaml 수정...")
    
    token_key = get_token_key(channel_id)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = re.sub(r'display_name:\s*"[^"]*"', f'display_name: "{channel_name}"', content)
    content = re.sub(r'env_token_key:\s*"[^"]*"', f'env_token_key: "{token_key}"', content)
    content = re.sub(r'title_format:\s*"[^"]*"', 'title_format: "{title}"', content)
    content = re.sub(r'description:\s*"[^"]*"', 'description: ""', content)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"      ✅ display_name: {channel_name}")
    print(f"      ✅ env_token_key: {token_key}")


def update_schedule_yml(channel_id: str, channel_name: str, times: list):
    """schedule.yml에 새 채널 스케줄 추가"""
    print(f"   📅 schedule.yml 수정...")
    
    with open(SCHEDULE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 새 채널 스케줄 블록 생성
    times_yaml = '\n'.join([f'      - "{t}"' for t in times])
    new_channel_block = f'''
  {channel_id}:
    name: "{channel_name}"
    enabled: true
    times:
{times_yaml}
'''
    
    # 파일 끝에 추가 (주석 제외한 마지막 채널 뒤에)
    # 마지막 times 블록 찾기
    last_times_match = list(re.finditer(r'    times:\n(?:      - "[^"]+"\n)+', content))
    if last_times_match:
        insert_pos = last_times_match[-1].end()
        content = content[:insert_pos] + new_channel_block + content[insert_pos:]
    else:
        content += new_channel_block
    
    with open(SCHEDULE_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"      ✅ 스케줄 추가: {', '.join(times)}")


def update_workflow_yml(channel_id: str, times: list):
    """auto_upload.yml에 새 채널 job 추가"""
    print(f"   ⚙️ auto_upload.yml 수정...")
    
    token_key = get_token_key(channel_id)
    
    with open(WORKFLOW_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. schedule 섹션에 cron 추가
    cron_comments = []
    cron_lines = []
    for t in times:
        cron = kst_to_utc_cron(t)
        cron_lines.append(f"    - cron: '{cron}'  # KST {t}")
    
    # workflow_dispatch 바로 앞에 cron 추가
    cron_block = f"\n    # {channel_id}\n" + '\n'.join(cron_lines)
    content = re.sub(r'(\n  workflow_dispatch:)', cron_block + r'\1', content)
    
    # 2. workflow_dispatch options에 채널 추가
    options_match = re.search(r'(        options:\n(?:          - [^\n]+\n)+)', content)
    if options_match:
        options_block = options_match.group(1)
        new_option = f"          - {channel_id}\n"
        if new_option not in options_block:
            new_options = options_block.rstrip() + f"\n          - {channel_id}\n"
            content = content.replace(options_block, new_options)
    
    # 3. 새 job 추가
    cron_conditions = ' ||\n        '.join([f"github.event.schedule == '{kst_to_utc_cron(t)}'" for t in times])
    
    new_job = f'''
  # {channel_id} 채널
  {channel_id.replace('-', '_')}:
    runs-on: ubuntu-latest
    if: |
      github.event_name == 'workflow_dispatch' && github.event.inputs.channel == '{channel_id}' ||
      github.event_name == 'schedule' && (
        {cron_conditions}
      )
    
    steps:
    - uses: actions/checkout@v4
    
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        cache: 'pip'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        sudo apt-get update && sudo apt-get install -y ffmpeg
    
    - name: Generate and Upload Video
      env:
        REFRESH_TOKEN: ${{{{ secrets.{token_key} }}}}
      run: python main.py --channel {channel_id} --upload
    
    - name: Update History
      run: |
        git config user.name "GitHub Actions Bot"
        git config user.email "actions@github.com"
        git add channels/{channel_id}/history.json 2>/dev/null || true
        git diff --staged --quiet || git commit -m "Update history ({channel_id}) [skip ci]"
        git push || true
    
    - uses: actions/upload-artifact@v4
      with:
        name: {channel_id}-${{{{ github.run_number }}}}
        path: channels/{channel_id}/output/**/*.mp4
        retention-days: 1
        if-no-files-found: error
'''
    
    content += new_job
    
    with open(WORKFLOW_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"      ✅ job 추가: {channel_id.replace('-', '_')}")


MAIN_PY_FILE = PROJECT_ROOT / "main.py"


def update_main_py(channel_id: str):
    """main.py의 CHANNELS 딕셔너리에 새 채널 추가"""
    print(f"   📄 main.py 수정...")
    
    with open(MAIN_PY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # CHANNELS 딕셔너리에 새 채널 추가
    # 패턴: 마지막 채널 설정 블록 뒤, 주석 앞에 삽입
    new_channel_block = f'''    "{channel_id}": {{
        "enabled": True,          # True: 스케줄 실행
        "test_mode": True,        # True: 테스트 모드 (이미지 생성 생략)
        "upload": False,          # True: YouTube 업로드
        "privacy": "private",     # public / unlisted / private
        "parallel": False,        # True: 이미지 병렬 생성
        "allow_fallback": False,  # False: 실패 시 바로 종료
    }},'''
    
    # "# 새 채널 추가 시" 주석 찾아서 그 앞에 삽입
    pattern = r'(\n    # 새 채널 추가 시)'
    if re.search(pattern, content):
        content = re.sub(pattern, f'\n{new_channel_block}\\1', content)
    else:
        # 패턴이 없으면 CHANNELS = { } 블록 끝에 추가
        # 마지막 }, 앞에 삽입
        content = re.sub(r'(\n}\n\n# =)', f'\n{new_channel_block}\\1', content)
    
    with open(MAIN_PY_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"      ✅ CHANNELS에 '{channel_id}' 추가")


def run_get_refresh_token():
    """토큰 발급 실행"""
    print(f"\n🔐 Refresh Token 발급...")
    print(f"   브라우저에서 해당 채널의 Google 계정으로 로그인하세요.\n")
    
    import subprocess
    subprocess.run([sys.executable, str(PROJECT_ROOT / "get_refresh_token.py")], cwd=str(PROJECT_ROOT))


def create_channel(channel_name: str, schedule: list):
    """새 채널 생성"""
    
    channel_id = sanitize_channel_id(channel_name)
    channel_dir = CHANNELS_DIR / channel_id
    token_key = get_token_key(channel_id)
    
    print(f"\n{'='*60}")
    print(f"🆕 새 채널 생성: {channel_name}")
    print(f"{'='*60}")
    print(f"   채널 ID: {channel_id}")
    print(f"   토큰 키: {token_key}")
    print(f"   스케줄: {', '.join(schedule)} (KST)")
    
    if channel_dir.exists():
        print(f"\n❌ 오류: '{channel_id}' 채널이 이미 존재합니다!")
        return False
    
    # Step 1: 템플릿 복사
    print(f"\n[1/6] 📁 템플릿 복사...")
    shutil.copytree(TEMPLATE_DIR, channel_dir)
    print(f"      ✅ {channel_dir}")
    
    # Step 2: config.yaml 수정
    print(f"\n[2/6] 📝 config.yaml 수정...")
    update_config(channel_dir / "config.yaml", channel_name, channel_id)
    
    # Step 3: main.py CHANNELS 수정
    print(f"\n[3/6] 📄 main.py 수정...")
    update_main_py(channel_id)
    
    # Step 4: schedule.yml 수정
    print(f"\n[4/6] 📅 schedule.yml 수정...")
    update_schedule_yml(channel_id, channel_name, schedule)
    
    # Step 5: auto_upload.yml 수정
    print(f"\n[5/6] ⚙️ auto_upload.yml 수정...")
    update_workflow_yml(channel_id, schedule)
    
    # Step 6: 토큰 발급
    print(f"\n[6/6] 🔐 Refresh Token 발급...")
    run_get_refresh_token()
    
    # 완료
    print(f"\n{'='*60}")
    print(f"✅ 채널 '{channel_name}' 생성 완료!")
    print(f"{'='*60}")
    print(f"\n📋 마지막 단계:")
    print(f"   1. .env 파일에 토큰 추가:")
    print(f"      {token_key}=발급받은_토큰")
    print(f"")
    print(f"   2. GitHub Secrets에도 동일하게 추가:")
    print(f"      Repository → Settings → Secrets → {token_key}")
    print(f"")
    print(f"   3. 변경사항 커밋 & 푸시:")
    print(f"      git add . && git commit -m 'Add {channel_id}' && git push")
    
    return True


def main():
    if CHANNEL_NAME == "새채널이름":
        print("❌ add_channel.py 파일을 열어 CHANNEL_NAME을 수정해주세요.")
        sys.exit(1)
    
    # 스케줄 결정
    if SCHEDULE == "AUTO":
        schedule = calculate_auto_schedule()
        print(f"\n🕐 스케줄 자동 계산 완료: {', '.join(schedule)} (KST)")
    else:
        schedule = SCHEDULE
    
    create_channel(CHANNEL_NAME, schedule)


if __name__ == "__main__":
    main()
