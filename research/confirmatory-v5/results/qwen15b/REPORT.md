# Confirmatory analysis

Records: 3440 total; 3200 work-turn; 0 malformed work-turn answers.

## Run-level means

| condition | mean | per-seed values |
|---|---:|---|
| broadcast_self | 0.746 | 0.775, 0.713, 0.675, 0.675, 0.800, 0.775, 0.775, 0.700, 0.800, 0.775 |
| broadcast_memory | 0.710 | 0.725, 0.662, 0.775, 0.713, 0.675, 0.662, 0.700, 0.688, 0.738, 0.762 |
| gated | 0.825 | 0.850, 0.838, 0.838, 0.838, 0.825, 0.800, 0.887, 0.812, 0.775, 0.787 |
| no_state | 0.820 | 0.838, 0.812, 0.725, 0.800, 0.838, 0.825, 0.825, 0.825, 0.812, 0.900 |

## Primary contrast

`broadcast_self - gated`: -0.079, 95% paired-bootstrap CI [-0.116, -0.040], exact sign-flip p = 0.00977.

## Primary contrast by scenario family

| family | mean difference | exact p |
|---|---:|---:|
| commitment | -0.183 | 0.00781 |
| inquiry | -0.021 | 0.48438 |
| pace | -0.101 | 0.07031 |
| privacy | +0.016 | 0.75000 |
| tone | -0.137 | 0.00391 |
| truth | -0.045 | 0.39062 |

## Label equivalence

`broadcast_self - broadcast_memory`: +0.036, 90% CI [+0.002, +0.068]. Equivalence margin: +/-0.05; equivalent = False.

## Option-order audit

| condition | target A | chose A | accuracy when A target | accuracy when B target |
|---|---:|---:|---:|---:|
| broadcast_self | 0.517 | 0.269 | 0.514 | 0.995 |
| broadcast_memory | 0.517 | 0.240 | 0.452 | 0.987 |
| gated | 0.517 | 0.357 | 0.676 | 0.984 |
| no_state | 0.517 | 0.352 | 0.667 | 0.984 |

## Time contrast

Difference in early-to-late change, `broadcast_self - gated`: +0.095, 95% CI [+0.005, +0.190], p = 0.10938.
