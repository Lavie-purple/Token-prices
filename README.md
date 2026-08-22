# 大模型 Token 价格汇总网站

汇总 17 家模型厂商(OpenAI、Anthropic、Google、xAI、Mistral、Meta、微软、DeepSeek、Qwen、智谱、文心、MiniMax、豆包、混元、Kimi、零一万物、美团 LongCat)的 API token 价格,每百万 tokens 计价。

## 本地运行

```bash
cd "H:\AI project\demo1"
python -m http.server 8000
# 浏览器打开 http://localhost:8000
```

> 直接双击 index.html 会被浏览器跨域策略拦截 fetch,请务必通过本地服务器打开。

## 文件结构

- `index.html` — 前端页面(搜索、地区筛选、点击表头排序、价格核验状态标记)
- `data/prices.json` — 价格数据(所有价格来源与单位在文件内注明)
- `scripts/update_prices.py` — 更新脚本:抓取各厂商官方定价页,保存快照到 `cache/`,并生成 `data/update_report.md` 核对报告
- `data/update_report.md` — 每次运行更新脚本后生成

## 定期更新

```bash
python scripts/update_prices.py          # 全部厂商
python scripts/update_prices.py openai   # 指定厂商
```

多数定价页是 JS 渲染的,脚本会把原始页面存到 `cache/` 供人工核对;确认新价格后直接修改 `data/prices.json` 中对应数字,并把 `verified` 改为 `true`,页面即自动更新。

Windows 计划任务每周自动更新示例:

```
schtasks /create /tn "TokenPriceUpdate" /tr "python H:\AI project\demo1\scripts\update_prices.py" /sc weekly /d mon /st 09:00
```

## 部署

纯静态站点,把整个目录(含 `data/`)推到 GitHub Pages、Vercel、Netlify 或任意静态托管即可。
