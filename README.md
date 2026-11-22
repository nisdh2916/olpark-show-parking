# 공연날 주차 한눈에 (올림픽공원)

올림픽공원 공연 일정, 실시간 주차 대수, 2025년 입출차 기록으로 본 공연날 주차 흐름을 한 화면에 모은 정적 웹페이지입니다.
2026년도 한국체육산업개발(주) 공공데이터 활용 경진대회 출품작입니다.

## 구성

| 파일 | 역할 |
|---|---|
| `index.html` · `style.css` · `tokens.css` · `app.js` | 화면. 빌드 과정 없음 |
| `data/schedule.json` | 공연 일정(이번 달부터 4개월). `scripts/fetch_schedule.py`가 만든다 |
| `data/history.json` | 2025년 입출차·혼잡도 요약. `scripts/build_history.py`가 한 번 만든다 |
| `.github/workflows/update-schedule.yml` | 매일 06시(한국 시각) 공연 일정 갱신 |

실시간 주차 대수는 브라우저가 기관 API를 직접 부른다(키는 기관 개방데이터 64번 페이지에 공개된 값).

## 데이터

- 공연 일정: 올림픽공원 홈페이지 공연정보 (로그인·키 불필요)
- 실시간 주차: 한국체육산업개발 개방데이터 64번 '올림픽공원 실시간 주차현황' (공공데이터포털 15168686, 동2·남2·북2문 구역 합계)
- 입출차 기록: 문화빅데이터플랫폼 '올림픽공원 차량 이용현황 데이터' 2025-01~11 (원자료 약 330 MB는 저장소에 넣지 않는다)
- 혼잡도: 공공데이터포털 15164156 주차장 혼잡도 정보

## 로컬에서 보기

```
python -m http.server 8790
```
브라우저에서 http://localhost:8790

## GitHub Pages로 공개하기 (처음 한 번)

1. GitHub에서 새 저장소 `olpark-show-parking`을 만든다(공개).
2. 이 폴더에서:
   ```
   git init
   git add .
   git commit -m "첫 공개"
   git branch -M main
   git remote add origin https://github.com/<계정>/olpark-show-parking.git
   git push -u origin main
   ```
3. 저장소 Settings → Pages → Source를 `Deploy from a branch`, Branch를 `main` / `/ (root)`로 저장.
4. 몇 분 뒤 `https://<계정>.github.io/olpark-show-parking/`에서 열린다.
5. Actions 탭에서 '공연 일정 갱신'을 한 번 수동 실행(Run workflow)해 동작을 확인한다. 실패하면(해외 서버 접속 차단 등) 로컬에서 `python scripts/fetch_schedule.py data/schedule.json`을 돌리고 커밋한다.

## 한계

- 주차면수가 공개되지 않아 출입문별 "채움 정도"는 그 문의 2025년 하루 최대 대수 상위 5% 지점을 기준으로 삼았다.
- 실시간 값은 장기 주차 차량의 출차 기록이 없어 많게 나올 수 있다(기관 설명). 새벽 0시 실시간 1,074대, 2025 기록 복원값 같은 시각 중앙값 약 220대(2026-11-19 확인). 그래서 둘을 한 그래프에 겹치지 않는다.
- 각 주차장에서 공연장까지 걷는 거리는 확인하지 못했다.
