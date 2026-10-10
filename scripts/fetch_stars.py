"""刷新思维导图中所有仓库的 star 数（数据源：GitHub via shields.io）。

用法:
    python scripts/fetch_stars.py     # 刷新 data/stars.json 中已记录的仓库
输出:
    data/stars.json  {"owner/repo": "148k", ...}
"""
import json, os, urllib.request, time, concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, os.pardir, "data", "stars.json")


def load_repos():
    if os.path.exists(OUT):
        return list(json.load(open(OUT, encoding="utf-8")).keys())
    raise SystemExit("stars.json 不存在，请先在 HTML 中补齐仓库列表")


def fetch(full, tries=4):
    url = f"https://img.shields.io/github/stars/{full}.json"
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as r:
                d = json.load(r)
            return full, d.get("value") or d.get("message")
        except Exception:
            if i == tries - 1:
                return full, None
            time.sleep(1.5 * (i + 1))


def main():
    repos = load_repos()
    old = json.load(open(OUT, encoding="utf-8"))
    result = {}
    with cf.ThreadPoolExecutor(max_workers=5) as ex:
        for repo, stars in ex.map(fetch, repos):
            result[repo] = stars or old.get(repo)
            print(f"{repo:<52} {old.get(repo,'?'):>7} -> {result[repo]}", flush=True)
    json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n已更新 {len(result)} 个仓库 -> {OUT}")


if __name__ == "__main__":
    main()
