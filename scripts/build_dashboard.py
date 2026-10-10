"""把 data/analysis.json + data/manifest.json 渲染成自包含的交互式看板 projects.html。

每个项目呈现四块可视化梳理：
    功能全景 / 模块架构 / 技术栈 / 运行流程
全部数据来自对本地克隆代码的真实扫描。
"""
import json, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, os.pardir)
ANALYSIS = os.path.join(ROOT, "data", "analysis.json")
MANIFEST = os.path.join(ROOT, "data", "manifest.json")
OUT = os.path.join(ROOT, "projects.html")

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>开源项目可视化梳理 · 具身智能 × AI Agent</title>
<style>
  :root{
    --bg:#F7F7F5; --panel:#FFFFFF; --line:#E4E2DC; --line2:#EFEDE7;
    --ink:#2C2C2A; --ink2:#5F5E5A; --ink3:#8B8A85;
    --emb:#0F6E56; --emb-bg:#E1F5EE; --emb-soft:#F2FBF8;
    --agt:#185FA5; --agt-bg:#E6F1FB; --agt-soft:#F3F9FE;
    --crs:#854F0B; --crs-bg:#FAEEDA; --crs-soft:#FDF8EE;
    --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
    -webkit-font-smoothing:antialiased;font-size:14px}
  a{color:inherit}
  header{background:var(--panel);border-bottom:1px solid var(--line);padding:20px 26px 16px;position:sticky;top:0;z-index:20}
  h1{margin:0 0 4px;font-size:19px;font-weight:500}
  .sub{font-size:12.5px;color:var(--ink3)}
  .stats{display:flex;gap:26px;margin-top:14px;flex-wrap:wrap}
  .stat b{display:block;font-size:20px;font-weight:500;line-height:1.2}
  .stat span{font-size:11.5px;color:var(--ink3)}
  .bar{display:flex;gap:10px;align-items:center;margin-top:14px;flex-wrap:wrap}
  .seg{display:flex;border:1px solid var(--line);border-radius:9px;overflow:hidden;background:var(--panel)}
  .seg button{font:inherit;font-size:12.5px;background:transparent;border:none;padding:6px 13px;
    cursor:pointer;color:var(--ink2);border-right:1px solid var(--line)}
  .seg button:last-child{border-right:none}
  .seg button.on{background:#EDEBE4;color:var(--ink);font-weight:500}
  input[type=search],select{font:inherit;font-size:12.5px;padding:6px 11px;border:1px solid var(--line);
    border-radius:9px;background:var(--panel);color:var(--ink);outline:none}
  input[type=search]{width:230px}
  input[type=search]:focus,select:focus{border-color:#C9C7C0}
  main{padding:22px 26px 60px;max-width:1500px}
  .domain{margin-bottom:34px}
  .domain > h2{font-size:15px;font-weight:500;margin:0 0 4px;display:flex;align-items:center;gap:9px}
  .dot{width:9px;height:9px;border-radius:50%}
  .domain > .meta{font-size:12px;color:var(--ink3);margin-bottom:16px}
  .branch{margin:0 0 20px}
  .branch > h3{font-size:13px;font-weight:500;color:var(--ink2);margin:0 0 10px;
    padding-bottom:6px;border-bottom:1px solid var(--line2)}
  .cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(430px,1fr));gap:13px}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 15px;overflow:hidden}
  .card.miss{opacity:.55}
  .chead{display:flex;align-items:baseline;gap:9px;flex-wrap:wrap;margin-bottom:7px}
  .chead .nm{font-size:14.5px;font-weight:500}
  .chead .rp{font-size:11.5px;color:var(--ink3);font-family:var(--mono)}
  .chip{font-size:10.5px;padding:2px 8px;border-radius:20px;background:#F1EFE8;color:var(--ink2);white-space:nowrap}
  .chip.star{background:#FAEEDA;color:#854F0B;font-weight:500}
  .chip.lic{background:#EAF3DE;color:#3B6D11}
  .chip.lang{background:#E6F1FB;color:#185FA5}
  .desc{font-size:12.5px;color:var(--ink2);line-height:1.6;margin:0 0 9px}
  .feats{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:11px}
  .feats i{font-style:normal;font-size:11px;background:#FAFAF8;border:1px solid var(--line2);
    border-radius:6px;padding:2px 7px;color:var(--ink2);max-width:100%;overflow:hidden;
    text-overflow:ellipsis;white-space:nowrap}
  .sec{margin-top:11px}
  .sec > .t{font-size:11px;color:var(--ink3);margin-bottom:6px;letter-spacing:.4px}
  .bars{display:flex;flex-direction:column;gap:3px}
  .row{display:grid;grid-template-columns:118px 1fr 76px;align-items:center;gap:8px;font-size:11.5px}
  .row .lb{color:var(--ink2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:var(--mono)}
  .track{height:9px;background:#F1EFE8;border-radius:5px;overflow:hidden}
  .fill{height:100%;border-radius:5px;background:#B5D4F4}
  .fill.g{background:#9FE1CB}
  .row .vl{text-align:right;color:var(--ink3);font-family:var(--mono);font-size:11px}
  .cmd{background:#FAFAF8;border:1px solid var(--line2);border-radius:8px;padding:8px 10px;
    font-family:var(--mono);font-size:11.5px;color:var(--ink2);margin-bottom:5px;
    white-space:pre-wrap;word-break:break-all;position:relative;cursor:pointer}
  .cmd:hover{border-color:#C9C7C0}
  .cmd:active{background:#F1EFE8}
  .cfoot{display:flex;gap:12px;align-items:center;margin-top:11px;padding-top:10px;
    border-top:1px solid var(--line2);font-size:11px;color:var(--ink3);flex-wrap:wrap}
  .cfoot a{text-decoration:none;border-bottom:1px dotted var(--line)}
  .cfoot a:hover{color:var(--ink)}
  .path{font-family:var(--mono);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:100%}
  .empty{padding:60px;text-align:center;color:var(--ink3)}
  .ov{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 15px;margin-bottom:26px}
  .ov h2{font-size:13.5px;font-weight:500;margin:0 0 3px}
  .ov .hint{font-size:11.5px;color:var(--ink3);margin-bottom:11px}
  .ovrows{display:flex;flex-direction:column;gap:3px}
  .ovrow{display:flex;gap:3px;height:52px}
  .ovtile{border-radius:6px;padding:6px 8px;overflow:hidden;cursor:pointer;
    display:flex;flex-direction:column;justify-content:space-between;min-width:0;
    transition:filter .12s}
  .ovtile:hover{filter:brightness(.94)}
  .ovtile .n{font-size:11.5px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .ovtile .v{font-size:10px;opacity:.72;font-family:var(--mono);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .ovlegend{display:flex;gap:16px;margin-top:11px;font-size:11.5px;color:var(--ink3);flex-wrap:wrap}
  .ovlegend i{width:10px;height:10px;border-radius:3px;display:inline-block;margin-right:5px;vertical-align:-1px}
  .toast{position:fixed;left:50%;bottom:28px;transform:translateX(-50%);background:#2C2C2A;color:#fff;
    font-size:12.5px;padding:8px 16px;border-radius:9px;opacity:0;transition:opacity .18s;pointer-events:none;z-index:50}
  .toast.on{opacity:1}
</style>
</head>
<body>
<header>
  <h1>开源项目可视化梳理</h1>
  <div class="sub">具身智能 × AI Agent · 全部数据来自对本地克隆代码的真实扫描（非推测）· 生成于 __DATE__</div>
  <div class="stats" id="stats"></div>
  <div class="bar">
    <div class="seg" id="segDomain"></div>
    <input type="search" id="q" placeholder="搜索项目名 / 仓库 / 描述…">
    <select id="sort">
      <option value="star">按 star 排序</option>
      <option value="loc">按代码行数排序</option>
      <option value="files">按文件数排序</option>
      <option value="name">按名称排序</option>
    </select>
    <span class="sub" id="count"></span>
  </div>
</header>
<main>
  <section class="ov" id="overview"></section>
  <div id="list"></div>
</main>
<div class="toast" id="toast">已复制</div>

<script>
const DATA = __DATA__;
const DOMAINS = __DOMAINS__;

const PAL = {
  embodied:{c:'#0F6E56',bg:'#E1F5EE',soft:'#F2FBF8',label:'具身智能'},
  agent:{c:'#185FA5',bg:'#E6F1FB',soft:'#F3F9FE',label:'AI Agent'},
  cross:{c:'#854F0B',bg:'#FAEEDA',soft:'#FDF8EE',label:'交叉地带'}
};
const esc = s => String(s==null?'':s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = n => (n==null?0:n).toLocaleString('en-US');
const starNum = s => { if(!s) return 0; const m=String(s).match(/([\d.]+)\s*([kKmM]?)/); if(!m) return 0;
  let v=parseFloat(m[1]); const u=m[2].toLowerCase(); if(u==='k') v*=1e3; if(u==='m') v*=1e6; return v; };

let state = {domain:'all', q:'', sort:'star'};

function projectList(){
  return Object.values(DATA).filter(p => p.exists);
}

function renderStats(){
  const ps = projectList();
  const loc = ps.reduce((a,p)=>a+(p.loc||0),0);
  const files = ps.reduce((a,p)=>a+(p.file_count||0),0);
  const withReadme = ps.filter(p=>p.readme && (p.readme.summary||p.readme.features.length)).length;
  const langs = new Set(); ps.forEach(p=>(p.languages||[]).forEach(l=>langs.add(l.name)));
  const html = [
    [ps.length, '个已分析项目'],
    [fmt(loc), '总代码行数'],
    [fmt(files), '总文件数'],
    [langs.size, '种编程语言'],
    [withReadme, '个已提取功能说明']
  ].map(([v,l])=>`<div class="stat"><b>${v}</b><span>${l}</span></div>`).join('');
  document.getElementById('stats').innerHTML = html;
}

function renderSeg(){
  const ps = projectList();
  const counts = {all:ps.length};
  for(const k of Object.keys(DOMAINS)) counts[k] = ps.filter(p=>p.domains.includes(k)).length;
  const items = [['all','全部']].concat(Object.entries(DOMAINS).map(([k,v])=>[k,v.label]));
  document.getElementById('segDomain').innerHTML = items.map(([k,l])=>
    `<button data-d="${k}" class="${state.domain===k?'on':''}">${l} <span style="color:var(--ink3)">${counts[k]||0}</span></button>`).join('');
  document.querySelectorAll('#segDomain button').forEach(b=>{
    b.onclick = ()=>{ state.domain = b.dataset.d; renderSeg(); render(); };
  });
}

function bars(items, colorClass, unit){
  if(!items || !items.length) return '<div class="sub" style="font-size:11.5px">未检测到</div>';
  const max = Math.max(...items.map(i=>i.v)) || 1;
  return '<div class="bars">' + items.map(i =>
    `<div class="row"><span class="lb" title="${esc(i.n)}">${esc(i.n)}</span>
      <span class="track"><span class="fill ${colorClass}" style="width:${Math.max(2,(i.v/max)*100)}%"></span></span>
      <span class="vl">${unit==='loc'?fmt(i.v)+' 行':fmt(i.v)}</span></div>`).join('') + '</div>';
}

function card(p){
  const pal = PAL[p.domains[0]] || PAL.agent;
  const langs = (p.languages||[]).filter(l=>l.loc>0).slice(0,6).map(l=>({n:l.name, v:l.loc}));
  const dirs = (p.top_dirs||[]).slice(0,7).map(d=>({n:d.name+'/', v:d.loc||d.files}));
  const feats = ((p.readme&&p.readme.features)||[]).slice(0,5);
  const cmds = p.run_commands||[];
  const ents = p.entry_points||[];
  const desc = (p.readme && p.readme.summary) || p.description || '';
  const gh = 'https://github.com/' + p.repo;

  return `<div class="card" data-repo="${esc(p.repo)}" style="border-left:3px solid ${pal.c}">
    <div class="chead">
      <span class="nm">${esc(p.name)}</span>
      ${p.star?`<span class="chip star">★ ${esc(p.star)}</span>`:''}
      ${p.license&&p.license!=='无'?`<span class="chip lic">${esc(p.license)}</span>`:''}
      ${p.language?`<span class="chip lang">${esc(p.language)}</span>`:''}
    </div>
    <div class="rp" style="font-size:11.5px;color:var(--ink3);font-family:var(--mono);margin-bottom:8px">${esc(p.repo)}</div>
    ${desc?`<p class="desc">${esc(desc.slice(0,220))}</p>`:''}
    ${feats.length?`<div class="feats">${feats.map(f=>`<i title="${esc(f)}">${esc(f.slice(0,44))}</i>`).join('')}</div>`:''}
    <div class="sec"><div class="t">模块架构（按代码行数）</div>${bars(dirs,'g','loc')}</div>
    <div class="sec"><div class="t">技术栈（按代码行数）</div>${bars(langs,'','loc')}</div>
    ${cmds.length?`<div class="sec"><div class="t">运行流程（点击复制）</div>${
      cmds.slice(0,3).map(c=>`<div class="cmd" data-cmd="${esc(c)}">${esc(c)}</div>`).join('')}</div>`:''}
    ${ents.length?`<div class="sec"><div class="t">识别到的入口</div><div class="feats">${
      ents.slice(0,6).map(e=>`<i>${esc(e.kind)}: ${esc(e.file)}</i>`).join('')}</div></div>`:''}
    <div class="cfoot">
      <span>${fmt(p.file_count)} 文件 · ${fmt(p.loc)} 行${p.deps&&p.deps.count?` · 依赖 ${p.deps.count}`:''}</span>
      <a href="${gh}" target="_blank">GitHub ↗</a>
      <span class="path" title="${esc(p.path)}">${esc(p.path||'')}</span>
    </div>
  </div>`;
}

function render(){
  const q = state.q.trim().toLowerCase();
  let ps = projectList();
  if(state.domain!=='all') ps = ps.filter(p=>p.domains.includes(state.domain));
  if(q) ps = ps.filter(p =>
    (p.name||'').toLowerCase().includes(q) ||
    (p.repo||'').toLowerCase().includes(q) ||
    ((p.description||'')+((p.readme&&p.readme.summary)||'')).toLowerCase().includes(q));

  const cmp = {
    star:(a,b)=>starNum(b.star)-starNum(a.star),
    loc:(a,b)=>(b.loc||0)-(a.loc||0),
    files:(a,b)=>(b.file_count||0)-(a.file_count||0),
    name:(a,b)=>String(a.name).localeCompare(String(b.name),'zh')
  }[state.sort];

  let html = '';
  const domainKeys = state.domain==='all' ? Object.keys(DOMAINS) : [state.domain];
  for(const dk of domainKeys){
    const dp = ps.filter(p=>p.domains.includes(dk));
    if(!dp.length) continue;
    const pal = PAL[dk];
    const loc = dp.reduce((a,p)=>a+(p.loc||0),0);
    html += `<section class="domain">
      <h2><span class="dot" style="background:${pal.c}"></span>${pal.label}</h2>
      <div class="meta">${dp.length} 个项目 · ${fmt(loc)} 行代码</div>`;

    const branchOrder = DOMAINS[dk].branches;
    for(const br of branchOrder){
      const bp = dp.filter(p=>p.branches.includes(br)).sort(cmp);
      if(!bp.length) continue;
      html += `<div class="branch"><h3>${esc(br)} <span style="color:var(--ink3);font-weight:400">· ${bp.length}</span></h3>
        <div class="cards">${bp.map(card).join('')}</div></div>`;
    }
    const rest = dp.filter(p=>!branchOrder.some(b=>p.branches.includes(b))).sort(cmp);
    if(rest.length){
      html += `<div class="branch"><h3>其他 · ${rest.length}</h3><div class="cards">${rest.map(card).join('')}</div></div>`;
    }
    html += '</section>';
  }
  if(!html) html = '<div class="empty">没有匹配的项目</div>';
  document.getElementById('list').innerHTML = html;
  document.getElementById('count').textContent = `显示 ${ps.length} / ${projectList().length} 个项目`;

  document.querySelectorAll('.cmd').forEach(el=>{
    el.onclick = ()=>{
      const t = el.dataset.cmd;
      navigator.clipboard.writeText(t).then(()=>{
        const to = document.getElementById('toast');
        to.textContent = '已复制: ' + t.slice(0,40);
        to.classList.add('on');
        setTimeout(()=>to.classList.remove('on'), 1400);
      }).catch(()=>{});
    };
  });
}

function renderOverview(){
  const ps = projectList().slice().sort((a,b)=>(b.loc||0)-(a.loc||0));
  const total = ps.reduce((a,p)=>a+(p.loc||0),0) || 1;
  const ROWS = 6, target = total / ROWS;
  const rows = [];
  let cur = [], curSum = 0;
  for(const p of ps){
    cur.push(p); curSum += (p.loc||0);
    if(curSum >= target && rows.length < ROWS-1){ rows.push({items:cur, sum:curSum}); cur = []; curSum = 0; }
  }
  if(cur.length) rows.push({items:cur, sum:curSum});

  const body = rows.map(r => '<div class="ovrow">' + r.items.map(p=>{
    const pal = PAL[p.domains[0]] || PAL.agent;
    const w = ((p.loc||1)/r.sum*100).toFixed(2);
    return `<div class="ovtile" style="flex:0 0 ${w}%;background:${pal.bg};color:${pal.c}"
      data-jump="${esc(p.repo)}" title="${esc(p.name)} · ${fmt(p.loc)} 行 · ${esc(p.repo)}">
      <span class="n">${esc(p.name)}</span><span class="v">${fmt(p.loc)} 行</span></div>`;
  }).join('') + '</div>').join('');

  document.getElementById('overview').innerHTML =
    '<h2>项目全景图</h2><div class="hint">矩形面积正比于代码行数 · 颜色区分领域 · 点击定位到下方卡片</div>' +
    '<div class="ovrows">' + body + '</div>' +
    '<div class="ovlegend">' + Object.entries(PAL).map(([k,v])=>
      `<span><i style="background:${v.bg};border:1px solid ${v.c}"></i>${v.label}</span>`).join('') +
    `<span style="margin-left:auto">合计 ${fmt(total)} 行 · ${ps.length} 个项目</span></div>`;

  document.querySelectorAll('.ovtile').forEach(el=>{
    el.onclick = ()=>{
      const t = document.querySelector(`.card[data-repo="${el.dataset.jump}"]`);
      if(t) t.scrollIntoView({behavior:'smooth', block:'center'});
    };
  });
}

document.getElementById('q').addEventListener('input', e=>{ state.q = e.target.value; render(); });
document.getElementById('sort').addEventListener('change', e=>{ state.sort = e.target.value; render(); });

renderStats(); renderSeg(); renderOverview(); render();
</script>
</body>
</html>
"""


def main():
    analysis = json.load(open(ANALYSIS, encoding="utf-8"))
    manifest = json.load(open(MANIFEST, encoding="utf-8"))

    # 精简内嵌数据，只保留看板需要的字段
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

    domains = {}
    for k, v in manifest["domains"].items():
        domains[k] = {"label": v["label"], "branches": [b["label"] for b in v["branches"]]}

    import datetime
    date = datetime.date.today().isoformat()

    out = (TEMPLATE
           .replace("__DATA__", json.dumps(slim, ensure_ascii=False, separators=(",", ":")))
           .replace("__DOMAINS__", json.dumps(domains, ensure_ascii=False, separators=(",", ":")))
           .replace("__DATE__", date))

    open(OUT, "w", encoding="utf-8").write(out)
    exist = sum(1 for a in analysis.values() if a.get("exists"))
    print(f"已分析项目: {exist}/{len(analysis)}")
    print(f"看板已生成: {OUT}  ({len(out)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
