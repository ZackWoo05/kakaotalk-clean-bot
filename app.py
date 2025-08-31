from flask import Flask, request, jsonify, make_response
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

app = Flask(__name__)
KST = ZoneInfo("Asia/Seoul")

def kakao_simple_text(text: str) -> dict:
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": text}}
            ]
        }
    }

def make_kakao_response(payload: dict):
    resp = make_response(jsonify(payload), 200)
    resp.headers["Content-Type"] = "application/json; charset=utf-8"
    return resp

@app.route("/kakao/cleaner", methods=["POST"])
def kakao_cleaner():
    body = request.get_json(silent=True) or {}
    utter = (body.get("userRequest", {}).get("utterance") or "").strip()

    today = datetime.now(KST).date()
    if "내일" in utter:
        text = "내일 당번 안내입니다."  # ← 실제 로직으로 교체
    elif "이번주" in utter:
        text = "이번주 당번 안내입니다."  # ← 실제 로직으로 교체
    elif "도움말" in utter:
        text = "‘오늘 당번’, ‘내일 당번’, ‘이번주 당번’으로 물어보세요."
    else:
        # 기본: 오늘
        text = "오늘은 주말이라 당번이 없습니다." if today.weekday() >= 5 else "오늘 당번 안내입니다."  # ← 실제 로직

    return make_kakao_response(kakao_simple_text(text))
