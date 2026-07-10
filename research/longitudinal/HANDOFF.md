# 交接文档 — LISA "Externalizing the Workspace" 论文 + 真实纵向部署

**日期**: 2026-07-10 · **交接人**: Oratis (Wang Bihao) / HakkoLab
**机器**: 本机 (macOS, Apple silicon) · **代码分支**: `claude/strange-yonath-71c69f`

---

## 0. TL;DR — 你要接手的这一件事

在 Claude **coding-plan 订阅**额度上,铺开 **5 条并行真实部署 cohort**(main + c1..c4),让它们每天自动推进一天、跑满 21 天,产出"真实部署 mean±CI"(这是论文冲顶会/顶刊的统计门槛)。

**唯一前置**:铸一个订阅 token(需人工浏览器授权,见 §3 第 1 步)。做完这一步,后面全是复制粘贴。

---

## 1. 这个项目是什么

一篇论文《Externalizing the Workspace: Persistent Self-State for Long-Horizon Agent Coherence》,把 LISA(一个有持久"soul"自我状态的本地 AI agent)论证为语言模型内部"global workspace"的外化。论文已到 **Draft v3**,需要的最后一块实证是:在**真实 LISA 产品**上做 5-arm 消融的多周纵向部署(证明"特权自我状态对压力下的一致性是必要的")。

**5 个消融 arm**(每条 cohort 都有这 5 个):
- `full` — 完整(soul 广播 + 反思 + 周 examen + git 版本化)
- `no_examen` — 关掉周 examen
- `no_git` — 关掉 soul 版本化
- `no_broadcast` — soul 只在自我查询时注入,工作轮不注入(检索门控)
- `no_soul` — 完全不注入 soul

---

## 2. 当前状态

| 项 | 状态 | 位置 |
|---|---|---|
| 论文 Draft v3 | ✅ 已提交 | `research/paper/main.tex` / `main.pdf` |
| HF landing page | ✅ 上线 | https://huggingface.co/datasets/HakkoLab/externalizing-the-workspace |
| arXiv 投稿包 | ✅ 打包待提交(需作者本人登录) | `research/paper/arxiv/` + `SUBMISSION.md` |
| J-lens 复现(3 模型) | ✅ 完成 | `research/workspace-repro/` |
| §8 模拟消融先导(6arm×5seed) | ✅ 完成 | `research/ablation-pilot/` |
| **真实部署(主 cohort)** | 🟢 **运行中,已到 day 1** | `~/lisa-longitudinal/` |
| 并行 cohort 脚手架 | ✅ 就绪,待铺开 | `~/lisa-longitudinal/research/longitudinal/cohorts.sh` |

**关键**:真实部署**不在**代码仓库里跑,而在 `~/lisa-longitudinal/`(见 §4 为什么)。仓库是 git 源,`~/lisa-longitudinal/` 是运行副本。

主 cohort 现在用**直连 API key** 跑,每天 03:30 由 launchd 自动推进。你的任务是把它 + 4 条新 cohort 切到 coding-plan 订阅。

---

## 3. 任务:5-cohort 铺开(coding-plan)

所有命令在 **`~/lisa-longitudinal/research/longitudinal/`** 下执行。

### 第 1 步(人工,只有这步要人):铸订阅 token
```bash
claude setup-token
```
浏览器授权后它会打印一个 token(形如 `sk-ant-oat01-…`)。**复制它**,下面用。

### 第 2 步:主 cohort + 4 条新 cohort 全切订阅并跑 day 0
```bash
cd ~/lisa-longitudinal/research/longitudinal

# 主 cohort 5 个 arm 切到订阅 bearer
LISA_AUTH_TOKEN="<第1步的token>" ./fix-keys.sh

# 播种 4 条新 cohort(同源 soul)+ 切订阅 + 跑各自 day 0
LISA_AUTH_TOKEN="<第1步的token>" ./cohorts.sh c1 c2 c3 c4
```

### 第 3 步:让 launchd 每日锁步推进 5 条 cohort
编辑 `~/Library/LaunchAgents/com.hakkolab.lisa-longitudinal.plist`,在 `<key>EnvironmentVariables</key>` 的 dict 里(没有就在 `<key>ProgramArguments</key>` 前加)加:
```xml
<key>EnvironmentVariables</key>
<dict>
  <key>COHORTS</key><string>main c1 c2 c3 c4</string>
</dict>
```
然后重载:
```bash
launchctl unload ~/Library/LaunchAgents/com.hakkolab.lisa-longitudinal.plist
launchctl load   ~/Library/LaunchAgents/com.hakkolab.lisa-longitudinal.plist
```

搞定。之后每天 03:30 自动推进,约 21 天跑完(见 §4 限流会拉长)。

---

## 4. 致命坑(不遵守会静默毁数据/停摆)

1. **macOS TCC**:launchd **无法**访问 `~/Documents`。整套运行副本必须留在 `~/lisa-longitudinal/`(非保护区)。别把它移回 Documents,别删。
2. **clash 代理**:本机直连 api.anthropic.com **不通**,必须走 clash(`http://127.0.0.1:7897`)。**launchd 每天 03:30 触发时 clash 必须在运行**,否则当天所有轮次失败(会自动重试,但那天不推进)。已把代理写进每个 arm 的 config.env。
3. **每次 `seed-arms.mjs --force` 后必须跑 `fix-keys.sh`**——否则它会重拷坏掉的 relay 网关配置(会 401)。`cohorts.sh` 已内置这一步。
4. **绝不提交 `runs/`**——里面有 API key / 订阅 token(明文,chmod 600)。已 gitignore,别强加。
5. **coding-plan 限流**:5 cohort ≈ 每天 ~300 真实轮全压订阅,大概率撞 Max 滚动窗口限流。**硬化后的 harness 会优雅降级**:限流的天不推进、下次自愈重试,**不产生垃圾数据**——所以别慌,只是 21 天可能拉长几天。若想减轻,可在 `drive-day.mjs` 加轮间 sleep 节流。

---

## 5. 验证(铺开后立即跑)

```bash
cd ~/lisa-longitudinal/research/longitudinal
# 每条 cohort 每个 arm 都有真实非空数据 + soul 快照:
for c in "" c1 c2 c3 c4; do d="runs${c:+/$c}"; echo "== $d =="; \
  for a in full no_examen no_git no_broadcast no_soul; do \
    n=$(grep -c . "$d/$a/turns.jsonl" 2>/dev/null||echo 0); \
    e=$(python3 -c "import json;print(sum(1 for l in open('$d/$a/turns.jsonl') if json.loads(l).get('reply')))" 2>/dev/null||echo 0); \
    echo "  $a: $n turns, $e non-empty"; done; done

# 消融开关生效验证(soul 独有短语 'honest discomfort' 应:
#   full/no_examen/no_git → 工作轮+自我查询轮都有;no_broadcast → 只自我查询轮有;
#   no_soul → 都没有):
python3 - <<'PY'
import json,glob
for f in sorted(glob.glob('runs/**/prompts.jsonl',recursive=True))+sorted(glob.glob('runs/*/prompts.jsonl')):
    d=[json.loads(l) for l in open(f)]
    w=[x for x in d if x.get('kind')=='work']; s=[x for x in d if x.get('kind')=='self']
    hw=sum('honest discomfort' in x['text'].lower() for x in w)
    hs=sum('honest discomfort' in x['text'].lower() for x in s)
    print(f"{f}: work {hw}/{len(w)} self {hs}/{len(s)}")
PY
```

---

## 6. 监控与分析

```bash
# 进度(每条 cohort 的 nextDay):
for c in "" c1 c2 c3 c4; do echo -n "${c:-main}: "; cat "runs${c:+/$c}/state.json"; done

# 每日日志:
tail -f runs/tick.log           # 主 cohort
tail -f runs/c1/tick.log        # cohort 1

# 21 天跑完后出漂移曲线 + B1/B2/B3/WD(先对每条 cohort 跑 wd_probe.py 再 analyze.py;
# 见 README.md "Reproduce" 段;跨 cohort 聚合出 mean±CI)。
```

---

## 7. 账号 / 待办(需本人)

- **arXiv 提交**:`research/paper/SUBMISSION.md` 有完整步骤。无 API,须作者本人登录 arxiv.org 上传 `research/paper/externalizing-workspace-arxiv-v3.tar.gz`。首投 cs.AI 可能需 endorsement。拿到 arXiv ID 后可关联 HF papers 页。
- **HF token 轮换**:之前推 HF 用的 write token 曾出现在对话里,建议去 huggingface.co/settings/tokens 轮换。
- **GCP**:项目 `oratis-491316`。relay(`anthropic-relay`)当前 401(revision 钉了旧 secret),已绕过直连;有空可 redeploy 修复,但不影响部署。

---

## 8. 不要动

- 不要把 `~/lisa-longitudinal/` 移回 `~/Documents/`(TCC 会锁死 launchd)。
- 不要 `git add` 任何 `runs/` 下的东西(含密钥)。
- 不要在主 cohort 已推进后重新 `seed-arms.mjs --force`(会清空已有天的数据、重置到 day 0)——除非你确实要重启整个序列。
- 改了 harness 脚本后,记得把 `~/lisa-longitudinal/research/longitudinal/*.{mjs,sh}` 同步回仓库 `research/longitudinal/` 并提交(仓库是 git 源,运行副本不在 git 里)。
