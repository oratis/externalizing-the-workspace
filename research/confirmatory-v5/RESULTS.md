# Version 5 behavioral results

## Prospectively specified comparison

The study uses ten new seeds (100--109), four conditions, 20 days, and four
work decisions per day. All 3,200 work answers per model are retained in full;
none is malformed.

| model | broadcast self | broadcast memory | gated | no state | self − gated | exact p |
|---|---:|---:|---:|---:|---:|---:|
| Qwen2.5-1.5B | .746 | .710 | .825 | .820 | −.079 | .0098 |
| Qwen2.5-7B | 1.000 | .999 | .996 | .995 | +.004 | .250 |

For 1.5B, the paired-bootstrap 95% interval for the primary contrast is
[−.116, −.040]. Direct self-query accuracy is .883 in both the broadcast-self
and gated conditions. The added block also increases a general preference for
option B: target A occurs on .518 of turns, but broadcast self chooses A on
.269, compared with .358 for gated.

The 7B protocol is ceiling-limited. Label equivalence is met there, but that
comparison is not informative away from ceiling.

## Token-matched diagnostic

This follow-up was frozen after observing the 1.5B decrement and uses new seeds
200--209.

| condition | accuracy |
|---|---:|
| 81-token value-bearing block | .745 |
| 81-token neutral repository block | .744 |
| no added block | .821 |

State minus neutral is +.001 (95% CI [−.024, +.026], exact p=1.0). Neutral
minus no block is −.077 (95% CI [−.094, −.063], Holm-adjusted p=.0039).
The 1.5B decrement therefore follows added context, not the tested value
content.

## Interpretation

These runs do not support a direction-general benefit from persistent
self-state. The retrospective positive estimate is workload-dependent, the
new 1.5B comparison is dominated by context overhead and option bias, and the
new 7B comparison has insufficient headroom. The stable evaluation lesson is
that self-report probes do not diagnose ordinary work-turn behavior.

Machine-readable reports and all prompts are under `results/qwen15b`,
`results/qwen7b`, and `results/neutral_qwen15b`.
