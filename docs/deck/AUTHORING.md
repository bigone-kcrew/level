# 슬라이드 조각 작성 규약 — 키노트풍 테마

`slides/*.html` 은 `<section class="slide">` 조각만 담는다. `<html>`·`<head>`·`<body>` 금지.
`tools/build-deck.mjs` 가 이것을 `shell.html` 의 `<!--SLIDES-->` 자리에 조립한다.

## 절대 규칙 8

1. **한 `<section class="slide">` = 한 메시지.** 슬라이드 안에 소제목을 두 개 이상 두지 않는다.
2. **리터럴 색상 금지.** 전부 `var(--...)`. 새 색이 필요하면 `deck.css` 의 `:root` 에 토큰을 만든다.
3. **특정 본부·개인을 지목하지 않는다.** 평정 성향은 유형의 개수만 쓰고, 본부 유형은 반복마다
   무작위 배정한다는 사실을 명시한다.
4. **수치는 `docs/*.md` 와 `sim/sim.py` 에 있는 값만.** 새 수치를 만들지 않는다.
   조건이 다른 제거율을 같은 표에 섞지 않는다(〈09 수치의 근거〉 §4).
5. **발표자용 설명은 `<div class="notes">` 안에만.** 본문에 "이 페이지는…" 류 금지.
6. **필수 속성** — `data-ch`(장 이름) · `data-title`(목차에 뜨는 짧은 제목).
7. **애니메이션은 절제.** 기본은 `.rise`. 표지와 핵심 수치에만 `.materialize`.
   `data-fx` 는 표지·장 구분에만.
8. **본문 최소 크기와 대비를 지킨다.** 토큰(`--fs-body` 이상, `--ink-3` 이상)만 쓰면 지켜진다.

## 조각 골격

```html
<section class="slide" data-ch="Ⅰ. 먼저 사실부터" data-title="규칙에 평균 80점은 없다">
  <p class="eyebrow rise">Ⅰ-2<span class="sep">·</span>사전조정계수</p>
  <h2 class="title rise" style="--d:120ms">규칙에 <em>「평균 80점」</em>은 없다</h2>
  <p class="lead rise" style="--d:200ms">사전조정계수와 평균 80점은 연도별 평정계획에만 있다.</p>
  <div class="notes">발표 노트. 화면에 보이지 않는다.</div>
</section>
```

## 요소

| 클래스 | 쓸 곳 |
|---|---|
| `.eyebrow` | 장·절 표시. 강조색 |
| `.title` / `.title.huge` / `.title.mid` | 제목. `huge` 는 한 문장 선언용 |
| `.lead` | 제목 아래 한 문장 |
| `.body` `.cap` `.micro` | 본문 · 보조 · 각주 |
| `.stat` `.statlab` `.stat-row` | 숫자가 주인공인 화면. `.stat.ac` 강조색 |
| `.vs` | 두 값을 마주 놓기 (`.side` / `.mid` / `.side.b`) |
| `.gj` | 개조식 □ ○ – (중첩 `ul` 로 단계) |
| `.chip` `.chip.ac` `.chip.hi` | 문장 안의 덩어리 강조 |
| `blockquote.q` + `cite` | 조문 원문 인용 |
| `.box` `.box.ac` `.box.warn` | 상자. `.h` 로 머리글 |
| `.cols.c2` `.cols.c3` `.cols.c2-1` | 열 분할 |
| `table` + `tbody tr.hl` | 표. 숫자 칸은 `td.n` |
| `.diff` + `.now`/`.new` | 신구대조 |
| `.fig` + `.legend` | 인라인 SVG 차트 |
| `.push` | 아래로 밀기 |

## 슬라이드 종류

- `class="slide cover"` — 표지. 상단 규칙선·페이지 번호 없음
- `class="slide divider"` — 장 구분. `.num` 으로 큰 장 번호
- `class="slide center"` — 가운데 정렬. 한 문장 선언에만 쓴다

## 등장 효과

| 클래스 | 쓸 곳 | 비고 |
|---|---|---|
| `.rise` | 기본. 거의 모든 요소 | `style="--d:120ms"` 로 시차 |
| `.materialize` | 큰 숫자·핵심 한 장 | 흐림과 배율이 함께 풀린다. 슬라이드당 1~2개 |
| `.draw` | 괘선·막대 | 좌→우로 그려진다 |

시차는 60 → 120 → 200 → 300ms 정도로 준다. 다섯 개를 넘게 시차를 주면 느려 보인다.

`prefers-reduced-motion` 에서는 세 효과가 모두 교차 페이드로 바뀐다. 별도 처리 불필요.

## 슬라이드 전환 — `data-trans`

전환은 장식이 아니라 **「어디로 가는지」를 알려 주는 신호**다. 슬라이드마다 다른 효과를 뿌리지
말고, 아래 용도에 맞춰 고정해서 쓴다. 들어온 방향으로 나가므로 앞뒤 이동이 대칭이 된다.

| 값 | 움직임 | 쓸 곳 |
|---|---|---|
| *(생략)* `push` | 옆으로 | **기본.** 같은 장 안에서 넘어갈 때 |
| `deep` | 안으로 밀고 들어감 | **장(章) 구분 슬라이드**. 660ms |
| `blur` | 흐림이 풀리며 도착 | **표지**, 핵심 수치 한 장. 660ms |
| `scale` | 앞으로 다가옴 | **한 문장 선언** (「…는 없다」류) |
| `wipe` | 좌→우로 덮음 | **대비·전환점** (현행 → 개선으로 넘어가는 지점) |
| `rise` | 아래에서 올라옴 | **결론·요청** |
| `fade` | 위치 유지, 교차 페이드 | **같은 주제에서 수치만 바뀔 때** (연속 차트). 440ms |

```html
<section class="slide divider" data-trans="deep" data-ch="…" data-title="…">
```

**한 장에서 `data-trans`와 요소 등장(`.rise`·`.materialize`)을 둘 다 강하게 주지 않는다.**
전환이 `blur`·`deep`이면 요소 등장은 `.rise` 한두 개로 절제한다.

`prefers-reduced-motion` 에서는 전환 7종이 모두 교차 페이드로 바뀐다. 별도 처리 불필요.

## 차트

인라인 SVG 로 직접 그린다. 라이브러리 금지. 축·격자·범례를 극단적으로 덜어낸다.

- 계열 색: 현행 `var(--series-now)` · 개선 `var(--series-new)` · 강조 `var(--series-hi)`
- **색만으로 구분하지 않는다.** 직접 라벨을 붙이거나 현행 계열에 해칭을 넣는다
- `preserveAspectRatio` 를 건드리지 않는다 (글자가 찌그러진다)
- 글자는 `font-size="15"` 이상, `fill="var(--ink-2)"` 이상

## 지연 렌더

무거운 계산은 슬라이드가 열릴 때 실행한다. **인덱스가 아니라 id 로 등록한다.**

```html
<section class="slide" id="sim" data-ch="Ⅳ. 개정안" data-title="시뮬레이터">…</section>
<script>window.DECK_HOOKS = window.DECK_HOOKS || {};
window.DECK_HOOKS["sim"] = () => { /* 처음 열릴 때 한 번 */ };</script>
```

## 검증

```
npm run build:deck
```

빌드가 리터럴 hex·`border-radius` 하드코딩·`.slide` 누락을 경고한다.
