"""从 mindmap.html 提取全部仓库，调用 gh CLI 拉取元数据（体积/语言/许可证/活跃度）。

用法:
    python scripts/fetch_meta.py
输出:
    data/repos-meta.json
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, os.pardir)
HTML = os.path.join(ROOT, "mindmap.html")
OUT = os.path.join(ROOT, "data", "repos-meta.json")
GH = r"C:\Users\25785\.local\bin\gh.exe"


def extract_repos():
    src = open(HTML, encoding="utf-8").read()
    # 捕获 L('名称','star','owner/repo')
    pairs = re.findall(r"L\('([^']*)','([^']*)','([^']+)'\)", src)
    repos, stars, names = [], {}, {}
    for name, star, repo in pairs:
        if repo not in repos:
            repos.append(repo)
        stars[repo] = star
        names[repo] = name
    return repos, stars, names


def gh_api(path):
    r = subprocess.run([GH, "api", path], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except Exception:
        return None


def main():
    repos, stars, names = extract_repos()
    print(f"从 mindmap.html 提取到 {len(repos)} 个唯一仓库\n", flush=True)

    meta = {}
    total_kb = 0
    for i, repo in enumerate(repos, 1):
        d = gh_api(f"repos/{repo}")
        if not d:
            print(f"[{i:>3}/{len(repos)}] {repo:<52} !! 拉取失败", flush=True)
            meta[repo] = {"repo": repo, "name": names.get(repo, repo), "star": stars.get(repo), "error": True}
            continue
        size_kb = d.get("size") or 0
        total_kb += size_kb
        lic = (d.get("license") or {}).get("spdx_id") or "无"
        meta[repo] = {
            "repo": repo,
            "name": names.get(repo, repo),
            "star": stars.get(repo),
            "size_kb": size_kb,
            "size_mb": round(size_kb / 1024, 1),
            "language": d.get("language"),
            "license": lic,
            "pushed_at": (d.get("pushed_at") or "")[:10],
            "archived": d.get("archived", False),
            "description": (d.get("description") or "").strip(),
            "topics": d.get("topics", []),
        }
        print(f"[{i:>3}/{len(repos)}] {repo:<52} {size_kb/1024:>8.1f} MB  {lic:<14} {d.get('language')}", flush=True)

    json.dump(meta, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    ok = [m for m in meta.values() if not m.get("error")]
    ok.sort(key=lambda m: -m["size_mb"])
    print("\n" + "=" * 78)
    print(f"成功: {len(ok)}/{len(repos)}   总体积: {total_kb/1024/1024:.2f} GB (GitHub 统计的仓库体积)")
    print(f"\n体积 Top 15:")
    for m in ok[:15]:
        print(f"  {m['repo']:<52} {m['size_mb']:>8.1f} MB")
    print(f"\n已写入 {OUT}")


if __name__ == "__main__":
    main()
