# -*- coding: utf-8 -*-
"""
新模型发现脚本:抓取各厂商官方定价页/文档页,用厂商特定的命名规则
提取疑似"新模型"名称,与 data/prices.json 中已收录的模型对比,
把未收录的写入 data/new_models.json,网站首页会展示提醒。

用法:
    python scripts/discover_new_models.py          # 检查全部厂商
    python scripts/discover_new_models.py openai   # 只检查指定厂商

注意:
- 页面为 JS 渲染或需登录的厂商(豆包、智谱等)会抓取失败并记录,
  建议定期人工访问其定价页核对。
- 发现的新模型只是名称候选,价格和特性需要人工补充到 prices.json。
"""
import json
import os
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

# 国内访问 GitHub/各厂商定价页常需代理;脚本默认尝试本地 10808 端口
if 'HTTP_PROXY' not in os.environ and not os.environ.get('CI'):
    for cand in ('http://127.0.0.1:10808', 'http://127.0.0.1:7890', 'http://127.0.0.1:10809'):
        try:
            urllib.request.urlopen(urllib.request.Request(
                'https://github.com', headers={'User-Agent': 'test'}), timeout=3).close()
            break
        except Exception:
            os.environ['HTTP_PROXY'] = os.environ['HTTPS_PROXY'] = cand

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "prices.json"
NEW_FILE = ROOT / "data" / "new_models.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (token-price-tracker/1.0)"}

# 每个厂商的模型命名模式(用于从页面文本中提取模型名)
PATTERNS = {
    "openai": r"\bgpt-[0-9][0-9a-z.\-]*\b",
    "anthropic": r"\bclaude[- ][a-z0-9]+[- ][0-9][0-9a-z.\-]*\b",
    "google": r"\bgemini[- ][0-9][0-9a-z.\-]*\b",
    "xai": r"\bgrok[- ][0-9][0-9a-z.\-]*\b",
    "mistral": r"\b(mistral|magistral|ministral)[ -][a-z0-9][0-9a-z.\-]*\b",
    "deepseek": r"\bdeepseek[- ][a-z0-9][0-9a-z.\-]*\b",
    "qwen": r"\bqwen[0-9][0-9a-z.\-]*\b",
    "zhipu": r"\bglm[- ]?[0-9][0-9a-z.\-]*\b",
    "ernie": r"\bernie[- ]?[0-9][0-9a-z.\-]*\b",
    "minimax": r"\bminimax[- ]?[a-z0-9][0-9a-z.\-]*\b",
    "doubao": r"\bdoubao[- ][a-z0-9][0-9a-z.\-]*\b",
    "hunyuan": r"\bhunyuan[- ][a-z0-9][0-9a-z.\-]*\b",
    "moonshot": r"\bkimi[- ]?[k0-9][0-9a-z.\-]*\b",
    "meta": r"\bllama[- ]?[0-9][0-9a-z.\-]*\b",
    "microsoft": r"\bphi[- ]?[0-9][0-9a-z.\-]*\b",
    "longcat": r"\blongcat[- ][a-z0-9][0-9a-z.\-]*\b",
}


def normalize(name: str) -> str:
    return re.sub(r"[\s\-_.]", "", name.lower())


def version_of(name: str) -> float:
    """取名称中的第一个数字作为版本号,如 gpt-4.1 -> 4.1,claude opus 4.5 -> 4.5"""
    m = re.search(r"(\d+(?:\.\d+)?)", name)
    return float(m.group(1)) if m else -1.0


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    result = {"checkedAt": date.today().isoformat(), "newModels": [], "errors": []}

    for vendor in data["vendors"]:
        vid = vendor["id"]
        if only and vid != only:
            continue
        pat = PATTERNS.get(vid)
        if not pat:
            continue
        known = {normalize(m["name"]) for m in vendor["models"]}
        # 只报告版本号高于已收录最新版的名称,过滤掉定价页上的历史旧型号
        known_max_ver = max((version_of(m["name"]) for m in vendor["models"]), default=-1.0)
        try:
            html = fetch(vendor["source"])
        except Exception as e:
            result["errors"].append({"vendor": vendor["name"], "error": str(e)})
            continue

        found = set()
        for raw in re.findall(pat, html, flags=re.IGNORECASE):
            n = normalize(raw)
            if any(n == k or (len(n) >= 4 and (k.startswith(n) or n.startswith(k))) for k in known):
                continue
            if version_of(raw) <= known_max_ver:
                continue  # 版本号不高于已收录最新版,视为旧型号
            found.add(raw.lower())
        for name in sorted(found)[:15]:
            result["newModels"].append({
                "vendor": vendor["name"],
                "vendorId": vid,
                "name": name,
                "source": vendor["source"],
            })

    NEW_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"检查完成:发现 {len(result['newModels'])} 个候选新模型,抓取失败 {len(result['errors'])} 家")
    print(f"详情见 {NEW_FILE}")


if __name__ == "__main__":
    main()
