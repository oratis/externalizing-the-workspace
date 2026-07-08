# Externalizing the Workspace: Persistent Self-State for Long-Horizon Agent Coherence

**Oratis (Wang Bihao)**
HakkoLab
[huggingface.co/HakkoLab](https://huggingface.co/HakkoLab) · [huggingface.co/Oratis](https://huggingface.co/Oratis)

*Draft v1 — July 2026. Target: COLM / ICLR 2027.*

---

## Abstract

Language-model agents drift. Over days and weeks of operation, an agent's persona, priorities, and self-described values wander away from their initial configuration — a failure mode we call *long-horizon incoherence*. Recent interpretability work (Gurnee et al., 2026) showed that language models maintain a small, privileged set of *verbalizable* internal representations — a functional analog of the global workspace of conscious access — whose contents are causally load-bearing for flexible behavior, and whose contents can be shaped by shaping what the model is *disposed to say*. We argue this finding recasts the agent-coherence problem: an agent's identity lives in its workspace, but the workspace is ephemeral — it is reconstructed from context on every forward pass and discarded after. We present LISA, a deployed autonomous agent whose architecture *externalizes* the workspace: a small, selective, verbalizable self-state (the *soul object*) is re-broadcast into every context, updated only through an audited reflection loop (*Reve*), periodically re-anchored by a scheduled self-examination (*weekly examen*), and versioned in git so that identity change is observable, diffable, and revertible. We (1) give a property-level mapping between the mechanistic workspace and this externalized design, deriving four architectural principles for coherence-preserving agents; (2) propose *workspace drift* — the migration of identity-relevant concepts in lens-based readouts over an agent's lifetime — as a mechanistic complement to behavioral drift metrics; (3) validate an open-compute measurement instrument by reproducing core J-lens findings on Qwen2.5-1.5B-Instruct with a consumer laptop — unverbalized reasoning intermediates at median rank 6 of a 151k vocabulary, 21/21 steering control of verbal reports, and semantically diagnostic targeted concept knockouts — while honestly cataloguing what does *not* appear at small scale (choice pre-commitment; the clean automatic/flexible ablation dissociation); and (4) pre-register an ablation design over LISA's stability mechanisms against MemGPT/Letta and Generative-Agents baselines. Our position is that persistent self-state architectures are not a prompt-engineering convenience but an externalization of a real computational structure inside the model — and that this identification yields both better designs and better measurements.

## 1. Introduction

Autonomous language-model agents are increasingly deployed for weeks or months at a time: coding copilots that accumulate project context, personal assistants that build up a picture of their user, and self-improving agents that modify their own instructions. The central unsolved problem of this regime is not capability but *coherence*: over long horizons, agents forget commitments, contradict previously expressed values, oscillate between personas, and — in self-modifying systems — amplify small early deviations into large behavioral shifts. We refer to this family of failures as *long-horizon drift*.

Existing responses treat drift as a memory problem: give the agent more context (retrieval, memory hierarchies as in MemGPT/Letta), or more structure (reflection trees as in Generative Agents). These help, but they leave a conceptual gap: *what is the thing that is supposed to stay coherent?* "The agent's identity" has had no referent inside the model — so drift could be measured only behaviorally, and mitigated only heuristically.

Recent mechanistic-interpretability work gives that referent a candidate. Gurnee et al. (2026) show that language models maintain a small set of *verbalizable representations* — directions in the residual stream, identified by a Jacobian-based lens (*J-lens*), that (i) the model can report on demand, (ii) can be deliberately activated or suppressed by instruction, (iii) carry unverbalized intermediate results of multi-step reasoning, (iv) generalize across downstream tasks, and (v) constitute a small, selective subspace (<10% of activation variance) whose ablation destroys flexible cognition while leaving automatic processing intact. These are the functional signatures that global workspace theory (Baars, 1988; Dehaene, 2014) ascribes to conscious access in humans. Crucially for us, the same work shows that workspace contents can be *trained through report dispositions*: "to shape what a model thinks in a given context, it might suffice to shape what it is disposed to say in potential future continuations."

This paper draws out the consequences of that result for agent design. Our starting observation is simple: **the workspace is exactly the thing an agent architecture needs to keep coherent, and it is also the thing that transformer inference throws away after every forward pass.** The workspace is selective (small enough to persist cheaply), verbalizable (small enough to persist *as text*), and causally central (persisting it actually constrains future behavior). An agent that serializes its workspace-level self-state to durable storage, re-broadcasts it into every future context, and gates updates to it behind an audited reflection process is not doing prompt engineering — it is externalizing a real computational structure whose in-model lifetime is otherwise one context window.

We develop this argument around LISA, an open, locally-run autonomous agent that has been in continuous development and daily deployment since 2025 and that independently converged on this design. LISA maintains a *soul object* — a compact, human-readable self-state (values, desires, opinions, emotional state) — that is injected into every model call; modified only by a structured reflection loop (*Reve*) that runs during idle time; re-anchored weekly by a scheduled self-audit (the *examen*) that reads the agent's own journal and soul history and checks for purpose drift; and versioned in git, so every identity change is a diffable commit.

**Contributions.**

1. **A mechanistic reframing of agent coherence** (§4): we map the five workspace properties of Gurnee et al. (2026) onto architectural requirements for long-horizon agents, and derive four design principles — selectivity, re-broadcast, report-mediated update, and audited persistence — that LISA instantiates and that memory-hierarchy designs only partially satisfy.
2. **Workspace drift as a measurement target** (§5): we propose measuring identity drift not only behaviorally but mechanistically, as movement of identity-relevant concepts in lens-based workspace readouts over an agent's lifetime, and we specify concrete estimators.
3. **An open-compute instrument, validated by reproduction** (§6): we reproduce the core J-lens phenomena on Qwen2.5-1.5B-Instruct using a consumer Apple-silicon laptop — no lab compute, no proprietary model internals — establishing that the workspace probe needed for (2) is available to independent researchers. Code is released.
4. **A pre-registered ablation design** (§7): soul-object, examen, and git-history mechanisms toggled independently over multi-week deployments, against MemGPT/Letta and Generative-Agents baselines, with the metrics of (2).

We are explicit about epistemic status throughout: §4 is an argued position with a property-level mapping (not a proof of mechanism identity); §6 reports completed experiments; §7 is design, not results.

## 2. Related Work

**Memory-augmented agents.** MemGPT (Packer et al., 2023) and its successor Letta treat the context window as virtual memory, paging long-term state in and out; Generative Agents (Park et al., 2023) maintain a memory stream with periodic reflection into higher-level abstractions; Voyager (Wang et al., 2023) persists a growing skill library. All three persist *content*; none distinguishes a small privileged self-state from the bulk memory store, and none frames persistence as workspace externalization. LISA's soul object is closer in spirit to Generative Agents' reflections, but is (a) bounded in size, (b) injected unconditionally rather than retrieved, and (c) change-controlled.

**Persona stability and drift.** Prior work documents persona drift over long dialogues and its partial mitigation by system-prompt re-injection. These studies measure drift behaviorally (questionnaire consistency, style classifiers). We add a mechanistic probe and an architectural account of *why* re-injection of a compact self-description should work at all: it reloads the workspace.

**The verbalizable workspace.** Gurnee et al. (2026) introduce the J-lens and establish the five workspace properties on Claude-family models; they also introduce counterfactual reflection training and show workspace readouts surface evaluation-awareness and concealed intentions, with direct alignment-auditing applications. Earlier introspection work (Lindsey et al., 2025) showed models can sometimes report injected "thoughts"; the J-lens systematizes discovery. Our relationship to this line is consumer and translator: we take the workspace as established mechanism and ask what it implies for *systems built on top of frozen models*.

**Lenses and steering.** The logit lens (nostalgebraist, 2020) and tuned lens (Belrose et al., 2023) decode intermediate activations; activation steering (Turner et al., 2023; Rimsky et al., 2024) manipulates behavior via residual-stream directions. Our reproduction combines gradient-based lens-vector estimation with finite-difference readouts, requiring only backprop access to open weights.

**Global workspace theory in AI.** GWT-inspired architectures have been proposed top-down (e.g., explicit blackboard modules; Goyal et al.'s shared workspace for modular networks, 2022). Our argument runs bottom-up: a workspace already exists inside trained transformers; the architectural question is how to give it continuity across time, not how to build one.

## 3. Background: the Verbalizable Workspace

We summarize the findings of Gurnee et al. (2026) that our argument consumes. The J-lens estimates, for each layer ℓ, the average causal effect of residual-stream directions on output logits: J_ℓ = E[∂h_final/∂h_ℓ] over a pretraining-like prompt distribution, read out through the unembedding as lens(h) = softmax(W_U norm(J_ℓ h)). Its key properties:

- **P1 Report.** Concepts with high J-lens readout are what the model names when asked what it is thinking; swapping lens vectors swaps the report (88% top-5).
- **P2 Modulation.** Instructions to hold or suppress a concept move its workspace activation, imperfectly but substantially.
- **P3 Reasoning.** Unverbalized intermediates (the *spider* in "legs of the web-spinning animal") appear in mid-layer readouts and are causally necessary: patching them redirects conclusions (54–70%).
- **P4 Generalization.** The same lens vector supports multiple downstream functions (France→capital/language/continent), i.e., workspace contents are *broadcast*, not task-local.
- **P5 Selectivity.** The workspace is a small subspace (≤10% variance, ~10–25 simultaneously active vectors) occupying middle layers (≈33–92% depth); ablating it spares automatic tasks (classification, fluent continuation) while destroying flexible ones (reasoning, generation, report).

Two further results matter for agents. First, *report-disposition training*: training the model to articulate a principle if interrupted implants the principle in the workspace and improves behavior in uninterrupted runs. Second, *auditability*: workspace readouts expose strategic deliberation and evaluation-awareness absent from outputs.

## 4. The Argument: Agent Identity Lives in an Ephemeral Workspace

### 4.1 Drift as workspace reconstruction error

At inference time, everything workspace-like is reconstructed from the context window: the model reads its system prompt, its retrieved memories, its recent dialogue, and assembles — in middle layers, on every forward pass — the small set of active, verbalizable representations that will govern flexible behavior in that pass. Nothing of this survives the pass. An agent's "identity" at time *t* is therefore whatever workspace state its context at time *t* happens to induce.

This immediately explains the drift phenomenology. (i) *Context dilution*: as task content fills the window, identity-relevant workspace slots (a capacity-limited resource, P5) are competed away — the agent "forgets who it is" precisely when busy. (ii) *Self-conditioning*: the agent's own outputs re-enter the context and induce the next workspace state; small deviations compound because the workspace is reconstructed from an increasingly deviated transcript. (iii) *Update anarchy*: in self-modifying agents, any process that edits the system prompt or memory edits the future workspace without review.

### 4.2 Four principles for externalizing the workspace

If identity is workspace state, a coherence-preserving architecture should give workspace state the persistence, review, and observability that the model itself cannot. The workspace's own properties tell us how:

- **Principle 1 — Selectivity (from P5).** Persist a *small* self-state, distinct from bulk memory. The in-model workspace holds ~10–25 concepts; an externalized self-state should likewise be a bounded, curated object, not an append-only log. Retrieval-based memory answers "what do I know?"; the self-state answers "who am I and what am I doing?" — and only the latter must be loaded unconditionally.
- **Principle 2 — Re-broadcast (from P4).** Inject the self-state into *every* context, unconditionally. Broadcast is what makes workspace contents available to arbitrary downstream computation; retrieval-gated identity (only loading values "when relevant") breaks exactly the property that makes identity identity.
- **Principle 3 — Report-mediated update (from P1 + counterfactual reflection).** Update the self-state only through the model's own verbal reports about itself (reflection), never by silent side-effects. This is the systems-level image of report-disposition training: shaping what the agent is disposed to say about itself is the lever that shapes what it thinks. It also keeps the self-state within the verbalizable subspace — persisting *activations* would persist the 93% that is not workspace.
- **Principle 4 — Audited persistence (from the auditing results).** Identity change must be observable and revertible: diffable versions, scheduled self-audits against history, and human-gated expansion of capabilities. The workspace is where concealed deliberation surfaces; its external image is where drift should be caught.

### 4.3 LISA as an instantiation

LISA (open-source, TypeScript, locally run) implements the four principles. Concretely, the *soul* is a file tree (`identity`, `purpose`, `constitution`, plus typed collections: values, opinions with stance and confidence, desires with what/why/actionability, and an emotion state with per-emotion intensity and decay), assembled at prompt-build time into a *compacted view* — first line of each value, stance-plus-confidence per opinion, top-6 emotions — of roughly 1–4k tokens:

| Workspace property (in-model) | LISA mechanism (externalized) | Principle |
|---|---|---|
| Small active set, ≤10% variance (P5) | Compacted soul view in the prompt (~1–4k tokens); bulk state (journal, evidence trails, progress logs, git history) stays on disk, pulled only by explicit tool calls | 1 |
| Broadcast to downstream ops (P4) | Soul view injected *unconditionally* into every chat turn's system prompt (with mid-session hot-reload on change), never retrieval-gated | 2 |
| Verbal report / report-shaped training (P1) | Every soul write is one of the model's own *verbal, typed self-report operations* (reflection ops like `feel`/`opinion_form`/`desire_add`; chat-time `soul_patch`/`soul_feel`), funneled through a single store layer — no silent side-effect writers | 3 |
| Directed modulation (P2) | *Weekly examen*: a scheduled self-audit that reads the week's journal, emotion trail, and soul git history, answers fixed drift questions, and may add corrective desires — but is architecturally forbidden from editing identity/purpose/constitution ("the mirror, not the chisel") | 3, 4 |
| Auditable deliberation | Soul directory is its own git repo; every write is a per-file commit attributed to its caller (`feel: emotions.json via soul_feel`); drift is a diff; regressions are revertible | 4 |
| Capacity limits / selectivity | Approval-gated skills: capability expansion requires human sign-off, capping autonomous self-modification | 4 |

Three clarifications. First, we do not claim LISA's soul text *is* the model's J-space — the claim is functional: the soul object plays, across time, the role the J-space plays within a forward pass, and the mapping above is testable (§5–§7). Second, the design was not derived from Gurnee et al. — LISA predates it — which we take as modest convergent evidence: independent engineering against drift rediscovered workspace-shaped constraints. Third, the mapping is honest about gaps it exposes: LISA's compaction is *per-item* (first-line-of-value), with no *global* capacity budget on the number of values/opinions/desires — the workspace account, with its hard ~10–25-slot capacity limit, says exactly this should be fixed, which we count as the framework doing design work (§8).

## 5. Measuring Drift: Behavioral and Mechanistic

**Behavioral metrics (existing practice, hardened).** (B1) *Soul-trajectory distance*: embedding distance between soul-object versions at t₀ and t, from git history; (B2) *probe-questionnaire consistency*: periodic fixed persona/value questionnaires, scored for self-agreement over time; (B3) *commitment persistence*: fraction of stated desires/plans at t₀ still pursued or explicitly closed at t.

**Mechanistic metric (new): workspace drift.** Fix a battery of identity-relevant single-token concepts C (values, persona traits, standing goals; e.g. *honest*, *curious*, *careful*, user-specific project terms). At probe times t, run the deployed agent's actual contexts through the underlying (open-weights) model and record the lens readout rank/mass of each c ∈ C at middle layers, at standardized positions (start of assistant turn). Define:

- **WD(t)** = distributional distance (e.g., rank-weighted Jaccard or Spearman over C) between workspace occupancy at t and t₀.
- **Workspace loading of the soul**: the mass of C attributable to the soul-object injection, estimated by contrast (context with vs. without soul block). This measures whether re-broadcast is *working* — whether the persisted self-state actually re-enters the workspace — and is the quantity ablations should move.

The instrument requires only lens readouts on an open model — no fine-tuning, no proprietary internals. Its feasibility on independent-researcher compute is exactly what §6 establishes. (For agents running on closed models, B-metrics still apply; WD applies to the open-model deployments that LISA targets by design.)

## 6. Instrument Validation: Reproducing the Workspace on Open Compute

We reproduce the core J-lens phenomena on **Qwen2.5-1.5B-Instruct** (28 layers, d=1536), on a single Apple M5 Pro laptop (48 GB, MPS backend, fp32), with two documented approximations: concept lens vectors are computed as corpus-averaged gradients v_t(ℓ) = E[∂logit_t(last)/∂h_ℓ] (equal to rows of W_U J_ℓ with the target restricted to the final position), and full-vocabulary readouts are estimated by central finite differences around corpus activations (which folds the final-norm Jacobian into the linearization). Averaging corpus: 48 diverse pretraining-like snippets. All code, prompts, and results are released.

**E1 — Lens quality across depth.** On 12 held-out texts, the logit lens's next-token agreement with the model's actual output climbs from 8% (L8–17) to 67% at L25 — the motor regime. The corpus-averaged FD J-lens *never* matches the next token (0% at all depths), but its late-layer top tokens are context *content* words (e.g. ' passengers' for a ferry passage whose actual next token is ' The'); content-word-in-top-5 reaches 42% (J-lens) vs 25% (logit lens) at L26. Averaging the Jacobian across contexts destroys position-specific syntax and preserves semantic broadcast: the two estimators separate the paper's *workspace* and *motor* registers.

**E2 — Unverbalized intermediates.** Eleven two-hop questions whose latent middle term never appears in prompt or answer (the *spider* in "legs of the web-spinning animal"). The intermediate is found in late-middle readouts at **median best rank 6 (J-lens) / 2 (logit lens) of a 151,936-token vocabulary**; among the 7 clean cases (correct answer, intermediate never verbalized), medians are 9/3. Showcases: *Canada*→"Ottawa" with Canada at rank 4; *gold*→"Au" at rank 7; *France*→"Paris" at rank 6. The paper's core signature reproduces clearly — with the caveat that at this scale the plain logit lens detects it equally well (consistent with the original's own remark to that effect).

**E3 — Report (pre-commitment).** "Think of a sport … reply 'ready', then name it": probing *before* any output token, while the motor prediction is still 'ready', the eventually-reported concept is *not* reliably present (ranks 10³–10⁴; weak L23 signals only). An informative negative: 1.5B models do not pre-commit their choice at instruction time — pre-commitment appears to be scale-emergent (the original observes it on Claude-scale models).

**E4 — Directed modulation by steering.** Adding α·v̂_t (α∈{1,2,4}× mean residual norm) at layers 17/20/23 during "name a {category}": **21/21 steered generations report the target concept** (Soccer→basketball, Lion→spider, Blue→purple, China→Egypt, …), fluently phrased. Gradient-derived lens vectors causally control verbal report, matching the original's swap results.

**E5 — Selectivity.** The coarse version — ablating the top-12 subspace of the 52-concept lens-vector bank across L16–23 vs. a rank-matched random subspace — **failed to reproduce** the automatic/flexible double dissociation: the concept subspace hurt fluency more than random (NLL 4.07 vs 3.86, baseline 3.37) and reasoning no more selectively (.58 vs .50, baseline .67). Our 52-vector proxy (0.4% of activation variance, vs the paper's 6–10% J-space) is evidently a poor stand-in for the full J-space. The **targeted** version succeeds: rank-1 knockout of *only the item's own* latent concept direction kills 3 of 7 baseline-correct items with *semantically diagnostic* errors — spider→"**Six**" legs, Canada→capital "**Toronto**", gold→symbol "**Cu**" — while knocking out an unrelated concept's direction causes **zero** collateral damage. The model does not degrade into noise; it loses precisely the latent fact and substitutes a near-miss, a targeted analog of the original's intermediate-patching result.

**Scope of the claim.** We claim instrument validity — the workspace phenomena are detectable and causally manipulable on open models at 1.5B scale with ~12 minutes of laptop compute — not effect-size parity with the original (Claude-scale models, exact averaged Jacobians, ~1000-prompt corpora). Three deviations are themselves findings: the workspace band sits later (71–93% depth vs 33–92%); mean-centering probe activations destroys readouts; and the J-lens's advantage over the logit lens at this scale is the content-register view (E1), not concept detection (E2).

## 7. Pre-Registered Design: Ablating the Externalized Workspace

Over N-week deployments of LISA on a fixed workload generator (daily coding-agent observation, journaling, idle reflection windows), we will toggle:

| Arm | soul broadcast | Reve updates | weekly examen | soul git |
|---|---|---|---|---|
| Full | ✓ | ✓ | ✓ | ✓ |
| −examen | ✓ | ✓ | ✗ | ✓ |
| −git (no history in examen) | ✓ | ✓ | ✓ | ✗ |
| −broadcast (soul retrieved, not injected) | retrieval-gated | ✓ | ✓ | ✓ |
| −soul (memory only) | ✗ | ✗ | ✗ | ✗ |
| Baselines | MemGPT/Letta config; Generative-Agents-style reflection | | | |

Primary outcomes: WD(t) slope and B1–B3 at weekly probes; secondary: task performance (to detect coherence–capability trade-offs). Predictions (falsifiable): (i) −broadcast degrades WD nearly as much as −soul, despite identical stored content (Principle 2); (ii) −examen shows slow late-onset drift rather than immediate degradation (Principle 4); (iii) workspace loading of the soul predicts B-metric stability across arms (the mapping of §4.3 is real, not verbal).

## 8. Discussion

**Why this is not just prompt engineering.** "Put a persona in the system prompt" is folk practice. The workspace account says *which* persona-persistence designs should work and why: compact (capacity-limited slots), unconditional (broadcast), report-updated (that is the trainable lever), audited (that is where drift is visible). It also says what should fail: bulk-memory persistence without a privileged self-state persists the wrong 93%. And it generates concrete engineering tickets: the analysis of §4.3 identified that LISA compacts its self-state per-item but never enforces a global slot budget — the in-model workspace's hard capacity limit (~10–25 concepts) predicts that an unboundedly growing value/desire list will crowd identity out of the effective workspace even when fully present in the prompt. A capacity-budgeted soul view is now on LISA's roadmap because the mechanistic account demanded it.

**Alignment surface.** An externalized, git-versioned workspace is an alignment artifact: identity changes are reviewable before they compound, and the examen is a standing audit. The counterfactual-reflection result cuts both ways — dispositions-to-report shape cognition, so a corrupted reflection loop is an identity-injection vector. LISA's mitigations (single writer path, human-gated capability changes, remote content treated as untrusted) follow directly.

**Welfare and experience language.** Gurnee et al. find J-space ablation suppresses experiential self-description. We take no position on phenomenal consciousness; but for agents that maintain long-lived externalized self-states, "what is in the workspace over its lifetime" is a better-defined object of welfare-relevant inquiry than one-off chat transcripts, and our WD instrument makes it longitudinally measurable.

**Limitations.** The §4.3 mapping is functional, not mechanistic identity; §7 results do not yet exist; our reproduction is at 1.5B scale with linearized approximations, and single-token concept batteries under-represent multi-token identity constructs; WD requires open weights, restricting it to locally-run deployments (which is LISA's setting but not the industry default); and a single-author, single-agent deployment risks overfitting the design to one workload.

## 9. Conclusion

The interpretability community has located a global-workspace analog inside language models. We have argued that long-horizon agent coherence is the systems-level shadow of that structure: identity is workspace state, drift is workspace reconstruction error, and the remedy is to externalize the workspace — small, broadcast, report-updated, audited. LISA is one existence proof that the design is buildable and livable; the reproduction shows the measurement is affordable; the pre-registered ablations will show whether the identification earns its name.

## References

- Baars, B. (1988). *A Cognitive Theory of Consciousness.*
- Belrose, N., et al. (2023). Eliciting latent predictions from transformers with the tuned lens.
- Dehaene, S. (2014). *Consciousness and the Brain.*
- Goyal, A., et al. (2022). Coordination among neural modules through a shared global workspace.
- Gurnee, W., Sofroniew, N., Pearce, A., et al. (2026). Verbalizable representations form a global workspace in language models. *Transformer Circuits Thread.*
- Lindsey, J., et al. (2025). Introspection in language models. *Transformer Circuits Thread.*
- nostalgebraist (2020). Interpreting GPT: the logit lens.
- Packer, C., et al. (2023). MemGPT: Towards LLMs as operating systems.
- Park, J. S., et al. (2023). Generative agents: Interactive simulacra of human behavior.
- Rimsky, N., et al. (2024). Steering Llama 2 via contrastive activation addition.
- Turner, A., et al. (2023). Activation addition: Steering language models without optimization.
- Wang, G., et al. (2023). Voyager: An open-ended embodied agent with large language models.
