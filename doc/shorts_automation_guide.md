# 🎬 Antigravity Shorts Automation Guide

이 문서는 **"AI로 10-20초 숏폼 영상을 200원에 제작하는 자동화 파이프라인"**의 사용법과 아키텍처를 설명합니다.

## 📌 핵심 전략: "저예산 고효율 (Low Budget High Efficiency)"
비싼 동영상 생성 AI(Veo, Runway 등) 대신, **"고화질 이미지 + 모션 효과"**를 사용하여 비용을 획기적으로 절감했습니다.

- **비용**: 영상 1편(10-20초) 당 **약 200원** (기존 약 14,000원 대비 98% 절감)
- **퀄리티**: Gemini가 분석한 검증된 대본 + 4K급 AI 이미지 + 자연스러운 성우 나레이션
- **정확도**: 장면별 개별 오디오로 나레이션과 영상 타이밍이 완벽히 일치

## 🛠 아키텍처 (Processing Pipeline)

### 1️⃣ 주제 분석 & 대본 (Analysis & Script)
- **Engine**: **Gemini Flash Latest**
- **역할**: 
    1. 유튜브에서 인기 있는 동영상을 찾아 분석(Hook, 구성 요소).
    2. 해당 성공 공식을 반영하여 **JSON 형식의 대본** 자동 작성.
    3. 각 장면별로 필요한 **이미지 프롬프트**와 **나레이션 텍스트** 생성.
    4. **통합 비주얼 스타일** 정의로 모든 이미지의 일관성 보장.

**대본 구조:**
```json
{
  "global_visual_style": "warm cinematic lighting, vibrant colors, professional photography style, 4k quality",
  "scenes": [
    {
      "scene_id": 1,
      "visual_description": "Close-up shot of a clock face",
      "audio_text": "건강을 지키는 비법을 공개합니다",
      "duration": 3
    }
  ]
}
```

### 2️⃣ 시각 자료 생성 (Visuals)
- **Engine**: **Google Imagen 4.0 Fast**
- **역할**: 대본의 프롬프트를 바탕으로 **고화질 세로(9:16) 이미지** 생성.
- **특징**: 
    - 단순한 사진이 아니라 시네마틱 조명과 구도가 적용된 고퀄리티 아트 생성.
    - **배치 생성**: 여러 이미지를 병렬 처리하여 시간 단축 (50-70% 단축).
    - **스타일 일관성**: `global_visual_style`이 모든 이미지에 자동 적용.

**이미지 생성 방식:**
- 각 장면의 `visual_description` + `global_visual_style` = 최종 프롬프트
- 예: `"Close-up of clock, warm cinematic lighting, vibrant colors, professional photography style, 4k quality"`

### 3️⃣ 오디오 생성 (Audio)
- **Engine**: **Gemini 2.5 Flash Preview TTS**
- **역할**: 각 장면의 나레이션을 **자연스러운 성우 목소리**로 생성.
- **특징**: 
    - **장면별 개별 오디오**: 각 장면마다 별도 TTS 생성으로 정확한 타이밍 보장.
    - **자동 길이 측정**: 실제 오디오 길이를 측정하여 `duration` 자동 업데이트.
    - **자동 재시도**: 503 서버 과부하 시 자동으로 3회까지 재시도.
    - 한국어 발음이 자연스러우며 추가 비용이 거의 없음.

**오디오 생성 흐름:**
```
Scene 1: "건강 비법" → TTS → 2.8초 오디오 → duration = 2.8초
Scene 2: "신선한 채소" → TTS → 3.2초 오디오 → duration = 3.2초
...
최종 영상 길이 = 모든 장면 duration 합계 (10-20초)
```

### 4️⃣ 영상 합성 & 편집 (Composition)
- **Tool**: **Python MoviePy**
- **역할**:
    1. **Ken Burns Effects**: 정지된 이미지에 천천히 줌인(Zoom-in)하는 모션 효과를 주어 동영상처럼 만듦.
    2. **장면별 오디오 동기화**: 각 장면에 해당 오디오를 정확히 매칭.
    3. **Subtitle**: 나레이션 타이밍에 맞춰 자막 자동 생성 및 삽입.
    4. **Rendering**: 최종 `.mp4` 파일로 렌더링 (1080x1920, 9:16 비율).

**영상 합성 특징:**
- 각 장면이 해당 오디오와 정확히 일치 (애매하게 끝나지 않음).
- 자연스러운 전환과 흐름.
- 자동 폴더 구조: `output/{영상제목}_{날짜}/`

## 🚀 사용법 (How to Run)

1. **필수 요건 설치**:
    ```bash
    python3 -m pip install -r requirements.txt
    ```

2. **환경 변수 설정**:
    - `.env` 파일 생성
    - `GOOGLE_API_KEY` (Gemini API 키)
    - `YOUTUBE_API_KEY` (YouTube Data API 키)

3. **실행**:
    ```bash
    python main.py
    ```

4. **결과물**:
    ```
    output/
      └── {영상제목}_{날짜}/
          ├── audio_scene_1.wav
          ├── audio_scene_2.wav
          ├── scene_1.png
          ├── scene_2.png
          ├── ...
          └── final_short.mp4
    ```

## 🎯 주요 개선 사항 (최신 버전)

### ✅ 스타일 일관성 보장
- `global_visual_style`로 모든 이미지가 동일한 스타일 유지
- 조명, 색상, 아트 디렉션이 완벽히 일치

### ✅ 정확한 타이밍
- 장면별 개별 오디오 생성으로 나레이션과 영상이 정확히 일치
- 실제 오디오 길이 기반으로 duration 자동 설정

### ✅ 배치 처리 & 병렬화
- 이미지 배치 생성으로 스타일 일관성 확보
- 병렬 처리로 생성 시간 50-70% 단축

### ✅ 유연한 영상 길이
- 10-20초 범위 (이상적으로 15초)
- 스토리 완성도 우선, 길이는 자연스럽게 결정

### ✅ 강화된 에러 처리
- 503 서버 과부하 자동 재시도
- 상세한 에러 메시지와 해결 방법 제시

## 📊 비용 구조

| 항목 | 비용 | 비고 |
|------|------|------|
| Gemini 분석/대본 | ~10-20원 | 트렌드 분석 + 대본 생성 |
| Imagen 이미지 | ~150-180원 | 이미지당 30-40원 × 5개 |
| Gemini TTS | ~10-20원 | 장면별 개별 생성 (문자 수 기반) |
| **총합** | **~200원** | 영상 1편당 |

## 📂 프로젝트 구조

```
.
├── main.py                      # 메인 실행 파일 (파이프라인 오케스트레이션)
├── src/
│   ├── youtube_client.py        # YouTube API 클라이언트
│   ├── gemini_analyzer.py       # 대본 작성 및 트렌드 분석 (Gemini Flash)
│   ├── image_generator.py       # 이미지 생성 (Imagen 4.0) + 배치 처리
│   ├── audio_generator.py       # 나레이션 생성 (Gemini 2.5 TTS) + 장면별 개별
│   ├── motion_effects.py        # 영상 편집, 자막, 효과 (MoviePy)
│   └── video_generator_imagen.py # (레거시) 대체 이미지 생성기
├── output/                      # 생성된 영상 저장 폴더
│   └── {영상제목}_{날짜}/       # 각 영상별 폴더
├── doc/
│   └── shorts_automation_guide.md  # 이 문서
└── requirements.txt             # 필수 패키지 목록
```

## 📝 프롬프트 요청 예시 (Future Request)
다른 프로젝트에서 이 방식을 다시 구현하고 싶다면, AI에게 다음과 같이 요청하세요:

> "지난번 Antigravity 프로젝트처럼 **'Imagen 4.0 이미지 생성 + MoviePy Ken Burns 효과 + Gemini 2.5 TTS 장면별 개별 생성'** 조합으로 저예산 쇼츠 자동화 파이프라인을 구축해줘. 스타일 일관성을 위해 global_visual_style을 사용하고, 장면별 개별 오디오로 정확한 타이밍을 보장해야 해."

## 🔧 기술 스택

- **Python 3.x**
- **Google Gemini API**: 분석, 대본 생성, TTS
- **Google Imagen API**: 이미지 생성
- **YouTube Data API**: 트렌딩 영상 검색
- **MoviePy**: 영상 편집 및 합성
- **pydub**: 오디오 변환 (선택사항)

## 💡 최적화 팁

1. **이미지 생성 시간 단축**: 병렬 처리 모드 사용 (기본값)
2. **비용 절감**: 불필요한 재시도 방지, 에러 처리 강화
3. **품질 향상**: `global_visual_style`을 구체적으로 설정
4. **안정성**: 503 에러 자동 재시도로 서버 과부하 대응
