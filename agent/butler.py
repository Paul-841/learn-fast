#!/usr/bin/env python3
"""Learn Fast Butler · 学习管家 —— 常驻定时版：每天把到期复习题收集成一页"今日复习"

它做的事：扫描 learn-fast-logs/（教练日志）和 learn-fast-research/（研究员产出），
找出所有"今天到期"的复习项，把对应提取问题汇编成一页——问题在前、答案在最后
（先答后看，提取练习）。纯本地、零 Key、零联网、不碰 shell：最小权限，天生安全。

用法：
  python agent/butler.py                  # 扫描当前目录，生成 learn-fast-today/今日复习.md
  python agent/butler.py --root D:\学习   # 指定日志所在目录（默认当前目录）
  python agent/butler.py --install-task   # 注册 Windows 每日 08:00 计划任务（自动记住当前目录）
  python agent/butler.py --remove-task    # 删除计划任务
  python agent/butler.py --selftest
"""
import argparse
import os
import re
import subprocess
import sys
from datetime import date

TASK_NAME = "LearnFastButler"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def due_dates(text):
    """抠出复习日期：'下次复习：2026-10-27' / '| 第 1 次 | 2026-11-21 |' / '第1次 2026-11-20'"""
    out = set()
    out |= {m for m in re.findall(r"下次复习[：:]\s*(\d{4}-\d{2}-\d{2})", text)}
    out |= {m for m in re.findall(r"第\s*\d+\s*次\s*\|?\s*(\d{4}-\d{2}-\d{2})", text)}
    return out


def qa_pairs(text):
    """研究员风格 Q:/A: 优先；退回教练日志的数字编号问题。"""
    out = []
    qs = re.findall(r"^\s*(?:Q|问题)\s*[：:]\s*(.+)$", text, re.M)
    ans = re.findall(r"^\s*A\s*[：:]\s*(.+)$", text, re.M)
    out = [(q, ans[i] if i < len(ans) else "（对照原文核对）") for i, q in enumerate(qs)]
    if not out:
        out = [(m, "（合书回忆后，对照原文核对）")
               for m in re.findall(r"^\s*\d+\s*[、.．)]\s*(.+)$", text, re.M)]
    return out


def collect(root, today: str):
    topics = []
    logs = os.path.join(root, "learn-fast-logs")
    research = os.path.join(root, "learn-fast-research")
    if os.path.isdir(logs):
        for f in sorted(os.listdir(logs)):
            if not f.endswith(".md"):
                continue
            text = read(os.path.join(logs, f))
            due = sorted(d for d in due_dates(text) if d <= today)
            if due:
                topics.append({"name": f[:-3], "kind": "教练日志", "due": due[-1], "qa": qa_pairs(text)})
    if os.path.isdir(research):
        for d in sorted(os.listdir(research)):
            sub = os.path.join(research, d)
            mapf = os.path.join(sub, "学习地图.md")
            if not os.path.isdir(sub) or not os.path.exists(mapf):
                continue
            due = sorted(x for x in due_dates(read(mapf)) if x <= today)
            if not due:
                continue
            qf = os.path.join(sub, "提取问题.md")
            qa = qa_pairs(read(qf)) if os.path.exists(qf) else []
            topics.append({"name": d, "kind": "研究员产出", "due": due[-1], "qa": qa})
    return topics


def build_md(topics, today: str):
    head = [f"# 今日复习 · {today}", "",
            f"到期主题 {len(topics)} 个。规则：**先答后看**，答案统一在最后一页。", ""]
    body, answers, n = [], [], 0
    for t in topics:
        body += [f"## {t['name']}（{t['kind']} · 最近到期 {t['due']}）", ""]
        if t["qa"]:
            for q, a in t["qa"]:
                n += 1
                body.append(f"{n}. {q}")
                answers.append(f"{n}. {a}")
        else:
            body.append("（今日到期但没有现成问题：合上材料，凭记忆复述这个主题的结构和要点，再对照原文核对。）")
        body.append("")
    return "\n".join(head + body + ["---", "", "# 答案区（全部答完再看）", ""] + answers + [""])


def install_task(root):
    cmd = ["schtasks", "/create", "/tn", TASK_NAME, "/tr",
           f'"{sys.executable}" "{os.path.abspath(__file__)}" --root "{root}"',
           "/sc", "daily", "/st", "08:00", "/f"]
    subprocess.run(cmd, check=True)
    print(f"✓ 已注册每日 08:00 计划任务 {TASK_NAME}（监控目录：{root}）")
    print("  产出位置：%s" % os.path.join(root, "learn-fast-today", "今日复习.md"))


def remove_task():
    subprocess.run(["schtasks", "/delete", "/tn", TASK_NAME, "/f"], check=True)
    print(f"✓ 已删除计划任务 {TASK_NAME}")


def main():
    ap = argparse.ArgumentParser(description="Learn Fast 学习管家：每日到期复习题汇编")
    ap.add_argument("--root", default=os.getcwd(), help="日志所在目录（默认当前目录）")
    ap.add_argument("--install-task", action="store_true", help="注册 Windows 每日计划任务")
    ap.add_argument("--remove-task", action="store_true", help="删除计划任务")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        t = "下次复习：2026-10-27（间隔 3 天）\n| 第 1 次 | 2026-11-21 | 隔27天 |\n第2次 2026-12-05"
        assert due_dates(t) == {"2026-10-27", "2026-11-21", "2026-12-05"}
        assert qa_pairs("Q: 什么是间隔？\nA: 10-20%规则")[0] == ("什么是间隔？", "10-20%规则")
        assert qa_pairs("1、装饰器等价于什么？")[0][0] == "装饰器等价于什么？"
        print("selftest OK")
        return
    if a.remove_task:
        return remove_task()
    if a.install_task:
        return install_task(os.path.abspath(a.root))
    today = date.today().isoformat()
    topics = collect(a.root, today)
    outdir = os.path.join(a.root, "learn-fast-today")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "今日复习.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(build_md(topics, today))
    if not topics:
        print(f"今天（{today}）没有到期复习项。文件已写到 {out}")
        print("提示：先跑 learning_coach.py 或 researcher.py 产生学习内容，管家才有东西可收。")
    else:
        total = sum(len(t["qa"]) for t in topics)
        print(f"今天（{today}）到期 {len(topics)} 个主题，共 {total} 个问题 → {out}")
        for t in topics:
            print(f"  - {t['name']}（{t['kind']}，到期 {t['due']}，{len(t['qa'])} 题）")


if __name__ == "__main__":
    main()
