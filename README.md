# 具身智能 × AI Agent 学习地图

一份把**具身智能（Embodied AI）**和 **AI Agent** 两条学习主线，连同各自的 GitHub 高 star 项目，落到同一张思维导图上的学习资料。

不止是项目清单——**109 个开源项目已全部克隆到本地并逐个做了代码级可视化梳理**，每个项目的功能全景、模块架构、技术栈、运行入口都有真实数据支撑。

## 在线访问

| 页面 | 链接 | 内容 |
|---|---|---|
| 交互式思维导图 | [mindmap.html](https://forthefuture22.github.io/embodied-agent-learning/mindmap.html) | 25 分支 / 134 节点，点击展开、搜索、跳转仓库 |
| **项目浏览器** | [projects.html](https://forthefuture22.github.io/embodied-agent-learning/projects.html) | 入口树 + 逐级索引：总览 → 板块 → 分支 → 项目详情 |
| 文字版学习地图 | [learning-map.md](./learning-map.md) | 分支说明 + 项目表 + 12 周计划 + 避坑提示 |
| **任务设计文档** | [docs/TASK-DESIGN.md](./docs/TASK-DESIGN.md) | 语义架构图批次规划 · 网页工具改造选型 · 子 agent 并行方案 |

直达某个板块：`?tab=embodied` · `?tab=agent` · `?tab=cross`
项目浏览器支持深链接：`#/embodied/3/huggingface__lerobot` 可直接分享某个项目的架构分析

---

## 数据概览

对 109 个仓库做了完整代码扫描（排除 `.git`、`node_modules`、`venv` 等）：

| 板块 | 分支 | 项目 | 代码行数 | 文件数 |
|---|---|---|---|---|
| 具身智能 | 9 | 42 | 8,496,090 | 50,886 |
| AI Agent | 13 | 67 | 52,231,093 | 239,067 |
| 交叉地带 | 3 | 复用上表 3 个项目 | — | — |
| **合计** | **25** | **109** | **60,727,183** | **289,953** |

- **语言分布**：Python 22.8M 行 · TypeScript 12.8M · JSON 8.8M · Go 2.7M · YAML 2.1M · Markdown 2.0M · C++ 1.9M · Rust 1.5M
- **许可证分布**：Apache-2.0 44 个 · MIT 37 个 · 其他/未标注 28 个
- **提取覆盖率**：功能说明 108/109 · 运行命令 99/109 · 入口点 90/109

代码量 Top 5：n8n 5.56M 行 · suna 5.41M · LiteLLM 4.14M · Unsloth 3.25M · SGLang 3.01M

---

## 文件说明

```
.
├── README.md                 # 本文件
├── mindmap.html              # 交互式思维导图（单文件，双击即用）
├── projects.html             # 项目浏览器（入口树 + 逐级索引）
├── learning-map.md           # 文字版学习地图
├── docs/
│   └── TASK-DESIGN.md        # 任务设计：批次规划 / 选型模型 / 并行方案
├── data/
│   ├── manifest.json         # 从导图提取的树结构 + 109 个仓库清单
│   ├── repos-meta.json       # GitHub 元数据（体积/语言/许可证/活跃度）
│   ├── analysis.json         # 109 个项目的结构级扫描结果
│   ├── priority.json         # 109 个项目的双任务优先级评分
│   ├── arch/                 # 语义级架构分析（子 agent 产出）
│   │   └── *.json            #   每份 15 字段：核心抽象/分层/数据流/Mermaid 图/阅读顺序
│   └── stars.json            # star 数据快照
└── scripts/
    ├── build_manifest.js     # 从 mindmap.html 提取仓库清单
    ├── fetch_meta.py         # 拉取 GitHub 元数据
    ├── fetch_stars.py        # 刷新 star 数据
    ├── clone_all.py          # 批量浅克隆到 D:\github
    ├── analyze_repos.py      # 结构级分析（断点续跑）
    ├── score_projects.py     # 双任务优先级评分
    ├── build_dashboard.py    # 生成 projects.html
    └── verify_dashboard.js   # 浏览器功能级校验
```

---

## 信息架构

项目浏览器从「一屏平铺 109 张卡片」重构为**入口树 + 四级下钻**：

| 层级 | 路由 | 呈现内容 |
|---|---|---|
| L0 总览 | `#/` | 统计 + 全景树图 + 3 个板块 |
| L1 板块 | `#/embodied` | 9 个分支卡片 |
| L2 分支 | `#/embodied/3` | 项目紧凑表格（可横向比较） |
| L3 项目 | `#/embodied/3/huggingface__lerobot` | 完整详情（语义架构 + 结构四维） |

侧栏树自动展开当前路径并高亮；**109 个项目全部带 `◆` 标记**（语义架构分析已全部完成）。首屏信息量从 435 KB 降到 28 KB。

### 语义架构分析（109/109）

每个项目都有一份由子 agent 深读源码产出的结构化分析，15 个字段：

| 字段组 | 回答的问题 |
|---|---|
| `one_liner` / `problem` / `difficulty` | 这是什么、解决什么问题、多难 |
| `core_abstractions` / `layers` | 系统由哪些核心抽象构成、如何分层 |
| `data_flow` / `diagram_mermaid` | 数据从输入到输出怎么走（含可渲染的架构图） |
| `key_files` / `learning_path` | 该按什么顺序读源码 |
| `extension_points` / `surprises` | 想扩展改哪里、有哪些反直觉的坑 |
| `confidence` | 分析者对这份结论的把握 |

**质量保障**：`scripts/verify_arch.py` 会逐条校验所有 `file` / `path` 是否在本地仓库真实存在——这是防幻觉的关键闸门。最终 **109/109 通过，路径真实性 100%**（累计校验 5000+ 条路径引用）。

分析过程中子 agent 还发现并修复了多处克隆不完整问题（Isaac Lab 缺 `source/`、GR00T 缺 `gr00t/`、AutoGen 的 `python/` 与 `dotnet/` 被删），并如实标注了若干仓库的实况偏差（OpenHands 克隆实为 TS 前端、RAGFlow 已用 Go 重写、Letta 已是 landing page 元仓库等）。

---

## 可视化梳理做了什么

对每个项目，从**真实文件系统**中提取四类信息（不是推测，也不依赖 README 自述）：

| 维度 | 提取方式 | 用途 |
|---|---|---|
| **功能全景** | README 标题 / 摘要 / 特性要点 + GitHub topics | 快速判断这个项目解决什么问题 |
| **模块架构** | 顶层与二级目录的文件数、代码行数 | 看出代码集中在哪、哪里是核心 |
| **技术栈** | 按扩展名统计的文件数与 LOC 分布 | 判断学习门槛和语言要求 |
| **运行流程** | 依赖清单 / 入口文件 / Dockerfile / Makefile / npm scripts | 知道从哪一行开始跑 |

另外提供**项目全景图**：矩形面积正比于代码行数的树图，一眼看出整个项目群的体量分布，点击可定位到对应卡片。

---

## 快速开始

```bash
git clone https://github.com/forthefuture22/embodied-agent-learning.git
cd embodied-agent-learning
start mindmap.html      # Windows
open  mindmap.html      # macOS
```

浏览器直接打开即可，无任何依赖。

---

## 复现整套流程

```bash
# 1. 提取仓库清单
node scripts/build_manifest.js

# 2. 拉取 GitHub 元数据 + star 数
python scripts/fetch_meta.py
python scripts/fetch_stars.py

# 3. 批量浅克隆到 D:\github（约 20 GB，109 个仓库）
python scripts/clone_all.py --jobs 3 --timeout 900

# 4. 代码结构分析（支持断点续跑，全量约 45 分钟）
python scripts/analyze_repos.py --flush-every 10

# 5. 生成看板 + 校验
python scripts/build_dashboard.py
node scripts/verify_dashboard.js
```

### 已知环境要求

- **`git-lfs` 未安装**：`qdrant/qdrant` 等使用 LFS 的仓库会回退为指针文件（不影响代码结构分析）。如需完整 LFS 内容请先安装 git-lfs。
- **网络不稳定时**：`clone_all.py` 已内置低速自动中断（1KB/s 持续 60 秒即断）与 HTTP/1.1 回退，避免连接挂死。实测首次全量克隆时有 4 个连接卡死，重跑一次即全部补齐。

---

## 几条核心判断

1. **具身线的主干是 VLA，但真正能出成果的入口在模仿学习。**
   [LeRobot](https://github.com/huggingface/lerobot)（28k，19.5 万行）是目前唯一把「采集—训练—部署」打通的端到端工具链，比直接啃 OpenVLA 现实得多。

2. **VLA 主线记住四个锚点就够：**
   [openpi / π0](https://github.com/Physical-Intelligence/openpi)（14k）→
   [GR00T N1](https://github.com/NVIDIA/Isaac-GR00T)（8.2k）→
   [OpenVLA](https://github.com/openvla/openvla)（7.1k）→
   [Octo](https://github.com/octo-models/octo)（1.8k，最好的学习基线，因为足够小足够干净）。

3. **世界模型（WAM）暂时不要重投入。**
   Genie 2、WALL-E、UniSim 全部闭源，开源可复现的只剩 Genesis 和 Vista，投入产出比很差。

4. **交叉地带是差异化区。**
   把机器人每个技能封装成 MCP 工具 → LLM 做高层规划 → VLA 做低层执行 → 结果回流做反思重试。
   这条路径的论文线（SayCan / PaLM-E / Code as Policies / VoxPoser）都还没有成熟开源实现。

5. **两个方向的共同底座是评测。**
   具身看 ManiSkill / LIBERO / SimplerEnv，Agent 看 SWE-bench。没有评测就没有迭代。

6. **star 数 ≠ 适合你。**
   AutoGPT 有 188k 但工程可用性一般；Octo 只有 1.8k 却是很好的学习基线。

---

## 数据说明

- star 数抓取时间：**2026-10-10**，数据源 GitHub via [shields.io](https://shields.io)
- 代码扫描时间：**2026-10-10**，对 `--depth 1` 浅克隆的仓库做全量文件扫描
- 代码行数为**文件行数**（含注释与空行），用于横向比较体量，不等同于有效代码行数
- star 数仅代表社区热度，**不代表质量排名**，选型请结合自身场景判断

---

## TODO

完整规划见 [docs/TASK-DESIGN.md](./docs/TASK-DESIGN.md)。

- [x] **语义级架构分析 109/109 全部完成**（8 批 × 3-5 个并行子 agent，全部通过校验，路径真实性 100%）
- [x] 反幻觉校验脚本 `verify_arch.py`（结构完整性 / 路径真实性 / 图表合法性 / 内容质量）
- [x] 信息架构重构（入口树 + 四级下钻，首屏从 435 KB 降到 28 KB）
- [ ] 网页工具改造试点（优先 A 类：gpt-engineer · SWE-agent · Docling 等无需 GPU 的项目）
- [ ] 补充每个分支的必读论文清单（带链接）
- [ ] 为 VLA 主线补一张演进时间线
- [ ] 把 star 刷新与 HTML 打通，避免手工同步

---

## License

学习资料，自由取用。引用的第三方项目版权归各自作者所有。
