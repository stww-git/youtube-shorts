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

