# 具身智能 × AI Agent 学习地图

一份把**具身智能（Embodied AI）**和 **AI Agent** 两条学习主线，连同各自的 GitHub 高 star 项目，落到同一张思维导图上的学习资料。

不是项目清单堆砌——每个分支都标注了「学什么、为什么学、从哪个项目切入」。

## 在线访问

- **交互式思维导图**：https://forthefuture22.github.io/embodied-agent-learning/mindmap.html
- **文字版学习地图**：[learning-map.md](./learning-map.md)
- **直达某个板块**：`?tab=embodied` · `?tab=agent` · `?tab=cross`

---

## 内容概览

| 板块 | 分支数 | 节点数 | 覆盖内容 |
|---|---|---|---|
| **具身智能** | 9 | 46 | RL 地基 → 仿真引擎 → 基准环境 → 模仿学习 → VLA → VLM 底座 → 世界模型 → 运控部署 → 资源清单 |
| **AI Agent** | 13 | 72 | 核心范式 → 编排框架 → 官方 SDK → 多智能体 → 自主 Agent → 工具协议 → 记忆 → RAG → 电脑操作 → 编码 Agent → 平台 → 数据管道 → 模型服务 |
| **交叉地带** | 3 | 16 | 语言驱动机器人论文线 · Agent 能力迁移到机器人 · 融合学习路线 |
| **合计** | **25** | **134** | **112 个仓库**（star 数实时抓取） |

---

## 文件说明

```
.
├── README.md              # 本文件
├── mindmap.html           # 交互式思维导图（单文件，双击即用）
├── learning-map.md        # 完整学习地图：分支说明 + 项目表 + 12 周计划 + 避坑
├── data/
│   └── stars.json         # star 数据快照
└── scripts/
    └── fetch_stars.py     # 刷新 star 数据
```

### `mindmap.html`

单文件交互式 SVG 思维导图，无需安装任何依赖，双击用浏览器打开即可。

- 三个标签页切换：具身智能 / AI Agent / 交叉地带
- 点击分支节点折叠展开，聚焦某个方向
- 点击项目节点直接跳转 GitHub 仓库
- 支持搜索高亮、缩放、适应宽度
- 支持 URL 参数直达：`mindmap.html?tab=embodied`、`?tab=agent`、`?tab=cross`

### `learning-map.md`

思维导图的文字版，适合阅读、搜索、复制到笔记软件。包含：

- 每个分支的「学什么」说明
- 完整项目表（star 数 + 一句话定位）
- **12 周行动计划**（具身线与 Agent 线并行推进）
- **6 条避坑提示**

---

## 快速开始

```bash
git clone https://github.com/forthefuture22/embodied-agent-learning.git
cd embodied-agent-learning
# 直接用浏览器打开
start mindmap.html          # Windows
open  mindmap.html          # macOS
```

---

## 更新 star 数据

项目中的 star 数会随时间变化，可随时刷新：

```bash
python scripts/fetch_stars.py
```

脚本读取 `data/stars.json` 中的仓库列表，逐个查询最新 star 数并回写。
数据源为 `https://img.shields.io/github/stars/{owner}/{repo}.json`
（GitHub 官方 API 对未认证请求限流较严，shields.io 更稳定）。

> 刷新后 `data/stars.json` 会更新，但 `mindmap.html` 中的数字是硬编码的，
> 如需同步到导图，请一并更新 HTML 中 `MAPS` 对象的 `star` 字段。

---

## 几条核心判断

1. **具身线的主干是 VLA，但真正能出成果的入口在模仿学习。**
   [LeRobot](https://github.com/huggingface/lerobot)（28k）是目前唯一把「采集—训练—部署」打通的端到端工具链，
   比直接啃 OpenVLA 现实得多。

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

- star 数抓取时间：**2026-10-10**
- 数据源：GitHub via [shields.io](https://shields.io)
- star 数仅代表社区热度，**不代表质量排名**，选型请结合自身场景判断

---

## TODO

- [ ] 补充每个分支的必读论文清单（带链接）
- [ ] 为 VLA 主线补一张演进时间线
- [ ] 增加「真实实验记录」目录，沉淀跑通过的项目
- [ ] 把 star 数刷新脚本与 HTML 打通，避免手工同步

---

## License

学习资料，自由取用。引用请注明来源。
