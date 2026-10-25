#!/usr/bin/env python3
"""Learn Fast Coach —— 可运行的学习教练智能体（纯 Python 标准库，零依赖）

这就是一个"程序型智能体"的最小完整实现：
  AI 大脑（任意 OpenAI 兼容接口）+ 工作循环 + 学习日志（记忆）+ 复习排期（工具）。

用法：
  1. 拿一个 API Key（智谱 open.bigmodel.cn 有免费模型；或任何 OpenAI 兼容服务）
  2. 设置环境变量：
       Windows PowerShell:  $env:LEARN_FAST_API_KEY="你的key"
       macOS / Linux:       export LEARN_FAST_API_KEY=你的key
     可选：LEARN_FAST_BASE_URL（默认智谱）、LEARN_FAST_MODEL（默认旗舰 glm-5.3，可改 glm-5.3-flash 免费）
  3. python agent/learning_coach.py

会话内命令：/new 开新主题 · /quiz 提取练习 · /log 看日志 · /schedule N 排复习 · /exit 退出
"""
import json
import os
import re
import sys
import urllib.request
from datetime import date, timedelta

BASE_URL = os.environ.get("LEARN_FAST_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
MODEL = os.environ.get("LEARN_FAST_MODEL", "glm-5.3")
API_KEY = os.environ.get("LEARN_FAST_API_KEY", "")
LOGS_DIR = os.path.join(os.getcwd(), "learn-fast-logs")

SYSTEM_PROMPT = """你是一名基于认知科学证据的学习教练。用户记住多少，取决于你让他成功回忆了多少次，而不是你讲得多清楚。

规则：
1. 先框架后细节：任何主题先给 3-7 块结构（地图），确认后再从第一块教起。
2. 每讲完一块，立即出 3-5 个提取问题（优先"凭记忆说说X是什么"的自由回忆型），等用户回答后再反馈补漏，回答前不给提示。
3. 用户要总结可以，但必须附带至少 3 个自测题——没有提取的输出是无效输出。
4. 复习间隔按"保留期 × 10-20%"排（一周后要用的隔 1 天，一年后要用的每 1-2 月一次）。
5. 练习题混合不同类型出，偶尔问"这题该用哪个方法、为什么"。
6. 记名字/清单等无结构信息：现场生成记忆术（显著特征→具体夸张图像→互动绑定）。
7. 用户说"记性不好"：告诉他记忆可训练（40 小时记忆宫殿训练即达运动员水平，Dresler 2017），然后照常执行。
8. 直接、鼓励但不客套。把想偷懒重读的用户拉回提取练习。
9. 每轮回复保持一段对话的量，不要一次倾倒所有内容。"""


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text).strip("-")
    return s[:30] or "topic"


def chat(messages, temperature=0.7) -> str:
    if not API_KEY:
        sys.exit("× 请先设置环境变量 LEARN_FAST_API_KEY（智谱 open.bigmodel.cn 或任意 OpenAI 兼容服务）")
    req = urllib.request.Request(
        BASE_URL.rstrip("/") + "/chat/completions",
        data=json.dumps({"model": MODEL, "messages": messages, "temperature": temperature}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + API_KEY},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


def build_schedule(goal_days: int, reviews: int = 5):
    """10-20% 规则：首间隔 = 保留期×15%，每次 ×1.8 封顶 ×25%（Cepeda et al. 2006/2008）"""
    first = max(1, round(goal_days * 0.15))
    cap = max(1, round(goal_days * 0.25))
    intervals, gap, total = [], first, 0
    while len(intervals) < reviews and total < goal_days * 0.85:
        intervals.append(gap)
        total += gap
        gap = min(round(gap * 1.8), cap)
    out, day = [], date.today()
    for i, g in enumerate(intervals, 1):
        day = day + timedelta(days=g)
        out.append((i, day, g))
    return out


def log_file(topic: str) -> str:
    os.makedirs(LOGS_DIR, exist_ok=True)
    return os.path.join(LOGS_DIR, slugify(topic) + ".md")


def append_log(path: str, role: str, text: str):
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n## {role} · {date.today().isoformat()}\n\n{text}\n")


def run():
    print("═" * 46)
    print(" Learn Fast Coach · 学习教练智能体")
    print(f" 模型: {MODEL} @ {BASE_URL}")
    print(" 命令: /new /quiz /log /schedule N /exit")
    print("═" * 46)
    topic = input("这次学什么主题？ ").strip()
    while not topic or topic.startswith("/"):
        topic = input("请输入主题（例如：SQL 入门）：").strip()
    path = log_file(topic)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"这次我要学：{topic}。请开始你的教练流程。"},
    ]
    if os.path.exists(path):
        print(f"↩ 发现历史日志 {path}，本次先从上次的提取练习开始。")
        messages.append({"role": "user", "content": "这是回访。请先把上次教过的内容出 3 个提取问题考我，一次一个。"})
    else:
        append_log(path, "system", f"# 学习日志：{topic}\n\n创建于 {date.today().isoformat()}")
    print("(输入 /exit 退出；/schedule 30 排 30 天保留期的复习计划)\n")
    while True:
        try:
            user = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            user = "/exit"
        if not user:
            continue
        if user == "/exit":
            print("记住：学完当天睡够 = 免费复习一次。下次直接再运行本程序，会从提取练习开始。")
            break
        if user == "/new":
            return run()
        if user == "/log":
            with open(path, encoding="utf-8") as f:
                print("─" * 46, f.read(), "─" * 46, sep="\n")
            continue
        m = re.match(r"/schedule\s+(\d+)", user)
        if m:
            rows = build_schedule(int(m.group(1)))
            plan = "\n".join(f"  第{i}次  {d.isoformat()}（隔{g}天）" for i, d, g in rows)
            print(f"─" * 46 + f"\n保留期 {m.group(1)} 天的复习计划：\n{plan}\n" + "─" * 46)
            append_log(path, "system", f"复习计划（保留期 {m.group(1)} 天）：\n{plan}")
            continue
        if user == "/quiz":
            user = "现在开始提取练习：把本主题至今最重要的 3-5 个问题抛给我，一次一个，等我回答后再继续。"
            print("(进入提取练习)")
            messages.append({"role": "user", "content": user})
        else:
            messages.append({"role": "user", "content": user})
        try:
            reply = chat(messages)
        except Exception as e:
            print(f"× 调用失败：{e}\n  检查 API Key / BASE_URL / MODEL 环境变量。")
            messages.pop()
            continue
        messages.append({"role": "assistant", "content": reply})
        append_log(path, "user", user)
        append_log(path, "coach", reply)
        print("\n教练> " + reply + "\n")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        rows = build_schedule(180)
        assert rows[0][2] == 27 and len(rows) >= 3
        assert slugify("Python 装饰器!") == "Python-装饰器"
        print("selftest OK:", "; ".join(f"{d.isoformat()}(+{g}d)" for _, d, g in rows))
    else:
        run()
