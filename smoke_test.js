// Mock API 冒烟测试：在 Node 中模拟浏览器环境，跑通核心业务闭环
const fs = require('fs');
const vm = require('vm');

const FRONT = 'D:\\AI电脑购买指导项目\\前端\\assets\\js';

/* ---- 浏览器环境桩（sandbox 即全局，window 指向它自己） ---- */
const store = new Map();
const sandbox = {
  localStorage: {
    getItem: k => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: k => store.delete(k),
  },
  location: { href: 'file:///x.html' },
  document: { addEventListener: () => {} },
  btoa: s => Buffer.from(s, 'binary').toString('base64'),
  unescape: s => decodeURIComponent(s.replace(/\+/g, ' ')),
  encodeURIComponent,
  decodeURIComponent,
  setTimeout, clearTimeout,
  Math, JSON, Date, Number, String, Object, Array, Promise, RegExp,
  parseInt, parseFloat, isNaN, Error,
  console,
};
sandbox.window = sandbox;
const ctx = vm.createContext(sandbox);

function load(file) {
  vm.runInContext(fs.readFileSync(FRONT + '\\' + file, 'utf8'), ctx, { filename: file });
}
load('config.js');
load('data.js');
load('ui.js');
load('api.js');

const api = vm.runInContext('api', ctx);
let pass = 0, fail = 0;
function check(name, cond, extra) {
  if (cond) { pass++; console.log('  PASS ' + name); }
  else { fail++; console.log('  FAIL ' + name + (extra ? '  => ' + JSON.stringify(extra) : '')); }
}

(async () => {
  console.log('[1] 注册 / 登录');
  let r = await api.register({ username: '张三三', password: '123456' });
  check('注册成功 code=0', r.code === 0, r);
  r = await api.register({ username: '张三三', password: '123456' });
  check('重复注册被拒', r.code !== 0, r);
  r = await api.login({ username: '张三三', password: 'wrong' });
  check('错误密码 40101', r.code === 40101, r);
  r = await api.login({ username: '张三三', password: '123456' });
  check('登录成功返回 token+plan', r.code === 0 && !!r.data.token && r.data.plan === '免费版', r);
  r = await api.login({ username: 'demo', password: 'demo123' });
  check('演示账号 demo/demo123 可用', r.code === 0, r);

  console.log('[2] 公开数据');
  r = await api.hardware();
  check('10 类硬件', r.code === 0 && r.data.length === 10, r.data && r.data.length);
  check('45 个型号合计', r.code === 0 && r.data.reduce((a, b) => a + b.productCount, 0) === 45);
  r = await api.search('4060');
  check('搜索 4060 命中型号', r.code === 0 && r.data.products.some(p => p.model.indexOf('4060') >= 0), r.data && r.data.products && r.data.products.length);
  r = await api.search('固态');
  check('搜索 固态 命中分类', r.code === 0 && r.data.hardware.some(h => h.type === 'ssd'), r.data && r.data.hardware);
  r = await api.priceContent('cpu');
  check('CPU 文案完整', r.code === 0 && r.data.name === 'CPU（台式机）' && r.data.func && r.data.scene && r.data.pitfall);
  r = await api.priceSeries('gpu');
  check('GPU 6 条折线 × 30 天', r.code === 0 && r.data.series.length === 6 && r.data.dates.length === 30, r.data && r.data.series && r.data.series.length);
  check('推荐平台表 6 行且含平台', r.code === 0 && r.data.recommend.length === 6 && r.data.recommend.every(x => x.platform), r.data && r.data.recommend && r.data.recommend[0]);
  const kb = await api.priceSeries('keyboard');
  check('键盘 6 条折线（可显隐）', kb.code === 0 && kb.data.series.length === 6, kb.data && kb.data.series && kb.data.series.length);

  console.log('[3] 免费版额度（3 次/日，仅文本）');
  r = await api.quota();
  check('免费版 3/60', r.code === 0 && r.data.dayTotal === 3 && r.data.monthTotal === 60, r.data);
  r = await api.aiChat({ content: '5000元预算打游戏' });
  check('文本问答 ok，扣 1 次', r.code === 0 && r.data.cost === 1 && r.data.dayRemain === 2, r.data);
  check('回答含配置行', r.code === 0 && /•/.test(r.data.answer), r.data && r.data.answer);
  r = await api.aiChat({ content: 'RTX 4060 和 RX 6750 XT 哪个划算？' });
  check('对比问答 ok', r.code === 0 && /结论/.test(r.data.answer), r.data && r.data.answer);
  r = await api.aiChat({ content: '固态硬盘怎么选', imageUrl: 'data:image/png;base64,xxx' });
  check('免费版图片被拒 40301', r.code === 40301, r);
  r = await api.aiChat({ content: '再来一次' });
  check('第 3 次用尽日额度', r.code === 0 && r.data.dayRemain === 0, r.data);
  r = await api.aiChat({ content: '还想问' });
  check('额度用尽 42901 + 可升级列表', r.code === 42901 && r.data && r.data.upgradable && r.data.upgradable.length === 3, r);

  console.log('[4] 升级订阅');
  r = await api.plans();
  check('4 个套餐', r.code === 0 && r.data.length === 4);
  r = await api.subscribe(2);
  check('升级基础版成功', r.code === 0 && r.data.planName === '基础版' && r.data.quotaDay === 20, r.data);
  r = await api.aiChat({ content: '看图', imageUrl: 'data:image/png;base64,xxx' });
  check('基础版图片问答 ok，扣 2 次（已用量延续：3+2=5，剩 15）', r.code === 0 && r.data.cost === 2 && r.data.dayRemain === 15, r.data);
  r = await api.quotaLogs(1, 20);
  check('消耗明细可查', r.code === 0 && r.data.records.length >= 4, r.data && r.data.records && r.data.records.length);

  console.log('[5] 数据质量');
  const ser = await api.priceSeries('ssd');
  const flat = ser.data.series.flatMap(s => s.data).filter(v => v != null);
  check('SSD 价格全部为正', flat.every(v => v > 0), flat.length);
  check('价格区间合理', Math.min(...flat) > 30 && Math.max(...flat) < 20000, [Math.min(...flat), Math.max(...flat)]);

  console.log('---');
  console.log('RESULT: ' + pass + ' passed, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('FATAL', e); process.exit(2); });
