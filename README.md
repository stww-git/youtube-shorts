# YouTube Shorts 자동 생성 시스템 🍳📹

**10000recipe.com**에서 레시피를 자동으로 가져와 **YouTube Shorts 영상**을 생성하는 자동화 파이프라인입니다...

## 🌟 주요 특징

- **멀티 채널 지원**: 채널별 독립적인 설정과 파이프라인
- **레시피 자동 크롤링**: 만개의레시피에서 베스트 레시피 자동 선택
- **중복 방지**: 히스토리 기반으로 동일 레시피 재사용 방지
- **All-in-One Google AI**: Gemini Flash + Imagen + TTS 통합
- **저비용**: '이미지 + 모션 효과' 전략으로 편당 ~200원

---

## 📂 프로젝트 구조

```
youtube-shorts-upload-receipy/
├── main.py                      # 메인 실행 파일
├── core/                        # 공통 유틸리티
│   ├── channel_manager.py       # 채널 관리 및 모듈 로드
│   ├── utils.py                 # 공통 함수
│   └── upload/
│       └── youtube_uploader.py  # YouTube 업로드 모듈
│
├── defaults/                    # 기본 템플릿 (fallback)
│   ├── pipeline.py              # 기본 파이프라인
│   ├── crawler.py               # 기본 크롤러
│   ├── script_generator.py      # 대본 생성기
│   ├── image_generator.py       # 이미지 생성기
│   ├── audio_generator.py       # TTS 오디오 생성기
│   ├── motion_effects.py        # 영상 합성/효과
│   └── prompts.py               # AI 프롬프트 템플릿
│
├── channels/                    # 채널별 독립 폴더
│   ├── __template__/            # 새 채널 생성용 템플릿
│   │   ├── config.yaml          # 채널 설정
│   │   ├── fonts/               # 채널 전용 폰트
│   │   └── src/                 # 채널 전용 코드
│   │       ├── config/          # 설정 파일들
│   │       │   ├── audio_config.py
│   │       │   ├── subtitle_config.py
│   │       │   ├── title_config.py
│   │       │   └── model_config.py
│   │       ├── pipeline.py
│   │       └── prompts.py
│   │
│   └── sokpyeonhan/             # 속편한밥상 채널
│       ├── config.yaml
│       ├── fonts/
│       ├── output/              # 생성된 영상 저장
│       └── src/
│
├── assets/
│   └── test_images/             # 테스트 모드용 이미지
│
├── fonts/                       # 공통 폰트
└── doc/                         # 문서
    ├── shorts_automation_guide.md
    └── API_COST_ANALYSIS.md
```

---

## 🚀 시작하기

### 1. 필수 요건 설치
```bash
pip3 install -r requirements.txt
```

### 2. 환경 변수 설정
`.env.example`을 `.env`로 복사하고 API 키를 입력합니다:
```env
GOOGLE_API_KEY=your_api_key_here
```

### 3. 실행

**기본 실행** (테스트 모드):
```bash
python3 main.py --channel sokpyeonhan --test
```

**실제 영상 생성**:
```bash
python3 main.py --channel sokpyeonhan
```

**YouTube 업로드 포함**:
```bash
python3 main.py --channel sokpyeonhan --upload
```

---

## 🔄 워크플로우

1. **레시피 선택**: 베스트 → 카테고리 순환 (자동)
2. **대본 생성**: 레시피 정보 기반 8줄 구조
3. **제목 생성**: 클릭 유도형 제목 자동 생성
4. **오디오 생성**: Gemini TTS 나레이션
5. **이미지 생성**: Imagen 푸드 포토그래피 스타일
6. **영상 합성**: Ken Burns 효과 + 자막 + 제목

---

## ⚙️ 채널별 설정

각 채널 폴더의 `config.yaml`에서 설정을 관리합니다:

```yaml
channel:
  name: "속편한밥상"
  id: "sokpyeonhan"

upload:
  privacy_status: "public"
  category_id: "26"  # Howto & Style

paths:
  use_custom_output: true
  use_custom_config: true
  use_custom_fonts: true
```

### 자막/제목 커스터마이징

- **자막 설정**: `channels/{채널}/src/config/subtitle_config.py`
- **제목 설정**: `channels/{채널}/src/config/title_config.py`
- **TTS 음성**: `channels/{채널}/src/config/audio_config.py`

---

## 📊 레시피 선택 우선순위

1. **전체 베스트** (~100개)
2. **밑반찬** → **국/탕** → **찌개** → **메인반찬** → **초스피드** → **밥/죽/떡** → **면/만두** → **다이어트**

---

## 📚 문서

- [📖 자동화 가이드](doc/shorts_automation_guide.md)
- [💰 API 비용 분석](doc/API_COST_ANALYSIS.md)

---

## 🆕 새 채널 추가하기

1. `channels/__template__` 폴더를 복사하여 새 채널 폴더 생성
2. `config.yaml`에서 채널 정보 수정
3. 필요시 `src/prompts.py`에서 프롬프트 커스터마이징
4. `main.py`에서 `--channel 새채널명`으로 실행
