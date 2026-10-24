#!/usr/bin/env python3
"""复习排期计算器 —— 基于"最优间隔 ≈ 保留期 × 10–20%"规则（Cepeda et al. 2006/2008）。

用法:
  python review_schedule.py --goal-days 180
  python review_schedule.py --goal-days 30 --start 2026-11-01
  python review_schedule.py --goal-days 365 --reviews 6
输出: 一张 Markdown 复习时间表（日期 + 间隔 + 依据）。
"""
import argparse
from datetime import date, timedelta


def build_schedule(goal_days: int, reviews: int, start: date):
    """扩展间隔：首间隔 = 保留期×15%（至少 1 天），每次 ×1.8，封顶 保留期×25%。"""
    first = max(1, round(goal_days * 0.15))
    cap = max(1, round(goal_days * 0.25))
    intervals, gap, total = [], first, 0
    while len(intervals) < reviews and total < goal_days * 0.85:
        intervals.append(gap)
        total += gap
        gap = min(round(gap * 1.8), cap)
    rows, day = [], start
    for i, gap in enumerate(intervals, 1):
        day = day + timedelta(days=gap)
        rows.append((i, day, gap))
    return rows


def main():
    ap = argparse.ArgumentParser(description="10-20% 规则复习排期")
    ap.add_argument("--goal-days", type=int, required=True, help="保留期（多少天后还要会）")
    ap.add_argument("--start", type=str, default=None, help="开始日期 YYYY-MM-DD（默认今天）")
    ap.add_argument("--reviews", type=int, default=5, help="复习次数（默认 5）")
    a = ap.parse_args()
    start = date.fromisoformat(a.start) if a.start else date.today()
    rows = build_schedule(a.goal_days, a.reviews, start)
    print(f"| 次序 | 复习日期 | 距上次 |")
    print(f"|---|---|---|")
    for i, day, gap in rows:
        print(f"| 第 {i} 次 | {day.isoformat()} | {gap} 天 |")
    print(f"\n依据: 最优间隔 ≈ 保留期 × 10–20%（Cepeda et al. 2006/2008）。")
    print(f"保留期 {a.goal_days} 天 → 首间隔 {rows[0][2]} 天。每次复习：先自由回忆，再核对。")


if __name__ == "__main__":
    main()
