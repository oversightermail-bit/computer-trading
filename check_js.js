// 对前端全部 JS 文件做 node --check 语法检查（受限环境：stdio inherit，不捕获输出）
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const NODE = 'C:\\Users\\admin\\.dsh\\dsh-runtimes\\dsh-primary-runtime\\dependencies\\node\\bin\\node.exe';
const FRONT = 'D:\\AI电脑购买指导项目\\前端';

function walk(dir, out) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name.endsWith('.js')) out.push(p);
  }
  return out;
}
const files = walk(FRONT, []);
let fail = 0;
for (const f of files) {
  const r = spawnSync(NODE, ['--check', f], { stdio: 'inherit' });
  console.log((r.status === 0 ? 'OK  ' : 'ERR ') + path.relative(FRONT, f) + ' (exit ' + r.status + ')');
  if (r.status !== 0) fail++;
}
console.log('---');
console.log(files.length + ' files checked, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
