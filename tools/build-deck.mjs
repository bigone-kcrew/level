import fs from 'node:fs';
import path from 'node:path';

/* docs/deck/slides/*.html 조각을 docs/deck/shell.html 에 조립해 docs/index.html 을 만든다.
   조각 파일로 나눈 이유는 여러 작업자가 같은 파일을 건드리지 않게 하려는 것이다. */

const ROOT   = path.resolve(import.meta.dirname, '..');
const DECK   = path.join(ROOT, 'docs', 'deck');
const SLIDES = path.join(DECK, 'slides');
const OUT    = path.join(ROOT, 'docs', 'index.html');

const shell = fs.readFileSync(path.join(DECK, 'shell.html'), 'utf8');
if (!shell.includes('<!--SLIDES-->')) {
  console.error('shell.html 에 <!--SLIDES--> 자리표시자가 없습니다.');
  process.exit(1);
}

const files = fs.existsSync(SLIDES)
  ? fs.readdirSync(SLIDES).filter(f => f.endsWith('.html')).sort()
  : [];
if (!files.length) { console.error('docs/deck/slides/ 에 조각 파일이 없습니다.'); process.exit(1); }

let body = '', n = 0, warn = [];
for (const f of files) {
  const src = fs.readFileSync(path.join(SLIDES, f), 'utf8').trim();
  const count = (src.match(/<section[^>]*class="[^"]*\bslide\b/g) || []).length;
  if (!count) warn.push(`${f} — .slide 섹션이 없습니다`);
  // 계약 점검: 리터럴 hex 색, 둥근 모서리, 그림자
  const hex = src.match(/#[0-9A-Fa-f]{3,8}\b/g);
  if (hex) warn.push(`${f} — 리터럴 색 ${[...new Set(hex)].join(' ')} (CSS 변수만 허용)`);
  if (/border-radius\s*:\s*(?!0)/.test(src)) warn.push(`${f} — border-radius 사용 (스위스 그리드: 0)`);
  if (/box-shadow\s*:\s*(?!none)/.test(src)) warn.push(`${f} — box-shadow 사용 (금지)`);
  body += `\n<!-- ══ ${f} ══ -->\n${src}\n`;
  n += count;
}

fs.writeFileSync(OUT, shell.replace('<!--SLIDES-->', body));
console.log(`  조각 ${files.length}개 · 슬라이드 ${n}장 → docs/index.html`);
if (warn.length) {
  console.log('\n  ⚠ 계약 점검');
  warn.forEach(w => console.log('    · ' + w));
}
