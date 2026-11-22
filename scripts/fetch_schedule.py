"""올림픽공원 홈페이지 공연 일정 → data/schedule.json (이번 달부터 3개월 뒤까지).
GitHub Actions가 하루 한 번 돌린다. 로그인·키 불필요.
usage: python -I fetch_schedule.py <out json> [YYYYMM 시작] [개월 수]"""
import html, json, re, sys, time, urllib.request
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _parse import start_hour

URL = "https://www.ksponco.or.kr/olympicpark/eventInfo/eventInfoListAjax.es"
REF = "https://www.ksponco.or.kr/olympicpark/eventInfo/eventInfoList?mid=a20301010100"
VENUE = {"01": "올림픽홀", "02": "KSPO DOME", "03": "티켓링크 라이브 아레나", "04": "우리금융아트홀", "06": "88잔디마당", "07": "뮤즈라이브"}
BIG = {"01", "02", "03"}
WD = {"월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5, "일": 6}


def fetch(ym):
    req = urllib.request.Request(URL, data=json.dumps({"nowYM": ym, "plcCd": ""}).encode(), method="POST",
                                 headers={"Content-Type": "application/json;charset=UTF-8", "User-Agent": "Mozilla/5.0", "Referer": REF})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def drange(a, b):
    while a <= b:
        yield a; a += timedelta(days=1)


def show_days(x):
    """분석 코드 p3_fullpark_vs_shows.py와 같은 규칙: 4일 이하는 기간 전체, 넘으면 문구의 날짜 → 요일."""
    b = date.fromisoformat(x["beginDt"]); e = date.fromisoformat(x["endDt"])
    if (e - b).days + 1 <= 4:
        return list(drange(b, e)), True
    tm = html.unescape(x.get("tm") or "")
    ex = set()
    for m_, d_ in re.findall(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", tm):
        for y in (b.year, e.year):
            try:
                dd = date(y, int(m_), int(d_))
            except ValueError:
                continue
            if b <= dd <= e:
                ex.add(dd)
    if ex:
        return sorted(ex), True
    wds = {WD[c] for c in re.findall(r"[월화수목금토일](?=\s*[)\s오0-9/,]|요일)", tm) if c in WD}
    if wds:
        return [d for d in drange(b, e) if d.weekday() in wds], True
    return list(drange(b, e)), False   # 날짜를 특정 못 함 → 기간 전체(전시·축제 등)


def main():
    out = Path(sys.argv[1])
    start = sys.argv[2] if len(sys.argv) > 2 else date.today().strftime("%Y%m")
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    y, m = int(start[:4]), int(start[4:])
    yms = []
    for _ in range(n):
        yms.append(f"{y}{m:02d}"); m += 1
        if m > 12: y, m = y + 1, 1
    ev = {}
    for ym in yms:
        for part in fetch(ym):
            for x in part:
                if x.get("delYn", "N") == "N":
                    ev[x["evtSeq"]] = x
        time.sleep(1)
    rows = []
    for x in ev.values():
        pc = (x.get("plcCd") or "").strip()
        tm = html.unescape(x.get("tm") or "")
        days, exact = show_days(x)
        for d in days:
            rows.append({"date": d.isoformat(), "venue": VENUE.get(pc, html.unescape(x.get("plc") or "")), "big": pc in BIG,
                         "title": html.unescape(x.get("title") or "").strip(), "start": start_hour(tm, d), "tm": re.sub(r"\s+", " ", tm).strip(),
                         "dateExact": exact, "link": x.get("evtLink") if x.get("evtLinkYn") == "Y" else None})
    rows.sort(key=lambda r: (r["date"], -r["big"], r["start"] or 99))
    json.dump({"fetched": time.strftime("%Y-%m-%d %H:%M"), "months": yms, "source": REF, "shows": rows},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(len(ev), "events", len(rows), "show-days")


if __name__ == "__main__":
    main()
