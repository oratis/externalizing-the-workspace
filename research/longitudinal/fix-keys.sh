#!/usr/bin/env bash
# Rewrite each arm's config.env to reach Anthropic DIRECTLY (bypassing the
# GCP relay, whose deployed revision 401s), using the relay's own upstream
# key + the local clash proxy. Run after every `seed-arms.mjs --force`, which
# otherwise copies ~/.lisa/config.env (the broken relay gateway).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="${GCP_PROJECT:-oratis-491316}"
PROXY="${LISA_PROXY:-http://127.0.0.1:7897}"

UP="$(gcloud secrets versions access latest --secret=anthropic-api-key --project="$PROJECT")"
[ "${UP:0:7}" = "sk-ant-" ] || { echo "failed to fetch upstream key"; exit 1; }

for home in "$HERE"/runs/*/; do
  [ -f "$home/config.env" ] || continue
  grep -vE '^(ANTHROPIC_BASE_URL|ANTHROPIC_API_KEY|HTTPS_PROXY)=' "$home/config.env" > "$home/config.env.tmp" || true
  {
    printf 'ANTHROPIC_API_KEY=%s\n' "$UP"
    printf 'HTTPS_PROXY=%s\n' "$PROXY"
  } >> "$home/config.env.tmp"
  mv "$home/config.env.tmp" "$home/config.env"
  chmod 600 "$home/config.env"
  echo "fixed $(basename "$home")/config.env (direct key + proxy, no relay)"
done
