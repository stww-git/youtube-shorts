"""
채널 관리 모듈 (Channel Manager)

channels/ 폴더에서 채널 설정을 로드하고 관리합니다.
채널 ID는 폴더 이름을 기준으로 합니다.
"""

import os
import sys
import yaml
import importlib.util
from pathlib import Path
from typing import Optional, Any

# 프로젝트 루트 기준 경로 (core/ 폴더의 상위)
PROJECT_ROOT = Path(__file__).parent.parent
CHANNELS_DIR = PROJECT_ROOT / "channels"
SHARED_DIR = PROJECT_ROOT / "shared"


def list_channels() -> list[dict]:
    """
    사용 가능한 모든 채널 목록을 반환합니다.
    
    Returns:
        [{"id": "sokpyeonhan", "display_name": "속편한밥상"}, ...]
    """
    channels = []
    
    if not CHANNELS_DIR.exists():
        return channels
    
    for folder in CHANNELS_DIR.iterdir():
        # __template__ 및 숨김 폴더 제외
        if folder.is_dir() and not folder.name.startswith(('__', '.')):
            config = get_channel_config(folder.name)
            if config:
                channels.append({
                    "id": folder.name,
                    "display_name": config.get("display_name", folder.name)
                })
    
    return sorted(channels, key=lambda x: x["display_name"])


def get_channel_config(channel_id: str) -> Optional[dict]:
    """
    특정 채널의 설정을 반환합니다.
    
    Args:
        channel_id: 채널 폴더 이름 (예: "sokpyeonhan")
    
    Returns:
        채널 설정 딕셔너리 또는 None
    """
    config_path = CHANNELS_DIR / channel_id / "config.yaml"
    
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[ChannelManager] Failed to load config for '{channel_id}': {e}")
        return None


def get_channel_prompts(channel_id: str):
    """
    채널 전용 프롬프트 모듈을 반환합니다.
    
    config.yaml에서 prompts.use_custom이 True이고 prompts.py가 있으면 해당 모듈을,
    그렇지 않으면 기본 프롬프트 모듈(src/prompts.py)을 반환합니다.
    
    Args:
        channel_id: 채널 폴더 이름
    
    Returns:
        프롬프트 모듈 (RECIPE_SCRIPT_GENERATION_PROMPT 등 포함)
    """
    import shared.prompts as default_prompts
    
    config = get_channel_config(channel_id)
    if not config:
        return default_prompts
    
    # use_custom이 False면 기본 프롬프트 사용
    prompts_config = config.get("prompts", {})
    if not prompts_config.get("use_custom", False):
        return default_prompts
    
    # 채널 전용 prompts.py 로드 시도
    prompts_path = CHANNELS_DIR / channel_id / "prompts.py"
    if not prompts_path.exists():
        return default_prompts
    
    try:
        spec = importlib.util.spec_from_file_location(
            f"channels.{channel_id}.prompts",
            prompts_path
        )
        custom_prompts = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(custom_prompts)
        
        # 커스텀 프롬프트와 기본 프롬프트를 병합 (None인 것은 기본값 사용)
        class MergedPrompts:
            pass
        
        merged = MergedPrompts()
        
        # 기본 프롬프트 목록
        prompt_names = [
            'SCRIPT_GENERATION_PROMPT',
            'TITLE_GENERATION_PROMPT', 
            'IMAGE_GENERATION_PROMPT'
        ]
        
        for name in prompt_names:
            custom_value = getattr(custom_prompts, name, None)
            if custom_value is not None:
                setattr(merged, name, custom_value)
            else:
                setattr(merged, name, getattr(default_prompts, name))
        
        return merged
        
    except Exception as e:
        print(f"[ChannelManager] Failed to load custom prompts for '{channel_id}': {e}")
        return default_prompts


def get_upload_config(channel_id: str) -> dict:
    """
    채널의 업로드 설정을 반환합니다.
    
    Args:
        channel_id: 채널 폴더 이름
    
    Returns:
        업로드 설정 딕셔너리 (title_format, description, tags 등)
    """
    # 기본값
    defaults = {
        "title_format": "{title}",
        "description": "",
        "tags": [],
        "category_id": "22",
        "privacy_status": "private",
        "made_for_kids": False
    }
    
    config = get_channel_config(channel_id)
    if not config:
        return defaults
    
    upload_config = config.get("upload", {})
    
    # 기본값과 병합
    for key, value in defaults.items():
        if key not in upload_config:
            upload_config[key] = value
    
    return upload_config


def get_refresh_token(channel_id: str) -> Optional[str]:
    """
    채널의 Refresh Token을 환경변수에서 가져옵니다.
    
    Args:
        channel_id: 채널 폴더 이름
    
    Returns:
        Refresh Token 문자열 또는 None
    """
    config = get_channel_config(channel_id)
    if not config:
        return None
    
    env_key = config.get("env_token_key", f"REFRESH_TOKEN_{channel_id.upper()}")
    return os.getenv(env_key)


def validate_channel(channel_id: str) -> tuple[bool, str]:
    """
    채널 설정이 올바른지 검증합니다.
    
    Returns:
        (성공 여부, 메시지)
    """
    config = get_channel_config(channel_id)
    if not config:
        return False, f"채널 '{channel_id}' 설정 파일이 없습니다."
    
    if not config.get("env_token_key"):
        return False, f"채널 '{channel_id}'에 env_token_key가 설정되지 않았습니다."
    
    token = get_refresh_token(channel_id)
    if not token:
        env_key = config.get("env_token_key")
        return False, f"환경변수 '{env_key}'가 설정되지 않았습니다."
    
    return True, f"채널 '{config.get('display_name', channel_id)}' 준비 완료"


# ============================================
# 채널별 리소스 경로 함수
# ============================================

def get_fonts_dir(channel_id: str = None) -> Path:
    """
    폰트 디렉토리 경로를 반환합니다.
    
    채널 설정에서 use_custom_fonts가 True이고 채널 폴더에 fonts/가 있으면 해당 경로,
    그렇지 않으면 기본 fonts/ 경로를 반환합니다.
    """
    default_path = PROJECT_ROOT / "fonts"
    
    if not channel_id:
        return default_path
    
    config = get_channel_config(channel_id)
    if not config:
        return default_path
    
    paths_config = config.get("paths", {})
    if not paths_config.get("use_custom_fonts", False):
        return default_path
    
    channel_fonts = CHANNELS_DIR / channel_id / "fonts"
    if channel_fonts.exists():
        return channel_fonts
    
    return default_path


def get_output_dir(channel_id: str = None) -> Path:
    """
    출력 디렉토리 경로를 반환합니다.
    
    채널 설정에서 use_custom_output이 True이면 채널 폴더의 output/,
    그렇지 않으면 기본 output/ 경로를 반환합니다.
    폴더가 없으면 자동 생성합니다.
    """
    default_path = PROJECT_ROOT / "output"
    
    if not channel_id:
        return default_path
    
    config = get_channel_config(channel_id)
    if not config:
        return default_path
    
    paths_config = config.get("paths", {})
    if not paths_config.get("use_custom_output", False):
        return default_path
    
    channel_output = CHANNELS_DIR / channel_id / "output"
    
    # 폴더가 없으면 생성
    if not channel_output.exists():
        channel_output.mkdir(parents=True, exist_ok=True)
    
    return channel_output


def get_channel_dir(channel_id: str) -> Optional[Path]:
    """
    채널 폴더 경로를 반환합니다.
    """
    if not channel_id:
        return None
    
    channel_path = CHANNELS_DIR / channel_id
    if channel_path.exists():
        return channel_path
    
    return None


# ============================================
# 채널별 모듈 로드 함수
# ============================================

def get_channel_module(channel_id: str, module_name: str) -> Any:
    """
    채널별 모듈을 동적으로 로드합니다.
    
    채널 폴더에 해당 모듈이 있으면 그것을 사용하고,
    없으면 shared/ 폴더의 공통 모듈을 사용합니다.
    
    Args:
        channel_id: 채널 폴더 이름 (예: "sokpyeonhan")
        module_name: 모듈 이름 (예: "pipeline", "crawler")
    
    Returns:
        로드된 모듈
    """
    # 채널별 모듈 경로
    channel_module_path = CHANNELS_DIR / channel_id / "src" / f"{module_name}.py"
    
    # shared 공통 모듈 경로
    shared_module_path = SHARED_DIR / f"{module_name}.py"
    
    # 채널별 모듈이 있으면 우선 사용
    if channel_module_path.exists():
        module_path = channel_module_path
        full_module_name = f"channels.{channel_id}.src.{module_name}"
    elif shared_module_path.exists():
        module_path = shared_module_path
        full_module_name = f"shared.{module_name}"
    else:
        raise FileNotFoundError(f"Module '{module_name}' not found in channel '{channel_id}' or shared/")
    
    try:
        spec = importlib.util.spec_from_file_location(full_module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        
        # 채널 src 디렉토리를 sys.path에 추가 (config 등 import 해결용)
        channel_src_dir = str(CHANNELS_DIR / channel_id / "src")
        if channel_src_dir not in sys.path:
            sys.path.insert(0, channel_src_dir)
        
        # 채널 루트 디렉토리를 sys.path에 추가 (prompts.py 등 import 해결용)
        channel_root_dir = str(CHANNELS_DIR / channel_id)
        if channel_root_dir not in sys.path:
            sys.path.insert(0, channel_root_dir)
        
        spec.loader.exec_module(module)
        return module
        
    except Exception as e:
        print(f"[ChannelManager] Failed to load module '{module_name}' for '{channel_id}': {e}")
        raise


def get_channel_src_dir(channel_id: str) -> Path:
    """
    채널의 src 디렉토리 경로를 반환합니다.
    """
    return CHANNELS_DIR / channel_id / "src"


