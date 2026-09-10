# vendor — html-ppt-skill 자산

출처: https://github.com/lewislulu/html-ppt-skill (MIT License, Copyright (c) 2026 lewis)
원본 LICENSE 를 이 디렉터리에 함께 둔다.

가져온 것
- `animations.css` — 27종 CSS 등장 애니메이션 (`data-anim` / `.anim-*`)
- `fx-runtime.js` + `fx/*.js` — 20종 Canvas FX (`data-fx`)

가져오지 않은 것과 그 이유
- `base.css` — 슬라이드 글자 크기가 절대 px(1920×1080 고정 캔버스)이어서 폭이 1920 이 아닌
  화면에서 내용이 잘린다. 이 저장소는 `deck.css` 의 vh 기반 clamp 스케일을 쓴다.
- `runtime.js` — 좌측 챕터 사이드바가 없고 슬라이드별 지연 렌더 훅을 걸 수 없다.
  `deck.js` 가 대체하며, `.slide` 에 `is-active` 를 토글하므로 `fx-runtime.js` 는 그대로 동작한다.
- `themes/*` — 스위스 그리드 팔레트 값만 `deck.css` 로 옮겨 적었다.
