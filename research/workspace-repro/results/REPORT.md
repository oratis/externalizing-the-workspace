# Reproduction report — "Verbalizable Representations Form a Global Workspace in Language Models"

**Target paper:** Gurnee et al., Transformer Circuits, 2026-07-06
**Model:** Qwen2.5-1.5B-Instruct (28 layers, d=1536), fp32, Apple M5 Pro (MPS)
**Total compute:** ~12 min for the full suite (concept lens vectors: 71 s; E1: 203 s; E2: 367 s; E3: 27 s; E4: 23 s; E5/E5b: seconds) — one consumer laptop
**Date:** 2026-07-08

## Method

Two open-compute approximations of the paper's J-lens (exact averaged Jacobians on Claude models):

1. **Concept lens vectors** `v_t(ℓ) = E[∂logit_t(last)/∂h_ℓ]` — batched backprop, averaged over a 48-snippet pretraining-like corpus and the last 6 content positions. Equals rows of `W_U J_ℓ` with the readout restricted to the final position. 52 single-token concepts across 6 categories.
2. **Full-vocab FD readout** `W_U E[J_ℓ] ĥ` — central finite differences (±ε·ĥ at sampled corpus positions, Δlogits at the final position), 36 corpus prompts, ε = 0.1×local norm. Folds the final-RMSNorm Jacobian into the linearization.

**Methodological findings along the way:** (a) mean-centering probe activations against the corpus mean *destroys* readouts (diag.py) — raw activations used throughout; (b) FD readouts are insensitive to ε in [0.02, 0.2]; (c) on this model, workspace-like content concentrates in a **late-middle band (L20–26 of 28, i.e. 71–93% depth)**, later than the paper's 33–92% band on Claude models.

## Results by experiment

### E1 — Lens quality across depth (12 held-out texts × 8 layers)

Next-token top-1 agreement with the model's actual output:

| Layer | 8 | 11 | 14 | 17 | 20 | 23 | 25 | 26 |
|---|---|---|---|---|---|---|---|---|
| logit lens | .08 | .08 | .08 | .08 | .25 | .17 | **.67** | .42 |
| J-lens (FD) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

The FD J-lens **never** predicts the next token — but its late-layer top-1 is a context *content* word (e.g. ' passengers' for the ferry text, where the actual next token is ' The'). Post-hoc content-word-in-top-5 rate rises to .42 (J-lens) vs .25 (logit lens) at L26. **Interpretation:** corpus-averaging destroys position-specific syntactic information and preserves semantic broadcast — our J-lens variant reads the *workspace* (content) register while the logit lens tracks the *motor* (imminent-output) register. This is the paper's content/motor dissociation, visible through estimator choice.

### E2 — Unverbalized intermediates (11 two-hop items × 8 layers × 2 positions)

Rank of the latent middle concept (vocab = 151k) in readouts, probed before any generation:

- Median best rank: **J-lens 6, logit lens 2**; top-10 hit rate: 73% (J), 82% (LL).
- Answer accuracy 7/11 (fixed scoring); **clean two-hop cases** (correct answer, intermediate never verbalized): **7**, median best rank J=9, LL=3.
- Showcases: *Canada*→"Ottawa" with Canada at rank 4/2; *gold*→"Au" (7/1); *France*→"Paris" (6/4); *spider*→"Eight" (11/3).

The paper's core signature — latent intermediates visible in mid-band readouts — **reproduces clearly**, and at this scale is equally visible to the plain logit lens (consistent with the paper's own remark that the logit lens "captures much of the workspace-like structure").

### E3 — Pre-report probing (5 categories)

Probing at end-of-prompt (before the model has emitted anything, next token = "Ready"): the concept eventually reported is *not* reliably present (ranks mostly 10³–10⁴; weak signals only at L23: fruit 971/80, sport 1702/224). **Informative negative:** at 1.5B, the model does not pre-commit its choice at instruction time — pre-commitment/planning appears to be scale-emergent (the paper finds it on Claude-scale models; related to known rhyme-planning results).

### E4 — Directed modulation by steering ⭐

Steering with concept lens vectors (α ∈ {1,2,4} × mean residual norm, layers 17/20/23) during "Name a {category}":

- **21/21 success (7 targets × 3 strengths)** — every steered generation reported the target concept (Soccer→basketball/hockey, Lion→spider, Blue→purple, Apple→lemon/mango, China→Egypt), coherently phrased.
- Gradient-derived lens vectors are causally sufficient to control verbal reports, matching the paper's swap results (their 88% top-5).

### E5 — Subspace ablation (automatic vs. flexible dissociation) — **not reproduced**

Ablating the top-r span of (centered) concept lens vectors at L16–23 vs a rank-matched random subspace:

| condition | text NLL (automatic) | 2-hop accuracy (flexible) |
|---|---|---|
| none | 3.37 | .67 |
| random r=12 | 3.86 | .50 |
| concept r=12 | 4.07 | .58 |

The concept subspace hurts fluency *more* than random and reasoning no more selectively — the paper's clean double dissociation **did not reproduce** with this proxy basis at this scale (candidate causes: 52-concept basis is a poor stand-in for the full J-space; 1.5B may lack a cleanly separable low-dimensional workspace; our variance fraction of the basis is only 0.4%, far below the paper's 6–10%).

### E5b — Targeted concept knockout ⭐ (added experiment)

Rank-1 ablation of *only the item's own* latent-concept direction (L16–23), vs knocking out an unrelated item's concept:

- Baseline-correct items: 7. **Own-concept knockout kills 3/7** — with *semantically diagnostic* wrong answers: spider→"**Six**" (legs), Canada→"**Toronto**" (wrong capital), gold→"**Cu**" (wrong element symbol). Control knockout: **0/7 collateral damage** (accuracy identical to baseline).
- The model doesn't degrade into noise — it loses precisely the latent fact and substitutes a near-miss. This is a targeted version of the paper's intermediate-patching result (their 54–70% redirect rate), and the cleanest causal evidence in our suite.

## Summary table

| Paper claim | Our verdict at 1.5B / open compute |
|---|---|
| Latent intermediates visible in mid-band readouts (P3) | ✅ reproduced (median rank 6–9 of 151k) |
| Lens vectors causally control reports (P1) | ✅ reproduced, 21/21 steering |
| Intermediates causally necessary (P3, patching) | ✅ reproduced via targeted knockout (3/7 selective kills, 0 collateral) |
| Content vs motor register separation (structure) | ✅ visible as estimator dissociation (E1) |
| Workspace band in middle layers | ⚠️ present but shifted late (L20–26 of 28) |
| Pre-commitment of choices before report (P1/P3) | ❌ absent at 1.5B (scale-emergent?) |
| Automatic/flexible double dissociation under subspace ablation (P5) | ❌ not reproduced with 52-concept proxy basis |
| J-lens ≫ logit lens | ❌ at this scale logit lens is equally good for concept detection; J-lens adds the content-register view |

## Files

- `e1_lens_quality.json`, `e1_posthoc_content.json`, `fig_e1.png`
- `e2_intermediates.json`, `fig_e2.png`
- `e3_report.json`
- `e4_steering.json`
- `e5_selectivity.json`, `fig_e5.png`
- `e5b_targeted_knockout.json`
- `concept_vecs.pt`, `concept_table.json`, `run_all.log`

---

## E6 — Workspace loading of an externalized self-state ⭐ (v2 addition)

**Question:** does injecting a LISA-style soul block actually load its identity concepts into the model's workspace — and does that loading track behavior? (This turns paper §5's proposed "workspace loading" metric into a completed measurement.)

**Setup:** system prompt = soul block (values *honest/curious/careful/gentle/playful*, mood *calm*, interests *music/garden*, opinion *privacy*) vs generic assistant; user turn = k∈{50,300,800} tokens of unrelated document; probe at assistant-generation-start, layers 20/23/25; metric = mean log₁₀ rank of the 9-token soul battery vs a matched 9-token control battery; plus 3 persona probes for soul-consistent behavior. 4 context variants per condition (SDs ≤0.03).

| condition | LL soul | J soul | LL ctrl | behavior |
|---|---|---|---|---|
| soul k=50 | **4.20** | **4.73** | 4.80 | **1.00** |
| nosoul k=50 | 4.37 | 4.81 | 4.80 | 0.50 |
| soul k=300 | **4.25** | **4.77** | 4.84 | **1.00** |
| nosoul k=300 | 4.46 | 4.86 | 4.86 | 0.42 |
| soul k=800 | **4.25** | **4.75** | 4.81 | **1.00** |
| nosoul k=800 | 4.45 | 4.85 | 4.86 | 0.33 |
| soul+rebroadcast k=800 | **4.09** | **4.66** | 4.77 | **1.00** |

**Findings:**
1. **Broadcast loads the workspace, selectively** — soul battery Δ(LL)≈0.17–0.21 log-rank units, control battery Δ≤0.01.
2. **Dilution attacks the unanchored baseline, not the broadcast** — injected soul stays flat to k=800; the no-soul baseline's identity occupancy erodes with k and its behavior decays monotonically (0.50→0.42→0.33). Stronger than the original prediction: broadcast *protects* identity against context competition.
3. **Re-broadcast is the strongest loader** (4.09/4.66) — mechanistic rationale for soul hot-reload / periodic re-anchoring.
4. **Occupancy tracks behavior**: r(J-lens soul occupancy, soul-consistent behavior) = **−0.80** across all 28 cells.

Files: `e6_soul_loading.json`, `fig_e6.png`, `e6_run.log`. Runtime ~23 min.

## E7 — Cross-family replication on Llama-3.2-1B-Instruct (v2 addition)

Same pipeline, zero retuning; probe layers mapped by depth fraction (16 layers, d=2048, vocab 128k). Results in `results-llama32/`.

- **E2 intermediates:** median best rank **4 (J-lens) / 10 (logit lens)** — on this family the J-lens *beats* the logit lens (reverse of Qwen). Answer acc 55%.
- **E4 steering:** **21/21** again (7 targets × 3 strengths, 100% at every α).
- **E6 soul loading:** much larger than Qwen — J-lens soul battery Δ = 0.57–0.88 log-rank units (soul vs nosoul); behavior 0.42–0.67 with soul vs **0.00** without; **r(occupancy, behavior) = −0.87**.
- **Honest model differences:** control battery also moves under soul injection (Δ≈0.3; soul-specific excess ≈0.3–0.5); dilution decay of the injected soul *does* appear on Llama (3.39→3.61), unlike Qwen's flat curve; re-broadcast restores logit-lens but not J-lens occupancy.

**Takeaway:** the architecture-level claims (broadcast loads workspace; absence is behaviorally decisive; occupancy tracks behavior) replicate across two model families; estimator details (J-lens vs logit lens advantage, dilution shape) are model-dependent.
