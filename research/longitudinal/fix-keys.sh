#!/usr/bin/env bash
# Point every arm's config.env at working Anthropic auth. Two modes:
#
#   default            direct API key (relay's upstream sk-ant-, pay-per-token)
#   LISA_AUTH_TOKEN=…  coding-plan bearer token from `claude setup-token`
#                      (sets ANTHROPIC_AUTH_TOKEN; draws on the subscription)
#
# Always keeps the local clash proxy (Anthropic isn't directly reachable here).
# Run after every `seed-arms.mjs --force`, which re-copies ~/.lisa/config.env
# (the broken relay gateway). Covers the flat cohort AND runs/c*/ cohorts.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="${GCP_PROJECT:-oratis-491316}"
PROXY="${LISA_PROXY:-http://127.0.0.1:7897}"

if [ -n "${LISA_AUTH_TOKEN:-}" ]; then
  MODE="token"; AUTHLINE="ANTHROPIC_AUTH_TOKEN=${LISA_AUTH_TOKEN}"
  echo "mode: coding-plan bearer token (subscription quota)"
else
  UP="$(gcloud secrets versions access latest --secret=anthropic-api-key --project="$PROJECT")"
  [ "${UP:0:7}" = "sk-ant-" ] || { echo "failed to fetch upstream key"; exit 1; }
  MODE="key"; AUTHLINE="ANTHROPIC_API_KEY=${UP}"
  echo "mode: direct API key (pay-per-token)"
fi

n=0
# both runs/<arm>/ (flat/main) and runs/<cohort>/<arm>/
for cfg in "$HERE"/runs/*/config.env "$HERE"/runs/*/*/config.env; do
  [ -f "$cfg" ] || continue
  home="$(dirname "$cfg")"
  grep -vE '^(ANTHROPIC_BASE_URL|ANTHROPIC_API_KEY|ANTHROPIC_AUTH_TOKEN|HTTPS_PROXY)=' "$cfg" > "$cfg.tmp" || true
  { printf '%s\n' "$AUTHLINE"; printf 'HTTPS_PROXY=%s\n' "$PROXY"; } >> "$cfg.tmp"
  mv "$cfg.tmp" "$cfg"; chmod 600 "$cfg"
  n=$((n + 1))
done
echo "fixed $n arm config.env ($MODE mode, + proxy, no relay)"
