"""
자막 설정 파일 (Subtitle Configuration)

자막의 위치, 스타일, 폰트 등을 한 곳에서 관리합니다.
자막을 수정하려면 이 파일만 수정하면 됩니다.
"""

import os

# ============================================
# 화면 크기 (YouTube Shorts)
# ============================================
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920


# ============================================
# 자막 위치 설정
# ============================================

# Y 위치 비율 (화면 높이 기준)
# 0.4: 화면 위쪽 (40%)
# 0.5: 정중앙 (50%)
# 0.55: 기본값 - 중앙 약간 아래 (55%)
# 0.7: 화면 아래쪽 (70%)
SUBTITLE_Y_RATIO = 0.55

# 실제 Y 위치 (픽셀) - 자동 계산
SUBTITLE_Y_POSITION = int(VIDEO_HEIGHT * SUBTITLE_Y_RATIO)


# ============================================
# 자막 스타일 설정
# ============================================

# 폰트 설정
SUBTITLE_FONT_SIZE = 80
SUBTITLE_FONT_PATH = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"

# 자막 너비 (좌우 여백 포함)
# 1080px 화면에서 960px = 좌우 60px 여백
SUBTITLE_MAX_WIDTH = 960

# 기본 색상
SUBTITLE_TEXT_COLOR = 'white'
SUBTITLE_STROKE_COLOR = 'black'
SUBTITLE_STROKE_WIDTH = 3

# 강조 색상 (impact keywords)
SUBTITLE_IMPACT_COLOR = '#FFD700'  # 금색
SUBTITLE_IMPACT_STROKE_WIDTH = 4

# 강조 키워드 목록
SUBTITLE_IMPACT_KEYWORDS = ["절대", "경고", "비밀", "정답", "비법"]


# ============================================
# 편의 함수
# ============================================

def get_subtitle_style(is_impactful: bool = False) -> dict:
    """
    자막 스타일 설정을 딕셔너리로 반환합니다.
    
    Args:
        is_impactful: 강조 키워드 여부
    
    Returns:
        스타일 설정 딕셔너리
    """
    return {
        'font_size': SUBTITLE_FONT_SIZE,
        'font_path': SUBTITLE_FONT_PATH,
        'text_color': SUBTITLE_IMPACT_COLOR if is_impactful else SUBTITLE_TEXT_COLOR,
        'stroke_color': SUBTITLE_STROKE_COLOR,
        'stroke_width': SUBTITLE_IMPACT_STROKE_WIDTH if is_impactful else SUBTITLE_STROKE_WIDTH,
        'max_width': SUBTITLE_MAX_WIDTH,
        'y_position': SUBTITLE_Y_POSITION,
    }


def is_impact_text(text: str) -> bool:
    """
    텍스트가 강조 키워드로 시작하는지 확인합니다.
    
    Args:
        text: 확인할 텍스트
    
    Returns:
        강조 키워드로 시작하면 True
    """
    words = text.split()
    if not words:
        return False
    first_word = words[0]
    return any(first_word.startswith(k) for k in SUBTITLE_IMPACT_KEYWORDS)
