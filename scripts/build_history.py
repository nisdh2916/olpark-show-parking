"""2025 기록 요약을 data/history.json으로 만든다 (한 번만 돌리면 된다. 원자료 330 MB는 저장소에 넣지 않는다).

usage: python -I build_history.py <입출차 CSV 폴더> <공연일_2025_2026.csv> <혼잡도 CSV(cp949)> <s1_result.json> <out json>
"""
import csv, glob, io, json, sys
from datetime import date
import numpy as np, pandas as pd

DATA, SHOWS, CONG, S1, OUT = sys.argv[1:6]
LIVE_GATES = ["동2", "남2", "북2"]  # 실시간 API가 다루는 구역

parts = []
for f in sorted(glob.glob(DATA + "/*.csv")):
    d = pd.read_csv(f, encoding="utf-8-sig", dtype=str)
    d.columns = [c.strip().lstrip("\ufeff") for c in d.columns]
    parts.append(d)
df = pd.concat(parts, ignore_index=True).drop_duplicates()
df["tin"] = pd.to_datetime(df["ENTVHCL_DT"].str.strip(), errors="coerce")
df["tout"] = pd.to_datetime(df["LVVHCL_DT"].str.strip(), errors="coerce")
df = df[df["tout"].notna() & (df["tout"] >= df["tin"]) & (df["tin"].dt.year == 2025)]
x = df[df["ENTVHCL_DOOR_NM"].str.strip().isin(LIVE_GATES)]
grid = pd.date_range("2025-01-01", "2026-01-01", freq="10min", inclusive="left")
occ = pd.Series(np.searchsorted(np.sort(x["tin"].values), grid.values, "right")
                - np.searchsorted(np.sort(x["tout"].values), grid.values, "right"), index=grid)
days = set(df["tin"].dt.normalize().unique())
occ = occ[occ.index.normalize().isin(days)]

sh = pd.read_csv(SHOWS, dtype=str); sh["date"] = pd.to_datetime(sh["date"])
sh = sh[sh["date"].dt.year == 2025]
big = set(sh.loc[sh["plcCd"].isin(["01", "02", "03"]), "date"])
dome = set(sh.loc[sh["plcCd"] == "02", "date"])
day = occ.index.normalize()
groups = {
    "dome_weekend": [d in dome and d.dayofweek >= 5 for d in day],
    "weekday_no_show": [d.dayofweek <= 3 and d not in big for d in day],
}


def curve(mask):
    s = occ[np.array(mask)]
    g = s.groupby(s.index.strftime("%H:%M"))
    q = g.quantile([0.25, 0.5, 0.75]).unstack()
    return {"n_days": int(len(set(s.index.normalize()))), "time": list(q.index),
            "p25": [int(v) for v in q[0.25]], "p50": [int(v) for v in q[0.5]], "p75": [int(v) for v in q[0.75]]}


s1 = json.load(open(S1, encoding="utf-8"))
gates = [{"gate": g, "high_p95": round(s1["high_p95"][g]),
          "show_weekend_median_fill": s1["S1"]["median_fill_by_gate"][g],
          "show_weekend_share_le_half": s1["S1"]["lo_share_by_gate"][g],
          "weekday_median_fill": s1["report_only_baseline_mon_thu"]["median_fill_by_gate"][g],
          "holdout_2024_share_le_half": s1["report_only_holdout_2024"]["lo_share_by_gate"][g]}
         for g in s1["rule"]["gates"]]

cong = list(csv.DictReader(io.StringIO(open(CONG, "rb").read().decode("cp949"))))
full_days = sorted({r["등록일"] for r in cong if r["혼잡도"] == "만차"})
bigs = {d.strftime("%Y-%m-%d") for d in pd.to_datetime(pd.read_csv(SHOWS, dtype=str).query("plcCd in ['01','02','03']")["date"])}
zones = {}
for r in cong:
    if r["혼잡도"] == "만차":
        zones.setdefault(r["주차구역"], set()).add(r["등록일"])
res = {
    "source": "문화빅데이터플랫폼 '올림픽공원 차량 이용현황 데이터' 2025-01~11 (출처: 한국체육산업개발㈜), 공공데이터포털 15164156 주차장 혼잡도 정보, 올림픽공원 홈페이지 공연 일정",
    "built": date.today().isoformat(),
    "live_gates": LIVE_GATES,
    "curves": {k: curve(m) for k, m in groups.items()},
    "gates": gates,
    "congestion": {"period": [min(r["등록일"] for r in cong), max(r["등록일"] for r in cong)],
                   "full_days": len(full_days), "full_days_on_big_show": sum(d in bigs for d in full_days),
                   "zones_full_days": {z: len(v) for z, v in sorted(zones.items(), key=lambda kv: -len(kv[1]))}},
}
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("ok", res["curves"]["dome_weekend"]["n_days"], res["curves"]["weekday_no_show"]["n_days"], res["congestion"]["full_days"], res["congestion"]["full_days_on_big_show"])
