#!/usr/bin/env python3
"""srs.py —— SM-2 简化版间隔重复引擎（Anki 的心脏），纯标准库，被 butler.py 调用。

核心思想：每张卡有 interval（当前间隔天数）与 ease（难易系数）。
评分越差 → ease 变小、间隔缩短、明天再见；评分越好 → 间隔按 ease 倍增。
答错的卡永远比答对的卡更早回来——这就是"反馈闭环"。
"""
import json
import os
from datetime import date, timedelta


def load(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"cards": {}}


def save(path, store):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=1)


def add(store, front, back, today):
    """新卡（按题目去重）默认今天到期。返回是否真的新增。"""
    k = front.strip()
    if k in store["cards"]:
        return False
    store["cards"][k] = {"front": front, "back": back, "due": today,
                         "interval": 0, "ease": 2.5, "reps": 0, "lapses": 0}
    return True


def due_cards(store, today):
    return [c for c in store["cards"].values() if c["due"] <= today]


def grade(card, g, today):
    """g ∈ {1,2,3,4}：1 没答上 / 2 费劲 / 3 顺利 / 4 秒答。原地修改并返回。"""
    if g <= 1:
        card["reps"] = 0
        card["lapses"] += 1
        card["interval"] = 1
        card["ease"] = max(1.3, card["ease"] - 0.2)
    else:
        first = {2: 1, 3: 1, 4: 3}
        second = {2: 3, 3: 6, 4: 9}
        if card["reps"] == 0:
            card["interval"] = first[g]
        elif card["reps"] == 1:
            card["interval"] = second[g]
        else:
            card["interval"] = max(1, round(card["interval"] * card["ease"] *
                                            {2: 0.8, 3: 1.0, 4: 1.3}[g]))
        card["reps"] += 1
        if g == 2:
            card["ease"] = max(1.3, card["ease"] - 0.15)
        if g == 4:
            card["ease"] = min(3.5, card["ease"] + 0.15)
    card["due"] = (date.fromisoformat(today) + timedelta(days=card["interval"])).isoformat()
    return card


if __name__ == "__main__":
    # 引擎自测：三种命运的卡
    c = {"front": "Q1", "back": "A1", "due": "2026-10-25", "interval": 0, "ease": 2.5, "reps": 0, "lapses": 0}
    grade(c, 3, "2026-10-25"); assert c["interval"] == 1 and c["due"] == "2026-10-26"
    grade(c, 3, "2026-10-26"); assert c["interval"] == 6 and c["due"] == "2026-11-01"
    grade(c, 3, "2026-11-01"); assert c["interval"] == round(6 * 2.5) and c["reps"] == 3
    bad = dict(c, interval=15, reps=3)
    grade(bad, 1, "2026-11-01"); assert bad["interval"] == 1 and bad["ease"] < 2.5 and bad["lapses"] == 1
    good = dict(c, interval=15, reps=3, ease=2.5)
    grade(good, 4, "2026-11-01"); assert good["ease"] == 2.65 and good["interval"] == round(15 * 2.5 * 1.3)
    print("srs selftest OK")
