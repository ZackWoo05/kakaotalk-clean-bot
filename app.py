# app.py
import os, json, re, datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# === 스케줄 로드 ===
with open(os.path.join(os.path.dirname(__file__), "clean_schedule.json"), "r", encoding="utf-8") as f:
    SCHEDULE = json.load(f)

KST = datetime.timezone(datetime.timedelta(hours=9))

def kakao_text(msg: str):
    return {
        "version": "2.0",
        "template": { "outputs": [ { "simpleText": { "text": msg } } ] }
    }

def fmt(d: datetime.date) -> str:
    return d.strftime("%Y-%m-%d")

def normalize6(lst):
    """추출 노이즈 방지: 항목이 7개 이상이어도 항상 6명만 노출"""
    if not lst: 
        return None
    return lst[:6]

def cleaners_for(d: datetime.date):
    key = fmt(d)
    return normalize6(SCHEDULE.get(key))

def parse_target_date(utter: str, today: datetime.date):
    utter = utter.strip()
    if "오늘" in utter:
        return today
    if "내일" in utter:
        return today + datetime.timedelta(days=1)
    m = re.search(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", utter)  # 2025-04-28
    if m:
        y, mo, dd = map(int, m.groups())
        return datetime.date(y, mo, dd)
    m2 = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", utter)      # 4월 28일
    if m2:
        mo, dd = map(int, m2.groups())
        return datetime.date(today.year, mo, dd)
    return None

def week_days_of(d: datetime.date):
    monday = d - datetime.timedelta(days=d.weekday())  # 월요일
    return [monday + datetime.timedelta(days=i) for i in range(5)]  # 월~금

@app.route("/kakao/cleaner", methods=["POST"])
def cleaner():
    body = request.get_json(silent=True) or {}
    utter = (body.get("userRequest", {}).get("utterance") or "").strip()
    today = datetime.datetime.now(KST).date()

    # 주간 요청
    if "이번주" in utter or "주간" in utter:
        blocks = []
        for d in week_days_of(today):
            c = cleaners_for(d)
            if c:
                blocks.append(f"{fmt(d)}\n- " + "\n- ".join(c))
            else:
                blocks.append(f"{fmt(d)}\n- 당번 정보가 없습니다.")
        return jsonify(kakao_text("이번주 청소 당번\n\n" + "\n\n".join(blocks)))

    # 특정일(오늘/내일/날짜 파싱)
    target = parse_target_date(utter, today)
    if not target:
        return jsonify(kakao_text(
            "청소 당번 조회 방법\n"
            "• 오늘 당번\n• 내일 당번\n• 이번주 당번\n"
            "• 2025-04-28 당번\n• 4월 28일 당번"
        ))

    c = cleaners_for(target)
    if not c:
        return jsonify(kakao_text(f"{fmt(target)} 당번 정보가 없습니다."))
    return jsonify(kakao_text(f"{fmt(target)} 청소 당번\n- " + "\n- ".join(c)))

@app.route("/", methods=["GET"])
def health():
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
