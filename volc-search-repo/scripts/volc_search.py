#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""火山引擎「豆包搜索 Custom 版」联网搜索客户端。

接口文档：https://docs.volcengine.com/docs/Networkedsearch/Networkedsearch-2
只用 Python 标准库（urllib），无需 pip install。

用法：
    python volc_search.py "北京天气"
    python volc_search.py "AI 芯片" --time-range OneWeek --auth-level 1
    python volc_search.py "小米 SU7" --type image --count 3
    python volc_search.py "某公司财报" --sites eastmoney.com|cls.cn
    python volc_search.py "某事件" --format json
"""

import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

DEFAULT_ENDPOINT = "https://open.feedcoopapi.com/search_api/web_search"
DEFAULT_COUNT = 10
SUMMARY_LIMIT = 1200
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(SKILL_ROOT, "config.json")
DEFAULT_KEY_FILE = "key"

TIME_RANGE_SHORTCUTS = {"OneDay", "OneWeek", "OneMonth", "OneYear"}
DATE_RANGE_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})$")


# ---------------------------------------------------------------- 配置

def load_config():
    cfg = {}
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f) or {}
        except (OSError, ValueError) as exc:
            print("[volc-search] 警告：读取 config.json 失败：%s" % exc, file=sys.stderr)
            cfg = {}
    return cfg


def read_key_file(cfg):
    """从 config.json 里 key_file 指定的纯文本文件读取 Key（相对路径按 skill 根目录解析）。"""
    name = (cfg.get("key_file") or DEFAULT_KEY_FILE).strip() or DEFAULT_KEY_FILE
    path = name if os.path.isabs(name) else os.path.join(SKILL_ROOT, name)
    if not os.path.isfile(path):
        return "", path
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return f.read().strip(), path
    except OSError as exc:
        print("[volc-search] 警告：读取 Key 文件失败：%s" % exc, file=sys.stderr)
        return "", path


def resolve_api_key(cli_key, cfg):
    key = (cli_key or "").strip()
    if key:
        return key
    for env_name in ("VOLC_SEARCH_API_KEY", "WEB_SEARCH_API_KEY"):
        env_val = (os.environ.get(env_name) or "").strip()
        if env_val:
            return env_val
    file_key, _ = read_key_file(cfg)
    if file_key:
        return file_key
    return (cfg.get("api_key") or "").strip()


# ---------------------------------------------------------------- 配置

def validate_time_range(value):
    if not value:
        return None
    if value in TIME_RANGE_SHORTCUTS:
        return value
    match = DATE_RANGE_PATTERN.match(value)
    if not match:
        raise ValueError("--time-range 需为 OneDay/OneWeek/OneMonth/OneYear，或 YYYY-MM-DD..YYYY-MM-DD")
    start_text, end_text = match.groups()
    try:
        start_date = datetime.date.fromisoformat(start_text)
        end_date = datetime.date.fromisoformat(end_text)
    except ValueError:
        raise ValueError("--time-range 中的日期需为合法的 YYYY-MM-DD")
    if start_date > end_date:
        raise ValueError("--time-range 的开始日期不能晚于结束日期")
    return value


def build_body(args):
    body = {"Query": args.query, "SearchType": args.type, "Count": args.count}

    search_filter = {}
    if args.sites:
        search_filter["Sites"] = args.sites
    if args.block_hosts:
        search_filter["BlockHosts"] = args.block_hosts
    if args.auth_level:
        search_filter["AuthInfoLevel"] = args.auth_level
    if args.need_content:
        search_filter["NeedContent"] = True

    if args.type == "web":
        if search_filter:
            body["Filter"] = search_filter
        if args.time_range:
            body["TimeRange"] = args.time_range
        if args.industry:
            body["Industry"] = args.industry
        if args.query_rewrite:
            body["QueryControl"] = {"QueryRewrite": True}
    elif args.type == "image":
        if search_filter:
            body["Filter"] = search_filter
        if args.query_rewrite:
            body["QueryControl"] = {"QueryRewrite": True}

    return body


# ---------------------------------------------------------------- 请求

def call_api(body, api_key, endpoint, timeout):
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": "Bearer %s" % api_key,
        "Accept": "application/json",
    }
    request = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        raise RuntimeError("HTTP %s: %s" % (exc.code, detail or exc.reason))
    except urllib.error.URLError as exc:
        raise RuntimeError("网络错误：%s" % exc.reason)

    try:
        return json.loads(raw)
    except ValueError:
        raise RuntimeError("响应不是合法 JSON：%s" % raw[:500])


def extract_error(data):
    meta = (data or {}).get("ResponseMetadata") or {}
    return meta.get("Error")


# ---------------------------------------------------------------- 输出

def format_text(data, search_type, need_content):
    result = data.get("Result") or {}
    count = result.get("ResultCount", 0)
    cost = result.get("TimeCost", 0)
    ctx = result.get("SearchContext") or {}
    lines = [
        "ResultCount: %s  TimeCost: %sms  Query: %s" % (count, cost, ctx.get("OriginQuery", "")),
        "",
    ]

    if search_type == "web":
        for item in result.get("WebResults") or []:
            lines.append("[%s] %s" % (item.get("SortId", ""), item.get("Title", "")))
            meta_parts = [p for p in (item.get("SiteName", ""), item.get("AuthInfoDes", "")) if p]
            if meta_parts:
                lines.append("    " + " | ".join(meta_parts))
            if item.get("Url"):
                lines.append("    " + item["Url"])
            if item.get("PublishTime"):
                lines.append("    " + item["PublishTime"])
            text = item.get("Summary") or item.get("Snippet") or ""
            if text:
                lines.append("    " + text[:SUMMARY_LIMIT])
            if need_content and item.get("Content"):
                lines.append("    --- 正文 ---")
                lines.append("    " + item["Content"][:SUMMARY_LIMIT])
            lines.append("")
    elif search_type == "image":
        for item in result.get("ImageResults") or []:
            image = item.get("Image") or {}
            lines.append("[%s] %s" % (item.get("SortId", ""), item.get("Title", "")))
            if image.get("Url"):
                lines.append("    " + image["Url"])
            lines.append(
                "    %sx%s (%s)"
                % (image.get("Width", "?"), image.get("Height", "?"), image.get("Shape", ""))
            )
            if item.get("Url"):
                lines.append("    " + item["Url"])
            lines.append("")

    if count == 0:
        lines.append("（没有搜到结果，换个关键词或放宽时间范围试试）")

    return "\n".join(lines).rstrip()


# ---------------------------------------------------------------- CLI

def main():
    parser = argparse.ArgumentParser(
        description="火山引擎联网搜索（豆包搜索 Custom 版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", help="搜索词（1~100 字符）")
    parser.add_argument("--type", "-t", default="web", choices=["web", "image"])
    parser.add_argument("--count", "-c", type=int, default=None)
    parser.add_argument("--time-range", help="OneDay/OneWeek/OneMonth/OneYear/YYYY-MM-DD..YYYY-MM-DD")
    parser.add_argument("--auth-level", type=int, default=0, choices=[0, 1])
    parser.add_argument("--sites", help="限定站点，完整域名，| 分隔，最多 20 个")
    parser.add_argument("--block-hosts", help="屏蔽站点，| 分隔，最多 5 个")
    parser.add_argument("--query-rewrite", action="store_true", help="开启 Query 改写")
    parser.add_argument("--industry", choices=["finance", "game", "gov"], help="行业搜索")
    parser.add_argument("--need-content", action="store_true", help="只返回有正文的结果并输出正文")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--api-key", help="临时覆盖配置里的 API Key")
    parser.add_argument("--retry", type=int, default=1, help="遇到 10500/限流时的重试次数，默认 1")
    args = parser.parse_args()

    if not args.query or not args.query.strip():
        print("错误：搜索词不能为空。", file=sys.stderr)
        return 1
    if len(args.query) > 100:
        print("错误：搜索词超过 100 字符会被截断，请精简后重试。", file=sys.stderr)
        return 1

    cfg = load_config()
    if args.count is None:
        args.count = int(cfg.get("default_count") or DEFAULT_COUNT)
    if args.count < 1:
        print("错误：--count 需 >= 1。", file=sys.stderr)
        return 1
    if args.type == "image" and args.count > 5:
        print("错误：图片搜索结果最多 5 条。", file=sys.stderr)
        return 1
    if args.type == "web" and args.count > 50:
        print("错误：网页搜索结果最多 50 条。", file=sys.stderr)
        return 1

    try:
        args.time_range = validate_time_range(args.time_range)
    except ValueError as exc:
        print("错误：%s" % exc, file=sys.stderr)
        return 1

    api_key = resolve_api_key(args.api_key, cfg)
    if not api_key:
        _, key_path = read_key_file(cfg)
        print(
            "错误：没有配置 API Key。\n"
            "  方式1：把 Key 写进 %s （纯文本，一行，只放 Key 本身）\n"
            "  方式2：设置环境变量 VOLC_SEARCH_API_KEY 或 WEB_SEARCH_API_KEY\n"
            "  方式3：--api-key 临时传入\n"
            "Key 获取：https://console.volcengine.com/search-infinity/api-key\n"
            "（注意要用「联网搜索」的 Key，方舟 Ark 的 Key 不通用）" % key_path,
            file=sys.stderr,
        )
        return 1

    endpoint = (cfg.get("endpoint") or DEFAULT_ENDPOINT).strip()
    timeout = int(cfg.get("timeout") or 30)
    body = build_body(args)

    data = None
    for attempt in range(args.retry + 1):
        try:
            data = call_api(body, api_key, endpoint, timeout)
        except RuntimeError as exc:
            print("[volc-search] 请求失败：%s" % exc, file=sys.stderr)
            return 1

        error = extract_error(data)
        if not error:
            break
        code = str(error.get("Code", ""))
        if code in ("10500", "700429") and attempt < args.retry:
            time.sleep(2)
            continue
        print("[volc-search] API 错误 [%s] %s" % (code, error.get("Message", "")), file=sys.stderr)
        if code in ("10403", "10401"):
            print(
                "提示：鉴权失败。请确认 Key 来自 https://console.volcengine.com/search-infinity/api-key ，\n"
                "且账号已开通联网搜索服务（方舟 Ark 的 Key 不通用）。",
                file=sys.stderr,
            )
        elif code in ("10406", "10412"):
            print("提示：搜索额度已用尽，请到控制台充值，或改用默认 web_search。", file=sys.stderr)
        elif code == "700429":
            print("提示：触发限流（默认 5 QPS），降频后再试。", file=sys.stderr)
        elif code == "10400":
            print("提示：参数错误，检查 Query 长度、Count 上限、TimeRange 格式。", file=sys.stderr)
        elif code == "10409":
            print("提示：当前套餐不支持该搜索类型。", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_text(data, args.type, args.need_content))
    return 0


if __name__ == "__main__":
    sys.exit(main())
