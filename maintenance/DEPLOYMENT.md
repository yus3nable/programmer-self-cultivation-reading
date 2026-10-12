# 构建和发布

仓库： https://github.com/yus3nable/programmer-self-cultivation-reading

阅读地址： https://yus3nable.github.io/programmer-self-cultivation-reading/

`main` 保存 Markdown、图片和构建源码；GitHub Pages 从 `gh-pages` 分支根目录发布。

在项目根目录执行：

```sh
python3 -m venv .tools/venv
.tools/venv/bin/python -m pip install -r requirements.txt
.tools/venv/bin/python website/build.py
.tools/venv/bin/python tools/check_reader.py website/build/site --reading-order maintenance/reading-pages.json --base-path /programmer-self-cultivation-reading/ --report maintenance/reports/site-check.json
.tools/venv/bin/python -m ghp_import -n -p -m "Publish reading site" website/build/site
```

日常编辑 `chapters/*/sections/*.md`、`front/*/sections/*.md`。构建时生成整章版、导航和搜索索引，校对辅助框、整页扫描图及原页对照页面不会进入网站；整页图只保留在本地临时目录供校对使用。不要使用转换脚本覆盖已校对书稿。重新构建不需要原 PDF、OCR 缓存或本机校对记录。

如需本地查看，运行 `.tools/venv/bin/python tools/serve.py --port 8766`。本地服务只监听回环地址，与线上网站相互独立。
