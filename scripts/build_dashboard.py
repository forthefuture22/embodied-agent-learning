"""生成 projects.html —— 「入口树 + 逐级索引」式的项目浏览器。

信息架构（替代原先一屏平铺 109 张卡片的重型看板）:
    #/                      总览：统计 + 全景树图 + 三大板块
    #/<domain>              板块：该板块下的分支列表
    #/<domain>/<branch>     分支：该分支下的项目紧凑列表
    #/<domain>/<branch>/<repo>   项目：详情（含语义架构，若已分析）

数据来源:
    data/analysis.json   结构级分析（模块/技术栈/运行入口）
    data/arch/*.json     语义级架构分析（子 agent 产出，可选）
    data/priority.json   优先级评分
    data/manifest.json   树结构
"""
import json, os, glob, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, os.pardir)
OUT = os.path.join(ROOT, "projects.html")

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>项目浏览器 · 具身智能 × AI Agent</title>
<style>
  :root{
    --bg:#F7F7F5; --panel:#FFFFFF; --line:#E4E2DC; --line2:#EFEDE7;
    --ink:#2C2C2A; --ink2:#5F5E5A; --ink3:#8B8A85; --ink4:#A9A8A3;
    --emb:#0F6E56; --emb-bg:#E1F5EE; --emb-soft:#F2FBF8;
    --agt:#185FA5; --agt-bg:#E6F1FB; --agt-soft:#F3F9FE;
    --crs:#854F0B; --crs-bg:#FAEEDA; --crs-soft:#FDF8EE;
    --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
  }
  *{box-sizing:border-box}
  html,body{height:100%;margin:0}
  body{background:var(--bg);color:var(--ink);font-size:13.5px;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
    -webkit-font-smoothing:antialiased}
  a{color:inherit}
  button{font:inherit;cursor:pointer}

  /* ---------- 顶栏 ---------- */
  header{position:sticky;top:0;z-index:30;background:var(--panel);border-bottom:1px solid var(--line);
    display:flex;align-items:center;gap:16px;padding:10px 18px;flex-wrap:wrap}
  .brand{font-size:14.5px;font-weight:500;white-space:nowrap}
  .brand span{color:var(--ink3);font-weight:400;font-size:12px;margin-left:7px}
  .search{display:flex;align-items:center;gap:7px;border:1px solid var(--line);border-radius:9px;
    padding:5px 11px;background:var(--panel);flex:0 1 300px}
  .search input{border:none;outline:none;font:inherit;font-size:12.5px;width:100%;background:transparent;color:var(--ink)}
  .search input::placeholder{color:var(--ink4)}
  .hstats{margin-left:auto;display:flex;gap:18px;font-size:11.5px;color:var(--ink3);flex-wrap:wrap}
  .hstats b{color:var(--ink);font-weight:500}

  /* ---------- 布局 ---------- */
  .layout{display:grid;grid-template-columns:286px 1fr;align-items:start;height:calc(100vh - 53px)}
  aside{height:100%;overflow-y:auto;background:var(--panel);border-right:1px solid var(--line);padding:12px 8px 40px}
  main{height:100%;overflow-y:auto;padding:20px 26px 80px}
  @media (max-width:900px){ .layout{grid-template-columns:1fr} aside{display:none} }

  /* ---------- 侧栏树 ---------- */
  .tnode{user-select:none}
  .trow{display:flex;align-items:center;gap:6px;padding:5px 8px;border-radius:7px;cursor:pointer;line-height:1.35}
  .trow:hover{background:#F4F3EE}
  .trow.on{background:#EDEBE4}
  .trow.on .tl{font-weight:500}
  .tw{width:13px;flex:0 0 13px;color:var(--ink4);font-size:9px;text-align:center;transition:transform .13s}
  .tnode.open > .trow .tw{transform:rotate(90deg)}
  .tl{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12.5px}
  .tc{font-size:10.5px;color:var(--ink4);font-family:var(--mono);flex:0 0 auto}
  .tkids{display:none;margin-left:11px;border-left:1px solid var(--line2);padding-left:3px}
  .tnode.open > .tkids{display:block}
  .dot{width:7px;height:7px;border-radius:50%;flex:0 0 7px}
  .tproj .tl{font-size:12px;color:var(--ink2)}
  .tproj .tl .st{color:var(--ink4);font-size:10px;margin-left:4px;font-family:var(--mono)}
  .archflag{color:#0F6E56;font-size:9px;margin-left:3px}

  /* ---------- 内容 ---------- */
  .crumbs{font-size:12px;color:var(--ink3);margin-bottom:14px;display:flex;gap:6px;align-items:center;flex-wrap:wrap}
  .crumbs a{cursor:pointer;border-bottom:1px dotted var(--line)}
  .crumbs a:hover{color:var(--ink)}
  h1.vt{font-size:17px;font-weight:500;margin:0 0 4px}
  .vs{font-size:12.5px;color:var(--ink3);margin-bottom:18px}

  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(268px,1fr));gap:11px}
  .dcard{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:13px 14px;cursor:pointer}
  .dcard:hover{border-color:#C9C7C0}
  .dcard .n{font-size:13.5px;font-weight:500;margin-bottom:5px;display:flex;align-items:center;gap:7px}
  .dcard .m{font-size:11.5px;color:var(--ink3);line-height:1.6}
  .dcard .bar{height:4px;background:#F1EFE8;border-radius:3px;margin-top:9px;overflow:hidden;display:flex}
  .dcard .bar i{height:100%;display:block}

  /* 紧凑项目列表 */
  table.pl{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);border-radius:11px;overflow:hidden}
  table.pl th{text-align:left;font-size:11px;font-weight:400;color:var(--ink3);padding:9px 12px;
    background:#FAFAF8;border-bottom:1px solid var(--line)}
  table.pl td{padding:9px 12px;border-bottom:1px solid var(--line2);font-size:12.5px;vertical-align:middle}
  table.pl tr:last-child td{border-bottom:none}
  table.pl tbody tr{cursor:pointer}
  table.pl tbody tr:hover{background:#FAFAF8}
  .pname{font-weight:500}
  .prepo{font-size:11px;color:var(--ink3);font-family:var(--mono)}
  .num{font-family:var(--mono);font-size:11.5px;color:var(--ink2);text-align:right;white-space:nowrap}
  .chip{display:inline-block;font-size:10.5px;padding:1.5px 7px;border-radius:20px;background:#F1EFE8;color:var(--ink2);white-space:nowrap}
  .chip.star{background:#FAEEDA;color:#854F0B;font-weight:500}
  .chip.lic{background:#EAF3DE;color:#3B6D11}
  .chip.lang{background:#E6F1FB;color:#185FA5}
  .chip.arch{background:#E1F5EE;color:#0F6E56;font-weight:500}
  .chip.pri{background:#EEEDFE;color:#534AB7;font-weight:500}

  /* ---------- 项目详情 ---------- */
  .dhead{display:flex;align-items:flex-start;gap:14px;flex-wrap:wrap;margin-bottom:6px}
  .dhead h1{font-size:19px;font-weight:500;margin:0}
  .dhead .sub{font-size:12px;color:var(--ink3);font-family:var(--mono);margin-top:3px}
  .dchips{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0 16px}
  .panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:15px 17px;margin-bottom:13px}
  .panel > h2{font-size:13.5px;font-weight:500;margin:0 0 3px}
  .panel > .ph{font-size:11.5px;color:var(--ink3);margin-bottom:12px}
  .lead{font-size:13.5px;line-height:1.72;color:var(--ink);margin:0 0 10px}
  .feats{display:flex;flex-wrap:wrap;gap:5px}
  .feats i{font-style:normal;font-size:11px;background:#FAFAF8;border:1px solid var(--line2);
    border-radius:6px;padding:2px 8px;color:var(--ink2)}
  .cols{display:grid;grid-template-columns:1fr 1fr;gap:13px}
  @media (max-width:1080px){ .cols{grid-template-columns:1fr} }
  .bars{display:flex;flex-direction:column;gap:4px}
  .row{display:grid;grid-template-columns:124px 1fr 84px;align-items:center;gap:9px;font-size:11.5px}
  .row .lb{color:var(--ink2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:var(--mono)}
  .track{height:9px;background:#F1EFE8;border-radius:5px;overflow:hidden}
  .fill{height:100%;border-radius:5px;background:#B5D4F4}
  .fill.g{background:#9FE1CB}
  .row .vl{text-align:right;color:var(--ink3);font-family:var(--mono);font-size:11px}
  .cmd{background:#FAFAF8;border:1px solid var(--line2);border-radius:8px;padding:8px 10px;
    font-family:var(--mono);font-size:11.5px;color:var(--ink2);margin-bottom:5px;
    white-space:pre-wrap;word-break:break-all;cursor:pointer}
  .cmd:hover{border-color:#C9C7C0}
  ol.flow,ul.pl2{margin:0;padding-left:19px}
  ol.flow li,ul.pl2 li{margin-bottom:6px;line-height:1.65;font-size:12.5px}
  .tbl{width:100%;border-collapse:collapse;font-size:12.5px}
  .tbl th{text-align:left;font-size:11px;font-weight:400;color:var(--ink3);padding:6px 10px 6px 0;border-bottom:1px solid var(--line2)}
  .tbl td{padding:7px 10px 7px 0;border-bottom:1px solid var(--line2);vertical-align:top;line-height:1.6}
  .tbl tr:last-child td{border-bottom:none}
  .tbl code,.kf code,.cmd{font-family:var(--mono)}
  .tbl code{font-size:11px;background:#FAFAF8;padding:1px 5px;border-radius:4px;color:var(--ink2)}
  .kf{list-style:none;margin:0;padding:0;counter-reset:k}
  .kf li{counter-increment:k;position:relative;padding-left:26px;margin-bottom:9px;line-height:1.6;font-size:12.5px}
  .kf li::before{content:counter(k);position:absolute;left:0;top:1px;width:17px;height:17px;border-radius:50%;
    background:#E1F5EE;color:#0F6E56;font-size:10px;text-align:center;line-height:17px;font-weight:500}
  .kf code{font-size:11px;background:#FAFAF8;padding:1px 5px;border-radius:4px;color:var(--ink2)}
  .note{font-size:12.5px;line-height:1.7;color:var(--ink2);background:#FAFAF8;border-left:2px solid var(--line);
    padding:9px 12px;border-radius:0 7px 7px 0;margin-bottom:7px}
  .mermaid-wrap{overflow-x:auto;background:#FCFCFB;border:1px solid var(--line2);border-radius:9px;padding:12px}
  .mermaid-wrap svg{max-width:100%;height:auto}
  details.src{margin-top:9px}
  details.src summary{font-size:11.5px;color:var(--ink3);cursor:pointer}
  details.src pre{background:#FAFAF8;border:1px solid var(--line2);border-radius:8px;padding:10px;
    font-size:11px;font-family:var(--mono);overflow-x:auto;margin-top:7px;color:var(--ink2)}
  .kpi{display:flex;gap:22px;flex-wrap:wrap;margin-bottom:18px}
  .kpi div b{display:block;font-size:19px;font-weight:500;line-height:1.25}
  .kpi div span{font-size:11.5px;color:var(--ink3)}
  .ovrows{display:flex;flex-direction:column;gap:3px;margin-top:12px}
  .ovrow{display:flex;gap:3px;height:46px}
  .ovtile{border-radius:6px;padding:5px 7px;overflow:hidden;cursor:pointer;display:flex;
    flex-direction:column;justify-content:space-between;min-width:0}
  .ovtile:hover{filter:brightness(.94)}
  .ovtile .n{font-size:11px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .ovtile .v{font-size:9.5px;opacity:.7;font-family:var(--mono);white-space:nowrap}
  .empty{padding:50px;text-align:center;color:var(--ink3)}
  .toast{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);background:#2C2C2A;color:#fff;
    font-size:12.5px;padding:8px 16px;border-radius:9px;opacity:0;transition:opacity .18s;pointer-events:none;z-index:60}
  .toast.on{opacity:1}
  .back{font-size:12.5px;color:var(--ink2);background:none;border:none;padding:0;margin-bottom:12px;
    border-bottom:1px dotted var(--line);cursor:pointer}
  .back:hover{color:var(--ink)}
</style>
</head>
<body>
<header>
  <div class="brand">项目浏览器<span>具身智能 × AI Agent</span></div>
  <div class="search"><input id="q" type="search" placeholder="搜索项目 / 仓库 / 描述…"></div>
  <div class="hstats" id="hstats"></div>
</header>
<div class="layout">
  <aside id="tree"></aside>
  <main id="view"></main>
</div>
<div class="toast" id="toast">已复制</div>

<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>
const DATA = __DATA__;
const ARCH = __ARCH__;
const PRIO = __PRIO__;
const DOMAINS = __DOMAINS__;
const META = __META__;

const PAL = {
  embodied:{c:'#0F6E56',bg:'#E1F5EE',soft:'#F2FBF8',label:'具身智能'},
  agent:{c:'#185FA5',bg:'#E6F1FB',soft:'#F3F9FE',label:'AI Agent'},
  cross:{c:'#854F0B',bg:'#FAEEDA',soft:'#FDF8EE',label:'交叉地带'}
};
const esc = s => String(s==null?'':s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = n => (n==null?0:n).toLocaleString('en-US');
const slug = r => r.replace(/\//g,'__');
const unslug = s => s.replace(/__/,'/');
const starNum = s => { if(!s) return 0; const m=String(s).match(/([\d.]+)\s*([kKmM]?)/); if(!m) return 0;
  let v=parseFloat(m[1]); const u=m[2].toLowerCase(); if(u==='k') v*=1e3; if(u==='m') v*=1e6; return v; };

const PROJECTS = Object.values(DATA).filter(p => p.exists);
const byRepo = {}; PROJECTS.forEach(p => byRepo[p.repo] = p);
const repoBySlug = {}; PROJECTS.forEach(p => repoBySlug[slug(p.repo)] = p.repo);

let mermaidReady = false;
if(window.mermaid){
  try{
    mermaid.initialize({startOnLoad:false, theme:'base', securityLevel:'loose',
      fontFamily:'-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif',
      themeVariables:{primaryColor:'#E1F5EE',primaryTextColor:'#04342C',primaryBorderColor:'#0F6E56',
        lineColor:'#888780',secondaryColor:'#E6F1FB',tertiaryColor:'#FAEEDA',fontSize:'12px'}});
    mermaidReady = true;
  }catch(e){}
}

/* ================= 路由 ================= */
function route(){
  const h = decodeURIComponent(location.hash.replace(/^#\/?/,''));
  if(!h) return {v:'home'};
  const p = h.split('/');
  if(p.length===1) return {v:'domain', d:p[0]};
  if(p.length===2) return {v:'branch', d:p[0], b:+p[1]};
  return {v:'project', d:p[0], b:+p[1], r:repoBySlug[p.slice(2).join('/')]};
}
function go(h){ location.hash = h; }

/* ================= 侧栏树 ================= */
function renderTree(){
  const cur = route();
  let html = `<div class="trow ${cur.v==='home'?'on':''}" onclick="go('')">
      <span class="tw">›</span><span class="tl">总览</span></div>`;
  for(const [dk, dv] of Object.entries(DOMAINS)){
    const pal = PAL[dk];
    const projs = PROJECTS.filter(p => p.domains.includes(dk));
    const open = cur.d === dk;
    html += `<div class="tnode ${open?'open':''}" data-d="${dk}">
      <div class="trow ${cur.v==='domain'&&cur.d===dk?'on':''}" onclick="go('/${dk}')">
        <span class="tw">›</span><span class="dot" style="background:${pal.c}"></span>
        <span class="tl">${pal.label}</span><span class="tc">${projs.length}</span></div>
      <div class="tkids">`;
    dv.branches.forEach((br, i) => {
      const bp = projs.filter(p => p.branches.includes(br));
      if(!bp.length) return;
      const bOpen = cur.d===dk && cur.b===i;
      html += `<div class="tnode ${bOpen?'open':''}">
        <div class="trow ${cur.v==='branch'&&cur.d===dk&&cur.b===i?'on':''}" onclick="go('/${dk}/${i}')">
          <span class="tw">›</span><span class="tl" title="${esc(br)}">${esc(br)}</span>
          <span class="tc">${bp.length}</span></div>
        <div class="tkids">`;
      bp.sort((a,b)=>starNum(b.star)-starNum(a.star)).forEach(p => {
        const on = cur.v==='project' && cur.r===p.repo;
        html += `<div class="trow tproj ${on?'on':''}" onclick="go('/${dk}/${i}/${slug(p.repo)}')">
          <span class="tw"></span>
          <span class="tl" title="${esc(p.name)}">${esc(p.name)}<span class="st">${esc(p.star||'')}</span>${
            ARCH[p.repo]?'<span class="archflag" title="已有语义架构分析">◆</span>':''}</span></div>`;
      });
      html += `</div></div>`;
    });
    html += `</div></div>`;
  }
  document.getElementById('tree').innerHTML = html;
  const on = document.querySelector('#tree .trow.on');
  if(on) on.scrollIntoView({block:'nearest'});
}

/* ================= 复用组件 ================= */
function bars(items, cls, unit){
  if(!items || !items.length) return '<div style="font-size:11.5px;color:var(--ink3)">未检测到</div>';
  const max = Math.max(...items.map(i=>i.v)) || 1;
  return '<div class="bars">' + items.map(i =>
    `<div class="row"><span class="lb" title="${esc(i.n)}">${esc(i.n)}</span>
      <span class="track"><span class="fill ${cls}" style="width:${Math.max(2,(i.v/max)*100)}%"></span></span>
      <span class="vl">${unit==='loc'?fmt(i.v)+' 行':fmt(i.v)}</span></div>`).join('') + '</div>';
}
function crumbs(items){
  return '<div class="crumbs">' + items.map((it,i) =>
    i===items.length-1 ? `<span>${esc(it.t)}</span>`
      : `<a onclick="go('${it.h}')">${esc(it.t)}</a><span>›</span>`).join('') + '</div>';
}

/* ================= 视图：总览 ================= */
function viewHome(){
  const loc = PROJECTS.reduce((a,p)=>a+(p.loc||0),0);
  const files = PROJECTS.reduce((a,p)=>a+(p.file_count||0),0);
  const archN = Object.keys(ARCH).length;
  let html = crumbs([{t:'总览', h:''}]);
  html += `<h1 class="vt">项目全景</h1><div class="vs">${PROJECTS.length} 个已克隆并完成结构分析的开源项目${
    archN?` · 其中 ${archN} 个已完成语义级架构分析`:''}</div>`;
  html += `<div class="kpi">
    <div><b>${PROJECTS.length}</b><span>个项目</span></div>
    <div><b>${fmt(loc)}</b><span>行代码</span></div>
    <div><b>${fmt(files)}</b><span>个文件</span></div>
    <div><b>${archN}</b><span>份语义架构</span></div>
  </div>`;

  html += `<div class="panel"><h2>项目全景图</h2><div class="ph">矩形面积正比于代码行数 · 点击进入项目详情</div>`;
  const ps = PROJECTS.slice().sort((a,b)=>(b.loc||0)-(a.loc||0));
  const total = ps.reduce((a,p)=>a+(p.loc||0),0)||1;
  const ROWS = 6, target = total/ROWS;
  const rows = []; let cur = [], curSum = 0;
  for(const p of ps){
    cur.push(p); curSum += (p.loc||0);
    if(curSum >= target && rows.length < ROWS-1){ rows.push({items:cur,sum:curSum}); cur=[]; curSum=0; }
  }
  if(cur.length) rows.push({items:cur, sum:curSum});
  html += '<div class="ovrows">' + rows.map(r => '<div class="ovrow">' + r.items.map(p=>{
    const pal = PAL[p.domains[0]] || PAL.agent;
    const w = ((p.loc||1)/r.sum*100).toFixed(2);
    const dk = p.domains[0];
    const bi = DOMAINS[dk].branches.findIndex(b => p.branches.includes(b));
    return `<div class="ovtile" style="flex:0 0 ${w}%;background:${pal.bg};color:${pal.c}"
      onclick="go('/${dk}/${bi}/${slug(p.repo)}')" title="${esc(p.name)} · ${fmt(p.loc)} 行">
      <span class="n">${esc(p.name)}</span><span class="v">${fmt(p.loc)}</span></div>`;
  }).join('') + '</div>').join('') + '</div></div>';

  html += `<div class="grid">`;
  for(const [dk, dv] of Object.entries(DOMAINS)){
    const pal = PAL[dk];
    const projs = PROJECTS.filter(p => p.domains.includes(dk));
    const dloc = projs.reduce((a,p)=>a+(p.loc||0),0);
    const darch = projs.filter(p=>ARCH[p.repo]).length;
    html += `<div class="dcard" onclick="go('/${dk}')">
      <div class="n"><span class="dot" style="background:${pal.c}"></span>${pal.label}</div>
      <div class="m">${dv.branches.length} 个分支 · ${projs.length} 个项目<br>${fmt(dloc)} 行代码${
        darch?` · ${darch} 份语义架构`:''}</div>
      <div class="bar">${dv.branches.map((br,i)=>{
        const n = projs.filter(p=>p.branches.includes(br)).length;
        return `<i style="width:${(n/projs.length*100).toFixed(1)}%;background:${pal.c};opacity:${0.35+i*0.06}"></i>`;
      }).join('')}</div></div>`;
  }
  html += `</div>`;
  document.getElementById('view').innerHTML = html;
}

/* ================= 视图：板块 ================= */
function viewDomain(dk){
  const dv = DOMAINS[dk]; if(!dv) return viewHome();
  const pal = PAL[dk];
  const projs = PROJECTS.filter(p => p.domains.includes(dk));
  let html = crumbs([{t:'总览',h:''},{t:pal.label,h:'/'+dk}]);
  html += `<h1 class="vt">${pal.label}</h1>
    <div class="vs">${dv.branches.length} 个分支 · ${projs.length} 个项目 · ${fmt(projs.reduce((a,p)=>a+(p.loc||0),0))} 行代码</div>`;
  html += `<div class="grid">`;
  dv.branches.forEach((br, i) => {
    const bp = projs.filter(p => p.branches.includes(br));
    if(!bp.length) return;
    const loc = bp.reduce((a,p)=>a+(p.loc||0),0);
    const top = bp.slice().sort((a,b)=>starNum(b.star)-starNum(a.star))[0];
    const darch = bp.filter(p=>ARCH[p.repo]).length;
    html += `<div class="dcard" onclick="go('/${dk}/${i}')">
      <div class="n">${esc(br)}</div>
      <div class="m">${bp.length} 个项目 · ${fmt(loc)} 行<br>代表：${esc(top.name)} ${esc(top.star||'')}${
        darch?`<br>◆ ${darch} 份语义架构`:''}</div></div>`;
  });
  html += `</div>`;
  document.getElementById('view').innerHTML = html;
}

/* ================= 视图：分支 ================= */
function viewBranch(dk, bi){
  const dv = DOMAINS[dk]; if(!dv) return viewHome();
  const br = dv.branches[bi]; if(br===undefined) return viewDomain(dk);
  const pal = PAL[dk];
  const projs = PROJECTS.filter(p => p.domains.includes(dk) && p.branches.includes(br))
    .sort((a,b)=>starNum(b.star)-starNum(a.star));
  let html = crumbs([{t:'总览',h:''},{t:pal.label,h:'/'+dk},{t:br,h:`/${dk}/${bi}`}]);
  html += `<h1 class="vt">${esc(br)}</h1>
    <div class="vs">${projs.length} 个项目 · ${fmt(projs.reduce((a,p)=>a+(p.loc||0),0))} 行代码 · 按 star 排序</div>`;
  html += `<table class="pl"><thead><tr>
    <th style="width:26%">项目</th><th style="width:22%">仓库</th><th>说明</th>
    <th style="width:82px;text-align:right">代码行</th><th style="width:60px;text-align:right">star</th>
    <th style="width:76px">架构</th></tr></thead><tbody>`;
  for(const p of projs){
    const desc = ((p.readme&&p.readme.summary) || p.description || '').slice(0, 70);
    html += `<tr onclick="go('/${dk}/${bi}/${slug(p.repo)}')">
      <td><span class="pname">${esc(p.name)}</span></td>
      <td><span class="prepo">${esc(p.repo)}</span></td>
      <td style="color:var(--ink2)">${esc(desc)}${desc.length>=70?'…':''}</td>
      <td class="num">${fmt(p.loc)}</td>
      <td class="num">${esc(p.star||'')}</td>
      <td>${ARCH[p.repo]?'<span class="chip arch">◆ 已分析</span>':'<span style="color:var(--ink4);font-size:11px">—</span>'}</td>
    </tr>`;
  }
  html += `</tbody></table>`;
  document.getElementById('view').innerHTML = html;
}

/* ================= 视图：项目详情 ================= */
function viewProject(dk, bi, repo){
  const p = byRepo[repo]; if(!p) return viewHome();
  const dv = DOMAINS[dk], pal = PAL[dk];
  const br = dv ? dv.branches[bi] : p.branches[0];
  const a = ARCH[repo];
  const pri = PRIO[repo];

  let html = crumbs([{t:'总览',h:''},{t:pal.label,h:'/'+dk},
    {t:br||'—',h:`/${dk}/${bi}`},{t:p.name,h:''}]);
  html += `<div class="dhead"><div>
      <h1>${esc(p.name)}</h1>
      <div class="sub">${esc(p.repo)} · ${esc(p.path||'')}</div></div></div>`;
  html += `<div class="dchips">
    ${p.star?`<span class="chip star">★ ${esc(p.star)}</span>`:''}
    ${p.language?`<span class="chip lang">${esc(p.language)}</span>`:''}
    ${p.license&&p.license!=='无'?`<span class="chip lic">${esc(p.license)}</span>`:''}
    ${a?`<span class="chip arch">◆ 语义架构已分析</span>`:''}
    ${pri?`<span class="chip pri" title="任务A 语义架构图优先级">架构优先级 ${pri.arch_score}</span>`:''}
    ${pri?`<span class="chip pri" title="任务B 网页工具改造适用性">工具改造 ${pri.tool_score}</span>`:''}
    <span class="chip">${fmt(p.file_count)} 文件 · ${fmt(p.loc)} 行</span>
  </div>`;

  if(a){
    html += `<div class="panel" style="border-left:3px solid ${pal.c}">
      <h2>语义架构</h2><div class="ph">由子 agent 深读源码产出 · 置信度 ${esc(a.confidence||'—')} · 难度 ${esc(a.difficulty||'—')}</div>
      <p class="lead">${esc(a.one_liner||'')}</p>
      <div class="note">${esc(a.problem||'')}</div>`;
    if(a.diagram_mermaid){
      html += `<div class="mermaid-wrap"><pre class="mermaid">${esc(a.diagram_mermaid)}</pre></div>
        <details class="src"><summary>查看 Mermaid 源码</summary><pre>${esc(a.diagram_mermaid)}</pre></details>`;
    }
    html += `</div>`;

    if((a.core_abstractions||[]).length){
      html += `<div class="panel"><h2>核心抽象</h2><div class="ph">读懂这几个类，就读懂了半个项目</div>
        <table class="tbl"><thead><tr><th style="width:150px">抽象</th><th>职责</th><th style="width:38%">定义位置</th></tr></thead><tbody>`;
      for(const c of a.core_abstractions)
        html += `<tr><td><b>${esc(c.name)}</b></td><td>${esc(c.role)}</td><td><code>${esc(c.file)}</code></td></tr>`;
      html += `</tbody></table></div>`;
    }
    if((a.layers||[]).length){
      html += `<div class="panel"><h2>分层结构</h2><div class="ph">自顶向下的职责划分</div>
        <table class="tbl"><thead><tr><th style="width:150px">层</th><th>职责</th><th style="width:34%">主要模块</th></tr></thead><tbody>`;
      for(const l of a.layers)
        html += `<tr><td><b>${esc(l.name)}</b></td><td>${esc(l.responsibility)}</td>
          <td>${(l.modules||[]).map(m=>`<code>${esc(m)}</code>`).join(' ')}</td></tr>`;
      html += `</tbody></table></div>`;
    }
    if((a.data_flow||[]).length){
      html += `<div class="panel"><h2>数据流</h2><div class="ph">从输入到输出的完整链路</div><ol class="flow">`;
      for(const s of a.data_flow) html += `<li>${esc(s)}</li>`;
      html += `</ol></div>`;
    }
    const two = [];
    if((a.key_files||[]).length){
      two.push(`<div class="panel"><h2>建议阅读顺序</h2><div class="ph">按这个顺序读，不要从入口直接跳</div><ol class="kf">` +
        a.key_files.map(k=>`<li><code>${esc(k.path)}</code><br>${esc(k.why)}</li>`).join('') + `</ol></div>`);
    }
    if((a.learning_path||[]).length || (a.extension_points||[]).length){
      let s = `<div class="panel"><h2>学习路径与扩展点</h2>`;
      if((a.learning_path||[]).length)
        s += `<div class="ph">建议学习顺序</div><ol class="flow">` +
             a.learning_path.map(x=>`<li>${esc(x)}</li>`).join('') + `</ol>`;
      if((a.extension_points||[]).length)
        s += `<div class="ph" style="margin-top:14px">想扩展时改哪里</div><ul class="pl2">` +
             a.extension_points.map(x=>`<li>${esc(x)}</li>`).join('') + `</ul>`;
      two.push(s + `</div>`);
    }
    if(two.length) html += `<div class="cols">${two.join('')}</div>`;

    if((a.surprises||[]).length){
      html += `<div class="panel"><h2>容易踩的坑</h2><div class="ph">反直觉的设计，读之前先知道</div>`;
      for(const s of a.surprises) html += `<div class="note">${esc(s)}</div>`;
      html += `</div>`;
    }
  } else {
    html += `<div class="panel"><h2>语义架构</h2><div class="ph">尚未分析</div>
      <div class="note">该项目还没有做语义级架构分析（需人工深读代码）。当前展示的是自动扫描出的结构级信息。
      优先级评分：架构优先级 <b>${pri?pri.arch_score:'—'}</b>。</div></div>`;
  }

  const desc = (p.readme&&p.readme.summary) || p.description || '';
  const feats = (p.readme&&p.readme.features)||[];
  if(desc || feats.length){
    html += `<div class="panel"><h2>功能全景</h2><div class="ph">来自 README 与仓库元数据</div>`;
    if(desc) html += `<p class="lead">${esc(desc)}</p>`;
    if(feats.length) html += `<div class="feats">${feats.slice(0,10).map(f=>`<i>${esc(f.slice(0,60))}</i>`).join('')}</div>`;
    html += `</div>`;
  }

  const langs = (p.languages||[]).filter(l=>l.loc>0).slice(0,7).map(l=>({n:l.name,v:l.loc}));
  const dirs = (p.top_dirs||[]).slice(0,8).map(d=>({n:d.name+'/', v:d.loc||d.files}));
  html += `<div class="cols">
    <div class="panel"><h2>模块架构</h2><div class="ph">顶层目录按代码行数</div>${bars(dirs,'g','loc')}</div>
    <div class="panel"><h2>技术栈</h2><div class="ph">按代码行数分布</div>${bars(langs,'','loc')}</div>
  </div>`;

  const cmds = p.run_commands||[], ents = p.entry_points||[];
  if(cmds.length || ents.length){
    html += `<div class="panel"><h2>运行流程</h2><div class="ph">点击命令可复制</div>`;
    for(const c of cmds.slice(0,4)) html += `<div class="cmd" data-cmd="${esc(c)}">${esc(c)}</div>`;
    if(ents.length) html += `<div class="feats" style="margin-top:9px">${
      ents.slice(0,8).map(e=>`<i>${esc(e.kind)}: ${esc(e.file)}</i>`).join('')}</div>`;
    html += `</div>`;
  }

  html += `<div class="panel"><h2>其他</h2><div class="ph">数据与出处</div>
    <table class="tbl"><tbody>
      <tr><td style="width:110px;color:var(--ink3)">GitHub</td><td><a href="https://github.com/${esc(p.repo)}" target="_blank">${esc(p.repo)} ↗</a></td></tr>
      <tr><td style="color:var(--ink3)">本地路径</td><td><code>${esc(p.path||'')}</code></td></tr>
      <tr><td style="color:var(--ink3)">最后推送</td><td>${esc(p.pushed_at||'—')}</td></tr>
      ${(p.topics||[]).length?`<tr><td style="color:var(--ink3)">Topics</td><td>${(p.topics||[]).map(t=>`<span class="chip">${esc(t)}</span>`).join(' ')}</td></tr>`:''}
    </tbody></table></div>`;

  document.getElementById('view').innerHTML = html;

  document.querySelectorAll('.cmd').forEach(el=>{
    el.onclick = ()=>{
      navigator.clipboard.writeText(el.dataset.cmd).then(()=>{
        const t = document.getElementById('toast');
        t.textContent = '已复制: ' + el.dataset.cmd.slice(0,44);
        t.classList.add('on'); setTimeout(()=>t.classList.remove('on'), 1400);
      }).catch(()=>{});
    };
  });
  if(mermaidReady){
    try{ mermaid.run({querySelector:'.mermaid'}); }catch(e){}
  }
}

/* ================= 搜索 ================= */
function runSearch(q){
  q = q.trim().toLowerCase();
  if(!q) return false;
  const hits = PROJECTS.filter(p =>
    (p.name||'').toLowerCase().includes(q) || (p.repo||'').toLowerCase().includes(q) ||
    ((p.description||'')+((p.readme&&p.readme.summary)||'')).toLowerCase().includes(q));
  let html = crumbs([{t:'搜索结果',h:''}]);
  html += `<h1 class="vt">搜索「${esc(q)}」</h1><div class="vs">命中 ${hits.length} 个项目</div>`;
  if(!hits.length){ html += `<div class="empty">没有匹配的项目</div>`; }
  else {
    html += `<table class="pl"><thead><tr><th style="width:24%">项目</th><th style="width:20%">仓库</th>
      <th>所属分支</th><th style="width:82px;text-align:right">代码行</th><th style="width:60px;text-align:right">star</th></tr></thead><tbody>`;
    for(const p of hits.sort((a,b)=>starNum(b.star)-starNum(a.star))){
      const dk = p.domains[0], bi = DOMAINS[dk].branches.findIndex(b=>p.branches.includes(b));
      html += `<tr onclick="go('/${dk}/${bi}/${slug(p.repo)}')">
        <td><span class="pname">${esc(p.name)}</span>${ARCH[p.repo]?' <span class="chip arch">◆</span>':''}</td>
        <td><span class="prepo">${esc(p.repo)}</span></td>
        <td style="color:var(--ink2);font-size:12px">${esc(p.branches.join(' / '))}</td>
        <td class="num">${fmt(p.loc)}</td><td class="num">${esc(p.star||'')}</td></tr>`;
    }
    html += `</tbody></table>`;
  }
  document.getElementById('view').innerHTML = html;
  return true;
}

/* ================= 渲染 ================= */
function render(){
  const q = document.getElementById('q').value;
  renderTree();
  const cur = route();
  if(q.trim()){ runSearch(q); }
  else if(cur.v==='home') viewHome();
  else if(cur.v==='domain') viewDomain(cur.d);
  else if(cur.v==='branch') viewBranch(cur.d, cur.b);
  else if(cur.v==='project') viewProject(cur.d, cur.b, cur.r);
  else viewHome();
  document.getElementById('view').scrollTop = 0;
}

function renderStats(){
  const loc = PROJECTS.reduce((a,p)=>a+(p.loc||0),0);
  const archN = Object.keys(ARCH).length;
  document.getElementById('hstats').innerHTML =
    `<span><b>${PROJECTS.length}</b> 项目</span>
     <span><b>${fmt(loc)}</b> 行</span>
     <span><b>${archN}</b> 份语义架构</span>
     <span>${META.date||''}</span>`;
}

window.addEventListener('hashchange', render);
document.getElementById('q').addEventListener('input', render);
renderStats(); render();
</script>
</body>
</html>
"""


def main():
    analysis = json.load(open(os.path.join(ROOT, "data", "analysis.json"), encoding="utf-8"))
    manifest = json.load(open(os.path.join(ROOT, "data", "manifest.json"), encoding="utf-8"))

    prio_path = os.path.join(ROOT, "data", "priority.json")
    prio = json.load(open(prio_path, encoding="utf-8")) if os.path.isfile(prio_path) else {}

    arch = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "arch", "*.json"))):
        try:
            d = json.load(open(f, encoding="utf-8"))
            if d.get("repo"):
                arch[d["repo"]] = d
        except Exception as e:
            print(f"  跳过 {os.path.basename(f)}: {e}")

    keep = ("repo", "name", "star", "domains", "branches", "path", "exists", "license",
            "language", "description", "topics", "file_count", "loc", "languages",
            "top_dirs", "readme", "run_commands", "entry_points", "deps", "pushed_at")
    slim = {}
    for repo, a in analysis.items():
        slim[repo] = {k: a.get(k) for k in keep if k in a}
        if slim[repo].get("readme"):
            slim[repo]["readme"] = {
                "summary": slim[repo]["readme"].get("summary", ""),
                "features": slim[repo]["readme"].get("features", []),
            }
    # 精简 priority
    prio_slim = {r: {"arch_score": v["arch_score"], "tool_score": v["tool_score"]}
                 for r, v in prio.items()}

    domains = {k: {"label": v["label"], "branches": [b["label"] for b in v["branches"]]}
               for k, v in manifest["domains"].items()}
    meta = {"date": datetime.date.today().isoformat()}

    out = (TEMPLATE
           .replace("__DATA__", json.dumps(slim, ensure_ascii=False, separators=(",", ":")))
           .replace("__ARCH__", json.dumps(arch, ensure_ascii=False, separators=(",", ":")))
           .replace("__PRIO__", json.dumps(prio_slim, ensure_ascii=False, separators=(",", ":")))
           .replace("__DOMAINS__", json.dumps(domains, ensure_ascii=False, separators=(",", ":")))
           .replace("__META__", json.dumps(meta, ensure_ascii=False, separators=(",", ":"))))

    open(OUT, "w", encoding="utf-8").write(out)
    exist = sum(1 for a in analysis.values() if a.get("exists"))
    print(f"项目 {exist}/{len(analysis)}   语义架构 {len(arch)} 份   优先级 {len(prio)} 条")
    print(f"已生成 {OUT}  ({len(out)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
