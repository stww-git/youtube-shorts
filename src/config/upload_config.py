# YouTube Upload Configuration

# ==========================================
# 기본 업로드 설정
# ==========================================

# 공개 범위 설정
# 'private': 비공개 (나만 볼 수 있음) - 테스트용으로 권장
# 'unlisted': 일부 공개 (링크가 있는 사람만 볼 수 있음)
# 'public': 공개 (모든 사람이 볼 수 있음)
DEFAULT_PRIVACY_STATUS = 'private'

# 아동용 콘텐츠 설정 (COPPA 준수)
# True: 아동용 콘텐츠임 (댓글, 알림 등 제한됨)
# False: 아동용 콘텐츠가 아님 (일반적인 설정)
MADE_FOR_KIDS = False

# ==========================================
# 메타데이터 (제목, 설명, 태그)
# ==========================================

# 제목 형식 (f-string 스타일)
# 사용 가능한 변수: {title} (영상 제목), {category} (레시피 카테고리)
UPLOAD_TITLE_FORMAT = "{title} #건강 #건강정보"

# 설명 템플릿
# 빈 문자열("")로 설정하면 설명 없이 업로드됩니다.
# 사용 가능한 변수: {title}, {original_title}, {url}
UPLOAD_DESCRIPTION_TEMPLATE = ""

# 기본 태그 (리스트 형태)
DEFAULT_TAGS = []
