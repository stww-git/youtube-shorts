"""
레시피 기반 YouTube Shorts 자동 생성 시스템

10000recipe.com에서 레시피를 가져와 쇼츠 영상을 생성합니다.
"""

import argparse
import warnings
from dotenv import load_dotenv

from src.pipeline import RecipeVideoPipeline
from src.utils import print_header, check_environment
from src.config.channel_manager import list_channels, get_channel_config, validate_channel

# Suppress ALL warnings before importing other modules
warnings.filterwarnings('ignore')
import logging
logging.captureWarnings(True)

# Suppress specific warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Suppress urllib3 warnings
try:
    import urllib3
    urllib3.disable_warnings()
except:
    pass

# Load environment variables
load_dotenv()

# ==========================================
# 사용자 설정 (User Configuration)
# ==========================================
# 테스트 모드 (이미지 생성 건너뛰기)
# True로 설정하면 --test 옵션 없이도 항상 테스트 모드로 실행됩니다.
TEST_MODE = True

# 이미지 생성 병렬 처리 (True: 빠름, False: 안정적)
# API Rate Limit 오류가 발생하면 False로 설정하세요.
IMAGE_PARALLEL = False

# 유튜브 업로드 여부
# True: 영상 생성 후 자동 업로드
# False: 영상 생성만 (업로드 안 함)
# 터미널에서 --upload 옵션을 주면 이 설정보다 우선합니다.
UPLOAD_TO_YOUTUBE = False

# ==========================================
# 타겟 채널 설정
# ==========================================
# channels/ 폴더 내의 채널 폴더명을 입력하세요.
# 예: "sokpyeonhan" (channels/sokpyeonhan/ 폴더 사용)
# None으로 설정하면 대화형 선택 또는 기본값(REFRESH_TOKEN) 사용
TARGET_CHANNEL = "sokpyeonhan"


def select_channel_interactive() -> str:
    """대화형으로 채널을 선택합니다."""
    import sys
    
    if not sys.stdin.isatty():
        return None
    
    channels = list_channels()
    
    if not channels:
        print("\n   ⚠️  등록된 채널이 없습니다. channels/ 폴더를 확인하세요.")
        return None
    
    print("\n   📺 사용 가능한 채널 목록:")
    print("   " + "-" * 40)
    
    for idx, ch in enumerate(channels, 1):
        print(f"   {idx}. {ch['display_name']} ({ch['id']})")
    
    print(f"   {len(channels) + 1}. 기본값 사용 (REFRESH_TOKEN)")
    print("   " + "-" * 40)
    
    try:
        choice = input(f"   👉 선택 (1-{len(channels) + 1}): ").strip()
        
        if not choice:
            return channels[0]['id'] if channels else None
        
        choice_num = int(choice)
        
        if 1 <= choice_num <= len(channels):
            selected = channels[choice_num - 1]
            print(f"\n   ✅ '{selected['display_name']}' 채널 선택됨")
            return selected['id']
        elif choice_num == len(channels) + 1:
            print("\n   ✅ 기본값(REFRESH_TOKEN) 사용")
            return None
        else:
            print("\n   ⚠️  잘못된 선택입니다. 기본값 사용")
            return None
            
    except (ValueError, EOFError):
        print("\n   ⚠️  입력 오류. 기본값 사용")
        return None


def main():
    print_header("🍳 YouTube Shorts 자동 생성 시스템 (Recipe-Based)")
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='YouTube Shorts Generator')
    parser.add_argument('--test', action='store_true', help='Test mode: use placeholder images instead of generating new ones')
    parser.add_argument('--upload', action='store_true', help='Upload generated video to YouTube')
    parser.add_argument('--channel', type=str, default=None, help='Target channel ID (folder name in channels/)')
    args = parser.parse_args()
    
    # Check both CLI arg and global constant
    is_test_mode = args.test or TEST_MODE
    
    # Determine channel: CLI arg > script constant > interactive selection
    channel_id = args.channel if args.channel else TARGET_CHANNEL
    
    # If no channel specified and running interactively, show selection menu
    if channel_id is None:
        channel_id = select_channel_interactive()
    
    # Determine upload: CLI arg takes precedence over script constant
    should_upload = args.upload or UPLOAD_TO_YOUTUBE
    
    # Validate channel if specified
    if channel_id:
        config = get_channel_config(channel_id)
        if config:
            print(f"\n   📺 타겟 채널: {config.get('display_name', channel_id)}")
            
            # Validate token availability (only warn, don't block)
            is_valid, message = validate_channel(channel_id)
            if not is_valid and should_upload:
                print(f"   ⚠️  {message}")
        else:
            print(f"\n   ⚠️  채널 '{channel_id}' 설정을 찾을 수 없습니다.")
            print(f"       channels/{channel_id}/config.yaml 파일을 확인하세요.")
    
    if is_test_mode:
        print("\n   🧪 [TEST MODE ENABLED] 이미지 생성을 건너뛰고 플레이스홀더를 사용합니다.\n")
    
    if should_upload:
        print("   🚀 [UPLOAD ENABLED] 영상 생성 후 YouTube에 업로드됩니다.\n")
    else:
        print("   📁 [UPLOAD DISABLED] 영상 생성만 진행됩니다. (업로드 안 함)\n")
    
    check_environment()
    
    # Initialize and run pipeline
    pipeline = RecipeVideoPipeline()
    pipeline.run(
        test_mode=is_test_mode, 
        image_parallel=IMAGE_PARALLEL, 
        upload_to_youtube=should_upload,
        channel_id=channel_id
    )



if __name__ == "__main__":
    main()

