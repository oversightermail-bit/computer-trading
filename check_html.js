// 校验每个 HTML 引用的本地资源（css/js/img）都存在
const fs = require('fs');
const path = require('path');

const FRONT = 'D:\\AI电脑购买指导项目\\前端';

function walk(dir, out) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name.endsWith('.html')) out.push(p);
  }
  return out;
}

const htmls = walk(FRONT, []);
let bad = 0;
for (const h of htmls) {
  const src = fs.readFileSync(h, 'utf8');
  const re = /(?:src|href)="([^"]+)"/g;
  let m;
  while ((m = re.exec(src)) !== null) {
    let ref = m[1];
    if (/^(https?:|mailto:|#|data:)/.test(ref)) continue;
    ref = ref.split('#')[0].split('?')[0];
    if (!ref) continue;
    try { ref = decodeURIComponent(ref); } catch (e) {}
    const abs = path.resolve(path.dirname(h), ref);
    if (!fs.existsSync(abs)) {
      bad++;
      console.log('MISSING  ' + path.relative(FRONT, h) + '  ->  ' + ref);
    }
  }
}
console.log('---');
console.log(htmls.length + ' html checked, ' + bad + ' missing refs');
process.exit(bad ? 1 : 0);
