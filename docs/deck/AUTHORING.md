# 슬라이드 조각 작성 계약

`slides/*.html` 조각 파일을 쓸 때 지켜야 할 것. `tools/build-deck.mjs` 가 조립하면서
리터럴 색·둥근 모서리·그림자를 자동으로 잡아 경고한다.

## 1. 골격

```html
<section class="slide" id="s-고유id" data-ch="Ⅰ. 장 이름" data-title="목차에 뜰 짧은 제목">
  <div class="eyebrow">Ⅰ. 장 이름 <span class="on">· 이 장의 몇 번째</span></div>
  <h2 class="title">한 문장으로 끝나는 <em>핵심</em> 메시지</h2>
  <p class="lead">제목을 풀어 주는 한두 문장. 폭이 제한되어 우측에 여백이 남는다.</p>
  <div class="slide-body">
    … 내용 …
  </div>
  <div class="notes"><p>발표자용 원고. 관객 화면에 절대 보이지 않는다.</p></div>
</section>
```

- `id` 는 필수다. 지연 렌더 훅(`window.DECK_HOOKS[id]`)의 키로 쓴다.
- `data-ch` 가 바뀌는 지점에서 목차에 장 제목이 삽입된다. 같은 장이면 문자열을 **똑같이** 써라.
- 페이지 번호는 `deck.js` 가 자동으로 넣는다. 직접 쓰지 마라.
- 장 구분 페이지는 `class="slide bare divider"` — `bare` 는 상단 규칙선을 끄고 `divider` 는 세로 중앙 정렬.

## 2. 절대 규칙

| | 규칙 |
|---|---|
| 1 | **한 슬라이드 = 한 메시지.** `h2.title` 은 하나. 슬라이드 안에 소제목 두 개를 두지 마라. 나눠라. |
| 2 | **리터럴 색 금지.** `#333` 같은 것을 쓰면 빌드가 경고한다. `var(--ink)` `var(--accent)` 만. |
| 3 | **`border-radius` · `box-shadow` 금지.** 구분은 괘선(`.box` `.hr`)으로만 한다. |
| 4 | **발표자용 설명은 `.notes` 안에만.** "이 페이지는…" 류를 본문에 쓰지 마라. |
| 5 | **특정 본부·개인을 지목하지 마라.** 평정 성향은 유형의 개수만 말하고, 무작위 배정임을 밝힌다. |
| 6 | **수치를 새로 만들지 마라.** `sim/sim.py` 실행값과 `docs/*.md` 에 있는 값만 쓴다. |
| 7 | **3열 카드 그리드는 슬라이드당 최대 1회.** 연속된 슬라이드에서 반복하지 마라. |

## 3. AI 생성물처럼 보이지 않게 — 실제 기법

| # | 기법 |
|---|---|
| 1 | **타이포 스케일을 건너뛴다.** 캡션(`--fs-cap`) 다음에 바로 큰 제목(`--fs-big`)으로 점프. 중간 크기를 빽빽히 채우지 마라 |
| 2 | **제목은 폭 제한 없이 좌측 정렬**, `.lead` 만 폭이 제한된다. 우측 여백을 의도적으로 남긴다 |
| 3 | **강조는 색이 아니라 블록으로** — `<span class="chip">`(검정 배경 흰 글자). `<b>` 남용 대신 문장 안에 덩어리를 박는다 |
| 4 | **장식은 상단 규칙선 하나뿐.** 페이지마다 다른 장식을 붙이지 마라 |
| 5 | **여백 계층** — 묶음 안은 `.tight`, 묶음 사이는 `.loose` |
| 6 | **차트는 축·격자·범례를 덜어낸다.** 값은 막대에 직접 붙인다. 데이터 시각화가 아니라 지면 요소로 |
| 7 | 빈 공간이 어색하면 `.slide-body spread` 로 위·아래로 벌리거나 `.push` 로 마지막 요소를 아래에 붙인다 |

## 4. 쓸 수 있는 조각

**머리** `.eyebrow` `.eyebrow .on` `h2.title` `h2.title em`(벽돌색) `.lead`
**장 구분** `.slide.divider` 안에 `.rn`(로마숫자·부제) + `h2` + `.lead`
**거대 수치** `.stat` `.stat.red` `.stat .u`(단위) `.stat-note`
**개조식** `.gj > li`(— 표식) `> ul > li`(· 2단) `.sq`(□ 소제목) `.gj b`
**강조** `.chip` `.chip.red` `.mark`(밑줄 강조)
**인용** `blockquote.q` 안에 `.txt` + `.src`
**면** `.box`(상 2px·하 1px 괘선) `.box.pad` `.box.fill`(연한 면) `.box.on`(상단 벽돌색 4px)
**열** `.cols.c2` `.cols.c3` `.cols.c-side`(좌 26% + 우) `.rows`
**표** `<table>` `<thead><th>` `td.n`(우측·고정폭 숫자) `tr.hl`(강조 행) `table.big`
**범례** `.legend` `.legend i`(색 블록) `.legend .ln`(점선)
**차트** `<svg class="chart">` 를 `.fig`(남은 높이) / `.fig.h-md` / `.fig.h-sm` 안에
**작은 것** `.k`(라벨) `.v`(값) `.kv` `.cap` `.cap.src` `.mid-txt` `.hr` `.hr.strong`
**레이아웃** `.push` `.grow` `.tight` `.loose` `.right` `.scroll-y` `.slide-body.spread` `.slide-body.mid`

## 5. 애니메이션

- 기본은 `class="anim-fade-up" data-anim="fade-up"` — **둘 다** 쓴다(초기 렌더 깜빡임 방지 + 재진입 시 재생).
- 목록은 부모에 `data-anim="stagger-list"`.
- 강한 등장은 `rise-in` `zoom-pop` `blur-in`.
- **Canvas FX(`data-fx`)는 지정된 슬라이드에만.** 컨테이너에 크기가 있어야 한다:
  `<div data-fx="constellation" style="position:absolute;inset:0;opacity:.5"></div>`
  쓸 수 있는 값은 `vendor/fx/` 파일명. `word-cascade` 는 단어가 중국어로 하드코딩되어 있어 쓰지 마라.
- `prefers-reduced-motion` 은 CSS 가 처리한다. 따로 분기하지 마라.

## 6. 계산이 필요한 슬라이드

`window.SIM.run({...})` / `window.SIM.transfer({...})` 로 계산한다(`sim-core.js`).
렌더는 지연 훅에 등록한다.

```html
<script>
window.DECK_HOOKS["s-내슬라이드id"] = function (slide) {
  const R = SIM.run({ reps: 100 });
  // R.current / R.reform 각각 sExt sEven cExt cEven sHqExt sHqEven rho dist
  // R.current.dist.S = {S:29.4, A:20.9, B:33.0, C:16.6}  ← 극단 성향 평정자 아래 등급 분포
};
</script>
```

한 번만 계산하고 결과를 유지할 슬라이드는 `data-hook-once="true"` 를 붙인다.

## 7. 검증

작성 후 반드시 확인한다.

```bash
node tools/build-deck.mjs      # 계약 위반 경고 확인
```

그리고 1920×1080 · 1600×900 · 1366×768 에서 **스크롤이 0** 이어야 한다. 넘치면 잘린다.
