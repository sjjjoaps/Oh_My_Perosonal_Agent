# 数字同事（QQ 群聊 Personal Agent）

常驻 QQ 群的数字同事，P0 阶段先跑通核心闭环。

## 当前状态（P0 已跑通）

```
群 @ 消息 → ingress(去重/合并/会话队列) → orchestrator(触发路由/上下文)
  → LLM(qwen3.7-flash) → reply(emoji+截断) → 渠道回复
  → Trace JSONL 落盘（runs/traces/YYYYMMDD/）
```

## 环境

- Python：conda `pytorch` 环境（`F:\Anaconda\envs\pytorch\python.exe`）
- 依赖：`litellm pyyaml python-dotenv pydantic`
- 凭据：`.env`（API_KEY / BASE_URL / QWEN_MODEL / QQ app_ID / app_SECRET）

## 跑离线冒烟测试

```powershell
F:\Anaconda\envs\pytorch\python.exe scripts\smoke_test.py
```

会构造一条 mock 群 @ 消息，真实调用 Qwen，回复打印到控制台，Trace 落到 `runs/traces/`。

## 目录

- `src/channel/` — 渠道（mock 离线跑通 / qq botpy 骨架待沙箱联调）
- `src/ingress/` — 去重 / 连发合并 / 会话队列 / WorkerPool
- `src/orchestrator/` — 触发路由 / 上下文构建 / 回复格式化 / 主流程
- `src/llm/` — litellm 封装（路由占位）
- `src/tracing/` — Trace JSONL 落盘
- `config/` — settings.yaml / models.yaml
- `scripts/` — smoke_test.py

## 后续里程碑

P1 记忆系统 → P2 本地命令 → P3 澄清机制 → P4 RAG → P5 评估自动化
