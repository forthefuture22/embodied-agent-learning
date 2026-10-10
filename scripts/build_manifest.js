// 从 mindmap.html 提取树结构，生成 data/manifest.json
// 用法: node scripts/build_manifest.js
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const HTML = path.join(ROOT, 'mindmap.html');
const OUT = path.join(ROOT, 'data', 'manifest.json');

const src = fs.readFileSync(HTML, 'utf8');
const start = src.indexOf('const L =');
const end = src.indexOf('const TABS =');
if (start < 0 || end < 0) throw new Error('无法定位 MAPS 定义');

const core = src.slice(start, end);

const sandbox = {};
const fn = new Function(core + '\nreturn MAPS;');
const MAPS = fn();

const DOMAIN_LABEL = { embodied: '具身智能', agent: 'AI Agent', cross: '交叉地带' };

const manifest = { generatedAt: new Date().toISOString().slice(0, 10), domains: {}, repos: {} };

for (const [dk, d] of Object.entries(MAPS)) {
  const root = d.root;
  const domain = { key: dk, label: DOMAIN_LABEL[dk] || root.label, branches: [] };
  for (const br of root.children || []) {
    const branch = { label: br.label, items: [] };
    for (const leaf of br.children || []) {
      const item = {
        label: leaf.label,
        kind: leaf.kind,
        star: leaf.star || null,
        repo: leaf.repo || null,
        branch: br.label,
        domain: dk,
      };
      branch.items.push(item);
      if (leaf.repo) {
        if (!manifest.repos[leaf.repo]) {
          manifest.repos[leaf.repo] = { repo: leaf.repo, name: leaf.label, star: leaf.star, domains: [], branches: [] };
        }
        const r = manifest.repos[leaf.repo];
        if (!r.domains.includes(dk)) r.domains.push(dk);
        if (!r.branches.includes(br.label)) r.branches.push(br.label);
      }
    }
    domain.branches.push(branch);
  }
  manifest.domains[dk] = domain;
}

fs.writeFileSync(OUT, JSON.stringify(manifest, null, 1), 'utf8');

const repoCount = Object.keys(manifest.repos).length;
console.log('域数量:', Object.keys(manifest.domains).length);
for (const [k, v] of Object.entries(manifest.domains)) {
  const n = v.branches.reduce((a, b) => a + b.items.filter(i => i.repo).length, 0);
  console.log(`  ${v.label.padEnd(10)} 分支 ${String(v.branches.length).padStart(2)}  条目 ${String(v.branches.reduce((a,b)=>a+b.items.length,0)).padStart(3)}  仓库 ${n}`);
}
console.log('唯一仓库数:', repoCount);
console.log('已写入', OUT);
