#!/usr/bin/env python3
"""Learn Fast Researcher —— 自主研究型学习智能体（plan → search → reflect → write）

给它一个学习主题，它会自己：
  1. 规划：把主题拆成若干检索子问题
  2. 执行：联网搜索 + 抓取网页正文（工具就是它的"手"）
  3. 反思：审视证据够不够，不够就补搜（自主循环）
  4. 成稿：产出三份文件——学习地图 / 提取问题 / Anki 牌组 CSV

零第三方依赖。LLM 走任意 OpenAI 兼容接口（默认智谱 glm-4-flash 免费模型）；
搜索三级降级：智谱 web-search-pro（与模型共用同一个 Key）→ DuckDuckGo → Wikipedia。
（注：直接爬 Bing 会拿到它喂给脚本的假结果，别走那条路。）

用法：
  export LEARN_FAST_API_KEY=你的key      # PowerShell: $env:LEARN_FAST_API_KEY="你的key"
  python agent/researcher.py "SQL 入门" --days 90
  python agent/researcher.py --search "spaced repetition"   # 只测搜索，不耗模型
  python agent/researcher.py --selftest
"""
import argparse
import csv
import html as htmllib
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import date, timedelta

BASE_URL = os.environ.get("LEARN_FAST_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
MODEL = os.environ.get("LEARN_FAST_MODEL", "glm-4-flash")
API_KEY = os.environ.get("LEARN_FAST_API_KEY", "")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

COACH_PROMPT = """你是"Learn Fast 研究员"，产出学习材料时遵守认知科学规则：
- 学习地图：先框架后细节，3-7 块结构，标注每块"为什么值得学"；
- 提取问题：全部是自由回忆型（"X 是什么/为什么/区别是什么"），附参考答案，不 出选择题；
- Anki 卡：一问一答、答案尽量短；禁止"阅读理解型"废卡。"""


# ---------- HTTP ----------
def http_get(url, timeout=15, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def strip_tags(s: str) -> str:
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", htmllib.unescape(s)).strip()


# ---------- 搜索工具（三级降级） ----------
def search_zhipu(q: str, k: int = 5):
    """智谱 web-search-pro：与 LLM 共用同一个 API Key。返回结构随版本漂移，递归兜底解析。"""
    if not API_KEY:
        raise ValueError("no api key")
    req = urllib.request.Request(
        BASE_URL.rstrip("/") + "/tools",
        data=json.dumps({"tool": "web-search-pro",
                         "messages": [{"role": "user", "content": q}],
                         "stream": False}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + API_KEY})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    hits = []

    def walk(o):
        if isinstance(o, list):
            for it in o:
                if isinstance(it, dict) and (it.get("link") or it.get("url")) and (it.get("title") or it.get("content")):
                    hits.append({"title": str(it.get("title", "")),
                                 "url": str(it.get("link") or it.get("url")),
                                 "snippet": str(it.get("content") or it.get("snippet") or "")[:300]})
                else:
                    walk(it)
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)

    walk(data)
    return hits[:k]


def search_ddg(q: str, k: int = 5):
    data = urllib.parse.urlencode({"q": q}).encode()
    req = urllib.request.Request("https://html.duckduckgo.com/html/", data=data,
                                 headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        page = r.read().decode("utf-8", "ignore")
    out = []
    for m in re.finditer(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', page, re.S):
        url = m.group(1)
        um = re.search(r"[?&]uddg=([^&]+)", url)
        if um:
            url = urllib.parse.unquote(um.group(1))
        out.append({"title": strip_tags(m.group(2)), "url": url, "snippet": ""})
        if len(out) >= k:
            break
    return out


def search_wiki(q: str, k: int = 5):
    api = ("https://zh.wikipedia.org/w/api.php?action=query&format=json&list=search"
           "&srlimit=%d&srsearch=" % k) + urllib.parse.quote(q)
    items = json.loads(http_get(api)).get("query", {}).get("search", [])
    return [{"title": htmllib.unescape(i["title"]),
             "url": "https://zh.wikipedia.org/wiki/" + urllib.parse.quote(i["title"]),
             "snippet": strip_tags(i.get("snippet", ""))[:300]} for i in items]


def web_search(q: str, k: int = 5):
    engines = (("zhipu", search_zhipu), ("ddg", search_ddg), ("wiki", search_wiki))
    for name, fn in engines:
        try:
            hits = fn(q, k)
            if hits:
                print(f"    [search:{name}] {q} → {len(hits)} 条")
                return hits
        except Exception:
            continue
    print(f"    [search:none] {q} → 三级引擎均失败，跳过")
    return []


def fetch_page(url: str, limit: int = 2200) -> str:
    try:
        return strip_tags(http_get(url, timeout=12))[:limit]
    except Exception:
        return ""


# ---------- LLM ----------
def chat(messages, temperature=0.6) -> str:
    if not API_KEY:
        sys.exit("× 请先设置环境变量 LEARN_FAST_API_KEY（智谱 open.bigmodel.cn 或任意 OpenAI 兼容服务）")
    req = urllib.request.Request(
        BASE_URL.rstrip("/") + "/chat/completions",
        data=json.dumps({"model": MODEL, "messages": messages, "temperature": temperature}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + API_KEY})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


def json_block(text: str):
    m = re.search(r"(\{.*\}|\[.*\])", text, re.S)
    if not m:
        raise ValueError("模型未输出 JSON: " + text[:120])
    return json.loads(m.group(1))


# ---------- 排期（10–20% 规则） ----------
def build_schedule(goal_days: int, reviews: int = 5):
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


# ---------- 主流程：plan → search → reflect → write ----------
def research(topic: str, days: int):
    print(f"▶ 主题：{topic}（保留期 {days} 天）")

    print("① 规划：拆解子问题…")
    plan = json_block(chat([
        {"role": "system", "content": "你是研究规划员，只输出 JSON。"},
        {"role": "user", "content":
            f'学习主题：{topic}。面向自学者的入门材料。输出 {{"subquestions": ["...", ...]}}，'
            f'3-6 个必须联网检索才能回答好的子问题（概念边界/核心原理/易错点/学习路径/权威资源）。只输出 JSON。'}]))
    subqs = [str(q) for q in plan.get("subquestions", [])][:6] or [topic]
    print("   子问题：" + " / ".join(subqs))

    def gather(queries):
        notes = []
        for q in queries:
            hits = web_search(q, 5)
            for h in hits[:2]:
                notes.append({"q": q, "title": h["title"], "url": h["url"],
                              "text": (h["snippet"] + "\n" + fetch_page(h["url"]))[:2600]})
        return notes

    print("② 执行：检索 + 抓正文…")
    notes = gather(subqs)

    print("③ 反思：证据够吗…")
    digest = "\n".join(f"- [{n['q']}] {n['title']}: {n['text'][:400]}" for n in notes) or "（无）"
    try:
        verdict = json_block(chat([
            {"role": "system", "content": "你是审校员，只输出 JSON。"},
            {"role": "user", "content":
                f'主题：{topic}。已收集证据：\n{digest[:9000]}\n\n'
                f'输出 {{"enough": true/false, "followup": ["最多2个补搜关键词"]}}。'}]))
        if not verdict.get("enough", True):
            follow = [str(q) for q in verdict.get("followup", [])][:2]
            if follow and len(notes) < 18:
                print(f"   缺口 → 补搜：{follow}")
                notes += gather(follow)
    except Exception as e:
        print(f"   （反思步骤跳过：{e}）")

    print(f"④ 成稿：共 {len(notes)} 条证据，生成三份材料…")
    sources = "\n".join(f"- {n['title']} | {n['url']}" for n in notes)
    final = chat([
        {"role": "system", "content": COACH_PROMPT},
        {"role": "user", "content":
            f"学习主题：{topic}，保留期 {days} 天，面向自学者入门。\n\n"
            f"检索笔记：\n{digest[:16000]}\n\n"
            "严格按以下格式输出（三个分隔符都要出现）：\n"
            "===MAP===\n（学习地图 markdown：3-7 块结构，每块含'为什么学'+关键概念+常见误区）\n"
            "===QUESTIONS===\n（20 道自由回忆型提取问题，格式：Q: …\\nA: …）\n"
            "===ANKI===\n（CSV：front,back,tag 三列，15-25 张，答案短）"}])

    parts = re.split(r"===\w+===", final)
    map_doc = parts[1].strip() if len(parts) > 1 else final
    qs_doc = parts[2].strip() if len(parts) > 2 else ""
    anki_doc = parts[3].strip() if len(parts) > 3 else ""

    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", topic).strip("-")[:30] or "topic"
    outdir = os.path.join(os.getcwd(), "learn-fast-research", f"{slug}-{date.today().isoformat()}")
    os.makedirs(outdir, exist_ok=True)
    schedule = "\n".join(f"| 第{i}次 | {d.isoformat()} | 隔{g}天 |" for i, d, g in build_schedule(days))
    with open(os.path.join(outdir, "学习地图.md"), "w", encoding="utf-8") as f:
        f.write(f"# {topic} · 学习地图\n\n{map_doc}\n\n## 复习计划（保留期 {days} 天）\n\n| 次序 | 日期 | 间隔 |\n|---|---|---|\n{schedule}\n\n## 资料来源\n{sources}\n")
    with open(os.path.join(outdir, "提取问题.md"), "w", encoding="utf-8") as f:
        f.write(f"# {topic} · 提取问题\n\n先答后看！\n\n{qs_doc}\n")
    rows = []
    for line in anki_doc.splitlines():
        line = line.strip()
        if line.count(",") >= 2 and not line.lower().startswith("front"):
            rows.append(line)
    with open(os.path.join(outdir, "anki.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["front", "back", "tag"])
        for r in rows:
            w.writerow(next(csv.reader(io.StringIO(r))))
    print(f"\n✓ 完成！材料在 {outdir}")
    print("  ├─ 学习地图.md   （先看这个：框架 + 复习计划 + 来源）")
    print("  ├─ 提取问题.md   （合上地图，先答后看）")
    print("  └─ anki.csv      （导入 Anki：文件→导入）")
    return outdir


def main():
    ap = argparse.ArgumentParser(description="Learn Fast 自主研究型学习智能体")
    ap.add_argument("topic", nargs="?", help="学习主题，例如 'SQL 入门'")
    ap.add_argument("--days", type=int, default=90, help="保留期天数（默认 90）")
    ap.add_argument("--search", metavar="QUERY", help="只测搜索工具，不调用模型")
    ap.add_argument("--selftest", action="store_true", help="离线自检")
    a = ap.parse_args()
    if a.selftest:
        assert build_schedule(180)[0][2] == 27
        assert strip_tags('T<b>itle</b> <p>Snip</p>') == 'T itle Snip'
        assert json_block('废话 {"subquestions": ["a","b"]} 结尾')["subquestions"] == ["a", "b"]
        print("selftest OK")
        return
    if a.search:
        for h in web_search(a.search):
            print(f"  - {h['title']}\n    {h['url']}\n    {h['snippet'][:120]}")
        return
    if not a.topic:
        ap.print_help()
        return
    research(a.topic, a.days)


if __name__ == "__main__":
    main()
