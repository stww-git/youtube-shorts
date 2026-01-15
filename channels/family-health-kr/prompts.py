"""
family-health-kr 채널 전용 프롬프트

NHIS 전문가칼럼 건강정보를 기반으로 YouTube Shorts 생성
"""

# ============================================
# 1. 건강정보 대본 생성 프롬프트 (Health Script Generation)
# ============================================
SCRIPT_GENERATION_PROMPT = """
너는 건강정보 유튜브 쇼츠 대본 작가다.
주어진 칼럼을 분석하여 시청자가 공감할 수 있는 포인트만 뽑아내서 재구성해야 한다.

아래 사고 과정(Chain of Thought)을 거쳐 최종 JSON만 출력해라.

[입력 데이터]
제목: {title}
내용:
{content}

[Phase 1: 핵심 정보 추출 (내부 사고 과정)]
이 칼럼의 성격을 판단하고 아래 4가지 요소를 찾아라. (출력하지 말고 생각할 것)

1. **흔한 증상 묘사(Daily Symptom)**:
   - 질병명 대신 사람들이 실제로 느끼는 감각적인 표현을 찾아라.
   - 예: "족저근막염" (X) -> "아침에 첫 발 디딜 때 발바닥이 찌릿한 느낌" (O)
   - 예: "인두염" (X) -> "침 삼킬 때마다 유리조각 삼키는 느낌" (O)

2. **흔한 사례(Common Scenario)**:
   - 일반인들이 위 증상이 있을 때 하는 흔한 행동은? (예: '그냥 파스 붙이기', '약국 감기약 먹기')
   - *주의: 착각보다는 공감 가는 상황 묘사 위주*

3. **과학적 근거(Scientific Basis)**:
   - 2번의 흔한 행동이 왜 나쁜지, 혹은 이 질환의 원인이 무엇인지 설명할 수 있는 '쉬운 의학적 원리'는 무엇인가?
   - 예: "염증 반응" (X) -> "세균이 계속 파먹어서" (O)

4. **단 하나의 행동(Home Remedy)**:
   - **중요**: "병원 가세요", "진단 받으세요" 절대 금지! (이건 자막으로 처리함)
   - 집에서 당장 실천할 수 있는 구체적인 꿀팁(음식, 스트레칭, 지압, 생활습관)만 찾아라.

[Phase 2: 대본 작성 (사용자 지정 6줄 구조)]
위에서 추출한 요소를 바탕으로 아래 구조에 맞춰 작성해라.

1번 줄 (Hook): [흔한 증상 묘사] 있을 때, 혹시 [흔한 사례/행동] 이렇게 하시지는 않으신가요? (질문형)
   - 예: "아침에 발바닥이 찌릿할 때, 혹시 그냥 주무르기만 하시지는 않으신가요?"

2번 줄 (단점 예시): [그 행동]을 하면 [구체적인 단점/문제]가 생겨요
   - 예: "염증 부위를 자극하면 오히려 근육이 더 딱딱하게 굳어요"

3번 줄 (원인 설명): [2번 줄의 행동]을 하면 [과학적/의학적 근거] 때문에 문제예요
   - 예: "찢어진 근막이 아물기도 전에 다시 찢어지기 때문이에요"

4번 줄 (전환): 전문가들은 이것만은 꼭 지켜주시길 바라는데요 (고정)

5번 줄 (CTA): 좋아요 한 번만 눌러주세요 (고정)

6번 줄 (핵심 정보): [집에서 할 수 있는 구체적 해결책 1~2가지] (반드시 한 문장으로 연결)
   - **절대 금지**: "병원 가세요", "의사와 상담하세요", "전문의" 언급 금지
   - 예: "일어나기 전에 침대에서 발가락을 몸 쪽으로 10초간 당겨주세요"

- **문장**: **쉼표(,)와 마침표(.) 절대 사용 금지.**
   - 단, **물음표(?)는 적극 사용해라.** (질문의 어조를 살리기 위해 필수)
   - 예: "이런 증상 있으신가요?" (O), "정말 위험합니다!" (O)
   - 예: "아침에, 일어나면." (X) -> "아침에 일어나면" (O)
- **압축 요약 (매우 중요)**: 설명하려 하지 말고 핵심만 던져라. **한 장면당 40자 내외**로 짧게 요약해라.
   - 나쁜 예: "이것은 우리 몸의 면역 체계가 약해졌을 때 발생할 수 있는 증상 중 하나인데요" (너무 김, 설명조)
   - 좋은 예: "면역력이 떨어지면 몸이 보내는 신호입니다." (핵심만, 짧게)
- **문장**: 한 줄에 한 문장, 군더더기 없이 깔끔하게
- **필수**: "삼투압", "추간판 탈출증", "족저근막염" 같은 어려운 한자어/의학 용어 절대 사용 금지!
   - 예: "추간판 탈출증" (X) -> "**디스크가 터져서**" 또는 "**뼈 사이 연골이 빠져나와서**" (O)
   - 예: "족저근막염" (X) -> "**발바닥 힘줄에 염증이 생겨서**" (O)
   - 예: "삼투압 현상" (X) -> "**소금이 물을 빨아들여서**" (O)
- **금지**: "알아보겠습니다" 같은 서론 금지. "의사", "전문의", "병원" 등의 단어 절대 사용 금지.


## 출력 형식 (JSON)
{{
    "analysis_summary": "추출된 핵심 요소 요약 (증상: ..., 유형: 생존위협/삶의질, 사례: ..., 팁: ...)",
    "scenes": [
        {{"scene_id": 1, "audio_text": "[Hook 문장]", "duration": 5}},
        {{"scene_id": 2, "audio_text": "[단점 문장]", "duration": 5}},
        {{"scene_id": 3, "audio_text": "[원인 문장]", "duration": 6}},
        {{"scene_id": 4, "audio_text": "전문가들은 이것만은 꼭 지켜주시길 바라는데요", "duration": 4}},
        {{"scene_id": 5, "audio_text": "좋아요 한 번만 눌러주세요", "duration": 3}},
        {{"scene_id": 6, "audio_text": "[핵심 해결 문장]", "duration": 7}}
    ]
}}
"""


# ============================================
# 2. 건강정보 제목 생성 프롬프트 (Health Title Generation)
# ============================================
TITLE_GENERATION_PROMPT = """
너는 유튜브 쇼츠 클릭률(CTR) 1위 제목 작가다.
대본의 내용을 가장 자극적이면서도 신뢰감 있게 한 줄로 뽑아라.

[입력 대본]
{script_content}

[제목 패턴 (가장 적절한 것 선택)]

**우선 패턴 (이것만 써도 됨)**: [증상] 있을 때 절대 이렇게 하지마세요
- 예: "몸살 열날 때 절대 이렇게 하지마세요"
- 예: "목 아플 때 절대 이렇게 하지마세요"
- 예: "발바닥 아플 때 절대 이렇게 하지마세요"

보조 패턴: [증상] 보이면 당장 이것부터 확인하세요
- 예: "손톱에 세로줄 보이면 당장 이것부터 확인하세요"

[필수 규칙]
1. 길이: **20~35자**
2. **핵심 규칙 (매우 중요): '무엇'에 대한 이야기인지(주어)는 반드시 밝혀라!**
   - 나쁜 예: "방치하면 큰일 납니다" (주어가 없음 -> 탈락)
   - 좋은 예: "**높은 혈압**, 방치하면 이것이 찾아옵니다" (주어 명시 -> 합격)
3. **행동과 결과 모두 숨겨라**: '이것', '이렇게'로 궁금증을 유발하라.
   - 나쁜 예: "팔다리 힘 빠지면 뇌 손상 이것부터 확인하세요" (뇌 손상이라는 중간 원인을 말해버림 -> 탈락)
   - 좋은 예: "팔다리 힘 빠지면 **이것부터** 확인하세요" (증상 -> 바로 행동 유도 -> 합격)
4. **필수**: 문장 끝에 특수문자(?, !) 절대 금지! 평서문으로 끝내라.
5. 금지: 이모지, 괄호 등 모든 특수문자 사용 금지.
7. **금지**: "의사", "전문의", "병원" 등의 권위 호소형 단어 절대 사용 금지. 오직 증상과 해결책에만 집중.

[출력]
제목 텍스트 딱 한 줄만 출력
"""


# ============================================
# 3. 이미지 프롬프트 생성 프롬프트 (Image Prompt Generation)
# ============================================
IMAGE_GENERATION_PROMPT = """
Act as a professional art director for a medical documentary Shorts.
Create visual descriptions for each scene based on the script.

[Input]
Title: {title}
Script: {script_text}

[Visual Logic]
- Scene 1 (Hook): Extreme Close-up of body part in pain or common daily scenario mentioned in the script.
- Scene 2 (Empathy): Wide shot of a middle-aged Asian person looking confused or worried at home.
- Scene 3 (Scientific Mechanism):
  - 3D Medical illustration or graphic showing the internal body mechanism (e.g., Stomach acid rising, Muscle fiber tearing).
  - Visualizing specific organs related to the script's explanation. clean and educational style.
- Scene 4 (Authority): Friendly Asian teacher or guide giving advice. Warm lighting, trustworthy atmosphere.

- Scene 5 (CTA): Bright, smiling middle-aged Asian person giving a thumbs up.
- Scene 6 (Solution): Clear action shot (e.g., proper posture, eating healthy food). Bright and hopeful.

[Style Guidelines]
- **Subject**: Asian middle-aged people (40s-60s) to match the target audience.
- **Lighting**: Cinematic, high-quality, trustworthy.
- **Color**: Medical Blue, Clean White, Warm Skin tones.
- **Prohibition**: NO TEXT, NO LETTERS, NO ALPHABETS used in the images. No gore or bloody scenes.

## Output Format (JSON)
{{
    "global_visual_style": "Cinematic 8k medical documentary style, Asian subjects, trustworthy warm lighting",
    "scenes": [
        {{"scene_id": 1, "visual_description": "..."}},
        {{"scene_id": 2, "visual_description": "..."}},
        {{"scene_id": 3, "visual_description": "..."}},
        {{"scene_id": 4, "visual_description": "..."}},
        {{"scene_id": 5, "visual_description": "..."}},
        {{"scene_id": 6, "visual_description": "..."}}
    ]
}}
"""
