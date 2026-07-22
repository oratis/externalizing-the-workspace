# 投稿指南 — Persistent Broadcast Self-State (v4，评审驱动大修版)

v4 按外部评审意见重写：**主张降级 + 新增匹配对照实验(E9)+ 中介实验(E10)+ 统计重做 + 文献扩充**。

## v4 相对 v3 改了什么

| 评审意见 | 本版处理 |
|---|---|
| "necessary" 过强 | 全文降级为 *effective architectural intervention*；§1 有一段显式写明"上一版的 necessity 主张过强"并给出理由 |
| baseline 不公平（self-state vs memory 混淆了特权 framing） | **新增 E9 匹配对照**（§7）：同一份 self-state 文本、同 token 数，只改标签／位置／通道／binding 指令。结论：**标签几乎无效应（0.05 log-rank），位置效应大 4.4 倍（0.21）** → "特权身份 framing" 解释被排除，但"位置/salience"解释被加强 |
| 因果链没闭合 | **新增 E10 中介实验**（§9）：prompt 完全固定，用 steering／投影直接移动 workspace 占用，带选择性门（held-out NLL + 能力电池） |
| 统计设计（伪重复／单位／多重比较／预声明端点） | **新增 §10 统计重分析** + `research/analysis/`：单位=run，精确配对置换检验，Holm 校正，cluster bootstrap，相关系数分解，4 套评分规则鲁棒性 |
| 相关工作只有 14 篇 | 扩到 **68 篇**，覆盖评审点名的 10 个方向 |
| 摘要过长／5 项贡献重叠／营销词 | 摘要 265 词；贡献压到 3 项；删掉 "the wrong 93%"、"buildable and livable" 等 |
| §8 说部署已完成、Limitations 说不存在 | 统一为：**21 个模拟日的部署已完成；多周 wall-clock 部署未完成** |

⚠️ **诚实提示**：统计重分析推翻了 v3 的三处表述（见论文 §10），最重要的一处是
**workspace 占用与行为的相关（r=−0.74~−0.95）是簇间对比，簇内不成立** —— 论文现在
把它作为负结果报告。这会让论文"看起来更弱"，但这正是评审要的可辩护性。

## 文件

- `main.tex` — 规范版（唯一需要编辑的文件）
- `arxiv/main.tex`、`tmlr/main.tex` — **由 `python make_variants.py` 生成，别手改**
  （v3 时期这三份已经漂移：arXiv/TMLR 版还停在旧标题和旧摘要）
- TMLR 版默认**已匿名**（作者块 + 仓库链接被替换并自检）；camera-ready 用
  `python make_variants.py --deanonymize`
- 编译：`tectonic main.tex`（TMLR 版需先下载 `tmlr.sty`）

## 推荐路径（与评审一致）

1. **TMLR 作主投**。滚动投稿、无严格页数限制、评审标准是"主张是否被证据支持"而非新颖度 ——
   最契合本文"框架 + 复现 + 仪器 + 系统评估 + 诚实负结果"的组合。
   - 提交稿必须匿名（`make_variants.py` 默认输出即匿名版）
   - 正文超 12 页会进较长审稿周期；当前 ~22 页（含约 3 页参考文献）
   - TMLR 投稿在评审后通常公开保留，投前需接受这一点
2. **ICLR 2027 作下一轮主会目标**，前提是 E10 中介实验拿到干净结果。
   ICLR 2027 的 CFP／日期尚未公布，不要按往年日期当既成事实。
3. **不赶 AAAI-27**：full paper 截止 2026-07-28、abstract 截止 07-21（已过），
   且主会正文约 7 页 —— 当前的问题是要补实验而不是压页数。
4. **arXiv**：可先挂（primary `cs.LG`，cross-list `cs.CL`/`cs.AI`）。
   先挂预印本前确认目标 venue 的匿名与 prior-publication 政策；TMLR 允许预印本，
   但提交稿本身仍需匿名。

## 投稿前卡点

- [ ] **部署研究的 per-cohort 原始数据入库**。当前 `research/longitudinal/runs/` 被 gitignore，
      仓库里只有 per-arm 汇总 + WD readouts，而 Data Availability 段原本承诺了
      raw per-turn trajectory。v4 已先把该段改成如实描述现状；要么补传数据，要么保持收窄措辞。
- [ ] **盲评一批 work-turn 输出**。`research/analysis/results/blind_scoring_sample.csv`
      已导出 400 条去臂化样本 + `blind_scoring_key.json`，跑完把 agreement 写进 §10。
- [ ] **审一遍 "Use of AI Assistance" 段**，按你实际的核查程度校准措辞。
- [ ] **参考文献核对**：68 条里多数是常见文献（已抽查若干条的年份/venue），
      投稿前建议用 DBLP/Semantic Scholar 批量核一遍。
- [ ] arXiv endorsement：已获得（cs.AI）。若 primary 改 `cs.LG` 需确认背书是否覆盖。
- [x] 仓库已 public。

## arXiv 元数据

- **License**：CC BY 4.0
- **分类**：primary `cs.LG`；cross-list `cs.CL`, `cs.AI`（不要加 `q-bio.NC`）
- **Title**：Persistent Broadcast Self-State Improves Long-Horizon Coherence in Language-Model Agents: A Workspace-Interpretability Account
- **Authors**：Wang Bihao (Independent Researcher)
- **Comments**：`22 pages, 4 figures. Code and data: https://github.com/oratis/externalizing-the-workspace`
- **投稿包**：`tar czf arxiv-source.tar.gz -C arxiv main.tex figs`（自包含，内嵌 thebibliography）

### TMLR 步骤
1. 从 jmlr.org/tmlr 作者说明下载 `tmlr.sty`（用 BibTeX 再下 `tmlr.bst`）放进 `tmlr/`
2. `python make_variants.py` 生成匿名版 → pdfLaTeX 编译核对
3. OpenReview（TMLR track）提交；可建议做可解释性/agent 的 Action Editor；滚动评审约 2 个月出首轮
