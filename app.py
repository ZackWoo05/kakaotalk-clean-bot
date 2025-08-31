# app.py
import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from flask import Flask, request, jsonify

app = Flask(__name__)

# ====== 설정 (여기만 바꾸면 됨) ======
STUDENTS = [
    "3-2 김민수", "3-2 이서연", "3-2 박지훈", "3-2 최유진",
    "3-2 정유나", "3-2 김도윤", "3-2 박서준", "3-2 한지민",
]
ROTATION_START = date(2025, 9, 1)   # 로테이션 시작일
KST = ZoneInfo("Asia/Seoul")
SKIP_WEEKENDS = True                # 주말 제외
# ====================================

def nth_weekday_index(target_date: date, start_date: date) -> int:
    """start_date~target_date 사이 '평일'만 세서 0부터 인덱스 반환"""
    step = 1 if target_date >= start_date else -1
    d, count = start_date, 0
    while d != target_date:
        d += timedelta(days=step)
        if not SKIP_WEEKENDS or d.weekday() < 5:
            count += step
    return count

def assign_for_day(d: date) -> str:
    if SKIP_WEEKENDS and d.weekday() >= 5:
        return "오늘은 주말이라 당번이 없습니다."
    idx = nth_weekday_index(d, ROTATION_START) % len(STUDENTS)
    return f"{d.strftime('%Y-%m-%d')} 청소당번: {STUDENTS[idx]}"

def build_kakao_response(text: str):
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": text}}
            ],
            "quickReplies": [
                {"label": "오늘 당번", "action": "message", "messageText": "오늘 당번"},
                {"label": "내일 당번", "action": "message", "messageText": "내일 당번"},
                {"label": "이번주",   "action": "message", "messageText": "이번주 당번"},
                {"label": "도움말",   "action": "message", "messageText": "도움말"},
            ]
        }
    }

@app.route("/kakao/cleaner", methods=["POST"])
def kakao_cleaner():
    body = request.get_json(silent=True) or {}
    utter = (body.get("userRequest", {}).get("utterance") or "").strip()

    today_kst = datetime.now(KST).date()

    if "내일" in utter:
        msg = assign_for_day(today_kst + timedelta(days=1))
    elif "이번주" in utter or "주간" in utter:
        week_start = today_kst - timedelta(days=today_kst.weekday())  # 월요일
        lines = []
        for i in range(5):  # 월~금
            d = week_start + timedelta(days=i)
            lines.append(assign_for_day(d))
        msg = "\n".join(lines)
    elif "도움말" in utter or "help" in utter.lower():
        msg = (
            "청소당번 안내 봇입니다.\n"
            "- '오늘 당번' : 오늘 담당자\n"
            "- '내일 당번' : 내일 담당자\n"
            "- '이번주 당번' : 월~금 담당자\n"
            "명단/시작일 수정은 관리자가 서버에서 변경하세요."
        )
    else:
        msg = assign_for_day(today_kst)

    return jsonify(build_kakao_response(msg))

# Render/Heroku 등에서 PORT 환경변수 사용
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
