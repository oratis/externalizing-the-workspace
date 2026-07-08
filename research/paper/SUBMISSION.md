# arXiv 投稿指南 — Externalizing the Workspace (Draft v3)

**投稿包**: `externalizing-workspace-arxiv-v3.tar.gz`(main.tex + figs/,已加 `\pdfoutput=1`,标准 pdflatex 可编译,无自定义类文件)

> 本地验证说明:`arxiv/main.tex` 与 `paper/main.tex` 逐字节相同(仅多首行 `\pdfoutput=1`),后者用 tectonic 编译 **0 error、出 715KB PDF**。`\pdfoutput=1` 是给 arXiv 的 **pdflatex** 引擎用的;本地 tectonic(XeTeX)会对该行报 `hpdftex.def` 假错——引擎差异,非投稿包问题,arXiv 侧 pdflatex 正常编译。

## 提交步骤(需要你的 arXiv 账号)

1. https://arxiv.org/submit → Start New Submission
2. **License**: 推荐 CC BY 4.0(利于 HF papers 页面聚合;保守可选 arXiv non-exclusive)
3. **分类**: primary `cs.AI`;cross-list `cs.CL`, `cs.LG`
4. **Title**: Externalizing the Workspace: Persistent Self-State for Long-Horizon Agent Coherence
5. **Authors**: Oratis (Wang Bihao) — 如需实名规范可写 Bihao Wang (Oratis), HakkoLab
6. **Abstract**: 从 main.tex 摘要复制(纯文本,去掉 \emph/\citep 命令;$r=-0.74$ 等数学可保留 $...$)
7. **Comments 字段建议**: "Draft v3. Code, raw results, and reproduction instructions: https://github.com/<LISA repo>/tree/main/research"
8. 上传 tarball → 预览编译 → announce

## 注意

- 首次在 cs.AI 投稿可能需要 endorsement;若遇到,arXiv 会给出 endorsement code,可找相识的已发表作者背书
- announce 后拿到 arXiv ID(如 2607.XXXXX),回来告诉我:HF papers 页面 (hf.co/papers/<id>) 依赖它自动建立,我再把 HF 页面与之关联

## HuggingFace 页面(等你 `huggingface-cli login` 后我来推)

计划:`HakkoLab/externalizing-the-workspace`(dataset repo 作 landing page):
- README.md = 论文页(摘要、关键图、结果表、复现指南)
- main.pdf + 三张关键图 + 全部结果 JSON(三模型复现 + 多 seed pilot)
