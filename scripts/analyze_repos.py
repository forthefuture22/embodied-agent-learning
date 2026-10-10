"""对 D:\\github 下已克隆的仓库做结构化分析，产出 data/analysis.json。

分析维度（全部来自真实文件系统，非推测）:
    功能全景   README 标题/摘要/特性要点 + GitHub topics
    模块架构   顶层与二级目录的文件数、代码行数
    技术栈     按扩展名的文件数与 LOC 分布
    运行入口   依赖清单 / 入口文件 / Dockerfile / Makefile / npm scripts
    规模指标   文件数、总 LOC、磁盘占用
"""
import json, os, re, sys, argparse
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, os.pardir)
MANIFEST = os.path.join(ROOT, "data", "manifest.json")
META = os.path.join(ROOT, "data", "repos-meta.json")
OUT = os.path.join(ROOT, "data", "analysis.json")

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env", ".env",
    "dist", "build", ".next", "target", "out", ".cache", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "site-packages", ".tox", "coverage",
    ".idea", ".vscode", "vendor", "third_party", ".gradle", ".terraform",
}
CODE_EXT = {
    "py": "Python", "js": "JavaScript", "ts": "TypeScript", "tsx": "TypeScript",
    "jsx": "JavaScript", "java": "Java", "go": "Go", "rs": "Rust", "c": "C",
    "cpp": "C++", "cc": "C++", "h": "C/C++ Header", "hpp": "C/C++ Header",
    "cs": "C#", "rb": "Ruby", "php": "PHP", "swift": "Swift", "kt": "Kotlin",
    "scala": "Scala", "m": "Objective-C", "jl": "Julia", "lua": "Lua",
    "sh": "Shell", "bash": "Shell", "ps1": "PowerShell", "sql": "SQL",
    "html": "HTML", "css": "CSS", "scss": "SCSS", "vue": "Vue", "svelte": "Svelte",
    "ipynb": "Jupyter", "proto": "Protobuf", "yaml": "YAML", "yml": "YAML",
    "toml": "TOML", "json": "JSON", "md": "Markdown", "rst": "reStructuredText",
    "urdf": "URDF", "xml": "XML",
}
TEXT_EXT = set(CODE_EXT) | {"txt", "cfg", "ini", "env", "dockerfile", "makefile", "cmake"}


def read_text(p, limit=400_000):
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            return f.read(limit)
    except OSError:
        return ""


def count_lines(p):
    n = 0
    try:
        with open(p, "rb") as f:
            while True:
                chunk = f.read(1 << 20)
                if not chunk:
                    break
                n += chunk.count(b"\n")
    except OSError:
        return 0
    return n + 1


def ext_of(name):
    if name.lower().startswith("dockerfile"):
        return "dockerfile"
    if name.lower() in ("makefile", "gnumakefile"):
        return "makefile"
    _, e = os.path.splitext(name)
    return e.lstrip(".").lower()


def walk_repo(path):
    """返回 文件数、LOC、按扩展名统计、一级/二级目录统计"""
    total_files = 0
    total_loc = 0
    by_ext = defaultdict(lambda: {"files": 0, "loc": 0})
    dir_stats = defaultdict(lambda: {"files": 0, "loc": 0, "name": ""})
    lvl2_stats = defaultdict(lambda: {"files": 0, "loc": 0})

    for dp, dns, fns in os.walk(path):
        dns[:] = [d for d in dns if d not in SKIP_DIRS and not d.startswith(".")]
        rel = os.path.relpath(dp, path)
        parts = [] if rel == "." else rel.replace("\\", "/").split("/")
        # 深度上限放宽到 12 层，避免 monorepo（如 langchain 的 libs/xxx/xxx/）被截断
        if len(parts) > 12:
            dns[:] = []
            continue
        for fn in fns:
            fp = os.path.join(dp, fn)
            if os.path.islink(fp):
                continue
            try:
                if os.path.getsize(fp) > 8_000_000:
                    continue
            except OSError:
                continue
            total_files += 1
            e = ext_of(fn)
            by_ext[e]["files"] += 1
            if e in TEXT_EXT:
                n = count_lines(fp)
                total_loc += n
                by_ext[e]["loc"] += n
            else:
                n = 0
            if parts:
                d1 = parts[0]
                dir_stats[d1]["files"] += 1
                dir_stats[d1]["loc"] += n
                dir_stats[d1]["name"] = d1
                if len(parts) >= 2:
                    k = d1 + "/" + parts[1]
                    lvl2_stats[k]["files"] += 1
                    lvl2_stats[k]["loc"] += n
    return total_files, total_loc, by_ext, dir_stats, lvl2_stats


def parse_readme(path):
    for fn in ("README.md", "readme.md", "README.rst", "README.MD", "README.txt", "README"):
        fp = os.path.join(path, fn)
        if os.path.isfile(fp):
            txt = read_text(fp, 200_000)
            break
    else:
        return {"title": "", "summary": "", "features": []}

    lines = txt.split("\n")
    title = ""
    for ln in lines[:40]:
        s = ln.strip()
        if s.startswith("# "):
            title = s[2:].strip()
            break
    if not title:
        for ln in lines[:10]:
            if ln.strip():
                title = ln.strip().lstrip("#").strip()
                break

    # 摘要：跳过徽章、图片、空行后第一段普通文本
    summary = ""
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("#") or s.startswith("[!") or s.startswith("![") or s.startswith("<"):
            continue
        if s.startswith("|") or s.startswith(">"):
            continue
        if len(s) < 25:
            continue
        summary = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
        summary = re.sub(r"[*`]", "", summary).strip()
        break

    # 特性要点：README 前 250 行中的短横线/数字列表
    features = []
    for ln in lines[:250]:
        s = ln.strip()
        m = re.match(r"^[-*+]\s+(.{8,120})$", s)
        if m:
            t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", m.group(1))
            t = re.sub(r"[*`]", "", t).strip()
            if t and not t.startswith("!"):
                features.append(t)
        if len(features) >= 8:
            break
    return {"title": title, "summary": summary, "features": features}


def detect_runtime(path, by_ext, lvl2):
    entries = []
    cmds = []
    deps = {"count": 0, "key": []}

    pj = os.path.join(path, "package.json")
    if os.path.isfile(pj):
        try:
            d = json.loads(read_text(pj))
            entries.append({"kind": "Node 包", "file": "package.json"})
            sc = d.get("scripts") or {}
            for k, v in list(sc.items())[:5]:
                cmds.append(f"npm run {k}    # {v[:60]}")
            deps["count"] += len(d.get("dependencies") or {}) + len(d.get("devDependencies") or {})
            deps["key"] += list((d.get("dependencies") or {}).keys())[:8]
        except Exception:
            pass

    for f in ("pyproject.toml", "setup.py", "requirements.txt", "setup.cfg"):
        if os.path.isfile(os.path.join(path, f)):
            entries.append({"kind": "Python 包", "file": f})
            if f == "requirements.txt":
                txt = read_text(os.path.join(path, f))
                pkgs = [l.split("==")[0].split(">=")[0].strip() for l in txt.split("\n")
                        if l.strip() and not l.strip().startswith("#")]
                deps["count"] += len(pkgs)
                deps["key"] += pkgs[:8]
    if os.path.isfile(os.path.join(path, "pyproject.toml")):
        txt = read_text(os.path.join(path, "pyproject.toml"), 120_000)
        m = re.search(r"\[project\.scripts\](.*?)(\n\[|\Z)", txt, re.S)
        if m:
            for ln in m.group(1).strip().split("\n")[:5]:
                if "=" in ln:
                    cmds.append(ln.strip().replace("=", " -> ", 1))
        if not cmds and os.path.isfile(os.path.join(path, "setup.py")):
            cmds.append("pip install -e .")

    for f in ("Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        if os.path.isfile(os.path.join(path, f)):
            entries.append({"kind": "容器化", "file": f})

    if os.path.isfile(os.path.join(path, "Makefile")):
        txt = read_text(os.path.join(path, "Makefile"), 60_000)
        targets = re.findall(r"^([a-zA-Z][\w.-]*):(?!=)", txt, re.M)
        targets = [t for t in targets if t not in ("PHONY",)][:4]
        entries.append({"kind": "Makefile", "file": "Makefile", "targets": targets})
        cmds += [f"make {t}" for t in targets[:3]]

    for d in ("examples", "scripts", "tools", "demo", "demos"):
        if os.path.isdir(os.path.join(path, d)):
            entries.append({"kind": "示例/脚本目录", "file": d + "/"})

    for f in ("main.py", "__main__.py", "app.py", "cli.py", "server.py", "run.py"):
        if os.path.isfile(os.path.join(path, f)):
            entries.append({"kind": "入口文件", "file": f})
            cmds.append(f"python {f}")

    if not cmds:
        if "py" in by_ext:
            cmds.append("python -m <模块名>    # 或查看 README 的 Usage 章节")
        if "ts" in by_ext or "js" in by_ext:
            cmds.append("npm install && npm run dev")

    return entries, cmds[:6], deps


DEST = r"D:\github"


def repo_path(repo, info):
    """与 clone_all.py 保持一致的落盘规则: D:\\github\\<domain>\\<repo-name>"""
    if info.get("path"):
        return info["path"]
    domain = (info.get("domains") or ["agent"])[0]
    return os.path.join(DEST, domain, repo.split("/")[-1])


def analyze(repo, info, meta):
    path = repo_path(repo, info)
    base = {
        "repo": repo, "name": info["name"], "star": info["star"],
        "domains": info["domains"], "branches": info["branches"],
        "path": path,
    }
    md = meta.get(repo, {})
    base.update({
        "license": md.get("license"), "language": md.get("language"),
        "pushed_at": md.get("pushed_at"), "description": md.get("description"),
        "topics": md.get("topics", []), "gh_size_mb": md.get("size_mb"),
    })

    if not path or not os.path.isdir(path):
        base["exists"] = False
        return base

    base["exists"] = True
    files, loc, by_ext, d1, lvl2 = walk_repo(path)
    base["file_count"] = files
    base["loc"] = loc
    base["languages"] = sorted(
        [{"ext": k, "name": CODE_EXT.get(k, k.upper() or k), "files": v["files"], "loc": v["loc"]}
         for k, v in by_ext.items() if v["loc"] > 0 or k in CODE_EXT],
        key=lambda x: -x["loc"])[:12]
    base["top_dirs"] = sorted(
        [{"name": k, "files": v["files"], "loc": v["loc"]} for k, v in d1.items()],
        key=lambda x: -(x["loc"] or x["files"]))[:14]
    base["sub_modules"] = sorted(
        [{"name": k, "files": v["files"], "loc": v["loc"]} for k, v in lvl2.items()],
        key=lambda x: -(x["loc"] or x["files"]))[:12]
    base["readme"] = parse_readme(path)
    ent, cmds, deps = detect_runtime(path, by_ext, lvl2)
    base["entry_points"] = ent
    base["run_commands"] = cmds
    base["deps"] = deps
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="忽略已有结果，全部重算")
    ap.add_argument("--flush-every", type=int, default=5, help="每分析 N 个落盘一次")
    args = ap.parse_args()

    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    meta = json.load(open(META, encoding="utf-8")) if os.path.isfile(META) else {}

    # 断点续跑：读取已有结果
    out = {}
    if os.path.isfile(OUT) and not args.force:
        try:
            out = json.load(open(OUT, encoding="utf-8"))
        except Exception:
            out = {}

    repos = sorted(manifest["repos"].items())
    ok = miss = skip = 0
    pending = 0
    for i, (repo, info) in enumerate(repos, 1):
        prev = out.get(repo)
        if prev and prev.get("exists") and not args.force:
            ok += 1
            skip += 1
            continue

        a = analyze(repo, info, meta)
        out[repo] = a
        pending += 1
        if a["exists"]:
            ok += 1
            print(f"[{i:>3}/{len(repos)}] OK   {repo:<50} {a['file_count']:>7} 文件 "
                  f"{a['loc']:>10,} 行", flush=True)
        else:
            miss += 1
            print(f"[{i:>3}/{len(repos)}] MISS {repo:<50} 尚未克隆", flush=True)

        if pending >= args.flush_every:
            json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            pending = 0

    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n已分析 {ok} 个（本次新算 {len(repos)-skip}，跳过已缓存 {skip}），"
          f"{miss} 个尚未克隆 -> {OUT}")


if __name__ == "__main__":
    main()
