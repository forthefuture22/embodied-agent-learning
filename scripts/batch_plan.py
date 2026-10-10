"""批次进度与下一批名单。

用法:
    python scripts/batch_plan.py            # 进度概览
    python scripts/batch_plan.py --next 15  # 下一批 15 个项目（含本地路径）
"""
import json, os, glob, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, os.pardir)
PRIO = os.path.join(ROOT, "data", "priority.json")
ARCH = os.path.join(ROOT, "data", "arch")
DEST = r"D:\github"


def load():
    prio = json.load(open(PRIO, encoding="utf-8"))
    done = {}
    for f in glob.glob(os.path.join(ARCH, "*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
            if d.get("repo"):
                done[d["repo"]] = d
        except Exception:
            pass
    return prio, done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--next", type=int, default=0, help="输出下一批 N 个项目的路径")
    args = ap.parse_args()

    prio, done = load()
    ranked = sorted(prio.values(), key=lambda x: -x["arch_score"])
    todo = [v for v in ranked if v["repo"] not in done]
    total = len(ranked)
    pct = len(done) / total * 100 if total else 0

    if args.next:
        n = min(args.next, len(todo))
        print(f"# 下一批 {n} 个项目（共剩 {len(todo)}）\n")
        groups = {}
        for v in todo[:n]:
            dk = v["domains"][0]
            groups.setdefault(dk, []).append(v)
        for dk, vs in groups.items():
            print(f"## {dk}")
            for v in vs:
                path = os.path.join(DEST, dk, v["repo"].split("/")[-1])
                slug = v["repo"].replace("/", "__")
                mark = "OK" if os.path.isdir(path) else "MISSING"
                print(f"  [{mark}] {v['arch_score']:>5}  {v['name']}  ({v['repo']})")
                print(f"          path: {path}")
                print(f"          out : data/arch/{slug}.json")
            print()
        return

    print(f"语义架构进度: {len(done)}/{total}  ({pct:.0f}%)")
    bar = "=" * int(pct / 2) + "-" * (50 - int(pct / 2))
    print(f"[{bar}]")
    print()
    # 按分支统计
    from collections import defaultdict
    byb = defaultdict(lambda: [0, 0])
    for v in ranked:
        key = f"{v['domains'][0]} · {v['branches'][0]}"
        byb[key][1] += 1
        if v["repo"] in done:
            byb[key][0] += 1
    print(f"{'分支':<46}{'完成/总数'}")
    print("-" * 62)
    for k, (a, b) in sorted(byb.items(), key=lambda x: -x[1][1]):
        flag = "  ✓" if a == b else ""
        print(f"{k:<46}{a}/{b}{flag}")
    print()
    if todo:
        print(f"下一个待做: {todo[0]['name']} ({todo[0]['repo']})  优先级 {todo[0]['arch_score']}")


if __name__ == "__main__":
    main()
