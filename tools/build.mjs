import fs from 'node:fs';
import path from 'node:path';
import { marked } from 'marked';

const ROOT = path.resolve(import.meta.dirname, '..');
const DOCS = path.join(ROOT, 'docs');
const layout = fs.readFileSync(path.join(import.meta.dirname, 'layout.html'), 'utf8');

const NAV = [
  ['diagnosis', '01 진단'],
  ['amendments', '02 개정안'],
  ['benchmark', '03 타기관'],
  ['bargaining', '04 교섭'],
  ['plan', '05 계획'],
  ['union', '06 전임자'],
  ['plan2027', '07 시행계획'],
  ['guide', '08 세부지침'],
  ['method', '09 근거'],
  ['compare', '10 대비'],
];

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
  const nav = NAV.map(([k, label]) =>
    `<a href="${k}.html"${k === key ? ' class="on" aria-current="page"' : ''}>${label}</a>`).join('');
  const out = layout
    .replace('__TITLE__', esc(fm.title || key))
    .replace('__DESC__', esc(fm.description || ''))
    .replace('__NAV__', nav)
    .replace('__CONTENT__', html);
  fs.writeFileSync(path.join(DOCS, path.basename(f, '.md') + '.html'), out);
  built++;
  console.log('  ✓', path.basename(f, '.md') + '.html');
}
fs.writeFileSync(path.join(DOCS, '.nojekyll'), '');
console.log(`\n${built}개 문서를 정적 HTML 로 빌드했습니다. Jekyll 없이 동작합니다.`);
