import fs from 'node:fs';
import path from 'node:path';
import { marked } from 'marked';

const ROOT = path.resolve(import.meta.dirname, '..');
const DOCS = path.join(ROOT, 'docs');
const layout = fs.readFileSync(path.join(import.meta.dirname, 'layout.html'), 'utf8');

/* 문서를 세 묶음으로 나눈다.
     share  — 사측과 함께 보는 분석 자료. 상단 탭에 노출한다
     inside — 조합 내부 검토용(교섭 전략). 상단 탭에 넣지 않고 하단 메뉴에만 둔다
     apart  — 본안과 완전히 분리된 별도 안건. 하단에 따로 둔다
   상단 탭에서 빼는 이유는 발표 중에 실수로 띄우는 것을 막기 위한 것이다.
   문서 번호는 재편하지 않는다 — 문서 사이 상호참조가 번호로 되어 있다. */
const GROUPS = [
  { id: 'share', label: '분석 자료', note: '사측과 함께 보는 자료', items: [
    ['diagnosis', '01 진단'],
    ['amendments', '02 개정안'],
    ['benchmark', '03 타기관'],
    ['plan2027', '07 시행계획'],
    ['guide', '08 세부지침'],
    ['method', '09 근거'],
    ['compare', '10 대비'],
    ['census', '부록 전수집계'],
  ]},
  { id: 'inside', label: '조합 내부', note: '교섭 전략 — 협의 전 조합 내부 검토용', items: [
    ['proposals', '제시사항 한눈에'],
    ['bargaining', '04 교섭 전략'],
    ['plan', '05 협의 계획'],
  ]},
  { id: 'apart', label: '별도 안건', note: '본안과 분리해 다루는 안건', items: [
    ['union', '근로시간면제자 평정'],
  ]},
];
const NAV = GROUPS.flatMap(g => g.items);
const GROUP_OF = Object.fromEntries(GROUPS.flatMap(g => g.items.map(([k]) => [k, g.id])));

function frontMatter(src) {
  const m = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/.exec(src);
  if (!m) return [{}, src];
  const fm = {};
  for (const line of m[1].split(/\r?\n/)) {
    const k = /^([A-Za-z_-]+):\s*(.*)$/.exec(line);
    if (k) fm[k[1]] = k[2].replace(/^["']|["']$/g, '');
  }
  return [fm, src.slice(m[0].length)];
}
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

marked.setOptions({ gfm: true, breaks: false });

/* GFM 취소선은 물결 하나로도 열린다. 이 문서들은 숫자 범위에 물결을 쓰므로
   (83~85점, 11~19%, 70.01~70 등) 한 문단에 물결이 홀수 개면 그 사이가
   취소선으로 변하고 강조(**...**)까지 삼켜 버린다.
   취소선은 `~~두 개~~`로만 인정하도록 내장 토크나이저를 교체한다. */
marked.use({
  tokenizer: {
    del(src) {
      const m = /^~~(?=\S)([\s\S]*?\S)~~/.exec(src);
      if (!m) return;
      return { type: 'del', raw: m[0], text: m[1], tokens: this.lexer.inlineTokens(m[1]) };
    }
  }
});

let built = 0;
for (const f of fs.readdirSync(DOCS)) {
  if (!f.endsWith('.md')) continue;
  const src = fs.readFileSync(path.join(DOCS, f), 'utf8');
  const [fm, body] = frontMatter(src);
  const key = fm.key || path.basename(f, '.md');
  let html = marked.parse(body);
  // 표를 가로 스크롤 래퍼로 감싼다 — 본문은 절대 가로 스크롤되지 않는다
  html = html.replace(/<table>[\s\S]*?<\/table>/g, m => `<div class="tw">${m}</div>`);
  // .md 내부 링크를 .html 로
  html = html.replace(/href="([^"]+)\.md(#[^"]*)?"/g, 'href="$1.html$2"');

  /* 절 제목에 id 를 붙이고 목차를 만든다. 세부지침처럼 절이 서른 개를 넘는
     문서는 목차 없이 읽을 수 없다. 이미 id 가 있으면 그대로 쓴다. */
  const toc = [];
  const used = new Set();
  const slug = t => {
    let base = t.replace(/<[^>]+>/g, '').trim()
      .replace(/[^\p{L}\p{N}\s·-]/gu, '').trim()
      .replace(/\s+/g, '-').slice(0, 60) || 'sec';
    let id = base, n = 2;
    while (used.has(id)) id = base + '-' + n++;
    used.add(id);
    return id;
  };
  html = html.replace(/<(h[23])(\s[^>]*)?>([\s\S]*?)<\/\1>/g, (m, tag, attr, inner) => {
    const has = attr && /\sid="/.test(attr);
    const id = has ? /\sid="([^"]*)"/.exec(attr)[1] : slug(inner);
    const text = inner.replace(/<[^>]+>/g, '').trim();
    toc.push({ lv: tag === 'h2' ? 2 : 3, id, text });
    return `<${tag}${attr || ''}${has ? '' : ` id="${id}"`}>${inner}<a class="anchor" href="#${id}" aria-label="이 절 링크">§</a></${tag}>`;
  });
  // 절이 6개 미만이면 목차를 만들지 않는다 — 짧은 문서에는 방해가 된다
  const tocHtml = toc.filter(t => t.lv === 2).length < 6 ? '' :
    '<aside class="toc" aria-label="이 문서의 목차"><p class="toc-h">이 문서 안에서</p><ol>' +
    toc.map(t => `<li class="l${t.lv}"><a href="#${t.id}">${esc(t.text)}</a></li>`).join('') +
    '</ol></aside>';
  const group = GROUP_OF[key] || 'share';
  const link = ([k, label]) =>
    `<a href="${k}.html"${k === key ? ' class="on" aria-current="page"' : ''}>${label}</a>`;
  const nav = GROUPS[0].items.map(link).join('');
  // 하단 메뉴 — 상단 탭에 없는 묶음을 여기 둔다
  const foot = GROUPS.slice(1).map(g =>
    `<div class="fg" data-g="${g.id}"><p class="fg-h">${g.label}` +
    `<span>${g.note}</span></p><div class="fg-l">${g.items.map(link).join('')}</div></div>`
  ).join('');
  // 내부·별도 문서에는 눈에 보이는 고지를 붙인다
  const banner = group === 'inside'
    ? '<div class="warn-in" role="note"><b>조합 내부 검토용</b> — 교섭 전략과 예상 반론이 담겨 있습니다. ' +
      '<b>발표 자리에서 이 페이지를 띄우지 마십시오.</b> 상단 탭에는 넣지 않았습니다.</div>'
    : group === 'apart'
    ? '<div class="warn-ap" role="note"><b>본안과 분리된 별도 안건</b> — 근무평정 제도개선(본안)의 ' +
      '대가로 다루어지지 않기 위해 문서를 나누었습니다. <b>본안 의제에 끼워 넣지 않습니다.</b></div>'
    : '';
  const out = layout
    .replace('__TITLE__', esc(fm.title || key))
    .replace('__DESC__', esc(fm.description || ''))
    .replace('__NAV__', nav)
    .replace('__FOOTMENU__', foot)
    .replace('__BANNER__', banner)
    .replace('__TOC__', tocHtml)
    .replace('__BODYCLASS__', tocHtml ? ' has-toc' : '')
    .replace('__CONTENT__', html);
  fs.writeFileSync(path.join(DOCS, path.basename(f, '.md') + '.html'), out);
  built++;
  console.log('  ✓', path.basename(f, '.md') + '.html');
}
fs.writeFileSync(path.join(DOCS, '.nojekyll'), '');
console.log(`\n${built}개 문서를 정적 HTML 로 빌드했습니다. Jekyll 없이 동작합니다.`);
