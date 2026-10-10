# 具身智能 × AI Agent 学习地图

> star 数于 **2026-10-10** 实时抓取自 GitHub（经 shields.io），仅供参考热度，不代表质量排名。
> 配套交互式思维导图：[`mindmap.html`](./mindmap.html)（三个标签页：具身智能 46 节点 / AI Agent 72 节点 / 交叉地带 16 节点）

---

## 一、具身智能 Embodied AI（9 分支 · 42 个仓库）

### ① 深度学习与强化学习地基
**学什么**：MDP、值函数/策略梯度、PPO/SAC；先能在标准环境里跑通再谈机器人。

| 项目 | star | 定位 |
|---|---|---|
| [ray-project/ray](https://github.com/ray-project/ray) | 44k | 分布式计算底座，RLlib 是工业级 RL 训练库 |
| [DLR-RM/stable-baselines3](https://github.com/DLR-RM/stable-baselines3) | 14k | RL 算法实现最清晰，读源码首选 |
| [Farama-Foundation/Gymnasium](https://github.com/Farama-Foundation/Gymnasium) | 13k | 环境接口标准，所有机器人环境的通用 API |

**建议**：用 SB3 在 Gymnasium 上把 PPO 跑通一遍（CartPole → MuJoCo），再进入机器人领域。

### ② 仿真引擎与平台
**学什么**：物理引擎原理、GPU 并行仿真、sim2real gap。

| 项目 | star | 定位 |
|---|---|---|
| [Genesis-Embodied-AI/Genesis](https://github.com/Genesis-Embodied-AI/Genesis) | 30k | 新一代生成式物理引擎，速度快、可微 |
| [microsoft/AirSim](https://github.com/microsoft/AirSim) | 19k | 无人机/自动驾驶仿真 |
| [google-deepmind/mujoco](https://github.com/google-deepmind/mujoco) | 16k | 接触动力学金标准，学术默认选择 |
| [bulletphysics/bullet3](https://github.com/bulletphysics/bullet3) | 15k | 经典开源引擎，PyBullet 广泛用于研究 |
| [isaac-sim/IsaacLab](https://github.com/isaac-sim/IsaacLab) | 8.3k | NVIDIA 官方机器人学习框架，GPU 万级并行 |
| [isaac-sim/IsaacSim](https://github.com/isaac-sim/IsaacSim) | 4.2k | Omniverse 上的高保真仿真平台 |

**建议**：入门用 MuJoCo（轻量、文档好），做大规模并行训练上 Isaac Lab（需 NVIDIA 显卡）。

### ③ 操作 / 导航基准环境
**学什么**：任务定义、成功判据、基准可比性。

| 项目 | star | 定位 |
|---|---|---|
| [haosulab/ManiSkill](https://github.com/haosulab/ManiSkill) | 3.4k | GPU 并行操作基准，任务丰富 |
| [facebookresearch/habitat-lab](https://github.com/facebookresearch/habitat-lab) | 3.2k | 室内导航/交互基准 |
| [RoboTwin-Platform/RoboTwin](https://github.com/RoboTwin-Platform/RoboTwin) | 3k | 双臂操作数据生成与基准 |
| [ARISE-Initiative/robosuite](https://github.com/ARISE-Initiative/robosuite) | 2.6k | 机械臂操作仿真（Mujoco 后端） |
| [RoboVerseOrg/RoboVerse](https://github.com/RoboVerseOrg/RoboVerse) | 1.9k | 统一多仿真器平台 |
| [stepjam/RLBench](https://github.com/stepjam/RLBench) | 1.8k | 100+ 操作任务，模仿学习常用 |
| [StanfordVL/BEHAVIOR-1K](https://github.com/StanfordVL/BEHAVIOR-1K) | 1.7k | 1000 项家庭日常活动基准 |

### ④ 示教 · 模仿学习 · 数据
**学什么**：BC / ACT / Diffusion Policy、遥操作采集、数据集配比。**这是当前最容易出成果的方向。**

| 项目 | star | 定位 |
|---|---|---|
| [huggingface/lerobot](https://github.com/huggingface/lerobot) | 28k | 端到端机器人学习全家桶，**强烈推荐入门首选** |
| [real-stanford/diffusion_policy](https://github.com/real-stanford/diffusion_policy) | 4.6k | 扩散策略原论文实现，精度高 |
| [google-deepmind/open_x_embodiment](https://github.com/google-deepmind/open_x_embodiment) | 2.1k | 22 种机器人、百万级轨迹的统一数据集 |
| [thu-ml/RoboticsDiffusionTransformer](https://github.com/thu-ml/RoboticsDiffusionTransformer) | 1.8k | RDT-1B，10 亿参数双臂基础模型 |
| [ARISE-Initiative/robomimic](https://github.com/ARISE-Initiative/robomimic) | 1.6k | 模仿学习标准化训练/评测框架 |
| [droid-dataset/droid](https://github.com/droid-dataset/droid) | 448 | 76k 条真实场景操作轨迹 |

### ⑤ VLA 视觉-语言-动作主线
**学什么**：VLM 主干 + 动作头、动作 token 化、Flow Matching。**具身智能当前最热的主线。**

| 项目 | star | 定位 |
|---|---|---|
| [Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi) | 14k | π0 官方开源，Flow Matching 动作生成，工业级 |
| [NVIDIA/Isaac-GR00T](https://github.com/NVIDIA/Isaac-GR00T) | 8.2k | 人形机器人 VLA 基础模型 |
| [openvla/openvla](https://github.com/openvla/openvla) | 7.1k | 首个开源 7B VLA，社区基线 |
| [octo-models/octo](https://github.com/octo-models/octo) | 1.8k | Transformer 通用策略，轻量易改 |

**建议路径**：先读 RT-1 / RT-2 论文 → 跑通 OpenVLA 推理 → 微调 Octo → 再看 π0。

### ⑥ 多模态底座 VLM
**学什么**：视觉编码器、跨模态对齐、指令跟随。VLA 的能力上限很大程度取决于底座。

| 项目 | star | 定位 |
|---|---|---|
| [openai/CLIP](https://github.com/openai/CLIP) | 34k | 视觉-语言对齐的奠基工作 |
| [OpenBMB/MiniCPM-V](https://github.com/OpenBMB/MiniCPM-V) | 27k | 端侧可部署多模态模型 |
| [OpenBMB/OmniLMM](https://github.com/OpenBMB/OmniLMM) | 27k | 多模态大模型系列 |
| [haotian-liu/LLaVA](https://github.com/haotian-liu/LLaVA) | 25k | 视觉指令微调范式开创者 |
| [QwenLM/Qwen2.5-VL](https://github.com/QwenLM/Qwen2.5-VL) | 20k | 中文场景强，空间定位能力好 |
| [OpenGVLab/InternVL](https://github.com/OpenGVLab/InternVL) | 10k | 开源多模态第一梯队，机器人常用底座 |

### ⑦ 世界模型 WAM（World-Action Model）
**学什么**：预测式具身智能——先预测未来帧/未来状态，再据此出动作。

- 前沿代表 **Genie 2（Google）、WALL-E（字节）、UniSim** 均为**闭源**，只有论文。
- 唯一可上手的开源落点：[OpenDriveLab/Vista](https://github.com/OpenDriveLab/Vista)（907★，驾驶世界模型），以及 ② 中的 Genesis（生成式物理引擎）。
- **结论**：WAM 目前开源可复现资源稀缺，建议先跟论文、把 VLA 线打扎实，等开源生态成熟。

### ⑧ 运控 · 真机 · 部署
**学什么**：IK / 轨迹规划 / 阻抗控制、腿足步态、ROS 2 通信。

| 项目 | star | 定位 |
|---|---|---|
| [ros2/ros2](https://github.com/ros2/ros2) | 6.1k | 机器人系统的事实标准中间件 |
| [stack-of-tasks/pinocchio](https://github.com/stack-of-tasks/pinocchio) | 3.8k | 刚体动力学与运动学计算 |
| [unitreerobotics/unitree_rl_gym](https://github.com/unitreerobotics/unitree_rl_gym) | 3.6k | 宇树机器人 RL 训练环境 |
| [leggedrobotics/legged_gym](https://github.com/leggedrobotics/legged_gym) | 3.1k | 腿足机器人 RL 经典框架（Isaac Gym） |
| [unitreerobotics/unitree_ros2](https://github.com/unitreerobotics/unitree_ros2) | 858 | 宇树真机 ROS 2 接口 |

### ⑨ 入门清单与资源聚合
| 项目 | star | 定位 |
|---|---|---|
| [TianxingChen/Embodied-AI-Guide](https://github.com/TianxingChen/Embodied-AI-Guide) | 16k | **中文具身智能入门指南，从这里开始** |
| [GT-RIPL/Awesome-LLM-Robotics](https://github.com/GT-RIPL/Awesome-LLM-Robotics) | 4.5k | LLM + 机器人论文清单 |
| [robotics-survey/Awesome-Robotics-Foundation-Models](https://github.com/robotics-survey/Awesome-Robotics-Foundation-Models) | 1.4k | 机器人基础模型综述 |
| [zc-xzc/embodied-ai-learning-handbook](https://github.com/zc-xzc/embodied-ai-learning-handbook) | 56 | 系统性学习手册（新，内容成体系） |

---

## 二、AI Agent 智能体（13 分支 · 67 个仓库）

### ① 核心范式与原理
必须先建立概念，否则写出来的只是「包了一层 API 的调用」。

- **ReAct / CoT**：推理与行动交替，是所有 Agent 的骨架
- **Tool Use**：函数调用协议，Agent 与外部世界交互的唯一通道
- **Planning**：任务分解（Plan-and-Execute / Tree-of-Thought）
- **Reflection**：自我批判与重试（Reflexion）
- **Memory**：短期上下文 + 长期向量记忆
- [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy) | 39k | 把 Prompt 变成可编译优化的程序

### ② 通用编排框架
| 项目 | star | 定位 |
|---|---|---|
| [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | 148k | 生态最大，组件最全，抽象也最重 |
| [run-llama/llama_index](https://github.com/run-llama/llama_index) | 52k | 数据/RAG 侧最强 |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | 43k | 图状态机，**复杂 Agent 生产首选** |
| [agno-agi/agno](https://github.com/agno-agi/agno) | 43k | 轻量高性能，API 干净 |
| [modelscope/agentscope](https://github.com/modelscope/agentscope) | 33k | 阿里系，中文友好 |

### ③ 官方与轻量 SDK
| 项目 | star | 定位 |
|---|---|---|
| [openai/openai-agents-python](https://github.com/openai/openai-agents-python) | 30k | 官方 SDK，概念最少，**新手推荐起点** |
| [huggingface/smolagents](https://github.com/huggingface/smolagents) | 30k | 极简，代码即工具 |
| [microsoft/semantic-kernel](https://github.com/microsoft/semantic-kernel) | 29k | 企业级 .NET/Python |
| [google/adk-python](https://github.com/google/adk-python) | 22k | Google 官方 Agent 框架 |
| [pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) | 21k | 类型安全，工程体验好 |
| [QwenLM/Qwen-Agent](https://github.com/QwenLM/Qwen-Agent) | 17k | 通义千问官方，中文工具调用强 |
| [microsoft/TaskWeaver](https://github.com/microsoft/TaskWeaver) | 6.2k | 代码优先的数据分析 Agent |

### ④ 多智能体协作
| 项目 | star | 定位 |
|---|---|---|
| [geekan/MetaGPT](https://github.com/geekan/MetaGPT) | 71k | 软件公司 SOP 角色分工 |
| [microsoft/autogen](https://github.com/microsoft/autogen) | 61k | 微软多 Agent 对话框架，理论扎实 |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | 60k | 角色+任务模型，上手最快 |
| [OpenBMB/ChatDev](https://github.com/OpenBMB/ChatDev) | 34k | 虚拟软件公司协作 |
| [camel-ai/camel](https://github.com/camel-ai/camel) | 18k | 角色扮演式 Agent 研究框架 |
| [OpenBMB/AgentVerse](https://github.com/OpenBMB/AgentVerse) | 5.2k | 多 Agent 仿真沙盒 |

### ⑤ 自主探索型 Agent
| 项目 | star | 定位 |
|---|---|---|
| [Significant-Gravitas/AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) | 188k | 自主循环鼻祖，适合理解 Agent Loop |
| [reworkd/AgentGPT](https://github.com/reworkd/AgentGPT) | 36k | 浏览器里跑自主 Agent |
| [OpenBMB/XAgent](https://github.com/OpenBMB/XAgent) | 8.6k | 自主任务求解 |

### ⑥ 工具 · 协议 · 沙箱
| 项目 | star | 定位 |
|---|---|---|
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | 91k | MCP 官方 Server 集合，**必学协议** |
| [a2aproject/A2A](https://github.com/a2aproject/A2A) | 26k | Agent 间通信协议 |
| [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | 25k | 写自己的 MCP Server |
| [e2b-dev/E2B](https://github.com/e2b-dev/E2B) | 14k | 代码执行安全沙箱 |
| [modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector) | 11k | MCP 调试工具 |

### ⑦ 记忆层
| 项目 | star | 定位 |
|---|---|---|
| [mem0ai/mem0](https://github.com/mem0ai/mem0) | 67k | 通用记忆层，接入成本最低 |
| [getzep/graphiti](https://github.com/getzep/graphiti) | 32k | 时序知识图谱记忆 |
| [topoteretes/cognee](https://github.com/topoteretes/cognee) | 32k | 记忆 + 图 RAG |
| [letta-ai/letta](https://github.com/letta-ai/letta) | 25k | 原 MemGPT，分层记忆架构经典 |

### ⑧ RAG 与向量库
| 项目 | star | 定位 |
|---|---|---|
| [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | 92k | 端到端 RAG 引擎，中文文档解析强 |
| [milvus-io/milvus](https://github.com/milvus-io/milvus) | 46k | 分布式向量库，十亿级 |
| [facebookresearch/faiss](https://github.com/facebookresearch/faiss) | 41k | 向量检索算法库，本地首选 |
| [qdrant/qdrant](https://github.com/qdrant/qdrant) | 35k | Rust 实现，过滤能力强 |
| [chroma-core/chroma](https://github.com/chroma-core/chroma) | 29k | 轻量，原型开发最快 |
| [Cinnamon/kotaemon](https://github.com/Cinnamon/kotaemon) | 26k | 开箱即用的文档问答 UI |

### ⑨ 浏览器与电脑操作（Computer Use）
| 项目 | star | 定位 |
|---|---|---|
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | 117k | 让 LLM 直接操作浏览器，当前最热 |
| [microsoft/playwright](https://github.com/microsoft/playwright) | 97k | 底层浏览器自动化，事实标准 |
| [microsoft/OmniParser](https://github.com/microsoft/OmniParser) | 26k | 截图转可交互元素，GUI 理解基础 |
| [browserbase/stagehand](https://github.com/browserbase/stagehand) | 26k | AI 驱动的浏览器操作 SDK |
| [kortix-ai/suna](https://github.com/kortix-ai/suna) | 20k | 开源通用 AI 助理 |
| [bytedance/UI-TARS](https://github.com/bytedance/UI-TARS) | 12k | 字节端到端 GUI Agent 模型 |

### ⑩ 编码智能体
| 项目 | star | 定位 |
|---|---|---|
| [anthropics/claude-code](https://github.com/anthropics/claude-code) | 150k | 终端编码 Agent 标杆 |
| [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) | 107k | 开源 CLI Agent |
| [All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands) | 90k | 开源自主软件工程 Agent |
| [gpt-engineer-org/gpt-engineer](https://github.com/gpt-engineer-org/gpt-engineer) | 55k | 自然语言生成整个代码库 |
| [Aider-AI/aider](https://github.com/Aider-AI/aider) | 49k | 终端内结对编程，diff 式改代码 |
| [SWE-agent/SWE-agent](https://github.com/SWE-agent/SWE-agent) | 21k | 自动修 GitHub Issue，学术影响力大 |
| [princeton-nlp/SWE-bench](https://github.com/princeton-nlp/SWE-bench) | 6k | 编码 Agent 评测基准，**评估必看** |

### ⑪ 平台与工作流
| 项目 | star | 定位 |
|---|---|---|
| [n8n-io/n8n](https://github.com/n8n-io/n8n) | 207k | 可视化自动化 + AI 节点 |
| [langgenius/dify](https://github.com/langgenius/dify) | 158k | LLM 应用开发平台，中文生态最好 |
| [FlowiseAI/Flowise](https://github.com/FlowiseAI/Flowise) | 55k | 拖拽式 LangChain |
| [eosphoros-ai/DB-GPT](https://github.com/eosphoros-ai/DB-GPT) | 20k | 数据库场景 Agent |
| [microsoft/agent-lightning](https://github.com/microsoft/agent-lightning) | 19k | Agent 强化学习训练框架 |
| [AgentOps-AI/agentops](https://github.com/AgentOps-AI/agentops) | 5.9k | Agent 可观测与调试 |

### ⑫ 数据获取与文档解析
| 项目 | star | 定位 |
|---|---|---|
| [Firecrawl/firecrawl](https://github.com/Firecrawl/firecrawl) | 190k | 网页转 LLM 友好格式 |
| [microsoft/markitdown](https://github.com/microsoft/markitdown) | 189k | 万物转 Markdown |
| [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai) | 85k | LLM 友好爬虫 |
| [docling-project/docling](https://github.com/docling-project/docling) | 69k | 复杂 PDF/表格结构化解析 |
| [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher) | 30k | 自动化研究报告生成 |
| [dzhng/deep-research](https://github.com/dzhng/deep-research) | 20k | 极简深度研究 Agent |

### ⑬ 模型服务与微调
| 项目 | star | 定位 |
|---|---|---|
| [vllm-project/vllm](https://github.com/vllm-project/vllm) | 93k | 高吞吐推理引擎，部署必用 |
| [unslothai/unsloth](https://github.com/unslothai/unsloth) | 78k | 单卡微调加速 2-5 倍 |
| [hiyouga/LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory) | 75k | 一站式微调，中文友好 |
| [BerriAI/litellm](https://github.com/BerriAI/litellm) | 61k | 100+ 模型统一网关，多模型切换必备 |
| [sgl-project/sglang](https://github.com/sgl-project/sglang) | 37k | 结构化生成场景性能强 |

---

## 三、交叉地带：具身 Agent（3 分支）

这是你两个方向真正的交汇点，也是最有差异化的能力区。

### ① 语言驱动机器人（论文线，均无开源仓库）
- **SayCan**：LLM 负责"能做什么"，可行性打分负责"做得到吗"
- **PaLM-E**：把感知、语言、控制塞进同一个大模型
- **Code as Policies**：用生成的代码表达策略，天然支持组合与复用
- **VoxPoser**：LLM 生成 3D 空间价值图，再做运动规划
- **Inner Monologue**：把执行结果反馈回语言，形成闭环

### ② Agent 能力 × 机器人
| 复用项 | 来源 | 在机器人上的作用 |
|---|---|---|
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | 91k | 把机器人技能（抓取/移动/拍照）封装成标准工具 |
| [mem0ai/mem0](https://github.com/mem0ai/mem0) | 67k | 跨会话记住环境布局与用户偏好 |
| [OpenGVLab/InternVL](https://github.com/OpenGVLab/InternVL) | 10k | 场景理解与目标定位的感知底座 |
| 概念 | — | LLM Planner + 技能库：高层规划与低层控制解耦 |
| 概念 | — | Reflexion 模式：失败后反思并重试 |

### ③ 融合学习路线（建议顺序）
1. **第 1 步**：RL + 仿真地基 —— Gymnasium / MuJoCo / Isaac Lab
2. **第 2 步**：跑通一个模仿学习 Demo —— LeRobot / Diffusion Policy
3. **第 3 步**：微调或部署一个开源 VLA —— OpenVLA / openpi
4. **第 4 步**：学 Agent 范式与 MCP 协议 —— LangGraph / MCP
5. **第 5 步**：把机器人技能封装成 MCP 工具
6. **第 6 步**：做「语言 → 规划 → 执行 → 反馈」完整闭环

---

## 四、12 周行动计划（建议）

| 周次 | 具身线 | Agent 线 | 产出 |
|---|---|---|---|
| 1-2 | 读《Embodied-AI-Guide》+ 跑通 MuJoCo | 读 ReAct 论文 + 写最小 Agent | 环境跑通 + 一个能调工具的 Agent |
| 3-4 | SB3 跑 PPO / SAC | 学 LangGraph 状态机 | 两个 Demo |
| 5-6 | 用 LeRobot 复现一个操作任务 | 接入 MCP，写自己的 MCP Server | 一个真机/仿真操作 Demo |
| 7-8 | 跑通 OpenVLA 推理 + 微调 Octo | 加记忆层（mem0）与 RAG | VLA 微调结果 |
| 9-10 | 学 π0 / GR00T 架构，读论文 | 多 Agent 协作（CrewAI / AutoGen） | 架构笔记 |
| 11-12 | **交叉项目**：语言指令 → LLM 规划 → VLA 执行 → 反馈重试 | | 一个完整具身 Agent Demo |

---

## 五、避坑提示

1. **不要一上来就选框架**。先想清楚"这个任务真的需要 Agent 吗"，很多需求单次调用 + 串联就够了。
2. **具身不要只学模型**。仿真、数据、运控三个环节任一短板都会让模型跑不起来。
3. **VLA 的数据比模型更关键**。同样架构，数据质量和配比差异带来的效果差距远大于模型改动。
4. **star 数 ≠ 适合你**。AutoGPT 188k 但工程可用性一般；Octo 只有 1.8k 却是很好的学习基线。
5. **WAM 暂时不要投入太多**。开源可复现资源稀缺，等生态成熟。
6. **两个方向的共同底座是"评测"**。具身看 ManiSkill / LIBERO / SimplerEnv，Agent 看 SWE-bench，没有评测就没有迭代。

---

*star 数据抓取时间：2026-10-10 · 数据源：GitHub via shields.io*
