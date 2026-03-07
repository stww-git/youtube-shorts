"""
핵심 정보 카드 설정
Summary Card Configuration

이 파일에서 핵심 정보 카드의 모든 스타일을 조절할 수 있습니다.
"""

# ===========================================
# 📐 카드 기본 설정
# ===========================================

# 카드 표시 시간 (초)
CARD_DURATION = 0.5

# 최대 체크리스트 항목 수
MAX_ITEMS = 5

# 칠판(배경) 여백 설정 (안전 마진)
BOARD_MARGIN_X = 150      # 좌우 프레임 침범 방지 여백
BOARD_MARGIN_TOP = 250    # 상단 여백 (제목 시작 위치)


# ===========================================
# 📌 카드 제목 스타일
# ===========================================

# 제목 글자 색상
TITLE_COLOR = "#FFFFFF"  # 흰색 (어두운 배경)

# 제목 외곽선
TITLE_STROKE_COLOR = "#000000"  # 검정 외곽선
TITLE_STROKE_WIDTH = 3

# 제목 밑줄 색상 (None이면 밑줄 없음)
TITLE_UNDERLINE_COLOR = "#FFD700"  # 골드 (Money Bite 브랜드)
TITLE_UNDERLINE_HEIGHT = 4  # 밑줄 두께

# 제목 폰트 (None이면 FONT_FILE 사용)
TITLE_FONT_FILE = "nanumsquare/NanumSquareEB.ttf"  # ExtraBold


# ===========================================
# 🎨 텍스트 스타일
# ===========================================

# 글자 크기 (픽셀)
FONT_SIZE = 55

# 줄 간격 (픽셀)
LINE_SPACING = 28

# 글자 색상 (어두운 배경이므로 밝은 색상)
TEXT_COLOR = "#FFD700"  # 골드 (Money Bite 브랜드 컬러)

# 텍스트 외곽선 (가독성 확보)
TEXT_STROKE_COLOR = "#000000"  # 검정 외곽선
TEXT_STROKE_WIDTH = 2          # 외곽선 두께 (0이면 외곽선 없음)

# 정렬 방식: 'left', 'center', 'right'
TEXT_ALIGN = "left"


# ===========================================
# 🖼️ 배경 설정
# ===========================================

# 배경 이미지 파일명 (assets/summary_card_backgrounds/ 폴더 내)
# None으로 설정하면 BG_COLOR 사용
BG_IMAGE = "summary_card_backgrounds/finance_background.png"

# 배경 색상 (배경 이미지가 없을 때 사용)
# RGB 튜플: (R, G, B)
BG_COLOR = (26, 26, 46)  # 딥 네이비 (Money Bite 브랜드)


# ===========================================
# 📝 폰트 설정
# ===========================================

# 폰트 파일명 (fonts 폴더 내)
# None으로 설정하면 시스템 기본 폰트 사용
FONT_FILE = "nanumsquare/NanumSquareB.ttf"

