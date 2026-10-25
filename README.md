# Learn Fast — 拉开差距的从来不是记忆力

一套**基于认知科学证据**的学习方法论，打包成三种形态：给 AI 编程助手的**技能（Skill）**、给任意聊天 AI 的**智能体系统提示词**、给人类看的**幻灯片**。全部内容源自 12+ 篇核心研究（Psychological Science / Science / Neuron / Psychological Bulletin 等），每个数字都有出处。

> 国际象棋大师看真实棋盘 5 秒能复盘 20+ 个子，看随机棋盘就和普通人没差别（Chase & Simon, 1973）。
> 拉开差距的不是记忆力，是**组块库（结构）**和**提取方式（练习）**——两者都可训练。

## 科学依据速览

| 发现 | 关键数字 | 出处 |
|---|---|---|
| 自测远胜重读 | 元分析 g≈0.61（272 项研究） | [Adesope et al. 2017](https://eric.ed.gov/?id=EJ1141817) |
| 短期错觉：5 分钟后重读占优，一周后自测反超（83%→40% vs 71%→56%） | — | [Roediger & Karpicke 2006](https://journals.sagepub.com/doi/10.1111/j.1467-9280.2006.01693.x) |
| 最优复习间隔 ≈ 保留期 × 10–20% | 1 年后要会 → 每 1–2 月一次 | [Cepeda et al. 2006](https://pubmed.ncbi.nlm.nih.gov/16719566) |
| 混着做题 vs 分块刷题 | 真实课堂 RCT：72% vs 38% | [Rohrer et al. 2015](https://gwern.net/doc/psychology/spaced-repetition/2014-rohrer.pdf) |
| 10 种学习法只有 2 种高效用（练习测试、间隔重复） | 重读/划线/摘录为低效用 | [Dunlosky et al. 2013](https://journals.sagepub.com/doi/abs/10.1177/1529100612453266) |
| 先给框架再给细节，回忆量翻倍以上 | 同一段文字只差一个"标题" | Bransford & Johnson 1972 |
| 40 小时记忆宫殿训练，普通人达记忆运动员水平 | 脑网络随之重塑 | [Dresler et al. 2017, Neuron](https://www.sciencedirect.com/science/article/pii/S0896627317300879) |

完整引用与解读见 [references/evidence.md](references/evidence.md)。

## 仓库内容

```
learn-fast/
├── SKILL.md                  # 技能定义（ZCode / Claude 等支持 Agent Skills 的助手）
├── references/evidence.md    # 全部证据与引用
├── scripts/review_schedule.py# 复习排期计算器（10–20% 规则，纯标准库）
├── agent/learning-coach.md   # 智能体系统提示词（任何聊天 AI 可用，无需工具）
├── agent/learning_coach.py   # ★ 程序型智能体：可独立运行的学习教练（零依赖）
├── agent/researcher.py       # ★★ 自主研究智能体：规划→搜索→反思→成稿（同款 Agent 循环）
├── agent/butler.py           # ★ 学习管家：定时收集到期复习题，生成"今日复习"（零Key零联网）
├── docs/分享文案.md           # 转发给朋友/发帖用的现成文案
└── deck/                     # 13 页幻灯片（pptx + pdf）
```

## 三种用法

### 1️⃣ 作为技能装进你的 AI 助手（推荐）

把本仓库 clone 或复制到技能目录（以 ZCode / Claude Code 为例）：

```bash
git clone https://github.com/<你的用户名>/learn-fast.git
# 个人级（所有项目可用）：
mkdir -p ~/.agents/skills && cp -r learn-fast ~/.agents/skills/
# 或项目级：cp -r learn-fast <项目>/.agents/skills/
```

之后对你的 AI 说「我要学 X」「帮我记住 X」「给我排个复习计划」，技能自动触发：先搭框架 → 每块学完立刻自测 → 按 10–20% 规则排下次复习 → 建学习日志跟踪掌握情况。**它会被禁止给你"只有总结没有问题"的输出**——这正是它有效的机制。

### 2️⃣ 作为智能体（任何聊天 AI：ChatGPT / GLM / Gemini / …）

把 [agent/learning-coach.md](agent/learning-coach.md) 的全部内容粘贴为系统提示词（或对话第一条消息），AI 即变成一个"提取优先"的学习教练：拒绝陪你无效重读，每块内容后必考你，帮你排间隔。

### 3️⃣ 命令行排复习计划

```bash
python scripts/review_schedule.py --goal-days 180
# 输出：第 1 次 2026-11-20（27 天后）→ 第 2 次 2027-01-04（45 天后）→ …
```

### 4️⃣ 运行真正的智能体程序（程序型 Agent）

`agent/learning_coach.py` 是一个**可独立运行**的学习教练智能体：LLM 是大脑，程序提供工作循环、学习日志（记忆）和复习排期（工具）——机制与大型 Agent 项目同款，单文件、零依赖、100 余行。

```bash
# 任意 OpenAI 兼容接口；默认智谱旗舰 GLM-5.3（模型不可用自动降级 GLM-5.3-Flash，可 env 覆盖）
export LEARN_FAST_API_KEY=你的key        # PowerShell: $env:LEARN_FAST_API_KEY="你的key"
python agent/learning_coach.py
# 会话内：/quiz 提取练习 · /schedule 30 排 30 天复习计划 · /log 看日志 · /exit
```

回访时它会读取上次的学习日志，**先考你上次的题**再教新内容——间隔 + 提取，两条最硬的证据都固化进了代码。

### 5️⃣ 自主研究智能体（plan → search → reflect → write）

`agent/researcher.py` 是标准意义的自主智能体循环：给它一个主题，它自己**拆解子问题 → 联网搜索抓正文 → 反思证据缺口并补搜 → 产出三份材料**（学习地图 / 20 道提取问题 / Anki CSV）。搜索走智谱 web-search-pro（与模型同一个 Key），自动降级 DuckDuckGo / Wikipedia。

```bash
export LEARN_FAST_API_KEY=你的key
python agent/researcher.py "SQL 入门" --days 90
# 产出 learn-fast-research/SQL-入门-日期/ 下的三个文件，含复习计划与资料来源
```

### 6️⃣ 学习管家（常驻定时，OpenClaw 式定时任务的微缩版）

`agent/butler.py`：每天扫描教练日志和研究员产出，把**今天到期**的复习题汇编成一页《今日复习》（问题在前、答案在最后——先答后看）。纯本地、零 Key、零联网、不碰 shell：最小权限，天生安全。

```bash
python agent/butler.py                # 手动跑一次，生成 learn-fast-today/今日复习.md
python agent/butler.py --install-task # 注册 Windows 每日 08:00 计划任务，之后全自动
python agent/butler.py --remove-task  # 不想要了就删
```

至此形成闭环：**researcher 生产地图和题目 → coach 日常教练并记日志 → butler 每天早上把到期的端到你面前**。

### 装到另一台电脑（3 分钟，无需命令行）

1. **装 Python**：python.org 下载安装（勾选 Add to PATH）
2. **拿项目**：本仓库页面点绿色 `Code` → `Download ZIP` → 解压（会 git 的直接 clone 也行）
3. **双击 `learn.bat`**：菜单里选 3（今日复习）/ 4（排计划）**不用任何 Key**；选 1（教练）/ 2（研究员）时按提示粘贴一次智谱 API Key（open.bigmodel.cn 免费注册）

### 幻灯片

`deck/` 里的 13 页 PPT 本身就是方法论的示范：第 2 页先给全景图（框架先行）、每页一个视觉焦点（双重编码）、结尾三道自测题（提取练习）。可直接用于分享与教学。

## 核心心法

**学得越"费劲"，记得越牢；读得越"流畅"，忘得越快。**（Bjork 合意困难理论）
你的学习体感是反的——记住这一点，就赢过大多数人。

## English TL;DR

An evidence-based learning method packaged three ways: an Agent Skill for coding assistants (SKILL.md), a standalone system prompt that turns any chatbot into a retrieval-first learning coach (agent/), and a 13-slide deck. Core findings from 12+ papers: retrieval practice beats rereading (g≈0.61), optimal review gap ≈ 10–20% of retention interval, interleaved practice 72% vs blocked 38%, framework-before-details doubles recall, and memory is trainable (40h of method-of-loci training reaches athlete level). The skill is *forbidden* from giving summaries without retrieval questions — that constraint is the product.

## License

MIT — 自取、魔改、二次发布均可，注明出处即可。如果它帮到了你，欢迎 star / 分享给还在划重点重读的朋友。
