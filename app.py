# app.py
import os, json, re, datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# === 스케줄 로드: clean_schedule.json은 app.py와 같은 폴더에 두세요 ===
with open(os.path.join(os.path.dirname(__file__), "clean_schedule.json"), "r", encoding="utf-8") as f:
    SCHEDULE = json.load(f)

KST = datetime.timezone(datetime.timedelta(hours=9))

def kakao_text(msg: str):
    # 카카오 오픈빌더 v2.0 simpleText
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": msg}}
            ]
        }
    }

def fmt(date_obj: datetime.date) -> str:
    return date_obj.strftime("%Y-%m-%d")

def cleaners_for(date_obj: datetime.date):
    """해당 날짜의 당번 목록(list[str])을 반환 (없으면 None)"""
    return SCHEDULE.get(fmt(date_obj))

def parse_target_date(utter: str, today: datetime.date):
    """발화에서 날짜 의도를 파싱: 오늘/내일/YYYY-MM-DD/ M월 D일"""
    utter = utter.strip()
    if "오늘" in utter:
        return today
    if "내일" in utter:
        return today + datetime.timedelta(days=1)

    m = re.search(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", utter)  # 2025-04-28
    if m:
        y, mo, d = map(int, m.groups())
        return datetime.date(y, mo, d)

    m2 = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", utter)  # 4월 28일
    if m2:
        mo, d = map(int, m2.groups())
        return datetime.date(today.year, mo, d)

    return None

def week_days_of(date_obj: datetime.date):
    """해당 날짜가 속한 주(월~금) 날짜 리스트 반환"""
    monday = date_obj - datetime.timedelta(days=date_obj.weekday())  # 월요일
    return [monday + datetime.timedelta(days=i) for i in range(5)]   # 월~금

@app.route("/kakao/cleaner", methods=["POST"])
def cleaner():
    body = request.get_json(silent=True) or {}
    utter = (body.get("userRequest", {}).get("utterance") or "").strip()
    today = datetime.datetime.now(KST).date()

    # 1) 이번주
    if "이번주" in utter or "주간" in utter:
        lines = []
        for d in week_days_of(today):
            c = cleaners_for(d)
            if c:
                lines.append(f"{fmt(d)}\n- " + "\n- ".join(c))
            else:
                lines.append(f"{fmt(d)}\n- 당번 정보가 없습니다.")
        return jsonify(kakao_text("이번주 청소 당번\n\n" + "\n\n".join(lines)))

    # 2) 특정일(오늘/내일/날짜 파싱)
    target = parse_target_date(utter, today)
    if not target:
        return jsonify(kakao_text(
            "청소 당번 조회 방법\n"
            "• 오늘 당번\n"
            "• 내일 당번\n"
            "• 2025-04-28 당번\n"
            "• 4월 28일 당번"
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
