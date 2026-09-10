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
