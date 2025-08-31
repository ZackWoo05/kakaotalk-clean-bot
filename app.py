# app.py
import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from flask import Flask, request, jsonify

app = Flask(__name__)

# ---- 설정 ----
STUDENTS = [
    "3-2 김민수","3-2 이서연","3-2 박지훈","3-2 최유진",
    "3-2 정유나","3-2 김도윤","3-2 박서준","3-2 한지민",
]
ROTATION_START = date(2025, 9, 1)        # 당번 시작 기준일
KST = ZoneInfo("Asia/Seoul")
SKIP_WEEKENDS = True                     # 주말 제외
# --------------

def nth_weekday_index(target: date, start: date) -> int:
    """start 기준으로 평일만 세서 target의 인덱스 반환(음수/양수 모두)."""
    step = 1 if target >= start else -1
    d, cnt = start, 0
    while d != target:
        d += timedelta(days=step)
        if (not SKIP_WEEKENDS) or (d.weekday() < 5):
            cnt += step
    return cnt

def assign_for_day(d: date) -> str:
    if SKIP_WEEKENDS and d.weekday() >= 5:
        return "오늘은 주말이라 당번이 없습니다."
    idx = nth_weekday_index(d, ROTATION_START) % len(STUDENTS)
    return f"{d.strftime('%Y-%m-%d')} 청소당번: {STUDENTS[idx]}"

def kakao_simple_text(text: str):
    """⚠️ 카카오 v2.0 스펙에 맞춘 응답. 필드명/배열 구조 정확히 유지."""
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": text}}
            ],
            # 필요 없으면 quickReplies 생략 가능하지만, 비워둘 때는 []로 둬도 OK
            # "quickReplies": [
            #     {"action":"message","label":"오늘 당번","messageText":"오늘 당번"},
            #     {"action":"message","label":"내일 당번","messageText":"내일 당번"},
            #     {"action":"message","label":"이번주 당번","messageText":"이번주 당번"},
            #     {"action":"message","label":"도움말","messageText":"도움말"},
            # ]
        }
    }

@app.route("/kakao/cleaner", methods=["POST"])
def kakao_cleaner():
    body = request.get_json(silent=True) or {}
    utter = (body.get("userRequest", {}).get("utterance") or "").strip()

    today = datetime.now(KST).date()

    if "내일" in utter:
        msg = assign_for_day(today + timedelta(days=1))
    elif "이번주" in utter or "주간" in utter:
        week_start = today - timedelta(days=today.weekday())
        lines = []
        for i in range(5):        # 월~금
            d = week_start + timedelta(days=i)
            lines.append(assign_for_day(d))
        msg = "\n".join(lines)
    elif "도움말" in utter or "help" in utter.lower():
        msg = (
            "청소당번 안내 봇입니다.\n"
            "- '오늘 당번' : 오늘 담당자\n"
            "- '내일 당번' : 내일 담당자\n"
            "- '이번주 당번' : 월~금 담당자"
        )
    else:  # 기본: 오늘
        msg = assign_for_day(today)

    return jsonify(kakao_simple_text(msg))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
