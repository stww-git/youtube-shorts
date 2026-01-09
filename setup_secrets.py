#!/usr/bin/env python3
"""
GitHub Secrets 설정 도우미

사용법:
    python3 setup_secrets.py

이 스크립트는 현재 .env 파일의 설정을 읽어서
GitHub Secrets에 추가해야 할 내용을 안내합니다.
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent
ENV_FILE = PROJECT_ROOT / ".env"
MAIN_PY_FILE = PROJECT_ROOT / "main.py"


def get_channel_token_keys() -> list:
    """main.py에서 필요한 토큰 키 목록 추출"""
    with open(MAIN_PY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # CHANNELS에서 채널 ID 추출
    pattern = r'"([^"]+)":\s*\{'
    channels = re.findall(pattern, content)
    
    # channel-id 템플릿 제외
    channels = [ch for ch in channels if ch != "channel-id"]
    
    # 토큰 키 생성
    token_keys = []
    for ch in channels:
        key = f"REFRESH_TOKEN_{ch.upper().replace('-', '_')}"
        token_keys.append((ch, key))
    
    return token_keys


def check_env_secrets():
    """현재 .env 파일 확인"""
    load_dotenv()
    
    # 필수 시크릿
    required_secrets = {
        'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
        'CLIENT_ID': os.getenv('CLIENT_ID'),
        'CLIENT_SECRET': os.getenv('CLIENT_SECRET'),
    }
    
    # 채널별 토큰
    channel_tokens = get_channel_token_keys()
    for channel, key in channel_tokens:
        required_secrets[key] = os.getenv(key)
    
    return required_secrets, channel_tokens


def display_setup_guide():
    """GitHub Secrets 설정 가이드 표시"""
    
    secrets, channel_tokens = check_env_secrets()
    
    print()
    print("=" * 70)
    print("🔐 GitHub Secrets 설정 가이드")
    print("=" * 70)
    print()
    print("GitHub 저장소 → Settings → Secrets and variables → Actions")
    print("→ New repository secret")
    print()
    print("-" * 70)
    print("📋 필수 Secrets")
    print("-" * 70)
    print()
    
    # 필수 시크릿 상태
    core_secrets = ['GOOGLE_API_KEY', 'CLIENT_ID', 'CLIENT_SECRET']
    for key in core_secrets:
        value = secrets.get(key)
        status = "✅ .env에 설정됨" if value else "❌ .env에 없음"
        masked = f"{value[:10]}..." if value and len(value) > 10 else value
        print(f"  {key}")
        print(f"    상태: {status}")
        if value:
            print(f"    값: {masked}")
        print()
    
    print("-" * 70)
    print("📺 채널별 Refresh Token")
    print("-" * 70)
    print()
    
    for channel, key in channel_tokens:
        value = secrets.get(key)
        status = "✅ .env에 설정됨" if value else "❌ 토큰 발급 필요"
        masked = f"{value[:20]}..." if value and len(value) > 20 else value
        
        print(f"  채널: {channel}")
        print(f"    시크릿 이름: {key}")
        print(f"    상태: {status}")
        if value:
            print(f"    값: {masked}")
        else:
            print(f"    💡 python3 get_refresh_token.py 실행하여 발급")
        print()
    
    print("-" * 70)
    print("📝 .env 파일에서 복사할 값들")
    print("-" * 70)
    print()
    
    # .env 파일 내용 표시 (마스킹)
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # 값 마스킹
                    if len(value) > 15:
                        masked = value[:10] + "..." + value[-5:]
                    else:
                        masked = value
                    print(f"  {key}={masked}")
        print()
    
    print("=" * 70)
    print()
    print("⚠️  주의사항:")
    print("  - GitHub Secrets에 추가 시 실제 전체 값을 복사하세요")
    print("  - .env 파일은 Git에 커밋되지 않습니다 (.gitignore)")
    print("  - 토큰 유출에 주의하세요")
    print()


def main():
    display_setup_guide()


if __name__ == "__main__":
    main()
