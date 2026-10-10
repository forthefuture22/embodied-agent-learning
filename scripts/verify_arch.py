"""校验 data/arch/*.json 的语义架构分析质量，重点抓「路径幻觉」。

子 agent 最容易出的问题不是格式错误，而是**编造出看起来很合理、但仓库里并不存在的文件路径**。
本脚本对每份分析做四类检查：

    A 结构完整性   15 个必填字段齐全、类型正确、数量在合理区间
    B 路径真实性   所有 file/path 必须能在本地克隆的仓库中找到（核心防线）
    C 图表合法性   Mermaid 以 graph 开头、标签内无圆括号、节点数合理
    D 内容质量     关键字段非空、无占位符残留、置信度取值合法

用法:
    python scripts/verify_arch.py                 # 校验全部
    python scripts/verify_arch.py --strict        # 有任一错误即退出码 1
    python scripts/verify_arch.py --report out.json
"""
import json, os, re, sys, argparse, glob
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, os.pardir)
ARCH_DIR = os.path.join(ROOT, "data", "arch")
ANALYSIS = os.path.join(ROOT, "data", "analysis.json")
DEST = r"D:\github"

REQUIRED = ["repo", "name", "one_liner", "problem", "difficulty", "core_abstractions",
            "layers", "data_flow", "entry_points", "key_files", "extension_points",
            "learning_path", "diagram_mermaid", "surprises", "confidence"]

RANGES = {                       # 字段 -> (最少, 最多)
    "core_abstractions": (4, 14),
    "layers": (3, 12),
    "data_flow": (5, 14),
    "key_files": (4, 12),
    "entry_points": (1, 12),
    "learning_path": (2, 10),
    "extension_points": (1, 10),
    "surprises": (1, 8),
}
VALID_DIFFICULTY = {"入门", "中等", "困难"}
VALID_CONFIDENCE = {"高", "中", "低"}
PLACEHOLDER = re.compile(r"(未确认|待补充|TODO|TBD|xxx|\.\.\.$|^无$|^—$|^N/A$)", re.I)


CODE_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".toml", ".yaml", ".yml", ".json",
            ".cfg", ".txt", ".sh", ".rs", ".go", ".java", ".cpp", ".cc", ".h", ".hpp", ".cu",
            ".cuh", ".proto", ".ini", ".xml", ".html", ".css", ".rst", ".sql", ".vue", ".ipynb"}


def classify(raw):
    """把 agent 写的「路径」分成三类：

        ('path', 相对路径)   需要校验真实性
        ('symbol', None)     Python 符号 / 模块路径（如 gymnasium.make）
        ('command', None)    CLI 命令名（如 lerobot-train）
    """
    if not isinstance(raw, str):
        return "symbol", None
    s = raw.strip().strip("`'\"")
    if not s:
        return "symbol", None

    s = re.sub(r"^[a-zA-Z]:\\", "", s)             # 盘符
    s = s.replace("\\", "/")
    s = re.sub(r"\s*[（(].*?[)）]\s*$", "", s)      # 尾部中文括注
    # 剥掉「路径:符号」或「路径:行号」后缀（:Team.run / :123 / ::method）
    s = re.sub(r"[#:]{1,2}(?:\d+(-\d+)?|[A-Za-z_][\w.]*)$", "", s)
    s = re.sub(r"^\./", "", s).strip().strip("`'\"").rstrip("/")
    if not s:
        return "symbol", None

    has_slash = "/" in s
    ext = os.path.splitext(s)[1].lower()

    # 无斜杠：要么是顶层文件，要么是命令/符号
    if not has_slash:
        if ext in CODE_EXT:
            return "path", s                      # README.md / setup.py
        return "command", None                    # lerobot-train / gs / isaaclab

    # 有斜杠：可能是文件，也可能是目录，都交给 exists() 判定
    if " " in s:                                  # 含空格 => 命令行，不是路径
        return "command", None
    return "path", s


def norm_path(p):
    kind, val = classify(p)
    return val if kind == "path" else None


class Checker:
    def __init__(self, repo_root):
        self.root = repo_root
        self._index = None

    def index(self):
        """建立 basename -> 相对路径 的索引，用于区分「路径写错」和「文件不存在」"""
        if self._index is not None:
            return self._index
        idx = defaultdict(list)
        if self.root and os.path.isdir(self.root):
            skip = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".next"}
            for dp, dns, fns in os.walk(self.root):
                dns[:] = [d for d in dns if d not in skip and not d.startswith(".")]
                rel = os.path.relpath(dp, self.root).replace("\\", "/")
                if rel == ".":
                    rel = ""
                if len(rel.split("/")) > 6:
                    dns[:] = []
                    continue
                for fn in fns:
                    idx[fn].append((rel + "/" + fn).lstrip("/"))
        self._index = idx
        return idx

    def exists(self, rel):
        if not rel:
            return False, "empty"
        p = os.path.join(self.root, rel.replace("/", os.sep))
        if os.path.isfile(p) or os.path.isdir(p):
            return True, "exact"
        # 大小写不敏感重试（Windows 仓库里偶尔大小写不一致）
        parent = os.path.dirname(p)
        if os.path.isdir(parent):
            base = os.path.basename(p).lower()
            for f in os.listdir(parent):
                if f.lower() == base:
                    return True, "case"
        return False, "missing"

    def suggest(self, rel):
        """给一个可能的正确路径，用于定位幻觉"""
        base = os.path.basename(rel or "")
        if not base:
            return None
        hits = self.index().get(base, [])
        if len(hits) == 1:
            return hits[0]
        if hits:
            return hits[0] + f"  (共 {len(hits)} 处同名文件)"
        # 退一步：按去掉扩展名的名字找
        stem = os.path.splitext(base)[0]
        if stem:
            for fn, paths in self.index().items():
                if os.path.splitext(fn)[0] == stem:
                    return paths[0]
        return None


def check_mermaid(src):
    issues = []
    if not isinstance(src, str) or not src.strip():
        return ["diagram_mermaid 为空"]
    s = src.strip()
    if not re.match(r"^(graph|flowchart)\s", s):
        issues.append("diagram_mermaid 未以 graph/flowchart 开头")
    # 标签内的圆括号会破坏 Mermaid 解析
    labels = re.findall(r"\[([^\]]*)\]", s)
    for lb in labels:
        if "(" in lb or ")" in lb:
            issues.append(f"Mermaid 标签含圆括号: [{lb[:30]}]")
            break
    if re.search(r"[\u4e00-\u9fff]", s) is None:
        issues.append("Mermaid 图无中文标签")
    nodes = len(set(re.findall(r"([A-Za-z_][\w]*)\s*[\[\{]", s)))
    if nodes < 5:
        issues.append(f"Mermaid 节点过少（{nodes}）")
    if nodes > 40:
        issues.append(f"Mermaid 节点过多（{nodes}）")
    return issues


def check_file(fpath, analysis):
    """返回 (errors, warnings, stats)"""
    errors, warnings = [], []
    fname = os.path.basename(fpath)
    try:
        d = json.load(open(fpath, encoding="utf-8"))
    except Exception as e:
        return [f"JSON 解析失败: {e}"], [], {}

    repo = d.get("repo")
    if not repo:
        return ["缺少 repo 字段"], [], {}

    # --- A 结构完整性 ---
    for k in REQUIRED:
        if k not in d:
            errors.append(f"缺字段 {k}")
        elif d[k] in (None, "", [], {}):
            errors.append(f"字段 {k} 为空")
    for k, (lo, hi) in RANGES.items():
        v = d.get(k)
        if isinstance(v, list):
            if len(v) < lo:
                warnings.append(f"{k} 数量偏少（{len(v)} < {lo}）")
            if len(v) > hi:
                warnings.append(f"{k} 数量偏多（{len(v)} > {hi}）")
    if d.get("difficulty") not in VALID_DIFFICULTY:
        warnings.append(f"difficulty 取值异常: {d.get('difficulty')}")
    if d.get("confidence") not in VALID_CONFIDENCE:
        warnings.append(f"confidence 取值异常: {d.get('confidence')}")

    # --- 本地仓库定位 ---
    a = analysis.get(repo, {})
    repo_root = a.get("path")
    if not repo_root or not os.path.isdir(repo_root):
        dom = (a.get("domains") or ["agent"])[0]
        repo_root = os.path.join(DEST, dom, repo.split("/")[-1])
    if not os.path.isdir(repo_root):
        warnings.append(f"本地仓库不存在，跳过路径校验: {repo_root}")
        repo_root = None

    ck = Checker(repo_root) if repo_root else None

    # --- B 路径真实性（核心）---
    path_fields = []
    for c in d.get("core_abstractions") or []:
        if isinstance(c, dict):
            path_fields.append(("core_abstractions.file", c.get("file")))
    for l in d.get("layers") or []:
        if isinstance(l, dict):
            for f in (l.get("files") or []):
                path_fields.append(("layers.files", f))
    for kf in d.get("key_files") or []:
        if isinstance(kf, dict):
            path_fields.append(("key_files.path", kf.get("path")))
    for ep in d.get("entry_points") or []:
        if isinstance(ep, dict):
            path_fields.append(("entry_points.path", ep.get("path")))

    checked = 0
    bad_paths = []
    skipped = {"symbol": 0, "command": 0}
    for field, raw in path_fields:
        if not raw:
            continue
        kind, rel = classify(raw)
        if kind != "path":
            skipped[kind] += 1
            continue
        checked += 1
        ok, how = ck.exists(rel)
        if not ok:
            sug = ck.suggest(rel)
            bad_paths.append({"field": field, "path": rel, "suggest": sug})

    if checked:
        rate = (checked - len(bad_paths)) / checked
        if bad_paths:
            msg = f"路径真实性 {checked-len(bad_paths)}/{checked}（{rate:.0%}）"
            if rate < 0.85:
                errors.append(msg + f"，疑似幻觉 {len(bad_paths)} 条")
            else:
                warnings.append(msg + f"，存疑 {len(bad_paths)} 条")
    else:
        rate = None
        warnings.append("未找到可校验的文件路径")

    # --- C 图表 ---
    errors += check_mermaid(d.get("diagram_mermaid"))

    # --- D 内容质量 ---
    for k in ("one_liner", "problem"):
        v = d.get(k)
        if isinstance(v, str):
            if PLACEHOLDER.search(v):
                warnings.append(f"{k} 含占位符: {v[:40]}")
            if len(v) < 8:
                warnings.append(f"{k} 过短: {v}")

    stats = {
        "file": fname, "repo": repo, "confidence": d.get("confidence"),
        "abstractions": len(d.get("core_abstractions") or []),
        "layers": len(d.get("layers") or []),
        "flow": len(d.get("data_flow") or []),
        "key_files": len(d.get("key_files") or []),
        "paths_checked": checked, "paths_bad": len(bad_paths),
        "path_rate": rate, "bad_paths": bad_paths, "skipped": skipped,
    }
    return errors, warnings, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="有错误则退出码 1")
    ap.add_argument("--report", help="把明细写入 JSON")
    ap.add_argument("--verbose", action="store_true", help="打印存疑路径")
    args = ap.parse_args()

    analysis = json.load(open(ANALYSIS, encoding="utf-8"))
    files = sorted(glob.glob(os.path.join(ARCH_DIR, "*.json")))
    if not files:
        print("data/arch/ 下没有找到分析文件")
        return 0

    all_stats, err_n, warn_n = [], 0, 0
    print(f"校验 {len(files)} 份语义架构分析\n" + "=" * 96)

    for f in files:
        errors, warnings, st = check_file(f, analysis)
        all_stats.append({**st, "errors": errors, "warnings": warnings})
        err_n += len(errors)
        warn_n += len(warnings)
        rate = f"{st.get('path_rate'):.0%}" if st.get("path_rate") is not None else "—"
        mark = "PASS" if not errors else "FAIL"
        print(f"\n[{mark}] {st.get('repo','?')}")
        sk = st.get("skipped") or {}
        print(f"       置信={st.get('confidence')}  抽象{st.get('abstractions')} 层{st.get('layers')} "
              f"流程{st.get('flow')} 关键文件{st.get('key_files')}")
        print(f"       路径真实性={rate}  已校验 {st.get('paths_checked')} 条  "
              f"跳过符号 {sk.get('symbol',0)} / 命令 {sk.get('command',0)}")
        for e in errors:
            print(f"       [错误] {e}")
        for w in warnings:
            print(f"       [提示] {w}")
        if args.verbose:
            for bp in st.get("bad_paths", []):
                print(f"         · {bp['field']}: {bp['path']}")
                if bp["suggest"]:
                    print(f"           可能应为: {bp['suggest']}")

    print("\n" + "=" * 96)
    ok = sum(1 for s in all_stats if not s["errors"])
    rates = [s["path_rate"] for s in all_stats if s.get("path_rate") is not None]
    print(f"通过 {ok}/{len(files)}   错误 {err_n}   提示 {warn_n}")
    if rates:
        print(f"路径真实性均值 {sum(rates)/len(rates):.1%}   "
              f"最低 {min(rates):.1%}")
    worst = sorted([s for s in all_stats if s.get("path_rate") is not None], key=lambda s: s["path_rate"])[:3]
    if worst and worst[0]["path_rate"] < 1:
        print("路径真实性最低的三份:")
        for s in worst:
            print(f"  {s['path_rate']:.0%}  {s['repo']}")

    if args.report:
        json.dump(all_stats, open(args.report, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"明细已写入 {args.report}")

    return 1 if (args.strict and err_n) else 0


if __name__ == "__main__":
    sys.exit(main())
