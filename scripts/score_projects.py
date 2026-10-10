"""为 109 个项目计算两套优先级评分：

    任务 A 语义级架构图优先级  -> 值得花人力深读代码、手绘架构图的项目
    任务 B 网页工具改造适用性  -> 适合改造成中文网页工具的命令行项目

用法:
    python scripts/score_projects.py
输出:
    data/priority.json
"""
import json, os, re, math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, os.pardir)
ANALYSIS = os.path.join(ROOT, "data", "analysis.json")
META = os.path.join(ROOT, "data", "repos-meta.json")
OUT = os.path.join(ROOT, "data", "priority.json")
DEST = r"D:\github"

# ---------------------------------------------------------------- 特征探测

WEB_DEPS = {"fastapi", "flask", "django", "streamlit", "gradio", "chainlit",
            "uvicorn", "aiohttp", "tornado", "sanic", "nicegui", "panel",
            "next", "nuxt", "react", "vue", "svelte", "express", "koa", "nest"}
CLI_DEPS = {"click", "typer", "fire", "docopt", "argparse", "rich", "questionary",
            "inquirer", "cmd2", "cliff", "prompt-toolkit"}
HEAVY_DEPS = {"torch", "torchvision", "torchaudio", "tensorflow", "jax", "vllm",
              "deepspeed", "flash-attn", "flash_attn", "transformers", "accelerate",
              "bitsandbytes", "sglang", "xformers", "triton", "cupy", "tensorrt",
              "apex", "megatron", "nemo", "onnxruntime-gpu", "paddlepaddle"}
WEB_DIRS = {"templates", "static", "web", "ui", "frontend", "public", "webui", "www", "assets"}
WEB_FILES = {"index.html", "app.py", "server.py", "webui.py", "main.js", "index.js"}

# 有界源码扫描：找实际 import 的重依赖（比依赖清单更准，因为很多项目把 torch 放 optional extras）
HEAVY_IMPORT = re.compile(
    r"^\s*(?:import|from)\s+(torch|tensorflow|jax|vllm|deepspeed|flash_attn|bitsandbytes"
    r"|triton|cupy|paddle|sglang|xformers|nemo_toolkit|megatron)\b", re.M)
SCAN_EXTS = {".py", ".cu", ".cuh", ".cpp", ".cc"}
SCAN_SKIP = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
             ".next", "target", "site-packages", "tests", "test", "docs", "examples"}

# 不适合做语义架构图的项目：合集型 / 清单型 / 非代码型
NOT_ARCH = {
    "modelcontextprotocol/servers", "e2b-dev/awesome-ai-agents", "GT-RIPL/Awesome-LLM-Robotics",
    "robotics-survey/Awesome-Robotics-Foundation-Models", "zc-xzc/embodied-ai-learning-handbook",
    "TianxingChen/Embodied-AI-Guide", "anthropics/claude-code", "openai/openai-cookbook",
    "Significant-Gravitas/AutoGPT",   # 主体已迁至平台，仓库以文档/配置为主
}

# 不适合做网页工具改造：协议/规范仓、合集仓、纯文档仓
NOT_TOOL = NOT_ARCH | {
    "a2aproject/A2A", "modelcontextprotocol/inspector",
    "Farama-Foundation/Gymnasium", "google-deepmind/mujoco", "bulletphysics/bullet3",
    "google-deepmind/open_x_embodiment", "droid-dataset/droid",
    "princeton-nlp/SWE-bench", "OpenAutoCoder/Agentless",
}
# 语言可读性：越靠前越容易深读
LANG_READ = {"Python": 1.0, "TypeScript": .72, "JavaScript": .70, "Markdown": .6,
             "Go": .60, "Java": .55, "Rust": .42, "C++": .35, "C": .33, "C#": .55,
             "Jupyter": .8, "Shell": .5, "Vue": .6, "HTML": .6}


def read(p, limit=200_000):
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            return f.read(limit)
    except OSError:
        return ""


def scan_heavy_imports(path, limit=150):
    """有界源码扫描：最多读 150 个源文件，找实际 import 的重依赖"""
    hits = set()
    seen = 0
    for dp, dns, fns in os.walk(path):
        dns[:] = [d for d in dns if d not in SCAN_SKIP and not d.startswith(".")]
        for fn in fns:
            e = os.path.splitext(fn)[1].lower()
            if e not in SCAN_EXTS:
                continue
            seen += 1
            if seen > limit:
                return sorted(hits)
            fp = os.path.join(dp, fn)
            try:
                if os.path.getsize(fp) > 300_000:
                    continue
                with open(fp, encoding="utf-8", errors="ignore") as f:
                    head = f.read(60_000)
            except OSError:
                continue
            for m in HEAVY_IMPORT.finditer(head):
                hits.add(m.group(1))
            if len(hits) >= 4:
                return sorted(hits)
    return sorted(hits)


def probe(repo, info, a):
    """针对性探测 CLI / Web / 依赖特征（只读少量配置文件，很快）"""
    path = os.path.join(DEST, (info.get("domains") or ["agent"])[0], repo.split("/")[-1])
    sig = {
        "cli_entry": False, "cli_names": [], "has_bin": False,
        "web_framework": [], "web_dirs": [], "web_files": [],
        "heavy_deps": [], "heavy_imports": [], "dep_count": 0, "dep_keys": [],
        "has_docs": False, "has_examples": False, "has_docker": False,
        "has_makefile": False, "license_ok": None,
    }
    if not os.path.isdir(path):
        return sig

    deps = set()
    # --- pyproject.toml ---
    pj = os.path.join(path, "pyproject.toml")
    if os.path.isfile(pj):
        txt = read(pj)
        m = re.search(r"\[(?:project|tool\.poetry)\.scripts\](.*?)(\n\[|\Z)", txt, re.S)
        if m:
            names = re.findall(r"^\s*([\w.-]+)\s*=", m.group(1), re.M)
            if names:
                sig["cli_entry"] = True
                sig["cli_names"] += names[:5]
        for sec in ("dependencies", "optional-dependencies"):
            for mm in re.finditer(rf"{sec}\s*\]\s*=\s*\[(.*?)\]", txt, re.S):
                deps |= {x.lower().strip(' "') for x in re.findall(r'"([^"]+)"', mm.group(1))}
        deps |= {x.lower() for x in re.findall(r'^\s*([\w.-]+)\s*=\s*"', txt, re.M) if x[0].isalpha()}
    # --- requirements.txt ---
    for f in ("requirements.txt", "requirements-dev.txt"):
        rq = os.path.join(path, f)
        if os.path.isfile(rq):
            for line in read(rq).split("\n"):
                line = line.split("#")[0].strip()
                if line:
                    deps.add(re.split(r"[<>=!\[;]", line)[0].strip().lower())
    # --- package.json ---
    pkg = os.path.join(path, "package.json")
    if os.path.isfile(pkg):
        try:
            d = json.loads(read(pkg))
            if d.get("bin"):
                sig["has_bin"] = True
                sig["cli_entry"] = True
                sig["cli_names"] += list(d["bin"])[:5] if isinstance(d["bin"], dict) else [str(d["bin"])]
            deps |= {k.lower() for k in (d.get("dependencies") or {})}
            deps |= {k.lower() for k in (d.get("devDependencies") or {})}
        except Exception:
            pass
    # --- setup.py entry_points ---
    sp = os.path.join(path, "setup.py")
    if os.path.isfile(sp) and "entry_points" in read(sp):
        sig["cli_entry"] = True

    sig["dep_count"] = len(deps)
    sig["dep_keys"] = sorted(deps)[:12]

    base = {re.split(r"[-_]", d)[0] for d in deps}
    sig["web_framework"] = sorted(deps & WEB_DEPS)
    sig["heavy_deps"] = sorted(deps & HEAVY_DEPS)
    if deps & CLI_DEPS:
        sig["cli_entry"] = True
        sig["cli_names"] += sorted(deps & CLI_DEPS)[:3]

    # --- 目录 / 文件特征 ---
    try:
        top = set(os.listdir(path))
    except OSError:
        top = set()
    sig["web_dirs"] = sorted(top & WEB_DIRS)
    sig["web_files"] = sorted(top & WEB_FILES)
    sig["has_docs"] = ("docs" in top) or ("doc" in top)
    sig["has_examples"] = bool({"examples", "example", "demo", "demos", "notebooks", "tutorials"} & top)
    sig["has_docker"] = bool({"Dockerfile", "docker-compose.yml", "docker-compose.yaml"} & top)
    sig["has_makefile"] = "Makefile" in top
    sig["heavy_imports"] = scan_heavy_imports(path)

    lic = (a.get("license") or "").upper()
    if lic in ("MIT", "APACHE-2.0", "BSD-3-CLAUSE", "BSD-2-CLAUSE", "ISC", "MPL-2.0"):
        sig["license_ok"] = 1.0
    elif lic == "AGPL-3.0":
        sig["license_ok"] = 0.35       # 传染性，改造成衍生作品需开源
    elif lic in ("GPL-3.0", "GPL-2.0", "LGPL-3.0"):
        sig["license_ok"] = 0.5
    elif lic in ("", "无", "NOASSERTION"):
        sig["license_ok"] = 0.15       # 未授权，公开分发有风险
    else:
        sig["license_ok"] = 0.7
    return sig


# ---------------------------------------------------------------- 评分

# 融合学习路线核心项目（来自交叉地带 C3 分支）
CORE_PATH = {
    "Farama-Foundation/Gymnasium", "google-deepmind/mujoco", "isaac-sim/IsaacLab",
    "huggingface/lerobot", "real-stanford/diffusion_policy",
    "openvla/openvla", "Physical-Intelligence/openpi",
    "langchain-ai/langgraph", "modelcontextprotocol/servers",
}


def star_num(s):
    if not s:
        return 0
    m = re.match(r"([\d.]+)\s*([kKmM]?)", str(s))
    if not m:
        return 0
    v = float(m.group(1))
    u = m.group(2).lower()
    return v * (1e3 if u == "k" else 1e6 if u == "m" else 1)


def score_arch(repo, info, a, sig, branch_rank):
    """任务 A：语义级架构图优先级"""
    det = {}
    # 1) 主线核心度 30
    s = 0
    if repo in CORE_PATH:
        s += 20
    if len(info.get("branches", [])) > 1:
        s += 6            # 跨分支复用 = 价值更高
    if branch_rank == 1:
        s += 6            # 该分支 star 第一
    elif branch_rank == 2:
        s += 3
    det["主线核心度"] = min(30, s)

    # 2) 社区热度 20（对数刻度，1k=8分, 10k=14分, 100k=20分）
    st = star_num(a.get("star"))
    det["社区热度"] = min(20, round(8 * math.log10(max(st, 10)) / 3, 1)) if st else 0

    # 3) 代码可读性 20：语言 + 规模适中
    lang = a.get("language") or ""
    lr = LANG_READ.get(lang, .5)
    loc = a.get("loc") or 0
    if 20_000 <= loc <= 400_000:
        size = 1.0
    elif loc < 20_000:
        size = max(.35, loc / 20_000)
    elif loc <= 1_000_000:
        size = 0.75
    else:
        size = 0.45
    det["代码可读性"] = round(20 * lr * size, 1)

    # 4) 资料完整度 15：README 要点 + docs + examples
    feats = len((a.get("readme") or {}).get("features") or [])
    d = min(6, feats * 1.2)
    d += 5 if sig["has_docs"] else 0
    d += 4 if sig["has_examples"] else 0
    det["资料完整度"] = round(min(15, d), 1)

    # 5) 架构清晰度 15：模块分层明显、非巨型 monorepo
    nd = len(a.get("top_dirs") or [])
    if 3 <= nd <= 10:
        mod = 9
    elif nd in (2, 11, 12):
        mod = 6
    else:
        mod = 3
    files = a.get("file_count") or 0
    conc = 6 if files <= 3000 else (3 if files <= 8000 else 1)
    det["架构清晰度"] = min(15, mod + conc)

    total = sum(det.values())
    if repo in NOT_ARCH:
        # 合集型 / 清单型 / 文档型项目没有可画的系统架构，大幅降权
        total *= 0.35
        det["合集型降权"] = round(total - sum(det.values()), 1)
    return round(total, 1), det


def score_tool(repo, info, a, sig):
    """任务 B：改造成中文网页工具的适用性（满分 100）

    评分逻辑上「有没有命令行入口」是一道硬门槛：没有 CLI 的项目本质不是
    「命令行项目」，靠其他维度拿高分会产生误导，故整体降权。
    """
    det = {}
    # 1) CLI 可包装性 22
    s = 0
    if sig["cli_entry"]:
        s += 13
    if sig["cli_names"]:
        s += 6
    if sig["has_bin"]:
        s += 3
    det["CLI 可包装"] = min(22, s)

    # 2) 改造空间 10 —— 已有 Web UI 的话改造价值低
    has_web = bool(sig["web_framework"] or sig["web_dirs"] or sig["web_files"])
    det["改造空间"] = 0 if has_web else 10

    # 3) 依赖轻量 18 —— 探测不到依赖清单时给中位分，不能默认「轻量」
    dc = sig["dep_count"]
    if dc == 0:
        s = 9
    else:
        s = 18 if dc <= 25 else (13 if dc <= 60 else (8 if dc <= 120 else 3))
    det["依赖轻量"] = s

    # 4) 算力门槛 20 —— 包装后仍要 GPU 才能用，网页化价值大打折扣（最大扣分项）
    heavy = set(sig["heavy_deps"]) | set(sig["heavy_imports"])
    if not heavy:
        s = 20
    elif heavy <= {"transformers"}:
        s = 14          # 只需跑小模型，CPU 可用
    elif heavy <= {"torch", "transformers", "accelerate", "bitsandbytes"}:
        s = 7           # 推理可 CPU，训练需 GPU
    else:
        s = 0           # 强 GPU 依赖（vllm / flash_attn / deepspeed 等）
    det["算力门槛"] = s

    # 5) 功能单一 15 —— 规模适中、单一入口，最好包装
    loc = a.get("loc") or 0
    if 5_000 <= loc <= 150_000:
        s = 15
    elif loc < 5_000:
        s = max(4, loc / 5_000 * 15)
    elif loc <= 400_000:
        s = 10
    else:
        s = 4
    det["功能单一"] = round(s, 1)

    # 6) 许可证 10
    det["许可证"] = round(10 * (sig["license_ok"] or 0), 1)

    # 7) 活跃度 5
    pa = a.get("pushed_at") or ""
    det["活跃度"] = 5 if pa >= "2026-06" else (3 if pa >= "2026-01" else 1)

    total = sum(det.values())
    if not sig["cli_entry"]:
        total *= 0.45            # 硬门槛：不是命令行项目
        det["无CLI降权"] = round(total - sum(det.values()), 1)
    if repo in NOT_TOOL:
        total *= 0.3             # 规范仓 / 合集仓 / 基准仓
        det["非工具型降权"] = round(total - sum(det.values()), 1)
    return round(total, 1), det


def main():
    analysis = json.load(open(ANALYSIS, encoding="utf-8"))
    meta = json.load(open(META, encoding="utf-8"))
    manifest = json.load(open(os.path.join(ROOT, "data", "manifest.json"), encoding="utf-8"))

    # 计算每个项目在其主分支内的 star 排名
    branch_rank = {}
    for dk, dv in manifest["domains"].items():
        for br in dv["branches"]:
            items = [i for i in br["items"] if i.get("repo")]
            items.sort(key=lambda x: -star_num(x.get("star")))
            for idx, it in enumerate(items, 1):
                r = it["repo"]
                branch_rank[r] = min(branch_rank.get(r, 99), idx)

    out = {}
    for repo, info in sorted(manifest["repos"].items()):
        a = analysis.get(repo, {})
        if not a.get("exists"):
            continue
        sig = probe(repo, info, a)
        sa, da = score_arch(repo, info, a, sig, branch_rank.get(repo, 99))
        sb, db = score_tool(repo, info, a, sig)
        out[repo] = {
            "repo": repo, "name": a.get("name"), "star": a.get("star"),
            "domains": info["domains"], "branches": info["branches"],
            "loc": a.get("loc"), "file_count": a.get("file_count"),
            "language": a.get("language"), "license": a.get("license"),
            "arch_score": sa, "arch_detail": da,
            "tool_score": sb, "tool_detail": db,
            "signals": {k: v for k, v in sig.items() if v not in (False, [], 0, None, "")},
        }

    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    def show(key, title, n=15):
        print(f"\n{'='*94}\n{title}\n{'='*94}")
        print(f"{'排名':<5}{'项目':<26}{'分':>6}  {'star':>7}{'语言':>12}  {'代码行数':>12}  主要维度")
        for i, v in enumerate(sorted(out.values(), key=lambda x: -x[key])[:n], 1):
            d = v[key.replace("_score", "_detail")]
            top = sorted(d.items(), key=lambda x: -x[1])[:2]
            tops = " ".join(f"{k}{val}" for k, val in top)
            print(f"{i:<5}{v['name'][:24]:<26}{v[key]:>6}  {str(v['star']):>7}{str(v['language']):>12}  {v['loc']:>12,}  {tops}")

    show("arch_score", "任务 A · 语义级架构图优先级 Top 15")
    show("tool_score", "任务 B · 网页工具改造适用性 Top 15")

    print(f"\n{'='*94}\n全部 {len(out)} 个项目已评分 -> {OUT}")


if __name__ == "__main__":
    main()
