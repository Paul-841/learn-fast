#!/usr/bin/env python3
"""Learn Fast Butler · 学习管家 v1.4 —— 到期复习题汇编 + 反馈闭环

扫描 learn-fast-logs/（教练日志）与 learn-fast-research/（研究员产出），
把提取问题导入间隔重复引擎（srs.py，SM-2 简化版），然后：

  python agent/butler.py            # 生成 learn-fast-today/今日复习.md（不互动）
  python agent/butler.py --review   # 逐题作答并自评 1-4，算法自动调整下次间隔

纯本地、零 Key、零联网、不碰 shell：最小权限，天生安全。
"""
import argparse
import os
import re
import subprocess
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srs

TASK_NAME = "LearnFastButler"
GRADES = "1 没答上 / 2 费劲 / 3 顺利 / 4 秒答"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def due_dates(text):
    out = set()
    out |= set(re.findall(r"下次复习[：:]\s*(\d{4}-\d{2}-\d{2})", text))
    out |= set(re.findall(r"第\s*\d+\s*次\s*\|?\s*(\d{4}-\d{2}-\d{2})", text))
    return out


def qa_pairs(text):
    qs = re.findall(r"^\s*(?:Q|问题)\s*[：:]\s*(.+)$", text, re.M)
    ans = re.findall(r"^\s*A\s*[：:]\s*(.+)$", text, re.M)
    out = [(q, ans[i] if i < len(ans) else "（对照原文核对）") for i, q in enumerate(qs)]
    if not out:
        out = [(m, "（合书回忆后，对照原文核对）")
               for m in re.findall(r"^\s*\d+\s*[、.．)]\s*(.+)$", text, re.M)]
    return out


def slug(name):
    return re.sub(r"[^\w\u4e00-\u9fff]+", "-", name).strip("-")[:40] or "topic"


def collect(root):
    """收集主题：{name, kind, qa, due_hint}"""
    topics = []
    logs = os.path.join(root, "learn-fast-logs")
    research = os.path.join(root, "learn-fast-research")
    if os.path.isdir(logs):
        for f in sorted(os.listdir(logs)):
            if f.endswith(".md"):
                text = read(os.path.join(logs, f))
                topics.append({"name": f[:-3], "kind": "教练日志", "qa": qa_pairs(text),
                               "due_hint": "（见复习计划）"})
    if os.path.isdir(research):
        for d in sorted(os.listdir(research)):
            sub = os.path.join(research, d)
            mapf = os.path.join(sub, "学习地图.md")
            if not os.path.isdir(sub) or not os.path.exists(mapf):
                continue
            qf = os.path.join(sub, "提取问题.md")
            due = sorted(due_dates(read(mapf)))
            topics.append({"name": d, "kind": "研究员产出",
                           "qa": qa_pairs(read(qf)) if os.path.exists(qf) else [],
                           "due_hint": due[0] if due else "（见学习地图）"})
    return topics


def srs_file(root, name):
    return os.path.join(root, "learn-fast-logs", slug(name) + ".srs.json")


def sync(root, topics, today):
    """把题目导入各主题的 srs 库（去重），返回 [(topic, store_path, store, new_n)]"""
    result = []
    for t in topics:
        path = srs_file(root, t["name"])
        store = srs.load(path)
        new_n = sum(srs.add(store, q, a, today) for q, a in t["qa"])
        srs.save(path, store)
        result.append((t, path, store, new_n))
    return result


def build_md(rows, today):
    """rows: [(topic, due_cards)] → 今日复习.md"""
    n_topics = len(rows)
    total = sum(len(c) for _, c in rows)
    head = [f"# 今日复习 · {today}", "",
            f"到期主题 {n_topics} 个、共 {total} 题。规则：**先答后看**，答案在最后一页。", ""]
    body, answers, n = [], [], 0
    for t, cards in rows:
        body += [f"## {t['name']}（{t['kind']}）", ""]
        for c in cards:
            n += 1
            body.append(f"{n}. {c['front']}")
            answers.append(f"{n}. {c['back']}")
        body.append("")
    return "\n".join(head + body + ["---", "", "# 答案区（全部答完再看）", ""] + answers + [""])


def review(rows, today):
    """互动模式：逐题作答 → 自评 → 引擎调间隔。EOF/Ctrl-C 随时安全退出。"""
    stats = {"answered": 0, "sum": 0, "stores": {}}
    print(f"\n开始复习（{GRADES}）。随时 Ctrl+C 退出，进度自动保存。\n")
    for t, cards in rows:
        todo = [c for c in cards if c["due"] <= today]
        if not todo:
            continue
        print(f"◆ {t['name']}（{len(todo)} 题）")
        for c in todo:
            try:
                print(f"\n  Q: {c['front']}")
                input("  （心里答完，回车看答案）")
                print(f"  A: {c['back']}")
                while True:
                    g = input(f"  自评 [{GRADES}]: ").strip()
                    if g in ("1", "2", "3", "4"):
                        break
                srs.grade(c, int(g), today)
                stats["answered"] += 1
                stats["sum"] += int(g)
                print(f"  → 间隔 {c['interval']} 天后再见（{c['due']}）")
            except (EOFError, KeyboardInterrupt):
                print("\n（提前结束，已保存）")
                return stats
        print()
    return stats


def install_task(root):
    cmd = ["schtasks", "/create", "/tn", TASK_NAME, "/tr",
           f'"{sys.executable}" "{os.path.abspath(__file__)}" --root "{root}"',
           "/sc", "daily", "/st", "08:00", "/f"]
    subprocess.run(cmd, check=True)
    print(f"✓ 已注册每日 08:00 计划任务 {TASK_NAME}（监控目录：{root}）")


def remove_task():
    subprocess.run(["schtasks", "/delete", "/tn", TASK_NAME, "/f"], check=True)
    print(f"✓ 已删除计划任务 {TASK_NAME}")


def main():
    ap = argparse.ArgumentParser(description="Learn Fast 学习管家 v1.4：到期复习 + 反馈闭环")
    ap.add_argument("--root", default=os.getcwd(), help="日志所在目录（默认当前目录）")
    ap.add_argument("--review", action="store_true", help="逐题作答并自评，算法调整间隔")
    ap.add_argument("--install-task", action="store_true")
    ap.add_argument("--remove-task", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        assert due_dates("下次复习：2026-10-27\n| 第 1 次 | 2026-11-21 | 隔27天 |") == {"2026-10-27", "2026-11-21"}
        assert qa_pairs("Q: 区别？\nA: 分组前后。")[0] == ("区别？", "分组前后。")
        assert slug("SQL 入门/基础") == "SQL-入门-基础"
        store = {"cards": {}}
        assert srs.add(store, "Q", "A", "2026-10-25") and not srs.add(store, "Q", "A", "2026-10-25")
        srs.grade(store["cards"]["Q"], 3, "2026-10-25")
        assert srs.due_cards(store, "2026-10-26")
        print("selftest OK")
        return
    if a.remove_task:
        return remove_task()
    if a.install_task:
        return install_task(os.path.abspath(a.root))
    today = date.today().isoformat()
    topics = collect(a.root)
    if not topics:
        print(f"还没有任何学习记录（{a.root} 下无 learn-fast-logs/ 与 learn-fast-research/）。")
        print("先跑 learning_coach.py 或 researcher.py，或双击 learn.bat 选 1/2。")
        return
    synced = sync(a.root, topics, today)
    rows = [(t, sorted(srs.due_cards(st, today), key=lambda c: c["front"])) for t, _, st, _ in synced]
    rows = [(t, c) for t, c in rows if c]
    outdir = os.path.join(a.root, "learn-fast-today")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "今日复习.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(build_md(rows, today))
    new_total = sum(n for *_, n in synced)
    print(f"今天（{today}）到期 {len(rows)} 个主题、{sum(len(c) for _, c in rows)} 题 → {out}"
          + (f"（新增导入 {new_total} 题）" if new_total else ""))
    for t, c in rows:
        print(f"  - {t['name']}（{t['kind']}，{len(c)} 题）")
    if a.review:
        stats = review(rows, today)
        for t, path, st, _ in synced:
            srs.save(path, st)
        if stats["answered"]:
            print(f"本次答了 {stats['answered']} 题，平均自评 {stats['sum'] / stats['answered']:.1f}。")
            nxt = [c["due"] for _, _, st, _ in synced for c in st["cards"].values()]
            print(f"全部卡片下一最早到期：{min(nxt)}（learn-fast-logs\\*.srs.json 已更新）")


if __name__ == "__main__":
    main()
