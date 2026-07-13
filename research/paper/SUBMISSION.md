# 投稿指南 — Externalizing the Workspace (Draft v3, 双条件部署版)

论文已定稿:复现(E1–E8)+ 工作空间加载(E6)+ 模拟 pilot + **真实部署(Qwen 行为+WD)**
+ **闭源鲁棒性(Gemini-2.5-pro)**,并含数据/代码可用性、复现说明、作者贡献、**AI 使用声明**。

- **源文件**(均已 `tectonic` 0-error 编译,~14 页 966KB):
  - `main.tex` — 本地/规范版
  - `arxiv/main.tex` — arXiv 版(`iftex` 守卫 `\pdfoutput`:arXiv 的 pdfLaTeX 强制出 PDF,本地 tectonic 也能编)
  - `tmlr/main.tex` — TMLR 版(正文与 main.tex 逐字相同,仅换 documentclass/title/author;**需下载 `tmlr.sty`** 后编译)
- **arXiv 投稿包**:`tar czf arxiv-source.tar.gz -C arxiv main.tex figs`(自包含,内嵌 thebibliography,PNG 图,无 .bib)
- **纯文本摘要**:`arxiv/abstract.txt`(≈3270 字符,可直接粘贴)

## 推荐路径
1. **先挂 arXiv**(primary `cs.AI`)—— 立时间戳 + 可分享,免费,1–2 天上线。
2. **TMLR 作主投**(顶刊目标)—— 滚动、无页数限制、看重"主张是否被证据支持"而非新颖度,最契合本文的诚实边界条件。
3. 冲刺备选:*Nature Machine Intelligence*(主打 GWT/agent 福祉跨学科角度);会议备选:ICLR 2027 / COLM(需压页数)。

## ⚠️ 投稿前先做(卡点 / 诚信)
- [ ] **把仓库设为 public**。论文写了"Code is released"并附链接,但仓库现为**私有**。已做安全扫描:tracked 文件**无真实密钥**,`runs/`(部署数据 + LISA 的个人 soul 日志)已 gitignore、不会泄露。你来点:`gh repo edit oratis/externalizing-the-workspace --visibility public`。
- [ ] **审一遍 "Use of AI Assistance" 段**(论文末)。它诚实写明实验与初稿由 AI agent 在你指导下完成 —— 按你**实际的核查程度**校准措辞后再定稿。
- [x] **arXiv endorsement**:已获得背书(cs.AI)。
- [ ] **HuggingFace 数据集**:把 `research/longitudinal/results/`(+ 原始 run tarball)传到 `HakkoLab`,确认链接可达。

## arXiv 元数据(填表用)
- **License**:推荐 CC BY 4.0(利于 HF papers 聚合)
- **分类**:primary `cs.AI`;cross-list `cs.LG`, `cs.CL`, `q-bio.NC`(最后一个对应全局工作空间/意识框架)
- **Title**:Externalizing the Workspace: Persistent Self-State for Long-Horizon Agent Coherence
- **Authors**:Wang Bihao (Oratis), HakkoLab
- **Abstract**:粘贴 `arxiv/abstract.txt`
- **Comments**:`18 pages, 4 figures. Code and data: https://github.com/oratis/externalizing-the-workspace`

### arXiv 步骤
1. https://arxiv.org/submit → Start New Submission → 上传 `arxiv-source.tar.gz`
2. 填 License / 分类 / Title / Authors / Abstract / Comments
3. 预览编译出的 PDF → submit → 审核 → 1–2 天上线,拿到 arXiv ID
4. 拿到 ID 告诉我,HF papers 页 (hf.co/papers/<id>) 会自动建立,我再关联 HF 数据集

### TMLR 步骤
1. 从 jmlr.org/tmlr 作者说明下载 `tmlr.sty`(如用 BibTeX 再下 `tmlr.bst`)放进 `tmlr/`
2. `tmlr/main.tex` 已预配好(TMLR 类 + title/author 宏,正文同 main.tex),pdfLaTeX 编译并核对
3. OpenReview(TMLR track)提交;可建议做可解释性/agent 的 Action Editor;滚动评审 ~2 月出首轮

## HuggingFace(等你 `huggingface-cli login` 后我来推)
`HakkoLab/externalizing-the-workspace`(dataset repo 作 landing page):
- README = 论文页(摘要、关键图、三表结果:E6 加载 / pilot / **真实部署 Qwen** / **Gemini 鲁棒性**)
- `main.pdf` + 关键图 + 全部结果 JSON(`research/longitudinal/results/`)+ 原始轨迹
