from src.config.title_config import TITLE_LINE_COLORS
from src.title_generator import create_title_image
import os

# 테스트할 제목 (두 줄로 나뉠 만한 길이)
test_title = "맛있는 김치볶음밥 쉽고 간단하게 만드는 방법"

# 색상 설정 (config에서 불러옴)
line_colors = TITLE_LINE_COLORS

print(f"테스트 제목: {test_title}")
print(f"색상 설정: {line_colors}")

# 이미지 생성
try:
    image_path = create_title_image(
        text=test_title,
        line_colors=line_colors
    )
    
    print(f"\n✅ 이미지 생성 완료: {image_path}")
    print("해당 파일을 열어서 하얀색 테두리가 잘 적용되었는지 확인해보세요!")
    
    # Mac에서 Preview로 바로 열기
    os.system(f"open {image_path}")
    
except Exception as e:
    print(f"❌ 이미지 생성 실패: {e}")
