# YouTube Shorts Automation (Recipe-Based) 🍳

이 프로젝트는 **10000recipe.com**에서 레시피를 자동으로 가져와 **YouTube Shorts 영상**을 생성하는 자동화 파이프라인입니다.

## 🌟 주요 특징 (Highlights)
- **레시피 자동 크롤링**: 만개의레시피에서 베스트 레시피 자동 선택
- **중복 방지**: 히스토리 기반으로 동일 레시피 재사용 방지
- **All-in-One Google AI**: Gemini Flash + Imagen + TTS 통합
- **저비용**: '이미지 + 모션 효과' 전략으로 편당 ~200원

## 📚 문서 (Documentation)
상세한 아키텍처와 사용법 가이드는 `doc` 폴더를 참고하세요.

- [📖 자동화 가이드](doc/shorts_automation_guide.md)
- [💰 API 비용 분석](doc/API_COST_ANALYSIS.md)

## 🚀 시작하기 (Quick Start)

1. **필수 요건 설치**:
    ```bash
    pip3 install -r requirements.txt
    pip3 install beautifulsoup4
    ```

2. **환경 변수 설정**:
    - `.env.example` 파일을 `.env`로 변경합니다.
    - `GOOGLE_API_KEY`를 입력합니다.

3. **실행**:
    ```bash
    python3 main_recipe.py
    ```

## 📂 프로젝트 구조

```text
.
├── main_recipe.py               # 메인 실행 파일 (레시피 기반)
├── src/
│   ├── recipe_crawler.py        # 10000recipe.com 크롤러
│   ├── recipe_script_generator.py  # 요리 대본 생성기
│   ├── image_prompt_generator.py   # 이미지 프롬프트 생성
│   ├── image_generator.py       # Imagen 이미지 생성
│   ├── audio_generator.py       # Gemini TTS 나레이션
│   ├── motion_effects.py        # 영상 편집, 자막, 효과
│   ├── config.py                # 모델 설정
│   └── prompts.py               # AI 프롬프트 템플릿
├── output/                      # 생성된 영상 저장 폴더
│   ├── recipe_history.json      # 사용한 레시피 기록
│   └── {레시피제목}_{날짜}/     # 각 영상별 폴더
└── doc/
    └── shorts_automation_guide.md
```

## 🔄 워크플로우

1. **레시피 선택**: 베스트 → 카테고리 순환 (자동)
2. **대본 생성**: 레시피 정보 기반 8줄 구조
3. **오디오 생성**: 장면별 TTS 나레이션
4. **이미지 생성**: Imagen 푸드 포토그래피 스타일
5. **영상 합성**: Ken Burns 효과 + 자막

## 📊 레시피 선택 우선순위

1. **전체 베스트** (~100개)
2. **밑반찬** → **국/탕** → **찌개** → **메인반찬** → **초스피드** → **밥/죽/떡** → **면/만두** → **다이어트**
