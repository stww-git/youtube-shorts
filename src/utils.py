"""
공통 유틸리티 함수 모듈

여러 모듈에서 공통으로 사용하는 함수들을 관리합니다.
"""


def format_ingredients(ingredients: list, max_count: int = 10) -> str:
    """
    재료 목록을 문자열로 포맷팅
    
    Args:
        ingredients: 재료 목록 [{"name": "...", "amount": "..."}, ...]
        max_count: 최대 재료 개수 (기본값: 10)
    
    Returns:
        포맷팅된 재료 문자열
    """
    if not ingredients:
        return "재료 정보 없음"
    
    formatted = []
    for ing in ingredients[:max_count]:
        name = ing.get('name', '')
        amount = ing.get('amount', '')
        if amount:
            formatted.append(f"- {name} {amount}")
        else:
            formatted.append(f"- {name}")
    return "\n".join(formatted)


def format_steps(steps: list, max_count: int = 8, max_chars: int = 100) -> str:
    """
    조리 단계를 문자열로 포맷팅
    
    Args:
        steps: 조리 단계 목록 [{"step": 1, "description": "..."}, ...]
        max_count: 최대 단계 개수 (기본값: 8)
        max_chars: 각 단계 최대 문자 수 (기본값: 100)
    
    Returns:
        포맷팅된 조리 단계 문자열
    """
    if not steps:
        return "조리 단계 정보 없음"
    
    formatted = []
    for step in steps[:max_count]:
        step_num = step.get('step', '')
        desc = step.get('description', '')
        if desc:
            formatted.append(f"{step_num}. {desc[:max_chars]}")
    return "\n".join(formatted)


# ==========================================
# Console Helper Functions
# ==========================================

def print_header(text):
    """Print a styled header."""
    print(f"\n{'🍳'*25}")
    print(f"  {text}")
    print(f"{'🍳'*25}")

def print_step(step_num, total_steps, title, status="🔄 진행 중"):
    """Print a step indicator with progress bar."""
    progress = "█" * step_num + "░" * (total_steps - step_num)
    percent = int((step_num / total_steps) * 100)
    
    print(f"\n{'='*60}")
    print(f"  📍 STEP {step_num}/{total_steps}  [{progress}] {percent}%")
    print(f"{'='*60}")
    print(f"  📌 {title}")
    print(f"  ⏳ {status}")
    print(f"{'='*60}")

def print_step_complete(step_num, total_steps, title):
    """Print step completion."""
    print(f"\n{'─'*60}")
    print(f"  ✅ STEP {step_num}/{total_steps} 완료: {title}")
    print(f"{'─'*60}")

def print_substep(text):
    """Print a sub-step or detail."""
    print(f"   ▶ {text}")

def print_success(text):
    """Print a success message."""
    print(f"   ✅ {text}")

def print_warning(text):
    """Print a warning message."""
    print(f"   ⚠️  {text}")

def print_error(text):
    """Print an error message."""
    print(f"   ❌ {text}")

def print_info(text):
    """Print an info message."""
    print(f"   ℹ️  {text}")


# ==========================================
# File System Helper Functions
# ==========================================

def sanitize_filename(filename: str) -> str:
    """Remove or replace characters that are not safe for filenames."""
    import re
    filename = re.sub(r'[<>:"/\\|?*#!@$%^&()\[\]{}+=~`\';,]', '', filename)
    filename = re.sub(r'\s+', ' ', filename)
    filename = filename.strip(' .')
    if len(filename) > 80:
        filename = filename[:80]
    return filename

def create_output_folder(recipe_title: str, base_output_dir: str = None) -> str:
    """Create output folder with recipe title and date.
    
    Args:
        recipe_title: 레시피 제목
        base_output_dir: 기본 출력 디렉토리 (없으면 project root의 output/ 사용)
    """
    import os
    from datetime import datetime
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    safe_title = sanitize_filename(recipe_title)
    
    if not safe_title or len(safe_title.strip()) == 0:
        safe_title = "recipe"
    
    folder_name = f"{safe_title}_{date_str}"
    
    # base_output_dir이 지정되면 해당 경로 사용, 아니면 기본 output/ 사용
    if base_output_dir:
        output_base = base_output_dir
    else:
        output_base = "output"
    
    if not os.path.exists(output_base):
        os.makedirs(output_base, exist_ok=True)
    
    output_dir = os.path.join(output_base, folder_name)
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir

def check_environment():
    """Check if necessary API keys are present."""
    import os
    import sys
    
    required_keys = ["GOOGLE_API_KEY"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        print(f"❌ Error: Missing API keys in .env file: {', '.join(missing_keys)}")
        sys.exit(1)
    print_success("Environment check passed. API keys loaded.")
