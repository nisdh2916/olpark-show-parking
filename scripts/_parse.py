"""공연 시각 문구 파서 (분석 코드 build_show_features.py와 같은 규칙)."""
import re

WDK = "월화수목금토일"


def _hour(seg):
    m = re.search(r"(오전|오후)\s*(\d{1,2})\s*시(?:\s*(\d{1,2})\s*분)?", seg)
    if m:
        h = int(m.group(2)) + (12 if m.group(1) == "오후" and int(m.group(2)) < 12 else 0)
        return h + (int(m.group(3)) / 60 if m.group(3) else 0)
    m = re.search(r"(\d{1,2})\s*:\s*(\d{2})\s*(PM|AM|pm|am)?", seg)
    if m:
        h = int(m.group(1)) + (12 if (m.group(3) or "").lower() == "pm" and int(m.group(1)) < 12 else 0)
        return h + int(m.group(2)) / 60
    m = re.search(r"(\d{1,2})\s*(PM|pm)", seg)
    if m:
        return int(m.group(1)) % 12 + 12
    m = re.search(r"(\d{1,2})\s*시(?:\s*(\d{1,2})\s*분)?", seg)
    if m:
        h = int(m.group(1)); h = h + 12 if h < 10 else h
        return h + (int(m.group(2)) / 60 if m.group(2) else 0)
    return None


PAIR = re.compile(r"(?<!\d)[(（]?([월화수목금토일])[)）]?(?:요일)?\s*(오전|오후|저녁)?\s*(\d{1,2})(?:\s*:\s*(\d{2}))?\s*(시|PM|pm|AM|am)?(?:\s*(\d{1,2})\s*분)?")


def start_hour(tm, dd):
    """그날 공연 시작 시각(시, 소수). ① '요일 + 시각' 짝 ② 날짜 뒤 시각 ③ 문구 첫 시각."""
    pairs = {}
    for w, ap, h, mi, unit, mi2 in PAIR.findall(tm):
        mi = mi or mi2
        if not (unit or mi):
            continue
        h = int(h)
        if (ap in ("오후", "저녁") or unit.lower() == "pm") and h < 12:
            h += 12
        elif unit == "시" and not ap and h < 10:
            h += 12
        pairs.setdefault(WDK.index(w), round(h + (int(mi) / 60 if mi else 0), 2))
    if dd.weekday() in pairs:
        return pairs[dd.weekday()]
    for pat in (rf"{dd.month}\s*월\s*0?{dd.day}\s*일", rf"(?<!\d){dd.month}\s*[./]\s*0?{dd.day}(?!\d)"):
        m = re.search(pat, tm)
        if m:
            seg = re.split(r"\d{1,2}\s*월\s*\d{1,2}\s*일|/", tm[m.end(): m.end() + 40])[0]
            h = _hour(seg)
            if h is not None:
                return round(h, 2)
    h = _hour(tm)
    return round(h, 2) if h is not None else None
