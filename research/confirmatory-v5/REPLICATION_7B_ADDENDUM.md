# Qwen2.5-7B replication addendum

Status: frozen after completion of the 1.5B run and before loading or running
the 7B model.

The original preregistration states that a 7B replication may be reported
separately under the same protocol. This run is now required because the
retrospective behavioral evidence used Qwen2.5-7B-Instruct, whereas the first
confirmatory run used 1.5B and returned an effect in the opposite direction.

No workload, prompt, condition, target, seed, endpoint, exclusion, or analysis
rule is changed. The replication uses:

- model: Qwen2.5-7B-Instruct;
- seeds: 100--109, paired across conditions and with the 1.5B schedules;
- 20 days and four work probes per day;
- the four conditions and exact prompts already frozen in `run.py` and
  `workload.py`;
- float16 inference on Apple MPS to fit the 7B model in local memory;
- the same primary contrast, exact paired sign-flip test, paired bootstrap,
  equivalence margin, and secondary family defined in `PREREGISTRATION.md`.

The 7B result will be reported regardless of direction. It will be interpreted
as a same-protocol, scale-matched replication, not pooled with the 1.5B run.
