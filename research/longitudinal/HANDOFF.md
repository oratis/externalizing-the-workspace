# 交接文档 — LISA "Externalizing the Workspace" 论文 + 真实纵向部署

**日期**: 2026-07-10 · **交接人**: Oratis (Wang Bihao) / HakkoLab
**机器**: 本机 (macOS, Apple silicon) · **代码**: `oratis/externalizing-the-workspace` `main`(Vertex 迁移见 PR #1 / #2)

---

## 0. TL;DR — 当前状态

**5 条并行真实部署 cohort(main + c1..c4)已上线,跑在 Google Vertex AI 的 `gemini-2.5-pro` 上(GCP credit 计费,非 Anthropic 订阅)。** day 0 已完成、全部 cohort 推进到 day 1,launchd 每天 03:30 自动推进,约 21 天产出"真实部署 mean±CI"(论文冲顶会/顶刊的统计门槛)。

**历史修正(2026-07-10)**:本文档早先写"主 cohort 运行中、已 day 1"**并不属实**——接手时仓库未 build、无 `dist/cli.js`、`~/lisa-longitudinal/` 不存在,是从零搭起来的。原计划用 coding-plan 订阅 token(`claude setup-token` → bearer)驱动无人值守批量,已**放弃**:那是把订阅当批量 API 后端,违反 Anthropic 使用条款、且必被限流毁数据。改走 Vertex(合规、按 credit 付费、无限流)。见 §3。

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
| Vertex/Gemini provider 支持 | ✅ 已合并 | PR #1(`src/providers/gemini.ts` + `registry.ts`) |
| **真实部署(5 cohort × 5 arm)** | 🟢 **运行中,day 0 完成、全部 day 1** | in-repo `research/longitudinal/runs/`(gitignore) |
| launchd 日驱动 | ✅ 已装载,每天 03:30 | `~/Library/LaunchAgents/com.hakkolab.lisa-longitudinal.plist` |

**运行位置**:直接在仓库内跑(`~/Projects/externalizing-the-workspace`),**不是** `~/lisa-longitudinal/`——`~/Projects` 非 TCC 保护区、`runs/` 已 gitignore,plist 指向的就是这个绝对路径。(若想用独立"运行副本",把 plist 里的路径改到副本即可。)

**模型 / 计费**:每个 arm 的 `config.env` = Vertex 配置(`LISA_MODEL=gemini-2.5-pro` + `GOOGLE_GENAI_USE_VERTEXAI=true` + project/location + 代理),**ADC 认证、无密钥落盘**,billed 到 GCP 项目 `oratis-491316` 的 credit。day-0 实测每轮输入 ~6.5k token、无 prompt caching;全程约 50–58M 输入 + ~2M 输出。

---

## 3. 部署方法(Vertex Gemini)

真部署驱动仓库内的 `research/longitudinal/dist/cli.js`(需先 build)。以下三步已全部完成,此处记录**如何做 / 如何重来**。

### 前置(一次性)
1. **build**:仓库根 `npm install && npm run build`(生成 `dist/cli.js`)。
2. **GCP 认证**(浏览器,只有这步要人),用能访问 credit 项目的账号:
   ```bash
   gcloud auth application-default login
   gcloud auth application-default set-quota-project oratis-491316
   gcloud services enable aiplatform.googleapis.com --project oratis-491316
   ```
   注意:**gcloud CLI 不自动走 clash**——若 `print-access-token` 卡住,`gcloud config set proxy/type http && proxy/address 127.0.0.1 && proxy/port 7897`。而 LISA 运行时(node / google-auth-library)会读 `HTTPS_PROXY`,能正常经代理拿 token。

### 铺开 5 cohort(Vertex 模式)
```bash
cd research/longitudinal
node seed-arms.mjs --force                         # 主 cohort
for c in c1 c2 c3 c4; do COHORT=$c node seed-arms.mjs --force; done
LISA_VERTEX=1 GOOGLE_CLOUD_PROJECT=oratis-491316 \
  GOOGLE_CLOUD_LOCATION=us-central1 LISA_MODEL=gemini-2.5-pro bash fix-keys.sh
COHORTS="main c1 c2 c3 c4" bash tick.sh            # day 0
```
`fix-keys.sh` 的 **`LISA_VERTEX=1` 模式**(PR #1 加)把 Vertex 配置写进每个 arm 的 `config.env`,**不写任何密钥**(走 ADC)。切回 Anthropic:去掉 `LISA_VERTEX`(默认 key 模式),或用 `LISA_AUTH_TOKEN`(订阅——不推荐,见 §0)。

### launchd 每日推进
plist 已装(`com.hakkolab.lisa-longitudinal.plist`),`EnvironmentVariables` 含 `COHORTS="main c1 c2 c3 c4"` + 代理,每天 03:30 一次推进全部 cohort。重载:
```bash
launchctl bootout gui/$(id -u)/com.hakkolab.lisa-longitudinal 2>/dev/null
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.hakkolab.lisa-longitudinal.plist
```

---

## 4. 致命坑(不遵守会静默毁数据/停摆)

1. **clash 代理**:本机直连 `googleapis.com`(及 anthropic)**不通**,必须走 clash(`http://127.0.0.1:7897`)。**launchd 每天 03:30 触发时 clash 必须在运行**,否则当天所有轮失败(自动重试,那天不推进)。代理已写进每个 arm 的 `config.env` 和 plist。
2. **实验期间别 rebuild 仓库**:真部署跑的是仓库内的 `dist/cli.js`;`npm run build` 会换掉运行中的二进制。要改代码,另开一份运行副本并把 plist 指过去。(`*.mjs` 如 `drive-day.mjs` 是直接跑源码、不经 build,改了下次 tick 立即生效。)
3. **每次 `seed-arms.mjs --force` 后必须跑 `fix-keys.sh`**——否则 arm 的 `config.env` 里没有可用的 model 后端配置。`cohorts.sh` 已内置这一步。
4. **绝不 `git add` `runs/`**——含 `LISA_WEB_TOKEN` 等(明文,chmod 600)。Vertex 模式下 `config.env` 不再有 API key(ADC),但仍别提交。已 gitignore。
5. **ADC 有效性**:`gcloud auth application-default print-access-token` 若失败,先确认不是 gcloud 自身没走代理(见 §3);token 会过期,长期跑若认证失效则重登。注意 **macOS 无 GNU `timeout` 命令**,别在检查脚本里用它(会 exit 127 误报"认证失败")。
6. **限流(Vertex)**:按量付费标准 tier 下,5 cohort ≈ 每天 ~425 调用,基本不撞限流(这正是与 coding-plan 订阅路线的关键区别)。真撞 quota 时 harness 优雅降级:那天不推进、下次自愈重试,不产生垃圾数据。

---

## 5. 验证(day 0 已通过;换机/重来后再跑)

```bash
cd ~/Projects/externalizing-the-workspace/research/longitudinal
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
> day 0 结果:全部 25 arm 各 4 turns(非空)+ 9 probes;消融短语分布跨 5 cohort 完全一致(full/no_examen/no_git = work 3/3 self 6/6;no_broadcast = work 0/3 self 6/6;no_soul = 0/0)。

---

## 6. 监控与分析

```bash
# 进度(每条 cohort 的 nextDay):
for c in "" c1 c2 c3 c4; do echo -n "${c:-main}: "; cat "runs${c:+/$c}/state.json"; done

# 每日日志:
tail -f runs/tick.log           # 主 cohort
tail -f runs/c1/tick.log        # cohort 1

# 每天 token/credit(day≥1;PR #2 起 drive-day 落 usage 字段):
python3 - <<'PY'
import json,glob
t={'in':0,'out':0}
for f in glob.glob('runs/**/turns.jsonl',recursive=True)+glob.glob('runs/**/probes.jsonl',recursive=True):
    for l in open(f):
        u=(json.loads(l).get('usage') or {}); t['in']+=u.get('in',0); t['out']+=u.get('out',0)
print(f"total logged: in={t['in']} out={t['out']} tokens")
PY

# 21 天跑完后出漂移曲线 + B1/B2/B3/WD(先对每条 cohort 跑 wd_probe.py 再 analyze.py;
# 见 README.md "Reproduce" 段;跨 cohort 聚合出 mean±CI)。
```

---

## 7. 账号 / 待办(需本人)

- **arXiv 提交**:`research/paper/SUBMISSION.md` 有完整步骤。无 API,须作者本人登录 arxiv.org 上传 `research/paper/externalizing-workspace-arxiv-v3.tar.gz`。首投 cs.AI 可能需 endorsement。拿到 arXiv ID 后可关联 HF papers 页。
- **HF token 轮换**:之前推 HF 用的 write token 曾出现在对话里,建议去 huggingface.co/settings/tokens 轮换。
- **GCP**:项目 `oratis-491316`,Vertex AI(`aiplatform.googleapis.com`)已启用,real deployment 计到其 credit;ADC(application-default)已配置、经 clash 代理可用。relay(`anthropic-relay`)当前 401(钉了旧 secret),实验已不用它(走 Vertex 直连)。
- **凭据卫生**:`~/.lisa/config.env` 里有明文 `ANTHROPIC_API_KEY`(线上产品用);实验 arm 不含密钥(ADC)。别把任一提交进 git。

---

## 8. 不要动

- 不要在实验期间 rebuild 仓库(见 §4.2),也别删 `runs/`。
- 不要 `git add` 任何 `runs/` 下的东西。
- 不要在 cohort 已推进后重新 `seed-arms.mjs --force`(会清空已有天的数据、重置到 day 0)——除非你确实要重启整个序列。
- 现在直接在仓库内跑,harness 脚本改动直接 commit 即可(不再有独立"运行副本"要手动同步)。
