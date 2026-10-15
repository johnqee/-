# -*- coding: utf-8 -*-
"""
深度研究助手（综合案例 02）——单文件实现
========================================
输入一个研究主题，自动完成：规划（拆子问题）→ 多轮检索 → 阅读抽取
→ 判断是否补检 → 综合生成带来源引用的研究报告。

架构：混合式。脚本控制循环骨架（轮数、检索、落盘、校验），
LLM 负责各环节的智能部分（拆解 / 抽取 / 缺口判断 / 写作 / 改写）。

产物（output/<时间戳>-<主题>/）：
  - report.md    结构化研究报告（含来源列表、置信度说明）
  - process.json 研究过程记录（检索词 / 读了哪些页面 / 迭代轮次 / 判断记录）

运行：uvicorn main:app --port 8000   然后浏览器打开 http://127.0.0.1:8000
"""

import json
import re
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel

# ============================================================
# 1. 配置（全部来自 .env，key 不硬编码）
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

import os

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-flash")
BOCHA_API_KEY = os.getenv("BOCHA_API_KEY", "")
BOCHA_SEARCH_COUNT = int(os.getenv("BOCHA_SEARCH_COUNT", "10"))
RESEARCH_MAX_ROUNDS = int(os.getenv("RESEARCH_MAX_ROUNDS", "3"))
LLM_RETRIES = int(os.getenv("LLM_RETRIES", "3"))
FETCH_ORIGINAL = os.getenv("FETCH_ORIGINAL", "true").lower() == "true"

BOCHA_URL = "https://api.bocha.cn/v1/web-search"
OUTPUT_DIR = BASE_DIR / "output"

llm_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


# ============================================================
# 2. LLM 调用封装（重试 + json_object 解析兜底）
# ============================================================

def parse_json(text: str) -> dict:
    """DeepSeek 只支持 json_object 不支持 json_schema，解析做双重兜底。"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            return json.loads(m.group(0))
        raise ValueError(f"LLM 输出不是合法 JSON：{text[:200]}")


def llm(prompt: str, system: str = "", json_mode: bool = True, temperature: float = 0.3) -> str:
    """调用 DeepSeek，失败重试 LLM_RETRIES 次。json_mode=True 时要求输出 JSON。"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    kwargs: dict[str, Any] = dict(
        model=MODEL_NAME,
        messages=messages,
        temperature=temperature,
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    last_err: Optional[Exception] = None
    for attempt in range(LLM_RETRIES):
        try:
            resp = llm_client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        except Exception as e:  # 网络/限流等，退避重试
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"LLM 调用失败（已重试 {LLM_RETRIES} 次）：{last_err}")


def llm_json(prompt: str, system: str = "", temperature: float = 0.3) -> dict:
    return parse_json(llm(prompt, system=system, json_mode=True, temperature=temperature))


# ============================================================
# 3. 博查搜索 + 原文抓取（阅读抽取的增强，失败静默降级）
# ============================================================

def bocha_search(query: str) -> list[dict]:
    """调用博查网页搜索，返回 [{title, url, snippet, summary}]。"""
    payload = {"query": query, "summary": True, "count": BOCHA_SEARCH_COUNT}
    headers = {
        "Authorization": f"Bearer {BOCHA_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        r = httpx.post(BOCHA_URL, headers=headers, json=payload, timeout=30)
        data = r.json()
    except Exception:
        return []  # 网络异常静默降级：该关键词本轮无结果

    pages = (data.get("data") or {}).get("webPages") or {}
    results = []
    for p in pages.get("value", []) or []:
        results.append({
            "title": p.get("name") or "",
            "url": p.get("url") or "",
            "snippet": p.get("snippet") or "",
            "summary": p.get("summary") or "",
        })
    return results


def fetch_page_text(url: str, max_chars: int = 2000) -> str:
    """抓取网页原文并粗提正文（失败返回空串 = 降级回摘要）。"""
    try:
        r = httpx.get(
            url,
            timeout=15,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (research-assistant)"},
        )
        if r.status_code != 200:
            return ""
        html = r.text
    except Exception:
        return ""
    # 粗暴去脚本/样式/标签，留正文文本
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<br\s*/?>|</p>|</div>|</li>", "\n", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = re.sub(r"&[a-zA-Z#0-9]+;", " ", text)
    text = re.sub(r"[ \t　]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text).strip()
    return text[:max_chars]


# ============================================================
# 4. 研究流水线各环节的提示词 + 逻辑
# ============================================================

PLAN_SYS = "你是一个严谨的深度研究规划助手，只输出合法 JSON，不要输出任何其他内容。"
EXTRACT_SYS = "你是一个严谨的研究资料抽取助手，只从给定资料中抽取信息，不编造，只输出合法 JSON。"
GAP_SYS = "你是一个严谨的研究缺口分析助手，只输出合法 JSON。"
WRITE_SYS = "你是一位资深行业研究员，擅长撰写结构严谨、引用可追溯的中文研究报告。"
REWRITE_SYS = "你是一位严谨的报告审校编辑，负责修正引用问题，只输出修正后的完整 Markdown 报告。"


def stage_plan(topic: str) -> dict:
    """规划：拆子问题 + 生成第一轮检索词。"""
    prompt = (
        f"研究主题：{topic}\n\n"
        "请完成：\n"
        "1. 拆解为 3~5 个互不重叠、合起来能覆盖主题的子问题；\n"
        "2. 为每个子问题生成 2~3 个适合网页搜索的检索词（中英文均可）。\n\n"
        '只输出 JSON，格式：{"sub_questions": ["..."], '
        '"search_queries": [{"query": "...", "sub_question": "..."}]}'
    )
    plan = llm_json(prompt, system=PLAN_SYS)
    plan.setdefault("sub_questions", [])
    plan.setdefault("search_queries", [])
    return plan


def stage_extract(sub_question: str, sources: list[dict]) -> dict:
    """阅读抽取：从搜索结果摘要（+可选原文）中抽关键信息点，带来源。"""
    blocks = []
    for i, s in enumerate(sources):
        body = s.get("summary") or s.get("snippet") or ""
        if s.get("fetched_text"):
            body += "\n【原文节选】" + s["fetched_text"]
        blocks.append(f"[{i + 1}] {s['title']}\nURL: {s['url']}\n{body[:800]}")
    prompt = (
        f"子问题：{sub_question}\n\n"
        f"以下是检索到的资料（共 {len(sources)} 条）：\n\n" + "\n\n".join(blocks) + "\n\n"
        "请从中抽取 3~6 条能回答子问题的关键信息点：\n"
        "- 每条给出简明结论文本；\n"
        "- source_urls 只能从上面出现过的 URL 中选取（支撑该结论的来源，可多个）；\n"
        "- 资料中没有依据的内容一律不要写；信息不足就少抽或返回空列表。\n\n"
        '只输出 JSON：{"points": [{"text": "...", "source_urls": ["..."]}]}'
    )
    out = llm_json(prompt, system=EXTRACT_SYS)
    return {"points": out.get("points", [])}


def stage_judge_gaps(topic: str, sub_questions: list[str], all_points: list[dict], round_no: int) -> dict:
    """缺口判断：对照子问题检查信息是否足够，决定是否补检。"""
    pts = "\n".join(f"- {p.get('text', '')}" for p in all_points) or "（暂无）"
    prompt = (
        f"研究主题：{topic}\n"
        f"子问题清单：{json.dumps(sub_questions, ensure_ascii=False)}\n\n"
        f"目前已抽取的信息点：\n{pts}\n\n"
        f"当前是第 {round_no} 轮检索（最多 {RESEARCH_MAX_ROUNDS} 轮）。请判断：\n"
        "1. 对照子问题逐项检查，现有信息是否已足够撰写一份合格的调研报告？\n"
        "2. 若足够，sufficient=true；若不够，列出关键缺口，并给出最多 4 个新的补检检索词。\n\n"
        '只输出 JSON：{"sufficient": true/false, "gaps": ["..."], "new_queries": ["..."]}'
    )
    out = llm_json(prompt, system=GAP_SYS)
    return {
        "sufficient": bool(out.get("sufficient", False)),
        "gaps": out.get("gaps", []),
        "new_queries": out.get("new_queries", []),
    }


def stage_write(topic: str, sub_questions: list[str], all_points: list[dict],
                source_registry: dict, info_date: str) -> str:
    """综合：生成带 [n] 引用的完整 Markdown 报告（来源列表由程序拼装）。"""
    # 编号映射：url -> [n]
    url2id = {u: meta["id"] for u, meta in source_registry.items()}
    pts_lines = []
    for p in all_points:
        ids = sorted({url2id[u] for u in p.get("source_urls", []) if u in url2id})
        cite = "".join(f"[{i}]" for i in ids) if ids else "（模型推断）"
        pts_lines.append(f"- {p.get('text', '')} {cite}")
    pts_text = "\n".join(pts_lines) or "（无抽取信息点）"
    sources_text = "\n".join(
        f"[{m['id']}] {m['title']} — {u}" for u, m in source_registry.items()
    )
    prompt = (
        f"研究主题：{topic}\n"
        f"子问题：{json.dumps(sub_questions, ensure_ascii=False)}\n\n"
        f"已抽取的信息点（行尾 [n] 为来源编号）：\n{pts_text}\n\n"
        f"来源清单（编号对应关系）：\n{sources_text}\n\n"
        "请撰写一份中文深度研究报告，要求：\n"
        "1. Markdown 结构：`# 报告标题`、`## 摘要`、`## 分节正文`（每个子问题一个小节，标题用 `###`）、"
        "`## 关键结论`、`## 遗留问题`、`## 置信度说明`；\n"
        "2. 正文与关键结论中的每条事实性结论，句末必须带来源角标如 [1][3]，"
        "编号只能来自上面的来源清单；\n"
        "3. 确实没有来源支撑的判断，句末明确标注（模型推断），不得伪装引用；\n"
        f"4. `## 置信度说明` 必须包含：总体可靠程度及理由、信息截止时间（{info_date}）、"
        "哪些部分属于模型推断；\n"
        "5. 不要写「来源列表」章节（系统会自动生成）；不要输出任何 Markdown 之外的说明文字。\n\n"
        "直接输出完整 Markdown 报告。"
    )
    return llm(prompt, system=WRITE_SYS, json_mode=False, temperature=0.4)


def stage_rewrite(report_md: str, problems: list[str]) -> str:
    """引用校验不通过时，打回重写一次。"""
    prompt = (
        "下面这份研究报告未通过引用校验，发现的问题：\n"
        + "\n".join(f"- {p}" for p in problems)
        + "\n\n请修正以上问题，重新输出完整 Markdown 报告"
        "（保持原有结构，结论句末的 [n] 角标必须能在来源清单中找到对应编号，"
        "没有来源的判断标注（模型推断），不要输出来源列表章节）：\n\n"
        + report_md
    )
    return llm(prompt, system=REWRITE_SYS, json_mode=False, temperature=0.3)


# ============================================================
# 5. 引用校验（[n] 角标与来源清单对账）
# ============================================================

def validate_citations(report_md: str, source_registry: dict) -> list[str]:
    """返回问题列表（空 = 通过）。只校验来源列表章节之前的正文。

    未被引用的来源不算问题——报告定稿后由 finalize_sources 裁剪重编号。
    """
    body = re.split(r"(?m)^##\s*来源列表", report_md)[0]
    max_id = max((m["id"] for m in source_registry.values()), default=0)
    # 只把合法范围内的 [n] 当引用角标，避免把 [2026] 这类年份误判为引用
    used = {int(n) for n in re.findall(r"\[(\d+)\]", body) if int(n) <= max_id}
    valid = {m["id"] for m in source_registry.values()}
    problems = []
    bad = sorted(used - valid)
    if bad:
        problems.append(f"正文引用了不存在的来源编号：{bad}")
    if not used and valid:
        problems.append("正文没有任何 [n] 引用角标，所有结论都必须带来源或标注（模型推断）")
    return problems


def finalize_sources(report_md: str, source_registry: dict) -> str:
    """报告定稿：正文 [n] 与来源列表按「实际被引用」裁剪并连续重编号，保证对账一致。"""
    body = re.split(r"(?m)^##\s*来源列表", report_md)[0].rstrip()
    max_id = max((m["id"] for m in source_registry.values()), default=0)
    used = sorted({int(n) for n in re.findall(r"\[(\d+)\]", body) if int(n) <= max_id})
    id2url = {m["id"]: u for u, m in source_registry.items()}
    remap = {old: new for new, old in enumerate(used, 1)}

    def repl(m: re.Match) -> str:
        n = int(m.group(1))
        return f"[{remap[n]}]" if n in remap else m.group(0)

    body = re.sub(r"\[(\d+)\]", repl, body)
    lines = ["## 来源列表", ""]
    for old in used:
        u = id2url.get(old)
        if not u:
            continue
        meta = source_registry[u]
        lines.append(f"- [{remap[old]}] [{meta['title'] or u}]({u})")
    return body + "\n\n" + "\n".join(lines) + "\n"


# ============================================================
# 6. 流水线编排（脚本控制循环骨架）+ 过程记录
# ============================================================

def safe_slug(text: str, max_len: int = 30) -> str:
    return re.sub(r'[\\/:*?"<>|\s]+', "_", text).strip("_")[:max_len] or "research"


class ResearchTask:
    """一次深度研究任务：状态 + 过程记录 + 产物落盘。"""

    def __init__(self, task_id: str, topic: str):
        self.id = task_id
        self.topic = topic
        self.state = "running"  # running / done / error
        self.error = ""
        self.report_md = ""
        self.process: dict[str, Any] = {
            "topic": topic,
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "finished_at": None,
            "model": MODEL_NAME,
            "max_rounds": RESEARCH_MAX_ROUNDS,
            "rounds": [],       # 每轮：检索词 / 读了哪些页面 / 抽取点数 / 缺口判断
            "pages_fetched": 0,  # 原文抓取次数（增强阅读）
            "validation": None,  # 引用校验结果
            "output_dir": None,
        }
        self.progress = {
            "phase": "规划中",
            "round": 0,
            "total_rounds": RESEARCH_MAX_ROUNDS,
            "message": "正在拆解子问题…",
            "sources_count": 0,
            "queries_done": 0,
        }

    def update(self, message: str, **kwargs):
        self.progress["message"] = message
        self.progress.update(kwargs)

    def run(self):
        try:
            self._run()
            self.state = "done"
        except Exception as e:
            self.state = "error"
            self.error = str(e)
            self.process["error"] = str(e)
        finally:
            self.process["finished_at"] = datetime.now().isoformat(timespec="seconds")
            self._save()

    # ---- 主流程 ----
    def _run(self):
        info_date = datetime.now().strftime("%Y-%m-%d")
        source_registry: dict[str, dict] = {}  # url -> {id, title, snippet, summary, fetched_text}
        all_points: list[dict] = []

        # ① 规划
        self.update("正在拆解子问题、规划检索词…", phase="规划中")
        plan = stage_plan(self.topic)
        sub_questions = plan["sub_questions"]
        queries = [
            {"query": q.get("query", ""), "sub_question": q.get("sub_question", "")}
            for q in plan["search_queries"] if q.get("query")
        ]
        self.process["sub_questions"] = sub_questions
        self.process["plan_queries"] = [q["query"] for q in queries]

        # ②③④ 多轮检索 → 阅读抽取 → 判断补检
        for round_no in range(1, RESEARCH_MAX_ROUNDS + 1):
            self.update(
                f"第 {round_no}/{RESEARCH_MAX_ROUNDS} 轮检索中…",
                phase="检索阅读", round=round_no,
            )
            round_rec: dict[str, Any] = {
                "round": round_no,
                "queries": [q["query"] for q in queries],
                "pages_read": [],
                "extracted_points": 0,
                "gap_judgment": None,
            }

            # 检索（url 全局去重，记录来源归属的子问题）
            round_sources: list[dict] = []
            for q in queries:
                self.update(
                    f"第 {round_no} 轮：正在检索「{q['query']}」",
                    phase="检索阅读", round=round_no,
                    queries_done=self.progress["queries_done"] + 1,
                )
                for r in bocha_search(q["query"]):
                    if not r["url"]:
                        continue
                    if r["url"] in source_registry:
                        # 已见过的来源补记归属，供该子问题抽取复用
                        source_registry[r["url"]]["subs"].add(q["sub_question"])
                        continue
                    source_registry[r["url"]] = {
                        "id": len(source_registry) + 1,
                        "title": r["title"],
                        "snippet": r["snippet"],
                        "summary": r["summary"],
                        "fetched_text": "",
                        "subs": {q["sub_question"]},
                    }
                    round_sources.append(source_registry[r["url"]] | {"url": r["url"]})

            self.progress["sources_count"] = len(source_registry)

            # 阅读抽取的增强：摘要太薄时抓原文，失败静默降级
            if FETCH_ORIGINAL:
                for s in round_sources:
                    summary = (s.get("summary") or "") + (s.get("snippet") or "")
                    if len(summary.strip()) < 120:
                        text = fetch_page_text(s["url"])
                        if text:
                            source_registry[s["url"]]["fetched_text"] = text
                            self.process["pages_fetched"] += 1
                            round_rec["pages_read"].append(s["url"])

            # 按子问题抽取：优先用检索归属该子问题的来源，兜底用全部来源
            new_urls = {r["url"] for r in round_sources}
            for sq in sub_questions or [""]:
                owned = [
                    {"url": u, **{k: v for k, v in meta.items() if k != "subs"}}
                    for u, meta in source_registry.items()
                    if sq in meta["subs"]
                ]
                if not owned:
                    owned = [
                        {"url": u, **{k: v for k, v in meta.items() if k != "subs"}}
                        for u, meta in source_registry.items()
                    ]
                # 本轮新来源优先，上限 12 条控制上下文长度
                owned.sort(key=lambda s: 0 if s["url"] in new_urls else 1)
                sq_sources = owned[:12]
                if not sq_sources:
                    continue
                self.update(
                    f"第 {round_no} 轮：正在从 {len(sq_sources)} 个来源抽取要点（{sq[:20]}…）",
                    phase="阅读抽取", round=round_no,
                )
                extracted = stage_extract(sq, sq_sources)
                for p in extracted.get("points", []):
                    p["sub_question"] = sq
                    all_points.append(p)
                round_rec["extracted_points"] += len(extracted.get("points", []))

            # 判断是否补检（最后一轮不必判断）
            if round_no < RESEARCH_MAX_ROUNDS:
                self.update(f"第 {round_no} 轮：正在判断信息缺口…", phase="缺口判断", round=round_no)
                judgment = stage_judge_gaps(self.topic, sub_questions, all_points, round_no)
                round_rec["gap_judgment"] = judgment
                self.process["rounds"].append(round_rec)
                if judgment["sufficient"] or not judgment["new_queries"]:
                    self.update("信息已足够，进入报告综合…", phase="综合生成")
                    break
                queries = [{"query": q, "sub_question": ""} for q in judgment["new_queries"][:4]]
            else:
                self.process["rounds"].append(round_rec)

        # ⑤ 综合写报告
        self.update("正在综合生成研究报告…", phase="综合生成")
        report_md = stage_write(self.topic, sub_questions, all_points, source_registry, info_date)

        # ⑥ 引用校验，不合规打回重写一次
        self.update("正在校验引用与来源对账…", phase="引用校验")
        problems = validate_citations(report_md, source_registry)
        rewrote = False
        if problems:
            self.update(f"引用校验发现 {len(problems)} 处问题，打回重写…", phase="引用校验")
            report_md = stage_rewrite(report_md, problems)
            problems = validate_citations(report_md, source_registry)
            rewrote = True
        self.process["validation"] = {
            "passed": not problems,
            "problems": problems,
            "rewrote_once": rewrote,
        }

        # 来源列表由程序按「实际被引用」裁剪并连续重编号，保证与正文角标严格对账
        report_md = finalize_sources(report_md, source_registry)
        body = re.split(r"(?m)^##\s*来源列表", report_md)[0]
        cited = {int(n) for n in re.findall(r"\[(\d+)\]", body)}
        self.process["sources_total"] = len(source_registry)
        self.process["sources_cited"] = len(cited)

        self.report_md = report_md
        self.update("研究完成！", phase="完成")

    # ---- 落盘 ----
    def _save(self):
        out = OUTPUT_DIR / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{safe_slug(self.topic)}"
        out.mkdir(parents=True, exist_ok=True)
        if self.report_md:
            (out / "report.md").write_text(self.report_md, encoding="utf-8")
        (out / "process.json").write_text(
            json.dumps(self.process, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self.process["output_dir"] = str(out)


# ============================================================
# 7. FastAPI：接口 + 静态前端
# ============================================================

app = FastAPI(title="深度研究助手")
TASKS: dict[str, ResearchTask] = {}
TASKS_LOCK = threading.Lock()


class TopicIn(BaseModel):
    topic: str


@app.post("/api/research")
def start_research(body: TopicIn):
    topic = body.topic.strip()
    if not topic:
        raise HTTPException(400, "研究主题不能为空")
    task = ResearchTask(uuid.uuid4().hex[:12], topic)
    with TASKS_LOCK:
        TASKS[task.id] = task
    threading.Thread(target=task.run, daemon=True).start()
    return {"task_id": task.id}


@app.get("/api/research/{task_id}")
def get_research(task_id: str):
    with TASKS_LOCK:
        task = TASKS.get(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    return {
        "task_id": task.id,
        "topic": task.topic,
        "state": task.state,
        "error": task.error,
        "progress": task.progress,
        "report_md": task.report_md,
        "process": task.process,
    }


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
