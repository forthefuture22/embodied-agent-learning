// 功能级验证：用 DOM 桩执行 projects.html 的渲染逻辑，检查输出完整性
// 用法: node scripts/verify_dashboard.js
const fs = require('fs');
const path = require('path');

const HTML = path.join(__dirname, '..', 'projects.html');
const src = fs.readFileSync(HTML, 'utf8');
const script = src.match(/<script>([\s\S]*)<\/script>/)[1];

const captured = {};
function makeEl(id) {
  return {
    _id: id,
    set innerHTML(v) { captured[id] = v; },
    get innerHTML() { return captured[id] || ''; },
    set textContent(v) { captured[id + ':text'] = v; },
    addEventListener() {},
    classList: { add() {}, remove() {}, toggle() {} },
    dataset: {},
    style: {},
    onclick: null,
  };
}
const els = {};
const document = {
  getElementById: id => (els[id] = els[id] || makeEl(id)),
  querySelectorAll: () => [],
  createElement: () => ({ getContext: () => ({ measureText: () => ({ width: 10 }) }), style: {} }),
};
const navigator = { clipboard: { writeText: () => Promise.resolve() } };
const window = {};

const fn = new Function('document', 'navigator', 'window', script + '\nreturn {DATA, DOMAINS};');
const { DATA, DOMAINS } = fn(document, navigator, window);

const main = captured['list'] || '';
const stats = captured['stats'] || '';
const seg = captured['segDomain'] || '';
const count = captured['count:text'] || '';
const overview = captured['overview'] || '';

let fail = 0;
const check = (cond, msg) => { if (!cond) { console.log('  ✗ ' + msg); fail++; } else console.log('  ✓ ' + msg); };

console.log('=== 数据层 ===');
const projects = Object.values(DATA).filter(p => p.exists);
check(Object.keys(DATA).length === 109, `内嵌数据 109 条（实际 ${Object.keys(DATA).length}）`);
check(projects.length === 109, `有效项目 109 个（实际 ${projects.length}）`);
check(Object.keys(DOMAINS).length === 3, `3 个域（实际 ${Object.keys(DOMAINS).length}）`);
const missingName = projects.filter(p => !p.name).length;
const missingStar = projects.filter(p => !p.star).length;
check(missingName === 0, `项目名无缺失（缺 ${missingName}）`);
check(missingStar === 0, `star 无缺失（缺 ${missingStar}）`);
// 元仓库（如 IsaacSim，仅 1 个 README 指针文件）LOC 为 0 属正常
const noLoc = projects.filter(p => !p.loc && (p.file_count || 0) >= 5).length;
check(noLoc === 0, `代码行数无缺失（排除纯元仓库后缺 ${noLoc}）`);

console.log('\n=== 渲染层 ===');
check(main.length > 50000, `主视图已渲染（${(main.length / 1024).toFixed(0)} KB HTML）`);
check(stats.includes('个已分析项目'), '统计卡片已渲染');
check(seg.includes('data-d="embodied"') && seg.includes('data-d="agent"') && seg.includes('data-d="cross"'), '域筛选按钮完整');
check(/显示 109 \/ 109/.test(count), `计数正确（"${count}"）`);

console.log('\n=== 全景图 ===');
check(overview.includes('项目全景图'), '全景图已渲染');
const tiles = (overview.match(/class="ovtile"/g) || []).length;
check(tiles === 109, `全景图含 109 个矩形（实际 ${tiles}）`);
const ovUndef = (overview.match(/undefined|NaN/g) || []).length;
check(ovUndef === 0, `全景图无 undefined/NaN（发现 ${ovUndef}）`);

console.log('\n=== 卡片完整性 ===');
// 跨分支复用的仓库会在多个分支下各渲染一次，故卡片数 >= 唯一仓库数
const cardCount = (main.match(/class="card"/g) || []).length;
const uniqueCards = new Set((main.match(/data-repo="([^"]+)"/g) || []).map(s => s.slice(11, -1)));
check(cardCount >= 109, `卡片数 >= 109（实际 ${cardCount}）`);
check(uniqueCards.size === 109, `唯一仓库 109 个（实际 ${uniqueCards.size}）`);
const undefinedLeak = (main.match(/undefined/g) || []).length;
check(undefinedLeak === 0, `无 undefined 泄漏（发现 ${undefinedLeak} 处）`);
const nanLeak = (main.match(/NaN/g) || []).length;
check(nanLeak === 0, `无 NaN 泄漏（发现 ${nanLeak} 处）`);
const ghLinks = (main.match(/https:\/\/github\.com\//g) || []).length;
check(ghLinks >= 109, `GitHub 链接 >= 109（实际 ${ghLinks}）`);
const cmdBlocks = (main.match(/class="cmd"/g) || []).length;
check(cmdBlocks > 100, `可复制运行命令 > 100 条（实际 ${cmdBlocks}）`);
const paths = (main.match(/D:\\github/g) || []).length;
check(paths >= 109, `本地路径 >= 109（实际 ${paths}）`);

console.log('\n=== 抽样检查 ===');
for (const repo of ['huggingface/lerobot', 'langchain-ai/langchain', 'vllm-project/vllm']) {
  const p = DATA[repo];
  if (!p) { console.log(`  ✗ 缺少 ${repo}`); fail++; continue; }
  console.log(`  ${repo}: ${p.name} ★${p.star} | ${p.loc.toLocaleString()} 行 / ${p.file_count} 文件 | 模块 ${(p.top_dirs || []).length} | 语言 ${(p.languages || []).length} | 命令 ${(p.run_commands || []).length}`);
  check(p.loc > 0 && p.file_count > 0, `  ${repo} 指标有效`);
  check(main.includes(p.name), `  ${repo} 出现在看板中`);
}

console.log('\n' + '='.repeat(50));
console.log(fail === 0 ? '全部检查通过 ✓' : `${fail} 项检查失败 ✗`);
process.exit(fail === 0 ? 0 : 1);
