# Money Bite 자막 분할 및 표시 시스템 분석

> 이 문서는 자막 시스템의 현재 구조, 설정값, 문제점, 개선 방향을 정리한 **살아있는 참고 문서**입니다.

---

## 1. 시스템 아키텍처 (파일 흐름)

```
main.py (설정값)
  └→ pipeline.py (파이프라인 실행)
       ├→ script_generator.py (AI 어절 분리 호출)
       │    └→ prompts.py :: SUBTITLE_EFFECT_PROMPT (어절 분리 규칙)
       └→ motion_effects.py (자막 렌더링)
            ├→ _add_subtitle() (비-AI 경로)
            ├→ _add_subtitle_with_ai_effects() (AI 효과 경로)
            └→ _create_subtitle_image() (이미지 생성)
                 └→ subtitle_config.py (폰트, 색상, 위치)
```

---

## 2. 자막 표시 모드 (`subtitle_mode`)

| 모드 | 설명 | 현재 사용 |
|------|------|----------|
| `static` | 문장 전체를 한 번에 표시 | ❌ |
| `accumulate` | 어절이 하나씩 추가되며 누적 (가로 한 줄) | ❌ |
| `single` | 한 어절씩만 교체하며 표시 | ❌ |
| **`stack`** | **어절 누적 + 줄바꿈 (최대 2줄, 슬라이딩 윈도우)** | **✅ 현재** |

### Stack 모드 동작 방식
```
[Step 1]  "EPS가"
[Step 2]  "EPS가"
          "뭐야?"
[Step 3]  "뭐야?"           ← 1번째 줄이 밀려나감
          "다음 어절..."
```
- 구현 위치: `motion_effects.py` → `_add_subtitle_with_ai_effects()` 내 `subtitle_mode == 'stack'` 분기
- 문장(Scene) 전환 시 자동 리셋 (함수가 Scene 단위로 호출됨)

---

## 3. 현재 설정값 요약

### 3-1. main.py 런타임 설정
| 설정 | 값 | 설명 |
|------|----|------|
| `subtitle_mode` | `"stack"` | 자막 표시 모드 |
| `typing_speed` | `0.5` | 어절당 타이핑 비율 (높을수록 느림) |
| `single_font_size` | `110` | single/stack 모드 폰트 크기 (px) |
| `static_font_size` | `100` | static 모드 폰트 크기 (px) |
| `ai_subtitle_effects` | `True` | AI 어절 분리 사용 여부 |

### 3-2. subtitle_config.py 스타일 설정
| 설정 | 값 | 설명 |
|------|----|------|
| `SUBTITLE_Y_RATIO` | `0.55` | 화면 높이 대비 Y 위치 비율 |
| `SUBTITLE_Y_POSITION` | `1056px` | 실제 Y 좌표 (1920 × 0.55) |
| `SUBTITLE_MAX_WIDTH` | `960px` | 자막 최대 가로 폭 |
| `SUBTITLE_TEXT_COLOR` | `white` | 기본 글자색 |
| `SUBTITLE_STROKE_WIDTH` | `10` | 외곽선 두께 |

### 3-3. 폰트 크기 → 한 줄 최대 글자 수

화면 너비 1080px, 여백 감안 ~1000px 기준:

| 폰트 크기 | 한 줄 최대 글자 수 | 계산식 |
|-----------|------------------|--------|
| 140px | ~7자 | `int(1000/140)` |
| **110px (현재)** | **~9자** | `int(1000/110)` |
| 80px | ~12자 | `int(1000/80)` |

> 이 값은 `script_generator.py`에서 `max_chunk_chars = int(1000 / single_font_size)`로 **동적 계산**되어 `SUBTITLE_EFFECT_PROMPT`에 주입됩니다.

---

## 4. AI 어절 분리 (SUBTITLE_EFFECT_PROMPT)

### 4-1. 현재 규칙 요약
1. 대본의 모든 Scene을 출력
2. 한 문장에 bounce 효과 최대 2개
3. words의 text를 이어붙이면 원문과 정확히 일치해야 함
4. **의미 단위(한 호흡)로 묶기** (글자 수 기계적 끊기 금지)
5. 한 묶음 최대 `{max_chunk_chars}`자 (현재 9자) 초과 시 의미 경계에서 분리

### 4-2. 색상 체계
| 색상 | 용도 |
|------|------|
| `#FFD700` 금색 | 금융 용어, 핵심 개념 |
| `#FF3333` 빨간색 | 경고, 위험, 손실 |
| `#00FF88` 녹색 | 팁, 해결책, 수익 |
| (미지정) 흰색 | 일반 어절 |

---

## 5. 현재 문제점 및 개선 필요 사항

### 5-1. 어절 분리 품질 문제

최신 "EPS" 영상 출력 기준 분석:

| 유형 | 문제 예시 | 분석 |
|------|----------|------|
| **너무 짧은 어절** | `"발행된"` (3자), `"나눈"` (2자), `"벌어도"` (3자), `"기억해"` (3자) | 2~3자 어절이 stack 모드에서 한 줄 전체를 차지하면 시각적으로 허전함 |
| **의미 끊김** | `"돈을 잘"` / `"벌어오는지"` | "돈을 잘 벌어오는지"가 한 덩어리여야 자연스러움 |
| **불완전 구절** | `"그럼 주인"` / `"한 명당"` | "주인 한 명당"이 더 자연스러운 의미 단위 |

### 5-2. 개선 방향 (TODO)

- [ ] **최소 글자 수 하한선 추가**: "한 묶음은 최소 4자 이상. 3자 이하는 인접 어절과 합쳐라" 규칙을 프롬프트에 추가
- [ ] **의미 그룹 예시 보강**: 나쁜 예/좋은 예를 더 추가하여 AI의 분리 정확도 높이기
- [ ] **stack 모드 전용 가이드라인 추가**: "stack 모드에서는 두 줄이 균등한 길이가 되도록 분할" 같은 힌트
- [ ] **max_chunk_chars 최적값 검증**: 현재 9자가 적정한지, 실제 생성 영상에서 검증 필요

---

## 6. 파일별 수정 가이드

| 수정 대상 | 파일 경로 | 목적 |
|----------|----------|------|
| 어절 분리 규칙 | `channels/money-bite/prompts.py` → `SUBTITLE_EFFECT_PROMPT` | AI 분할 품질 개선 |
| 폰트/색상/위치 | `channels/money-bite/src/config/subtitle_config.py` | 자막 스타일 조정 |
| 모드 선택/속도 | `main.py` → `money-bite` 설정 블록 | 런타임 파라미터 변경 |
| 렌더링 로직 | `channels/money-bite/src/motion_effects.py` | 표시 방식 변경 |
| AI 호출/변수 주입 | `channels/money-bite/src/script_generator.py` | 프롬프트 포맷 파라미터 |

---

## 7. 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-03-05 | `stack` 모드 신규 구현 (accumulate + 줄바꿈, 최대 2줄 슬라이딩) |
| 2026-03-05 | `_create_subtitle_image` 줄바꿈(`\n`) 렌더링 버그 수정 |
| 2026-03-05 | 어절 분리 규칙을 글자 수(3~6자) → 의미 단위로 전면 개편 |
| 2026-03-05 | `max_chunk_chars` 동적 계산 도입 (`int(1000/font_size)`) |
| 2026-03-05 | 비유 카테고리 룰렛 도입 (다양한 예시 생성) |
