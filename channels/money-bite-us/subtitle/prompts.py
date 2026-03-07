"""
Money Bite US Channel Subtitle Effect Prompts
Mode-specific prompts (common rules + mode-specific splitting rules)

Key differences from Korean version:
- English uses word-based splitting, not syllable-based
- Character counts are higher (English words are wider)
- Min chunk length adjusted for English word boundaries
- Examples use English finance terms
"""

# ============================================================
# Common Rules (shared across all modes)
# ============================================================
_SUBTITLE_COMMON_INTRO = """You are a **subtitle effect choreographer** for YouTube Shorts finance education videos.
Analyze the script below, split each sentence into natural phrase chunks,
decide which chunks get visual effects, and assign colors to key terms.

[Script]
{script_text}
"""

_SUBTITLE_COMMON_EFFECTS = """
==============================================
[Available Effects — only 2 types]
==============================================
1. "bounce" — pop-in size animation (only for emphasis chunks)
2. null — no effect (regular chunks)

==============================================
[Available Text Colors — 3 options]
==============================================
1. "#FFD700" — Gold (finance terms, key concepts, emphasis)
2. "#FF3333" — Red (warnings, danger, losses, decline)
3. "#00FF88" — Green (tips, solutions, gains, profits)
※ Unassigned chunks default to white
"""

_SUBTITLE_COMMON_RULES = """
==============================================
[Core Rules — MUST follow]
==============================================
1. **Output ALL scenes** from the script
2. **Maximum 2 bounces per sentence** (all others must be null)
3. **Joining all words texts with spaces must exactly reproduce the original sentence**
   - Original: "What is P/E ratio?"
   - words: ["What is", "P/E ratio?"]
   → Joined: "What is P/E ratio?" ✅
   - **Do NOT modify, omit, or add any words**
4. **Split strictly by meaning units (natural breath groups) — never break mid-phrase**
   - (Critical) Never split compound terms, phrasal verbs, or noun phrases
   - Bad: ["the price", "to earnings ratio"] → splits "price to earnings" ❌
   - Good: ["the price to earnings ratio"] ✅
   - Bad: ["if you", "ignore"] → too short ❌
   - Good: ["if you ignore this"] ✅
5. **color_keywords should only include words that need coloring** (most chunks need no color)
"""

_SUBTITLE_COMMON_SCENE_GUIDE = """
==============================================
[Scene Guidelines]
==============================================
- Scene 1 (Hook question): display=single
  → Finance term gets bounce + gold

- Scene 2–6 (Body explanation): display=single
  → Key finance terms get bounce + gold
  → Warning/danger phrases get red
  → Tips/solutions get green
  → Keep effects to 0–2 per scene

- Scene 7 (One-line takeaway): display=single
  → Key takeaway phrase gets bounce + gold or green
"""

_SUBTITLE_COMMON_OUTPUT = """
==============================================
[Output Format]
==============================================
{{
    "scenes": [
        {{
            "scene_id": 1,
            "display": "single",
            "words": [
                {{"text": "What is", "effect": null}},
                {{"text": "P/E ratio?", "effect": "bounce"}}
            ]
        }},
        ...
    ],
    "color_keywords": {{
        "#FFD700": ["P/E ratio?"],
        "#FF3333": [],
        "#00FF88": []
    }}
}}

⚠️ Output ONLY valid JSON. No explanations, markdown, or code blocks.
⚠️ Include ALL scenes and color_keywords.
"""

# Phrase mode Scene Guide (display=phrase)
_SUBTITLE_PHRASE_SCENE_GUIDE = """
==============================================
[Scene Guidelines — phrase mode]
==============================================
- Scene 1 (Hook question): display=phrase
  → Finance term gets bounce + gold
  → Split into 2–3 meaning chunks

- Scene 2–6 (Body explanation): display=phrase
  → Key finance terms get bounce + gold
  → Warning/danger phrases get red
  → Tips/solutions get green
  → Keep effects to 0–2 per scene
  → Split into 2–3 meaning chunks

- Scene 7 (One-line takeaway): display=phrase
  → Key takeaway phrase gets bounce + gold or green
  → Split into 2–3 meaning chunks

※ Very short sentences (questions, CTAs) can use display=static
"""

# Phrase mode Output Format
_SUBTITLE_PHRASE_OUTPUT = """
==============================================
[Output Format — phrase mode]
==============================================
Input script:
1. P/E ratio is the stock price divided by earnings per share

Output example:
{{
    "scenes": [
        {{
            "scene_id": 1,
            "display": "phrase",
            "words": [
                {{"text": "P/E ratio is", "effect": "bounce"}},
                {{"text": "the stock price divided by", "effect": null}},
                {{"text": "earnings per share", "effect": null}}
            ]
        }},
        ...
    ],
    "color_keywords": {{
        "#FFD700": ["P/E ratio is"],
        "#FF3333": [],
        "#00FF88": []
    }}
}}

⚠️ Output ONLY valid JSON. No explanations, markdown, or code blocks.
⚠️ Include ALL scenes and color_keywords.
⚠️ Each chunk must be at least 3 words. Merge short chunks with adjacent ones.
"""


# ============================================================
# Single Mode Prompt
# ============================================================
SUBTITLE_EFFECT_PROMPT_SINGLE = (
    _SUBTITLE_COMMON_INTRO
    + _SUBTITLE_COMMON_EFFECTS
    + _SUBTITLE_COMMON_RULES
    + """
==============================================
[single mode splitting rules]
==============================================
- One chunk is displayed alone at the center of the screen.
- Each chunk: minimum **2 words**, maximum **{max_chunk_chars} characters** (including spaces).
- If a chunk exceeds {max_chunk_chars} characters, split at a natural phrase boundary.
"""
    + _SUBTITLE_COMMON_SCENE_GUIDE
    + _SUBTITLE_COMMON_OUTPUT
)


# ============================================================
# Stack Mode Prompt
# ============================================================
SUBTITLE_EFFECT_PROMPT_STACK = (
    _SUBTITLE_COMMON_INTRO
    + _SUBTITLE_COMMON_EFFECTS
    + _SUBTITLE_COMMON_RULES
    + """
==============================================
[stack mode splitting rules]
==============================================
- Chunks stack as 2 lines (one line added at a time, max 2 lines visible).
- Each chunk: minimum **3 words**, maximum **{max_chunk_chars} characters** (including spaces).
- **Single-word chunks are forbidden — always merge with adjacent chunk.**
  - Bad: ["divided"] (1 word) → looks empty on a line ❌
  - Good: ["divided by the total shares"] ✅
- Keep adjacent chunks roughly equal in length.
"""
    + _SUBTITLE_COMMON_SCENE_GUIDE
    + _SUBTITLE_COMMON_OUTPUT
)


# ============================================================
# Phrase Mode Prompt
# ============================================================
SUBTITLE_EFFECT_PROMPT_PHRASE = (
    _SUBTITLE_COMMON_INTRO
    + _SUBTITLE_COMMON_EFFECTS
    + _SUBTITLE_COMMON_RULES
    + """
==============================================
[phrase mode splitting rules]
==============================================
- Phrases are displayed at the center of the screen. When a new phrase appears, it **completely replaces** the previous one.
- One chunk = **one complete thought** (subject+verb, noun phrase+verb phrase, etc.)
- Each chunk: minimum **3 words**, maximum **{max_chunk_chars} characters** (including spaces).
- If a chunk exceeds {max_chunk_chars} characters, split at a natural phrase boundary.
- **Chunks shorter than 3 words are FORBIDDEN — always merge with adjacent chunk.**
- **Split each sentence into 2–3 chunks (never more than 3)**
- Keep adjacent chunks roughly equal in length.
- Good examples:
  - ["P/E ratio is", "the stock price divided by", "earnings per share"] → 3 chunks ✅
  - ["If you ignore this", "you could end up overpaying", "at the absolute peak"] → 3 chunks ✅
  - ["What is P/E ratio?"] → short sentence stays as 1 chunk ✅
- Bad examples:
  - ["P/E", "ratio?"] → too short ❌
  - ["The", "stock price", "divided by", "earnings", "per share"] → 5 chunks, way too fragmented ❌
  - ["The stock price divided by earnings per", "share"] → unbalanced ❌
"""
    + _SUBTITLE_PHRASE_SCENE_GUIDE
    + _SUBTITLE_PHRASE_OUTPUT
)


# ============================================================
# Static Mode Prompt
# ============================================================
SUBTITLE_EFFECT_PROMPT_STATIC = (
    _SUBTITLE_COMMON_INTRO
    + _SUBTITLE_COMMON_EFFECTS
    + _SUBTITLE_COMMON_RULES
    + """
==============================================
[static mode rules]
==============================================
- Display the entire sentence at once.
- No splitting needed: put the entire sentence as one text in words.
- display MUST be set to "static".
"""
    + _SUBTITLE_COMMON_SCENE_GUIDE
    + _SUBTITLE_COMMON_OUTPUT
)


# ============================================================
# Prompt Selection Helper
# ============================================================
SUBTITLE_PROMPT_MAP = {
    "single": SUBTITLE_EFFECT_PROMPT_SINGLE,
    "stack": SUBTITLE_EFFECT_PROMPT_STACK,
    "phrase": SUBTITLE_EFFECT_PROMPT_PHRASE,
    "static": SUBTITLE_EFFECT_PROMPT_STATIC,
    "accumulate": SUBTITLE_EFFECT_PROMPT_SINGLE,
}

def get_subtitle_prompt(subtitle_mode: str) -> str:
    """Returns the prompt template for the given subtitle mode."""
    return SUBTITLE_PROMPT_MAP.get(subtitle_mode, SUBTITLE_EFFECT_PROMPT_SINGLE)
