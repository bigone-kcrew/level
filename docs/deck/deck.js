"use strict";
/* ══════════════════════════════════════════════════════════════════
   deck.js — 라우터 · 좌측 목차 · 발표 노트 · 전체화면
   html-ppt-skill 의 runtime.js 를 쓰지 않는 이유는 vendor/README.md 에 적었다.
   단, `.slide` 에 `is-active` 를 토글하므로 vendor/fx-runtime.js 는 그대로 동작한다.
   ══════════════════════════════════════════════════════════════════ */

const deck   = document.getElementById("deck");
const slides = Array.from(deck.querySelectorAll(".slide"));
const nav    = document.getElementById("nav");
const bar    = document.querySelector("#prog > span");
const drawer = document.getElementById("notes-drawer");
const nbody  = document.getElementById("notes-body");
const RM     = window.matchMedia("(prefers-reduced-motion: reduce)");

/* 슬라이드별 지연 렌더 훅 — 인덱스가 아니라 id 로 등록한다.
   슬라이드를 추가·재배치해도 깨지지 않는다. window.DECK_HOOKS 에 등록. */
window.DECK_HOOKS = window.DECK_HOOKS || {};
const rendered = new Set();

/* ─── 목차 ─────────────────────────────────────────────────────── */
let idx = 0;
const links = [];
(function buildNav(){
  let lastCh = null;
  slides.forEach((s, i) => {
    const ch = s.dataset.ch || "";
    if (ch !== lastCh) {
      const h = document.createElement("div");
      h.className = "ch"; h.textContent = ch;
      nav.appendChild(h); lastCh = ch;
    }
    const a = document.createElement("a");
    a.href = "#/" + (i + 1);
    a.innerHTML = '<span class="i">' + String(i + 1).padStart(2, "0") + "</span>" +
                  "<span>" + (s.dataset.title || ("슬라이드 " + (i + 1))) + "</span>";
    a.addEventListener("click", e => { e.preventDefault(); go(i); });
    nav.appendChild(a); links.push(a);
    // 페이지 번호를 슬라이드마다 자동으로 넣는다
    if (!s.querySelector(".pageno")) {
      const p = document.createElement("div");
      p.className = "pageno";
      p.textContent = String(i + 1).padStart(2, "0") + " / " + String(slides.length).padStart(2, "0");
      s.appendChild(p);
    }
  });
})();

/* ─── 이동 ─────────────────────────────────────────────────────── */
function go(n){
  n = Math.max(0, Math.min(slides.length - 1, n));
  slides.forEach((s, i) => {
    s.classList.toggle("is-active", i === n);
    s.classList.toggle("is-prev", i < n);
  });
  links.forEach((a, i) => a.setAttribute("aria-current", i === n ? "true" : "false"));
  idx = n;
  bar.style.width = ((n + 1) / slides.length * 100) + "%";

  // 활성 슬라이드의 data-anim 재트리거 (skill 규약)
  slides[n].querySelectorAll("[data-anim]").forEach(el => {
    const a = el.getAttribute("data-anim");
    el.classList.remove("anim-" + a);
    void el.offsetWidth;
    el.classList.add("anim-" + a);
  });

  // 지연 렌더 훅
  const id = slides[n].id;
  if (id && window.DECK_HOOKS[id]) {
    const once = slides[n].dataset.hookOnce === "true";
    if (!once || !rendered.has(id)) {
      rendered.add(id);
      requestAnimationFrame(() => requestAnimationFrame(() => {
        try { window.DECK_HOOKS[id](slides[n]); }
        catch (e) { console.error("hook", id, e); }
      }));
    }
  }

  // 노트
  const note = slides[n].querySelector(".notes");
  nbody.innerHTML = note ? note.innerHTML : '<i style="color:#8A8A8A">이 페이지에는 노트가 없습니다.</i>';

  // 활성 링크를 목차 안에서 보이게
  const a = links[n];
  if (a && a.offsetParent) {
    const r = a.getBoundingClientRect(), nr = nav.getBoundingClientRect();
    if (r.top < nr.top || r.bottom > nr.bottom) a.scrollIntoView({ block: "nearest" });
  }

  const h = "#/" + (n + 1);
  if (location.hash !== h) { try { history.replaceState(null, "", h); } catch (e) {} }
}

function fromHash(){
  const m = /^#\/(\d+)/.exec(location.hash || "");
  go(m ? parseInt(m[1], 10) - 1 : 0);
}
window.addEventListener("hashchange", fromHash);

/* ─── 도구 ─────────────────────────────────────────────────────── */
function toggleFull(){
  const d = document.documentElement;
  if (!document.fullscreenElement)
    (d.requestFullscreen || d.webkitRequestFullscreen || function(){}).call(d);
  else
    (document.exitFullscreen || document.webkitExitFullscreen || function(){}).call(document);
}
function toggleNotes(){
  document.body.classList.toggle("notes-on");
  if (document.body.classList.contains("notes-on")) {
    const n = slides[idx].querySelector(".notes");
    nbody.innerHTML = n ? n.innerHTML : '<p class="micro">이 슬라이드에는 발표 노트가 없습니다.</p>';
  }
}
function toggleSide(){
  const hid = document.body.classList.toggle("hide-side");
  document.getElementById("sideOpen").hidden = !hid;
  if (hid) document.getElementById("sideOpen").focus();
  else document.getElementById("btnSide").focus();
}
document.getElementById("btnFull").addEventListener("click", toggleFull);
document.getElementById("btnNotes").addEventListener("click", toggleNotes);
document.getElementById("btnSide").addEventListener("click", toggleSide);
document.getElementById("sideOpen").addEventListener("click", toggleSide);
if (!(document.documentElement.requestFullscreen || document.documentElement.webkitRequestFullscreen))
  document.getElementById("btnFull").style.display = "none";

/* 어느 호스트에서 열어도 문서 사이트로 간다 */
(function(){
  const a = document.getElementById("docLink");
  if (location.hostname !== "bigone-kcrew.github.io" && location.protocol !== "file:")
    a.href = "https://bigone-kcrew.github.io/level/diagnosis.html";
  a.target = "_blank"; a.rel = "noopener";
})();

/* ─── 테마 — 어두운 화면이 기본, 밝은 회의실·인쇄는 밝은 화면 ─────── */
const THEME_KEY = "deck-theme";
function applyTheme(t){
  if (t === "light") document.documentElement.setAttribute("data-theme", "light");
  else document.documentElement.removeAttribute("data-theme");
  const b = document.getElementById("btnTheme");
  if (b) b.title = (t === "light" ? "어두운 화면 전환 (T)" : "밝은 화면 전환 (T)");
}
function toggleTheme(){
  const next = document.documentElement.getAttribute("data-theme") === "light" ? "dark" : "light";
  try { localStorage.setItem(THEME_KEY, next); } catch (_) {}
  applyTheme(next);
}
(function initTheme(){
  let t = null;
  try { t = localStorage.getItem(THEME_KEY); } catch (_) {}
  applyTheme(t || "dark");
  const b = document.getElementById("btnTheme");
  if (b) b.addEventListener("click", toggleTheme);
})();

/* ─── 키보드 ───────────────────────────────────────────────────── */
document.addEventListener("keydown", e => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const t = e.target;
  if (t && t.matches && t.matches("input,textarea,select,summary")) return;
  switch (e.key) {
    case "ArrowRight": case "PageDown": case " ": e.preventDefault(); go(idx + 1); break;
    case "ArrowLeft":  case "PageUp":            e.preventDefault(); go(idx - 1); break;
    case "Home": e.preventDefault(); go(0); break;
    case "End":  e.preventDefault(); go(slides.length - 1); break;
    case "f": case "F": toggleFull(); break;
    case "n": case "N": toggleNotes(); break;
    case "h": case "H": toggleSide(); break;
    case "t": case "T": toggleTheme(); break;
    case "Escape": document.body.classList.remove("notes-on"); break;
    default:
      // 숫자키 → 해당 장(章)의 첫 슬라이드
      if (/^[1-9]$/.test(e.key)) {
        const chs = [];
        let last = null;
        slides.forEach((s, i) => { const c = s.dataset.ch || ""; if (c !== last) { chs.push(i); last = c; } });
        const k = parseInt(e.key, 10) - 1;
        if (chs[k] !== undefined) go(chs[k]);
      }
  }
});

fromHash();
