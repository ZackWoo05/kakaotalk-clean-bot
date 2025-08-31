import os, json, datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# === 스케줄 불러오기 ===
with open("clean_schedule.json", "r", encoding="utf-8") as f:
    SCHEDULE = json.load(f)

KST = datetime.timezone(datetime.timedelta(hours=9))

def kakao_text(msg: str):
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": msg}}
            ]
        }
    }

@app.route("/kakao/cleaner", methods=["POST"])
def cleaner():
    body = request.get_json(silent=True) or {}
    utter = (body.get("userRequest", {}).get("utterance") or "").strip()

    today = datetime.datetime.now(KST).date()

    # 발화 분석
    if "오늘" in utter:
        target = today
    elif "내일" in utter:
        target = today + datetime.timedelta(days=1)
    else:
        # "2025-04-28" 혹은 "4월 28일" 패턴 잡기
        import re
        target = None
        m = re.search(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", utter)
        if m:
            y, mth, d = map(int, m.groups())
            target = datetime.date(y, mth, d)
        else:
            m2 = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", utter)
            if m2:
                y = today.year
                mth, d = map(int, m2.groups())
                target = datetime.date(y, mth, d)

    if not target:
        return jsonify(kakao_text("예) '오늘 당번', '내일 당번', '2025-04-28 당번' 처럼 물어봐 주세요."))

    key = target.strftime("%Y-%m-%d")
    cleaners = SCHEDULE.get(key)

    if not cleaners:
        return jsonify(kakao_text(f"{key} 당번 정보가 없어요."))

    msg = f"{key} 청소 당번\n" + "\n".join(f"- {c}" for c in cleaners)
    return jsonify(kakao_text(msg))
