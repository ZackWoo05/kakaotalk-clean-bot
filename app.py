# app.py (초간단 버전)
import os, json, re, datetime
from flask import Flask, request, jsonify

app = Flask(__name__)
BASE = os.path.dirname(__file__)

# 그대로 믿고 쓰는 스케줄 JSON (너가 정확히 만든 파일)
with open(os.path.join(BASE, "clean_schedule.json"), "r", encoding="utf-8") as f:
    SCHEDULE = json.load(f)

KST = datetime.timezone(datetime.timedelta(hours=9))
fmt = lambda d: d.strftime("%Y-%m-%d")

def kakao_text(text: str):
    return {"version":"2.0","template":{"outputs":[{"simpleText":{"text":text}}]}}

def parse_date(utter: str, today: datetime.date):
    utter = utter.strip()
    if "오늘" in utter:  return today
    if "내일" in utter:  return today + datetime.timedelta(days=1)

    m = re.search(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", utter)  # 2025-04-28
    if m:
        y, mo, dd = map(int, m.groups())
        return datetime.date(y, mo, dd)

    m2 = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", utter)      # 4월 28일
    if m2:
        mo, dd = map(int, m2.groups())
        return datetime.date(today.year, mo, dd)

    return None

def weekdays_of(d: datetime.date):
    mon = d - datetime.timedelta(days=d.weekday())
    return [mon + datetime.timedelta(days=i) for i in range(5)]  # 월~금

@app.route("/kakao/cleaner", methods=["POST"])
def cleaner():
    body  = request.get_json(silent=True) or {}
    utter = (body.get("userRequest", {}).get("utterance") or "").strip()
    today = datetime.datetime.now(KST).date()

    # 이번주
    if "이번주" in utter or "주간" in utter:
        lines = []
        for day in weekdays_of(today):
            key = fmt(day)
            lst = SCHEDULE.get(key)
            if lst:
                lines.append(f"{key}\n- " + "\n- ".join(lst))
            else:
                lines.append(f"{key}\n- 당번 정보가 없습니다.")
        return jsonify(kakao_text("이번주 청소 당번\n\n" + "\n\n".join(lines)))

    # 특정일 (오늘/내일/직접 날짜)
    target = parse_date(utter, today)
    if not target:
        return jsonify(kakao_text(
            "청소 당번 조회\n"
            "• 오늘 당번\n• 내일 당번\n• 이번주 당번\n"
            "• 2025-04-28 당번 / 4월 28일 당번"
        ))

    key = fmt(target)
    lst = SCHEDULE.get(key)
    if not lst:
        return jsonify(kakao_text(f"{key} 당번 정보가 없습니다."))
    return jsonify(kakao_text(f"{key} 청소 당번\n- " + "\n- ".join(lst)))

@app.route("/", methods=["GET"])
def health():
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
