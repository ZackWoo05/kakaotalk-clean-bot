# app.py
import os
import re
import json
import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- 데이터 로드 -------------------------------------------------------------
BASE_DIR = os.path.dirname(__file__)

# 스케줄(JSON) : {"YYYY-MM-DD": ["27 우희재", "13 김수완", ...], ...}
with open(os.path.join(BASE_DIR, "clean_schedule.json"), "r", encoding="utf-8") as f:
    SCHEDULE = json.load(f)

# 번호→이름 사전(JSON, 선택) : {"33": "한승", "27": "우희재", ...}
try:
    with open(os.path.join(BASE_DIR, "roster.json"), "r", encoding="utf-8") as f:
        ROSTER = json.load(f)
except FileNotFoundError:
    ROSTER = {}  # 없어도 동작

# --- 유틸 -------------------------------------------------------------------
KST = datetime.timezone(datetime.timedelta(hours=9))

def kakao_text(msg: str):
    """카카오 오픈빌더 v2.0 simpleText 응답"""
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": msg}}
            ],
            # 필요하면 퀵리플라이 주석 해제
            # "quickReplies": [
            #   {"action":"message","label":"오늘 당번","messageText":"오늘 당번"},
            #   {"action":"message","label":"내일 당번","messageText":"내일 당번"},
            #   {"action":"message","label":"이번주 당번","messageText":"이번주 당번"}
            # ]
        }
    }

def fmt(d: datetime.date) -> str:
    return d.strftime("%Y-%m-%d")

def normalize6(lst):
    """추출 노이즈 방지: 항상 6명만 노출 (리스트가 더 길면 앞의 6명만 사용)"""
    if not lst:
        return None
    return lst[:6]

def apply_roster(lst):
    """'33 한' 같은 잘린 이름을 번호 기준으로 '33 한승'처럼 보정"""
    fixed = []
    for item in (lst or []):
        m = re.match(r"^\s*(\d{1,2})\s*([가-힣]*)\s*$", item)
        if m:
            num, name = m.group(1), (m.group(2) or "")
            full = ROSTER.get(num, name)  # 번호가 있으면 roster 이름으로 교체
            fixed.append(f"{num} {full}".strip())
        else:
            fixed.append(item)  # 매칭 안되면 원본 유지
    return fixed

def cleaners_for(d: datetime.date):
    """날짜별 당번 목록 조회 + 6명 고정 + 번호→이름 보정"""
    key = fmt(d)
    c = normalize6(SCHEDULE.get(key))
    return apply_roster(c)

def parse_target_date(utter: str, today: datetime.date):
    """발화에서 날짜 파싱: 오늘/내일/2025-04-28/ 4월 28일"""
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
    """해당 날짜가 속한 주의 월~금 날짜 리스트"""
    monday = d - datetime.timedelta(days=d.weekday())
    return [monday + datetime.timedelta(days=i) for i in range(5)]

# --- 라우팅 -----------------------------------------------------------------
@app.route("/kakao/cleaner", methods=["POST"])
def cleaner():
    body = request.get_json(silent=True) or {}
    utter = (body.get("userRequest", {}).get("utterance") or "").strip()
    today = datetime.datetime.now(KST).date()

    # 1) 이번주
    if "이번주" in utter or "주간" in utter:
        blocks = []
        for d in week_days_of(today):
            c = cleaners_for(d)
            if c:
                blocks.append(f"{fmt(d)}\n- " + "\n- ".join(c))
            else:
                blocks.append(f"{fmt(d)}\n- 당번 정보가 없습니다.")
        return jsonify(kakao_text("이번주 청소 당번\n\n" + "\n\n".join(blocks)))

    # 2) 특정일(오늘/내일/날짜 파싱)
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

# --- 로컬 실행 --------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
