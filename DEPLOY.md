# 部署上线指南

网站是纯静态站(index.html + data/*.json),不需要构建,任何静态托管都能用。
下面两条路线选一条即可。

## 路线 A:GitHub Pages(推荐,支持每日自动巡检)

1. 安装 Git:https://git-scm.com/download/win(一路下一步)
2. 在 GitHub 上新建一个公开仓库(例如 `token-prices`,不要勾选初始化 README)
3. 在本项目目录执行:

```bash
cd "H:\AI project\demo1"
git init
git add .
git commit -m "init: 大模型 token 价格汇总站"
git branch -M main
git remote add origin https://github.com/<你的用户名>/token-prices.git
git push -u origin main
```

4. 仓库页面 → Settings → Pages → Source 选 `main` 分支 `/ (root)` → Save
5. 约 1 分钟后访问 `https://<你的用户名>.github.io/token-prices/`

推送后 `.github/workflows/update.yml` 已就位:GitHub Actions 会每天北京时间 10 点
自动运行两个巡检脚本并提交变更(新模型横幅、历史归档自动更新),无需服务器。
可在仓库 Actions 页手动触发一次验证。

> GitHub 首次 push 需要登录:浏览器会弹出授权窗口,或使用 Personal Access Token。

## 路线 B:Netlify 拖拽部署(最快,无需命令行,但没有自动巡检)

1. 把整个项目文件夹压缩为 zip(可剔除 cache/ 和 scripts/)
2. 打开 https://app.netlify.com/drop ,注册/登录后把 zip 拖进去
3. 立即得到一个 https://xxx.netlify.app 地址,可后续绑定自己的域名

## 本地预览(部署前检查)

```bash
cd "H:\AI project\demo1"
python -m http.server 8000
# 打开 http://localhost:8000
```

## 注意事项

- 所有数据在 `data/prices.json`,价格以各厂商官方定价页为准
- `.gitignore` 已排除抓取的页面快照(cache/)和临时文件,不会推上仓库
- 若要绑定自定义域名,GitHub Pages 在仓库 Settings → Pages → Custom domain 设置
