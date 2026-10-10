// 功能级验证：用 DOM 桩执行 projects.html 的四个视图与搜索，检查输出完整性
// 用法: node scripts/verify_dashboard.js
const fs = require('fs');
const path = require('path');

const HTML = path.join(__dirname, '..', 'projects.html');
const src = fs.readFileSync(HTML, 'utf8');
const script = src.match(/<script>([\s\S]*?)<\/script>\s*<\/body>/)[1];

const captured = {};
function makeEl(id) {
  return {
    _id: id,
    set innerHTML(v) { captured[id] = v; },
    get innerHTML() { return captured[id] || ''; },
    set textContent(v) { captured[id + ':text'] = v; },
    addEventListener() {}, scrollIntoView() {}, classList: { add(){}, remove(){}, toggle(){} },
    dataset: {}, style: {}, value: '',
  };
}
const els = {};
const document = {
  getElementById: id => (els[id] = els[id] || makeEl(id)),
  querySelectorAll: () => [],
  querySelector: () => null,
  createElement: () => ({ getContext: () => ({ measureText: () => ({ width: 10 }) }), style: {} }),
};
const navigator = { clipboard: { writeText: () => Promise.resolve() } };
const location = { hash: '' };
const window = { addEventListener() {} };

const fn = new Function('document', 'navigator', 'window', 'location',
  script + '\nreturn {PROJECTS, ARCH, PRIO, DOMAINS, route, viewHome, viewDomain, viewBranch, viewProject, runSearch, renderTree, slug, starNum};');
const M = fn(document, navigator, window, location);
const { PROJECTS, ARCH, DOMAINS } = M;

let fail = 0;
const check = (cond, msg) => { if (!cond) { console.log('  x ' + msg); fail++; } else console.log('  v ' + msg); };
const noLeak = (html, label) => {
  const u = (html.match(/undefined/g) || []).length;
  const n = (html.match(/NaN/g) || []).length;
  check(u === 0 && n === 0, `${label} 无 undefined/NaN 泄漏（undefined ${u} / NaN ${n}）`);
};

// 语义架构份数随批次增长，以 data/arch/ 目录实际文件数为准
const archFiles = fs.readdirSync(path.join(__dirname, '..', 'data', 'arch'))
  .filter(f => f.endsWith('.json')).length;

console.log('=== 数据层 ===');
check(PROJECTS.length === 109, `项目 109 个（实际 ${PROJECTS.length}）`);
check(Object.keys(ARCH).length === archFiles,
  `语义架构 ${archFiles} 份全部内嵌（实际 ${Object.keys(ARCH).length}）`);
check(Object.keys(DOMAINS).length === 3, `域 3 个（实际 ${Object.keys(DOMAINS).length}）`);
const totalBranches = Object.values(DOMAINS).reduce((a, d) => a + d.branches.length, 0);
check(totalBranches === 25, `分支 25 个（实际 ${totalBranches}）`);
check(Object.keys(M.PRIO).length === 109, `优先级 109 条（实际 ${Object.keys(M.PRIO).length}）`);

console.log('\n=== 视图 1/4：总览 ===');
M.viewHome();
const home = captured['view'] || '';
check(home.length > 5000, `已渲染（${(home.length / 1024).toFixed(0)} KB）`);
check(home.includes('项目全景图'), '含全景树图');
const tiles = (home.match(/class="ovtile"/g) || []).length;
check(tiles === 109, `全景图 109 个矩形（实际 ${tiles}）`);
check((home.match(/class="dcard"/g) || []).length === 3, '含 3 个板块卡片');
noLeak(home, '总览');

console.log('\n=== 视图 2/4：板块 ===');
M.viewDomain('embodied');
const dom = captured['view'] || '';
check(dom.includes('具身智能'), '标题正确');
check((dom.match(/class="dcard"/g) || []).length === 9, `具身智能 9 个分支卡片（实际 ${(dom.match(/class="dcard"/g) || []).length}）`);
noLeak(dom, '板块');

console.log('\n=== 视图 3/4：分支 ===');
M.viewBranch('embodied', 3);
const br = captured['view'] || '';
const rows = (br.match(/<tr onclick=/g) || []).length;
check(rows > 0, `分支项目列表 ${rows} 行`);
check(br.includes('class="pl"'), '使用紧凑表格布局');
noLeak(br, '分支');

console.log('\n=== 视图 4/4：项目详情 ===');
M.viewProject('embodied', 3, 'huggingface/lerobot');
const pj = captured['view'] || '';
check(pj.includes('语义架构'), '含语义架构区块');
check(pj.includes('核心抽象'), '含核心抽象表');
check(pj.includes('分层结构'), '含分层结构表');
check(pj.includes('数据流'), '含数据流');
check(pj.includes('建议阅读顺序'), '含建议阅读顺序');
check(pj.includes('容易踩的坑'), '含踩坑提示');
check(pj.includes('class="mermaid"'), '含 Mermaid 图容器');
check(pj.includes('功能全景') && pj.includes('模块架构') && pj.includes('技术栈') && pj.includes('运行流程'),
  '含结构级四区块');
noLeak(pj, '项目详情');

console.log('\n=== 无架构分析的项目 ===');
// 随批次推进，已分析的项目会变化，故动态挑一个尚未分析的
const noArch = PROJECTS.find(p => !ARCH[p.repo]);
if (noArch) {
  const dk = noArch.domains[0];
  const bi = DOMAINS[dk].branches.findIndex(b => noArch.branches.includes(b));
  M.viewProject(dk, bi, noArch.repo);
  const pj2 = captured['view'] || '';
  check(pj2.includes('尚未分析'), `「${noArch.name}」正确显示「尚未分析」占位`);
  check(pj2.includes('架构优先级'), '显示优先级评分');
  noLeak(pj2, '未分析项目');
} else {
  console.log('  v 全部项目均已分析，跳过该检查');
}

console.log('\n=== 侧栏树 ===');
M.renderTree();
const tree = captured['tree'] || '';
check(tree.includes('总览'), '含总览入口');
check((tree.match(/class="trow/g) || []).length > 130, `树节点数 ${(tree.match(/class="trow/g) || []).length} > 130`);
check(tree.includes('archflag'), '标记了已做语义架构的项目');
noLeak(tree, '侧栏树');

console.log('\n=== 搜索 ===');
M.runSearch('robot');
const sr = captured['view'] || '';
check(sr.includes('搜索结果'), '搜索视图已渲染');
noLeak(sr, '搜索');

console.log('\n=== 路由 ===');
location.hash = '';
check(M.route().v === 'home', '空 hash -> 总览');
location.hash = '#/embodied';
check(M.route().v === 'domain' && M.route().d === 'embodied', '/embodied -> 板块');
location.hash = '#/embodied/3';
check(M.route().v === 'branch' && M.route().b === 3, '/embodied/3 -> 分支');
location.hash = '#/embodied/3/huggingface__lerobot';
check(M.route().v === 'project' && M.route().r === 'huggingface/lerobot', '深链接 -> 项目');

console.log('\n' + '='.repeat(50));
console.log(fail === 0 ? '全部检查通过' : `${fail} 项检查失败`);
process.exit(fail === 0 ? 0 : 1);
