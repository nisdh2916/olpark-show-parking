(() => {
  "use strict";
  const LIVE_URL = "https://www.ksponco.or.kr/online/main/parkingorsApi.do?apiKey=PARKING21803504"; // 기관 개방데이터 64번에 공개된 주소
  const DAYS = 14;
  const WK = ["일", "월", "화", "수", "목", "금", "토"];
  const $ = (id) => document.getElementById(id);
  const fmt = (n) => Math.round(n).toLocaleString("ko-KR");
  const pct = (x) => Math.round(x * 100) + "%";

  const seoulToday = () => {
    const p = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Seoul", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
    return new Date(p + "T00:00:00");
  };
  const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  const hm = (h) => {
    if (h == null) return "시각 미공지";
    const H = Math.floor(h), M = Math.round((h - H) * 60);
    return `${H < 12 ? "오전" : "오후"} ${H > 12 ? H - 12 : H}시${M ? " " + M + "분" : ""}`;
  };
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  let schedule = null, history = null, selected = iso(seoulToday());

  // ---------- 날짜 칩 ----------
  function renderChips() {
    const box = $("chips"); box.innerHTML = "";
    const t0 = seoulToday();
    for (let i = 0; i < DAYS; i++) {
      const d = new Date(t0); d.setDate(t0.getDate() + i);
      const key = iso(d);
      const has = schedule && schedule.shows.some((s) => s.date === key && s.big);
      const b = document.createElement("button");
      b.type = "button"; b.className = "chip" + (has ? " has-show" : "");
      b.textContent = i === 0 ? "오늘" : `${d.getMonth() + 1}/${d.getDate()}(${WK[d.getDay()]})`;
      b.setAttribute("aria-pressed", String(key === selected));
      if (has) b.setAttribute("aria-label", b.textContent + ", 대형 공연 있음");
      b.addEventListener("click", () => { selected = key; renderChips(); renderShows(); renderCurve(); });
      box.appendChild(b);
    }
  }

  // ---------- 공연 ----------
  function dayShows() {
    return schedule ? schedule.shows.filter((s) => s.date === selected) : [];
  }
  function renderShows() {
    const d = new Date(selected + "T00:00:00");
    $("shows-title").textContent = `${d.getMonth() + 1}월 ${d.getDate()}일(${WK[d.getDay()]}) 공연`;
    const body = $("shows-body");
    if (!schedule) { body.innerHTML = '<p class="err">공연 일정을 불러오지 못했습니다.</p>'; return; }
    const list = dayShows();
    if (!list.length) { body.innerHTML = '<p class="muted">이날 올림픽공원 공연장 일정이 없습니다.</p>'; return; }
    body.innerHTML = list.map((s) => `
      <div class="show">
        <div class="venue${s.big ? " big" : ""}">${esc(s.venue)}</div>
        <div class="title">${s.link ? `<a href="${esc(s.link)}" target="_blank" rel="noopener">${esc(s.title)}</a>` : esc(s.title)}</div>
        <div class="time">${s.dateExact ? hm(s.start) + " 시작" : "기간 중 운영(날짜별 시각 미공지)"}</div>
      </div>`).join("");
  }

  // ---------- 실시간 ----------
  async function renderLive() {
    try {
      const r = await fetch(LIVE_URL, { cache: "no-store" });
      const j = await r.json();
      const n = Number(j && j[0] && j[0].parking_sum);
      if (!Number.isFinite(n)) throw new Error("값 없음");
      $("live-num").innerHTML = `${fmt(n)}<small>대</small>`;
      $("live-num").classList.remove("err");
      $("live-time").textContent = new Date().toLocaleTimeString("ko-KR", { timeZone: "Asia/Seoul", hour: "2-digit", minute: "2-digit" }) + " 기준 · 1분마다 갱신";
    } catch (e) {
      $("live-num").textContent = "불러오지 못함";
      $("live-num").classList.add("err");
      $("live-time").textContent = "기관 서버가 응답하지 않습니다. 잠시 뒤 다시 시도합니다.";
    }
  }

  // ---------- 하루 흐름 그래프 ----------
  function renderCurve() {
    if (!history) return;
    const a = history.curves.dome_weekend, b = history.curves.weekday_no_show;
    const W = Math.max(300, Math.round($("curve").clientWidth || 680)), H = Math.round(Math.min(260, Math.max(200, W * 0.55))), L = 44, R = 12, T = 12, B = 28;
    const n = a.time.length, max = Math.max(...a.p75, ...b.p75) * 1.08;
    const x = (i) => L + (i / (n - 1)) * (W - L - R);
    const y = (v) => T + (1 - v / max) * (H - T - B);
    const line = (arr) => arr.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("");
    const band = (lo, hi) => line(hi) + lo.map((v, i) => `L${x(n - 1 - i).toFixed(1)},${y(lo[n - 1 - i]).toFixed(1)}`).join("") + "Z";
    let g = "";
    const step = max > 2000 ? 500 : 250;
    for (let v = 0; v <= max; v += step) g += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="var(--border-soft)"/><text x="${L - 6}" y="${y(v) + 4}" text-anchor="end">${fmt(v)}</text>`;
    for (let h = 0; h <= 24; h += 3) { const i = Math.min(n - 1, h * 6); g += `<text x="${x(i)}" y="${H - 8}" text-anchor="middle">${h}시</text>`; }
    let mark = "";
    const big = dayShows().filter((s) => s.big && s.dateExact && s.start != null);
    if (big.length) {
      const st = Math.min(...big.map((s) => s.start)), i = Math.round(st * 6);
      mark = `<line x1="${x(i)}" x2="${x(i)}" y1="${T}" y2="${H - B}" stroke="var(--fg)" stroke-dasharray="3 3"/><text x="${x(i) > W * 0.7 ? x(i) - 4 : x(i) + 4}" y="${T + 10}" text-anchor="${x(i) > W * 0.7 ? "end" : "start"}" style="fill:var(--fg)">이날 공연 시작 ${hm(st).replace("오후 ", "")}</text>`;
    }
    $("curve").innerHTML = `<svg viewBox="0 0 ${W} ${H}">${g}
      <path d="${band(b.p25, b.p75)}" fill="var(--muted-band)"/><path d="${line(b.p50)}" fill="none" stroke="var(--muted)" stroke-width="2"/>
      <path d="${band(a.p25, a.p75)}" fill="var(--primary-band)"/><path d="${line(a.p50)}" fill="none" stroke="var(--primary)" stroke-width="2.5"/>${mark}</svg>`;
    let pk = 0; a.p50.forEach((v, i) => { if (v > a.p50[pk]) pk = i; });
    $("curve-lead").textContent = `KSPO DOME 주말 공연일(${a.n_days}일)에는 ${a.time[pk].replace(":00", "시").replace(/:(\d0)/, "시 $1분")}께 가장 많아 중앙값 ${fmt(a.p50[pk])}대였습니다. 같은 시각 월~목 공연 없는 날(${b.n_days}일)은 ${fmt(b.p50[pk])}대입니다.`;
  }

  // ---------- 출입문 ----------
  function renderGates() {
    const gs = history.gates;
    const spare = gs.filter((g) => g.show_weekend_share_le_half >= 0.7);
    $("gate-lead").innerHTML = spare.length
      ? spare.map((g) => `<b>${esc(g.gate)}문</b> 쪽은 KSPO DOME 주말 공연일 ${pct(g.show_weekend_share_le_half)}가 가장 붐빌 때도 평소 최고치의 절반 이하였습니다. 월~목 공연 없는 날 가장 붐빌 때는 중앙값 ${pct(g.weekday_median_fill)}까지 찼습니다.`).join(" ")
      : "공연 주말에도 늘 비는 출입문은 없었습니다.";
    $("gates").innerHTML = gs.map((g) => {
      const v = g.show_weekend_median_fill, isSpare = g.show_weekend_share_le_half >= 0.7;
      return `<div class="bar-row"><span>${esc(g.gate)}문</span><div class="bar${isSpare ? " spare" : ""}" aria-hidden="true"><i style="width:${Math.min(100, v * 100)}%"></i></div><span class="bar-val">${pct(v)}</span></div>`;
    }).join("") + '<p class="note">막대 = 2025년 KSPO DOME 주말 공연일 82일의 채움 정도 중앙값. 점선 = 50%.</p>';
  }

  // ---------- 만차 ----------
  function renderCongestion() {
    const c = history.congestion;
    $("cong-tag").textContent = `${c.period[0]} ~ ${c.period[1]}`;
    $("cong-lead").textContent = `만차 기록이 남은 ${c.full_days}일 중 ${c.full_days_on_big_show}일이 KSPO DOME·올림픽홀·티켓링크 라이브 아레나 공연일이었습니다. 다만 이 기간 주말은 거의 모두 공연일이라, 공연 때문인지 주말이라서인지는 가를 수 없습니다.`;
    const z = Object.entries(c.zones_full_days), mx = Math.max(...z.map((e) => e[1]));
    $("zones").innerHTML = z.map(([k, v]) => `<div class="bar-row"><span>${esc(k)}</span><div class="bar no-mid" aria-hidden="true"><i style="width:${(v / mx) * 100}%"></i></div><span class="bar-val">${v}일</span></div>`).join("");
    document.querySelectorAll("#zones .bar").forEach((b) => b.classList.add("plain"));
  }

  async function load(path) { const r = await fetch(path, { cache: "no-cache" }); if (!r.ok) throw new Error(path); return r.json(); }

  (async () => {
    renderChips();
    try { schedule = await load("data/schedule.json"); $("sched-time").textContent = `(${schedule.fetched} 수집)`; } catch (e) { schedule = null; }
    try { history = await load("data/history.json"); } catch (e) { history = null; }
    renderChips(); renderShows();
    if (history) { renderCurve(); renderGates(); renderCongestion(); }
    renderLive(); setInterval(renderLive, 60000);
    let rt; window.addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(renderCurve, 150); });
  })();
})();
