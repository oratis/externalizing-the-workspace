# 投稿指南 — Persistent Agent Self-State（v5）

v5 将行为结果设为主线，将 workspace 分析降为探索性结果，并在运行新实验前冻结独立种子确认方案。

## v5 的核心修订

| 评审意见 | 本版处理 |
|---|---|
| “necessary” 过强 | 新确认实验不支持方向一致的收益；标题和结论改为 task/model dependent |
| baseline 不公平（self-state vs memory 混淆了特权 framing） | E9 显示标签效应小、位置效应更大；新增行为 neutral-block 对照后，1.5B 的下降可由 81-token 上下文负担复现 |
| 因果链没闭合 | E10 保留为探索性干预；论文明确说明 occupancy summary 不是充分中介 |
| 统计设计（伪重复／单位／多重比较／预声明端点） | 回顾性结果按 5 个 seed clusters 修正；确认实验用独立 seeds 100--109、冻结端点和 exact paired tests |
| 新实验是否复现旧结论 | 1.5B：self−gated = −.079，p=.0098；7B：四组 .995–1.000，无法估计效应；neutral 81-token block 与 state block 相同 |
| 相关工作只有 14 篇 | 扩到 **68 篇**，覆盖评审点名的 10 个方向 |
| 摘要过长／营销式措辞 | 摘要和贡献重写为可核查的事实陈述；删除版本辩解、口号和拟人化包装 |
| §8 说部署已完成、Limitations 说不存在 | 统一为：**21 个模拟日的部署已完成；多周 wall-clock 部署未完成** |

最重要的结论不再是“broadcast 有效”，而是：旧正效应不能外推；小模型对额外上下文出现非语义性的选项偏差，大模型在新任务上处于天花板；self-query 不能诊断这种 work-turn 差异。

## 文件

- `main.tex` — 规范版（唯一需要编辑的文件）
- `arxiv/main.tex`、`tmlr/main.tex` — **由 `python make_variants.py` 生成，别手改**
  （v3 时期这三份已经漂移：arXiv/TMLR 版还停在旧标题和旧摘要）
- TMLR 版默认**已匿名**（作者块 + 仓库链接被替换并自检）；camera-ready 用
  `python make_variants.py --deanonymize`
- 编译：`tectonic main.tex`（官方 `tmlr.sty` 已加入）

## 推荐路径

1. **TMLR 作主投**。其标准强调主张是否被证据支持，适合当前“行为证据 + 探索性机制分析”的结构。
   - 提交稿必须匿名（`make_variants.py` 默认输出即匿名版）
   - 正文超 12 页会进较长审稿周期；当前 ~22 页（含约 3 页参考文献）
   - TMLR 投稿在评审后通常公开保留，投前需接受这一点
2. **ICLR 2027 作备选**，前提是增加第二个模型家族和一个经校准、7B 不饱和的任务集。
3. **不赶 AAAI-27**：full paper 截止 2026-07-28、abstract 截止 07-21（已过），
   且主会正文约 7 页 —— 当前的问题是要补实验而不是压页数。
4. **arXiv**：可先挂（primary `cs.LG`，cross-list `cs.CL`/`cs.AI`）。
   先挂预印本前确认目标 venue 的匿名与 prior-publication 政策；TMLR 允许预印本，
   但提交稿本身仍需匿名。

## 投稿前卡点

- [ ] **部署研究的 per-cohort 原始数据入库**。当前 `research/longitudinal/runs/` 被 gitignore，
      仓库里只有 per-arm 汇总 + WD readouts，而 Data Availability 段原本承诺了
      raw per-turn trajectory。v4 已先把该段改成如实描述现状；要么补传数据，要么保持收窄措辞。
- [x] **臂盲评分诊断**。本地 1.5B judge 对三类 work-turn 样本均 100% 一致；整体 85%，
      在被截断的 commitment/pace 长答案上显著下降。正文只用它验证 forced-choice endpoint，
      不把它包装为独立人工标注。
- [ ] **审一遍 "Use of AI Assistance" 段**，按你实际的核查程度校准措辞。
- [ ] **参考文献核对**：68 条里多数是常见文献（已抽查若干条的年份/venue），
      投稿前建议用 DBLP/Semantic Scholar 批量核一遍。
- [ ] arXiv endorsement：已获得（cs.AI）。若 primary 改 `cs.LG` 需确认背书是否覆盖。
- [ ] **将本地 v5 结果同步到 public 仓库**。仓库虽然已公开，但线上 README、论文和
      实验结果仍是旧版本；当前 PDF 已链接该仓库，因此应先同步再提交 arXiv。

## arXiv 元数据

- **License**：CC BY 4.0
- **分类**：primary `cs.LG`；cross-list `cs.CL`。不主动添加 `cs.AI`，其官方范围说明
  明确将 Machine Learning 和 Computation and Language 分到独立类别。
- **Title**：Persistent Agent Self-State Has Task- and Model-Dependent Effects on Value Adherence
- **Authors**：Wang Bihao (Independent Researcher)
- **Comments**：`24 pages, 5 figures. Code and data: https://github.com/oratis/externalizing-the-workspace`
- **投稿包**：`arxiv-source-v5-2026-08.tar.gz`（已独立解包编译；自包含，内嵌 thebibliography）

### TMLR 步骤
1. `tmlr.sty` 已从官方模板加入；本文参考文献内嵌，不需要 `tmlr.bst`
2. `python make_variants.py` 生成匿名版 → `tectonic main.tex` 编译核对
3. OpenReview（TMLR track）提交；可建议做可解释性/agent 的 Action Editor；滚动评审约 2 个月出首轮
