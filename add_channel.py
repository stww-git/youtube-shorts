#!/usr/bin/env python3
"""
새 YouTube 채널 추가 스크립트

사용법:
    1. 아래 CHANNEL_NAME 변수에 채널 이름을 입력
    2. python3 add_channel.py 실행

자동으로 처리되는 작업:
    1. channels/__template__ 폴더를 복사하여 새 채널 폴더 생성
    2. get_refresh_token.py 실행하여 토큰 얻기
    3. config.yaml 자동 수정 (채널명, 토큰 키, 토큰 값 등)
"""

# ============================================
# 🎯 여기에 새 채널 이름을 입력하세요
# ============================================
CHANNEL_NAME = "test-channel-trial1"
# ============================================

import os
import sys
import shutil
import re
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
CHANNELS_DIR = PROJECT_ROOT / "channels"
TEMPLATE_DIR = CHANNELS_DIR / "__template__"


def sanitize_channel_id(name: str) -> str:
    """채널명을 폴더명/ID로 변환 (영문 소문자, 숫자, 하이픈만 허용)"""
    channel_id = name.lower()
    channel_id = re.sub(r'[^a-z0-9\s-]', '', channel_id)
    channel_id = re.sub(r'\s+', '-', channel_id)
    channel_id = re.sub(r'-+', '-', channel_id)
    channel_id = channel_id.strip('-')
    return channel_id


def get_token_key(channel_id: str) -> str:
    """채널 ID를 토큰 환경변수 키로 변환"""
    return f"REFRESH_TOKEN_{channel_id.upper().replace('-', '_')}"


def update_config(config_path: Path, channel_name: str, channel_id: str, refresh_token: str = None):
    """config.yaml 파일 수정"""
    print(f"\n📝 config.yaml 수정 중...")
    
    token_key = get_token_key(channel_id)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 채널명 수정
    content = re.sub(
        r'display_name:\s*"[^"]*"',
        f'display_name: "{channel_name}"',
        content
    )
    
    # 토큰 키 수정
    content = re.sub(
        r'env_token_key:\s*"[^"]*"',
        f'env_token_key: "{token_key}"',
        content
    )
    
    # 제목 형식 초기화
    content = re.sub(
        r'title_format:\s*"[^"]*"',
        'title_format: "{title}"',
        content
    )
    
    # 설명 초기화
    content = re.sub(
        r'description:\s*"[^"]*"',
        'description: ""',
        content
    )
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"   ✅ display_name: {channel_name}")
    print(f"   ✅ env_token_key: {token_key}")


def run_get_refresh_token():
    """get_refresh_token.py 실행하여 토큰 얻기"""
    print(f"\n🔐 Refresh Token 발급 프로세스 시작...")
    print(f"   브라우저에서 원하는 YouTube 채널의 계정으로 로그인하세요.\n")
    
    try:
        # get_refresh_token.py 실행
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "get_refresh_token.py")],
            cwd=str(PROJECT_ROOT),
            capture_output=False  # 터미널에 직접 출력
        )
        return result.returncode == 0
    except Exception as e:
        print(f"   ❌ 토큰 발급 실패: {e}")
        return False


def create_channel(channel_name: str):
    """새 채널 폴더 생성"""
    
    channel_id = sanitize_channel_id(channel_name)
    channel_dir = CHANNELS_DIR / channel_id
    token_key = get_token_key(channel_id)
    
    print(f"\n{'='*60}")
    print(f"🆕 새 채널 생성: {channel_name}")
    print(f"{'='*60}")
    print(f"   채널 ID: {channel_id}")
    print(f"   폴더 경로: {channel_dir}")
    print(f"   토큰 키: {token_key}")
    
    # 이미 존재하는지 확인
    if channel_dir.exists():
        print(f"\n❌ 오류: '{channel_id}' 채널이 이미 존재합니다!")
        return False
    
    # Step 1: 템플릿 복사
    print(f"\n📁 [1/3] 템플릿 복사 중...")
    shutil.copytree(TEMPLATE_DIR, channel_dir)
    print(f"   ✅ {TEMPLATE_DIR} → {channel_dir}")
    
    # Step 2: Refresh Token 발급
    print(f"\n🔐 [2/3] Refresh Token 발급...")
    run_get_refresh_token()
    
    # Step 3: config.yaml 수정
    print(f"\n📝 [3/3] config.yaml 수정...")
    config_path = channel_dir / "config.yaml"
    update_config(config_path, channel_name, channel_id)
    
    # 완료 메시지
    print(f"\n{'='*60}")
    print(f"✅ 채널 '{channel_name}' 생성 완료!")
    print(f"{'='*60}")
    print(f"\n📋 다음 단계:")
    print(f"   1. .env 파일에 토큰 추가:")
    print(f"      {token_key}=발급받은_토큰")
    print(f"")
    print(f"   2. (선택) 워크플로우 생성:")
    print(f"      기존 워크플로우 파일을 복사하여 수정하세요.")
    print(f"")
    print(f"   3. 테스트 실행:")
    print(f"      python3 main.py --channel {channel_id} --test")
    
    return True


def main():
    if CHANNEL_NAME == "새채널이름":
        print("❌ add_channel.py 파일을 열어 CHANNEL_NAME 변수를 수정해주세요.")
        sys.exit(1)
    
    create_channel(CHANNEL_NAME)


if __name__ == "__main__":
    main()
