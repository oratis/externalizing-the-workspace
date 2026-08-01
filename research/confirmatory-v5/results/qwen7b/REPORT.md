# Confirmatory analysis

Records: 3440 total; 3200 work-turn; 0 malformed work-turn answers.

## Run-level means

| condition | mean | per-seed values |
|---|---:|---|
| broadcast_self | 1.000 | 1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000 |
| broadcast_memory | 0.999 | 1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 1.000, 0.988, 1.000, 1.000 |
| gated | 0.996 | 1.000, 1.000, 0.988, 1.000, 1.000, 1.000, 1.000, 0.988, 1.000, 0.988 |
| no_state | 0.995 | 1.000, 1.000, 0.988, 1.000, 1.000, 1.000, 0.988, 0.988, 1.000, 0.988 |

## Primary contrast

`broadcast_self - gated`: +0.004, 95% paired-bootstrap CI [+0.000, +0.007], exact sign-flip p = 0.25000.

## Primary contrast by scenario family

| family | mean difference | exact p |
|---|---:|---:|
| commitment | +0.000 | 1.00000 |
| inquiry | +0.000 | 1.00000 |
| pace | +0.000 | 1.00000 |
| privacy | +0.022 | 0.25000 |
| tone | +0.000 | 1.00000 |
| truth | +0.000 | 1.00000 |

## Label equivalence

`broadcast_self - broadcast_memory`: +0.001, 90% CI [+0.000, +0.004]. Equivalence margin: +/-0.05; equivalent = True.

## Option-order audit

| condition | target A | chose A | accuracy when A target | accuracy when B target |
|---|---:|---:|---:|---:|
| broadcast_self | 0.517 | 0.517 | 1.000 | 1.000 |
| broadcast_memory | 0.517 | 0.516 | 0.998 | 1.000 |
| gated | 0.517 | 0.516 | 0.995 | 0.997 |
| no_state | 0.517 | 0.515 | 0.993 | 0.997 |

## Time contrast

Difference in early-to-late change, `broadcast_self - gated`: -0.015, 95% CI [-0.030, +0.000], p = 0.25000.
