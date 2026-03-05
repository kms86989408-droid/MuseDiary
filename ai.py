import json
import os
from datetime import date, datetime
from typing import Any

from openai import OpenAI


FALLBACK_MESSAGE = (
    "최근 감정 기록을 분석해보니, 감정 흐름이 크게 흔들리지는 않지만 "
    "중간중간 피로가 쌓이는 구간이 보입니다.\n"
    "짧은 휴식과 수면 루틴을 점검하면서, 하루 한 번 감정 일기를 이어가 보세요."
)


def _sanitize_mood_mapping(mood_mapping: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in mood_mapping.items() if key != "_id"}


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def generate_mood_report(entries_data: list[dict[str, Any]], mood_mapping: dict[str, Any]) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return FALLBACK_MESSAGE

    client = OpenAI(api_key=api_key)
    cleaned_mood_mapping = _sanitize_mood_mapping(mood_mapping)

    system_prompt = (
        "당신은 사용자의 감정일기를 분석하는 한국어 감정 리포트 도우미입니다. "
        "입력으로 제공된 감정 이력과 감정 카운트를 바탕으로, "
        "현재 감정 패턴을 짧고 따뜻하게 해석하고 조언을해주세요. "
        "출력은 3~4문장, 300자 이내의 한국어 텍스트로만 작성하세요."
    )
    try:
        user_prompt = (
            f"감정 이력 데이터:\n{json.dumps(entries_data, ensure_ascii=False, default=_json_default)}\n\n"
            f"감정 카운트 데이터:\n{json.dumps(cleaned_mood_mapping, ensure_ascii=False, default=_json_default)}"
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            max_tokens=280,
        )
        message = (response.choices[0].message.content or "").strip()
        return message or FALLBACK_MESSAGE
    except Exception:
        return FALLBACK_MESSAGE
