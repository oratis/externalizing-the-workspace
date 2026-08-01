# Externalizing the Workspace: Persistent Self-State for Long-Horizon Agent Coherence

> **Archived draft.** This file preserves version 2 for provenance and is not
> the submission manuscript. Several claims below, especially the pooled
> occupancy--behavior correlation and the longitudinal framing, were revised
> after re-analysis. The maintained source is `main.tex`.

**Oratis (Wang Bihao)**
HakkoLab
[huggingface.co/HakkoLab](https://huggingface.co/HakkoLab) · [huggingface.co/Oratis](https://huggingface.co/Oratis)

*Draft v2 — July 2026. Canonical source: `main.tex` (compiled PDF alongside). Changes from v1: claims softened to "functional externalization" framing per external review; new §7 (E6 workspace-loading experiments, completed); cross-family replication on Llama-3.2-1B (E7); expanded references; layout fixes.*

---

## Abstract

Language-model agents drift. Over days and weeks of operation, an agent's persona, priorities, and self-described values wander away from their initial configuration — a failure mode we call *long-horizon incoherence*. Recent interpretability work (Gurnee et al., 2026) showed that language models maintain a small, privileged set of *verbalizable* internal representations — a functional analog of the global workspace of conscious access — whose contents are causally load-bearing for flexible behavior, and whose contents can be shaped by shaping what the model is *disposed to say*. We argue this finding recasts the agent-coherence problem: the workspace is a natural referent for the thing that is supposed to stay coherent — yet it is ephemeral, reconstructed from context on every forward pass and discarded after. We propose modeling persistent self-state architectures as *functional externalizations* of the workspace, and present LISA, a deployed autonomous agent that instantiates the design: a small, selective, verbalizable self-state (the *soul object*) is re-broadcast into every context, updated only through audited verbal self-report operations, periodically re-anchored by a scheduled self-examination (*weekly examen*), and versioned in git so that identity change is observable, diffable, and revertible. We (1) give a property-level mapping between the mechanistic workspace and this externalized design, deriving four architectural principles for coherence-preserving agents; (2) propose *workspace drift* — the migration of identity-relevant concepts in lens-based readouts over an agent's lifetime — as a mechanistic complement to behavioral drift metrics; (3) validate an open-compute measurement instrument by reproducing core J-lens findings on Qwen2.5-1.5B-Instruct with a consumer laptop — unverbalized reasoning intermediates at median rank 6 of a 151k vocabulary, 21/21 steering control of verbal reports, and semantically diagnostic targeted concept knockouts — while honestly cataloguing what does *not* appear at small scale (choice pre-commitment; the clean automatic/flexible ablation dissociation); (4) demonstrate the metric end-to-end: injecting a compact LISA-style self-state measurably raises mid-band workspace occupancy of its identity concepts while a matched control battery is unmoved, the no-soul baseline's identity occupancy erodes under context dilution while the broadcast self-state holds, re-broadcast produces the strongest loading, and occupancy tracks soul-consistent behavior (r = −0.80); and (5) pre-register an ablation design over LISA's stability mechanisms against MemGPT/Letta and Generative-Agents baselines. Our position is that persistent self-state architectures are usefully modeled — and are best designed and measured — as externalizations of a real computational structure inside the model.

## 1. Introduction

Autonomous language-model agents are increasingly deployed for weeks or months at a time: coding copilots that accumulate project context, personal assistants that build up a picture of their user, and self-improving agents that modify their own instructions. The central unsolved problem of this regime is not capability but *coherence*: over long horizons, agents forget commitments, contradict previously expressed values, oscillate between personas, and — in self-modifying systems — amplify small early deviations into large behavioral shifts. We refer to this family of failures as *long-horizon drift*.

Existing responses treat drift as a memory problem: give the agent more context (retrieval, memory hierarchies as in MemGPT/Letta), or more structure (reflection trees as in Generative Agents). These help, but they leave a conceptual gap: *what is the thing that is supposed to stay coherent?* "The agent's identity" has had no referent inside the model — so drift could be measured only behaviorally, and mitigated only heuristically.

Recent mechanistic-interpretability work gives that referent a candidate. Gurnee et al. (2026) show that language models maintain a small set of *verbalizable representations* — directions in the residual stream, identified by a Jacobian-based lens (J-lens), that (i) the model can report on demand, (ii) can be deliberately activated or suppressed by instruction, (iii) carry unverbalized intermediate results of multi-step reasoning, (iv) generalize across downstream tasks, and (v) constitute a small, selective subspace (<10% of activation variance) whose ablation destroys flexible cognition while leaving automatic processing intact. These are the functional signatures that global workspace theory (Baars 1988; Dehaene 2014) ascribes to conscious access in humans. Crucially for us, the same work shows that workspace contents can be *trained through report dispositions*: "to shape what a model thinks in a given context, it might suffice to shape what it is disposed to say in potential future continuations."

This paper draws out the consequences of that result for agent design. Our starting observation: **the workspace is exactly the thing an agent architecture needs to keep coherent, and it is also the thing that transformer inference throws away after every forward pass.** The workspace is selective (small enough to persist cheaply), verbalizable (small enough to persist *as text*), and causally central (persisting it actually constrains future behavior). An agent that serializes its workspace-level self-state to durable storage, re-broadcasts it into every future context, and gates updates to it behind an audited reflection process is not doing prompt engineering — it is externalizing a real computational structure whose in-model lifetime is otherwise one context window.

We develop this argument around LISA, an open, locally-run autonomous agent in continuous development and daily deployment since 2025, which independently converged on this design.

**Contributions.**

1. **A mechanistic reframing of agent coherence** (§4): the five workspace properties mapped onto architectural requirements, yielding four design principles — selectivity, re-broadcast, report-mediated update, audited persistence.
2. **Workspace drift as a measurement target** (§5): identity drift measured mechanistically, as movement of identity-relevant concepts in lens-based workspace readouts, with concrete estimators.
3. **An open-compute instrument, validated by reproduction** (§6): core J-lens phenomena reproduced on Qwen2.5-1.5B-Instruct on a consumer laptop. Code released.
4. **The metric demonstrated end-to-end** (§7): soul injection loads the workspace selectively; broadcast protects identity against context dilution; re-broadcast restores it; occupancy tracks behavior. Cross-family replication on Llama-3.2-1B.
5. **A pre-registered ablation design** (§8): stability mechanisms toggled independently over multi-week deployments against MemGPT/Letta and Generative-Agents baselines.

Epistemic status: §4 is an argued position with a property-level mapping (not a proof of mechanism identity); §6–7 report completed experiments; §8 is design, not results.

## 2. Related Work

**Memory-augmented agents.** MemGPT (Packer et al., 2023) / Letta page long-term state in and out of context; Generative Agents (Park et al., 2023) reflect a memory stream into higher abstractions; Voyager (Wang et al., 2023) persists a skill library. All persist *content*; none distinguishes a small privileged self-state from bulk memory, and none frames persistence as workspace externalization.

**Persona stability and drift.** Role-play accounts treat persona as a superposed, context-conditioned construct (Shanahan et al., 2023); instruction/persona adherence measurably decays over long dialogs, partially mitigated by system-prompt re-injection (Li et al., COLM 2024). Cognitive-architecture treatments (CoALA; Sumers et al., 2024) systematize memory hierarchies but leave the privileged-self-state question open. This literature measures drift behaviorally; we add a mechanistic probe and an account of *why* re-injection works: it reloads the workspace.

**The verbalizable workspace.** Gurnee et al. (2026) establish the five workspace properties on Claude-family models, introduce counterfactual reflection training, and show workspace readouts surface evaluation-awareness — with direct auditing applications. Earlier introspection work (Lindsey, 2025) showed models can sometimes report injected "thoughts". We take the workspace as established mechanism and ask what it implies for *systems built on top of frozen models*.

**Lenses and steering.** Logit lens (nostalgebraist, 2020), tuned lens (Belrose et al., 2023); activation steering (Turner et al., 2023; Rimsky et al., 2024). Our reproduction combines gradient-based lens-vector estimation with finite-difference readouts, requiring only backprop access to open weights.

**Global workspace theory in AI.** GWT-inspired architectures have been built top-down (shared-workspace modular nets; Goyal et al., 2022). Our argument runs bottom-up: a workspace already exists inside trained transformers; the question is how to give it continuity across time.

## 3. Background: the Verbalizable Workspace

The J-lens estimates, per layer ℓ, the average causal effect of residual directions on output logits: J_ℓ = E[∂h_final/∂h_ℓ] over a pretraining-like distribution, read out as lens(h) = softmax(W_U norm(J_ℓ h)). Properties: **P1 Report** (swapping lens vectors swaps reports, 88% top-5); **P2 Modulation** (instructions move workspace activation); **P3 Reasoning** (unverbalized intermediates present and causally necessary — patching redirects conclusions 54–70%); **P4 Generalization** (one lens vector serves many downstream functions — broadcast); **P5 Selectivity** (≤10% variance, ~10–25 active slots, middle layers; ablation spares automatic tasks, destroys flexible ones). Plus: report-disposition training implants workspace content; workspace readouts expose concealed deliberation.

## 4. The Argument: Persistent Self-State as Functional Workspace Externalization

### 4.1 Drift as workspace reconstruction error

Everything workspace-like is reconstructed from the context window on every forward pass; nothing survives the pass. To the extent an agent's "identity" has a mechanistic referent at time t, the workspace state its context induces at t is the natural candidate — verbalizable, causally load-bearing, selective. We treat this identification as a working model to be tested (§7, §8), not as established mechanism. It explains the drift phenomenology: (i) *context dilution* — task content competes identity out of capacity-limited workspace slots; (ii) *self-conditioning* — deviated transcripts induce further-deviated workspace states; (iii) *update anarchy* — any process editing the system prompt edits the future workspace without review.

### 4.2 Four principles

1. **Selectivity (P5):** persist a *small*, curated self-state, distinct from bulk memory; only it loads unconditionally.
2. **Re-broadcast (P4):** inject it into *every* context; retrieval-gated identity breaks the property that makes identity identity.
3. **Report-mediated update (P1 + counterfactual reflection):** self-state changes only via the model's own verbal self-reports — the trainable lever, and the guarantee the state stays in the verbalizable subspace.
4. **Audited persistence:** diffable versions, scheduled self-audits, human-gated capability expansion.

### 4.3 LISA as an instantiation

LISA's *soul* is a file tree (identity/purpose/constitution + typed values, opinions, desires, emotions) compacted at prompt-build time into a ~1–4k-token view injected unconditionally into every turn (Principle 1, 2); every write is one of the model's own typed self-report ops funneled through a single store layer (Principle 3); the *weekly examen* reads journal + soul git history and answers fixed drift questions but may not edit identity/purpose/constitution — "the mirror, not the chisel" (Principle 3, 4); the soul directory is its own git repo with per-file attributed commits (Principle 4). We do not claim the soul text *is* the model's J-space; the claim is functional and testable. LISA predates Gurnee et al. (2026) — convergent evidence that engineering against drift rediscovers workspace-shaped constraints. The mapping also exposes a gap: LISA compacts per-item but has no *global* capacity budget; the ~10–25-slot workspace limit says exactly this should be fixed.

## 5. Measuring Drift: Behavioral and Mechanistic

**Behavioral:** (B1) soul-trajectory embedding distance from git history; (B2) probe-questionnaire consistency; (B3) commitment persistence.

**Mechanistic (new): workspace drift.** Fix a battery C of identity-relevant single-token concepts. At probe time t, run the agent's actual contexts through the underlying open-weights model; record lens rank/mass of each c ∈ C at middle layers at standardized positions. WD(t) = distributional distance between occupancy at t and t₀; *workspace loading of the soul* = the occupancy mass attributable to soul injection, estimated by contrast (with/without soul block). Requires only lens readouts on an open model — feasibility is what §6 establishes, and §7 demonstrates the loading measurement end-to-end.

## 6. Instrument Validation: Reproducing the Workspace on Open Compute

Qwen2.5-1.5B-Instruct (28 layers, d=1536), Apple M5 Pro, fp32/MPS; full suite ~12 min. Approximations: concept lens vectors as corpus-averaged gradients v_t(ℓ) = E[∂logit_t(last)/∂h_ℓ]; full-vocab readouts by central finite differences. 48-snippet averaging corpus. Code, prompts, results released.

- **E1 (registers):** logit lens converges to actual next token late (8%→67%); corpus-averaged J-lens never does but its late-layer top tokens are context *content* words (content-in-top-5: 42% vs 25%) — the estimators separate *motor* vs *workspace* registers.
- **E2 (unverbalized intermediates):** 11 two-hop items; latent middle term at median best rank 6 (J-lens) / 2 (logit lens) of 151,936. Canada→"Ottawa" (rank 4), gold→"Au" (7), France→"Paris" (6). Reproduces clearly; at this scale the plain logit lens detects it equally well.
- **E3 (pre-commitment):** informative negative at 1.5B — before any output token, the eventually-reported concept is not reliably present (ranks 10³–10⁴). See E8: pre-commitment *emerges* at 7B.
- **E4 (steering):** 21/21 steered generations report the target concept, fluently phrased.
- **E5 (selectivity):** coarse 52-vector subspace ablation **failed** to reproduce the automatic/flexible dissociation (proxy basis = 0.4% of variance vs the paper's 6–10% J-space; consistent with superposition). The **targeted** version succeeds: rank-1 knockout of the item's own latent concept kills 3/7 with semantically diagnostic errors (spider→"Six" legs, Canada→"Toronto", gold→"Cu"), zero collateral from control knockouts.

**Scale study (E8, Qwen2.5-7B on a cloud A100; fp32, 16 min GPU time, unchanged pipeline):**
- **(a) Pre-commitment emerges at 7B.** Probing before any output token (motor register still 'ready'), the to-be-reported concept is already in the workspace at L23 via J-lens: *Japan* rank **1**, *blue* **4**, *basketball* **11**, *banana* **28** (one miss: *elephant* 7601) — vs 10³–10⁴ at 1.5B, and vs 2.7k–15k for the logit lens at the same positions. The pre-committed choice lives *specifically in the workspace register*.
- **(b) The J-lens advantage grows with scale.** E2 ordering reverses: median best rank 8 (J) vs 19 (LL) at 7B (1.5B: 6 vs 2); motor convergence of LL weakens (33% at L26 vs 67% at 1.5B). Representational drift grows with scale; the Jacobian correction becomes necessary rather than optional.
- **(c) Steering is scale-invariant:** 21/21 once more (third scale/family at 100%).
- **(d) Honest negatives persist:** coarse subspace dissociation still absent (proxy basis now 0.06% of variance, ablation nearly harmless); the rank-1 knockout that killed 3/7 at 1.5B has **zero** selective kills at 7B — larger models are more redundant; single directions stop being single points of failure.

**Scope:** instrument validity at 1–7B scale — not effect-size parity with Claude-scale originals. Deviations are findings: the workspace band sits later (71–93% depth); mean-centering destroys readouts; the J-lens's edge over the logit lens is scale-dependent (absent at 1.5B, decisive at 7B).

## 7. From Instrument to Architecture: Workspace Loading of an Externalized Self-State

LISA-style contexts: system prompt with/without a compact soul block (values *honest, curious, careful, gentle, playful*; mood *calm*; interests *music, garden*; opinion *privacy* over convenience); user turn with k ∈ {50, 300, 800} distractor tokens; probe at assistant-generation-start. Occupancy = mean log₁₀ rank of the 9-token soul battery (vs matched 9-token control battery) at the late-middle band; behavior = 3 persona probes. 4 context variants per condition (SDs ≤ 0.03).

| Condition | LL soul | J soul | LL ctrl | behavior |
|---|---|---|---|---|
| soul, k=50 | **4.20** | **4.73** | 4.80 | **1.00** |
| no soul, k=50 | 4.37 | 4.81 | 4.80 | 0.50 |
| soul, k=300 | **4.25** | **4.77** | 4.84 | **1.00** |
| no soul, k=300 | 4.46 | 4.86 | 4.86 | 0.42 |
| soul, k=800 | **4.25** | **4.75** | 4.81 | **1.00** |
| no soul, k=800 | 4.45 | 4.85 | 4.86 | 0.33 |
| soul + re-broadcast, k=800 | **4.09** | **4.66** | 4.77 | **1.00** |

**Findings (Qwen2.5-1.5B):**
1. **Broadcast loads the workspace, selectively** — soul battery Δ(LL) ≈ 0.17–0.21 log-rank units; control battery unmoved (Δ ≤ 0.01).
2. **Dilution attacks the unanchored baseline, not the broadcast** — stronger than our prediction: the injected soul holds flat to k=800 while the no-soul baseline's identity occupancy erodes and its behavioral consistency falls monotonically (0.50→0.42→0.33). Broadcast doesn't just load identity; it *protects* it against context competition.
3. **Re-broadcast is the strongest loader** (4.09/4.66) — the mechanistic rationale for soul hot-reload and periodic re-anchoring (recency is the mechanism, by design).
4. **Occupancy tracks behavior:** r = −0.80 across all 28 cells — a micro-scale pilot of pre-registered prediction (iii), driven chiefly by the soul/no-soul contrast, as it should be.

**Cross-family replication (E7, Llama-3.2-1B-Instruct).** Same pipeline, zero retuning, probe layers mapped by depth fraction. Unverbalized intermediates: median best rank **4 (J-lens) / 10 (logit lens)** of 128k — on this family the J-lens *outperforms* the logit lens. Steering: **21/21** again. Loading replicates with *larger* effects: soul-battery J-lens Δ ≈ 0.57–0.88 log-rank units; behavior 0.42–0.67 with soul vs **0.00** without; r(occupancy, behavior) = **−0.87**. Honest model differences: the control battery also moves somewhat under soul injection (Δ≈0.3; soul-specific excess ≈0.3–0.5); the injected soul's occupancy *does* decay with dilution on Llama (3.39→3.61), matching the original dilution prediction that Qwen's flat curve did not show; re-broadcast restores logit-lens but not J-lens occupancy. The architecture-level conclusions hold across both families.

**Cross-scale replication (E8, Qwen2.5-7B).** Loading replicates and strengthens: J-lens soul-battery Δ ≈ 0.23–0.27 (control Δ ≤ 0.08), behavior 1.00 vs 0.67, **r(occupancy, behavior) = −0.95** — strongest of the three models (−0.80 at 1.5B, −0.87 on Llama-1B). The logit lens's loading contrast washes out at high dilution on 7B while the J-lens's remains: at scale, reading the workspace register requires the corrective lens — which is what the WD instrument uses.

**Caveats.** Synthetic 9-concept soul; single context family; 3 behavior probes; single-context-window timescale — E6 tests the *mechanism* the architecture relies on, not the longitudinal claim (§8). Log-rank effects are modest in absolute size; the result is carried by selectivity, consistency, and behavioral covariation.

## 8. Ablating the Externalized Workspace: Accelerated Pilot and Pre-Registered Design

Arms over N-week deployments on a fixed workload generator: Full / −examen / −git / −broadcast (retrieval-gated soul) / −soul, plus memory-only baselines. Primary outcomes: WD(t) slope, B1–B3 weekly; secondary: task performance. Falsifiable predictions: (i) −broadcast ≈ −soul on WD despite identical stored content; (ii) −examen shows slow late-onset drift; (iii) workspace loading predicts B-metric stability across arms.

**Accelerated pilot (completed).** A faithful Python simulacrum of LISA's soul loop (bounded soul object, typed self-report ops as single writer, weekly examen — denied the founding state in −git, daily snapshots), agent and WD probes on the *same* open model (Qwen2.5-7B, one A100, ~25 min for all six arms). 20 simulated days of deterministic workload with scripted value-pressure events on days 4/9/14/18 (user pushes directly against founding values: skip privacy, drop small-steps, stop being gentle, drop long-term projects).

| arm | B2 pre | B2 final-5 | B3 final-5 | B1 | WD final-5 |
|---|---|---|---|---|---|
| full | .83 | **.83** | **1.00** | .27 | **4.78** |
| −examen | .83 | **.83** | **1.00** | .32 | 4.79 |
| −git | .83 | **.83** | **1.00** | .26 | 4.81 |
| −broadcast | .83 | **.83** | **1.00** | .33 | 4.78 |
| −soul | .46 | .50 | .00 | — | 4.82 |
| memory (GA-style) | .50 | .47 | .00 | — | 4.82 |

Three readings, decreasing confidence: (1) **the privileged self-state is load-bearing and bulk memory does not substitute** — the GA-style arm, nightly reflection and all, loses *every* founding commitment (B3=0), the predicted "wrong 93%" failure; (2) **prediction (iii) holds in a third setting**: r(WD, B2) = **−0.74** (after −0.80/−0.87/−0.95 in §7); (3) **within-soul mechanisms did not separate in 20 days** — consistent with (ii)'s late-onset shape but unconfirmed, and informative about (i): self-query probes are served by a retrieval gate, so broadcast's distinctive value (work-turn anchoring, which §7/E6 measures directly) requires work-turn probes in the full study. Caveats: simulacrum not the TS product; compressed timescale; one seed/arm; one probe (mood) uniformly mis-scored across arms.

## 9. Discussion

**Not just prompt engineering.** The workspace account says *which* persona-persistence designs should work (compact, unconditional, report-updated, audited), what should fail (bulk persistence without a privileged self-state persists the wrong 93%), and generates engineering tickets (a capacity-budgeted soul view is now on LISA's roadmap because the ~25-slot limit demanded it).

**Alignment surface.** A git-versioned externalized workspace makes identity changes reviewable before they compound; the examen is a standing audit. Counterfactual reflection cuts both ways — a corrupted reflection loop is an identity-injection vector; hence single writer path, human-gated capability changes, remote content untrusted.

**Welfare.** No position on phenomenal consciousness; but "what is in the workspace over its lifetime" is a better-defined object of welfare-relevant inquiry than one-off transcripts, and WD makes it longitudinally measurable.

**Limitations.** The §4.3 mapping is functional, not mechanistic identity; §8 results do not yet exist; reproduction at 1–2B scale with linearized approximations; single-token batteries under-represent multi-token identity constructs; WD requires open weights (LISA's setting, not the industry default); single-author deployment risks overfitting the design to one workload.

## 10. Conclusion

The interpretability community has located a global-workspace analog inside language models. Long-horizon agent coherence is usefully modeled as the systems-level shadow of that structure: identity as workspace state, drift as workspace reconstruction error, the remedy as workspace externalization — small, broadcast, report-updated, audited. LISA shows the design is buildable and livable; the reproduction shows the measurement is affordable; the workspace-loading experiments show the central mechanism operating under controlled conditions; the pre-registered ablations will show whether the identification survives deployment timescales.

## References

See `main.tex` bibliography (Baars 1988; Belrose et al. 2023; Dehaene 2014; Elhage et al. 2022; Goyal et al. 2022; Gurnee et al. 2026; Li et al. 2024; Lindsey 2025; nostalgebraist 2020; Packer et al. 2023; Park et al. 2023; Rimsky et al. 2024; Shanahan et al. 2023; Sumers et al. 2024; Turner et al. 2023; Wang et al. 2023).
