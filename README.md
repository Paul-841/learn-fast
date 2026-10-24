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

### 幻灯片

`deck/` 里的 13 页 PPT 本身就是方法论的示范：第 2 页先给全景图（框架先行）、每页一个视觉焦点（双重编码）、结尾三道自测题（提取练习）。可直接用于分享与教学。

## 核心心法

**学得越"费劲"，记得越牢；读得越"流畅"，忘得越快。**（Bjork 合意困难理论）
你的学习体感是反的——记住这一点，就赢过大多数人。

## English TL;DR

An evidence-based learning method packaged three ways: an Agent Skill for coding assistants (SKILL.md), a standalone system prompt that turns any chatbot into a retrieval-first learning coach (agent/), and a 13-slide deck. Core findings from 12+ papers: retrieval practice beats rereading (g≈0.61), optimal review gap ≈ 10–20% of retention interval, interleaved practice 72% vs blocked 38%, framework-before-details doubles recall, and memory is trainable (40h of method-of-loci training reaches athlete level). The skill is *forbidden* from giving summaries without retrieval questions — that constraint is the product.

## License

MIT — 自取、魔改、二次发布均可，注明出处即可。如果它帮到了你，欢迎 star / 分享给还在划重点重读的朋友。
