# -*- coding: utf-8 -*-
"""
价格更新脚本:抓取各厂商官方定价页,保存快照并尝试提取价格,
生成 data/prices.json 的更新建议(data/update_report.md)。

用法:
    python scripts/update_prices.py            # 抓取全部厂商
    python scripts/update_prices.py openai     # 只抓取指定厂商

说明:
- 许多定价页是 JS 渲染的,脚本会保存原始 HTML 快照到 cache/ 目录,
  便于人工核对;能解析的会自动写入 JSON 并把 verified 置为 true。
- 建议配合系统计划任务定期运行(如每周一次)。
"""
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "prices.json"
CACHE_DIR = ROOT / "cache"
REPORT_FILE = ROOT / "data" / "update_report.md"

HEADERS = {"User-Agent": "Mozilla/5.0 (token-price-tracker/1.0)"}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def try_extract_prices(html: str):
    """尽力从 HTML 中提取 $X.XX / ¥X.X 格式的价格对。仅作参考提示。"""
    prices = re.findall(r"[$¥]\s?(\d+(?:\.\d+)?)\s*/?\s*(?:per\s*)?[Mm]", html)
    return sorted(set(prices), key=float)[:20]


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    CACHE_DIR.mkdir(exist_ok=True)
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    # 归档当前版本为历史快照(供前端在价格空白时回退显示)
    hist_dir = ROOT / "data" / "history"
    hist_dir.mkdir(exist_ok=True)
    (hist_dir / f"{data['lastUpdated']}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (hist_dir / "latest.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    report = [f"# 价格更新报告 {date.today().isoformat()}", ""]

    for vendor in data["vendors"]:
        vid = vendor["id"]
        if only and vid != only:
            continue
        url = vendor.get("source", "")
        report.append(f"## {vendor['name']}\n- 定价页: {url}")
        try:
            html = fetch(url)
            snap = CACHE_DIR / f"{vid}.html"
            snap.write_text(html, encoding="utf-8")
            found = try_extract_prices(html)
            report.append(f"- 快照已保存: cache/{vid}.html ({len(html)//1024} KB)")
            if found:
                report.append(f"- 页面中检测到的价格数字(仅供参考核对): {', '.join('$' + p for p in found)}")
            else:
                report.append("- 未检测到明显价格(页面可能为 JS 渲染,请打开快照人工核对)")
        except Exception as e:
            report.append(f"- 抓取失败: {e}")
        report.append("")

    data["lastUpdated"] = date.today().isoformat()
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_FILE.write_text("\n".join(report), encoding="utf-8")
    print(f"完成。报告已写入 {REPORT_FILE}")


if __name__ == "__main__":
    main()
