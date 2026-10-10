"""把 manifest.json 中的全部仓库浅克隆到 D:\\github\\<domain>\\<repo-name>。

用法:
    python scripts/clone_all.py [--jobs 4] [--dry-run]
特性:
    - --depth 1 浅克隆，大幅减小体积
    - 已存在且非空的目录自动跳过
    - 失败自动重试 2 次
    - 实时输出进度，末尾汇总体积与失败清单
"""
import json, os, subprocess, sys, time, shutil, argparse
import concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, os.pardir)
MANIFEST = os.path.join(ROOT, "data", "manifest.json")
DEST = r"D:\github"

ENV = dict(os.environ)
ENV["GIT_TERMINAL_PROMPT"] = "0"
ENV["GIT_LFS_SKIP_SMUDGE"] = "1"   # 跳过 LFS 大文件，避免模型权重下载
ENV["GIT_HTTP_LOW_SPEED_LIMIT"] = "1000"   # 低于 1KB/s ...
ENV["GIT_HTTP_LOW_SPEED_TIME"] = "60"      # ... 持续 60 秒即中断，避免连接挂死

# 网络加固参数：低速自动中断 + 回退 HTTP/1.1（对代理环境更稳）
GIT_OPTS = [
    "-c", "http.lowSpeedLimit=1000",
    "-c", "http.lowSpeedTime=60",
    "-c", "http.version=HTTP/1.1",
    "-c", "core.compression=0",
]


def dir_size_mb(p):
    total = 0
    for dp, _, fns in os.walk(p):
        for f in fns:
            try:
                total += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    return total / 1024 / 1024


def is_valid_repo(path):
    return os.path.isdir(os.path.join(path, ".git"))


def clone(repo, domain, timeout=900):
    name = repo.split("/")[-1]
    target = os.path.join(DEST, domain, name)

    # 已有完整仓库 -> 跳过
    if is_valid_repo(target):
        return {"repo": repo, "status": "skip", "path": target, "mb": dir_size_mb(target)}

    os.makedirs(os.path.dirname(target), exist_ok=True)
    url = f"https://github.com/{repo}.git"
    last_err = ""
    for attempt in range(3):
        # 清理上一次的残留（含被中断的半成品）
        if os.path.isdir(target):
            shutil.rmtree(target, ignore_errors=True)
        try:
            r = subprocess.run(
                ["git", *GIT_OPTS, "clone", "--depth", "1", "--single-branch", "--quiet", url, target],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                env=ENV, timeout=timeout,
            )
            rc, err = r.returncode, (r.stderr or r.stdout or "")
        except subprocess.TimeoutExpired:
            rc, err = -1, f"超时 {timeout}s"

        if rc == 0 and is_valid_repo(target):
            return {"repo": repo, "status": "ok", "path": target, "mb": dir_size_mb(target)}
        last_err = err.strip().replace("\n", " ")[:180] or f"rc={rc}"
        print(f"       retry {repo} (第 {attempt+1} 次失败: {last_err})", flush=True)
        time.sleep(3 * (attempt + 1))

    if os.path.isdir(target):
        shutil.rmtree(target, ignore_errors=True)
    return {"repo": repo, "status": "fail", "path": target, "mb": 0, "err": last_err}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=900, help="单个仓库克隆超时（秒）")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", nargs="*", help="只克隆指定仓库（owner/repo）")
    args = ap.parse_args()

    m = json.load(open(MANIFEST, encoding="utf-8"))
    repos = m["repos"]
    jobs = [(r, v["domains"][0]) for r, v in sorted(repos.items())]
    if args.only:
        want = set(args.only)
        jobs = [j for j in jobs if j[0] in want]
        print(f"限定克隆 {len(jobs)} 个仓库")

    print(f"目标目录: {DEST}")
    print(f"仓库总数: {len(jobs)}   并发: {args.jobs}\n", flush=True)

    if args.dry_run:
        for r, d in jobs:
            print(f"  {d:<10} {r}")
        return

    os.makedirs(DEST, exist_ok=True)
    results = []
    done = 0
    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(clone, r, d, args.timeout): r for r, d in jobs}
        for fut in cf.as_completed(futs):
            res = fut.result()
            results.append(res)
            done += 1
            flag = {"ok": "OK  ", "skip": "SKIP", "fail": "FAIL"}[res["status"]]
            extra = f"  <- {res.get('err','')}" if res["status"] == "fail" else ""
            print(f"[{done:>3}/{len(jobs)}] {flag} {res['repo']:<52} {res['mb']:>7.1f} MB{extra}", flush=True)

    ok = [r for r in results if r["status"] == "ok"]
    sk = [r for r in results if r["status"] == "skip"]
    bad = [r for r in results if r["status"] == "fail"]
    total = sum(r["mb"] for r in results)
    print("\n" + "=" * 78)
    print(f"成功 {len(ok)}   跳过 {len(sk)}   失败 {len(bad)}")
    print(f"实际占用: {total/1024:.2f} GB   耗时: {(time.time()-t0)/60:.1f} 分钟")
    if bad:
        print("\n失败清单:")
        for r in bad:
            print(f"  {r['repo']:<52} {r.get('err','')}")
    json.dump(results, open(os.path.join(ROOT, "data", "clone-report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n报告: data/clone-report.json")


if __name__ == "__main__":
    main()
