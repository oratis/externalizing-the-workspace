#!/usr/bin/env bash
# Point every arm's config.env at a working model backend. Three modes:
#
#   default            direct Anthropic API key (relay's upstream sk-ant-,
#                      pay-per-token, fetched from GCP Secret Manager)
#   LISA_AUTH_TOKEN=…  Anthropic coding-plan bearer from `claude setup-token`
#                      (sets ANTHROPIC_AUTH_TOKEN; draws on the subscription)
#   LISA_VERTEX=1      Google Vertex AI Gemini (ADC auth, billed to your GCP
#                      project — NO secret written to config.env). Configure via:
#                        GOOGLE_CLOUD_PROJECT=<proj> GOOGLE_CLOUD_LOCATION=<region> \
#                        LISA_MODEL=<gemini-model> LISA_VERTEX=1 ./fix-keys.sh
#
# Always keeps the local clash proxy (neither api.anthropic.com nor
# googleapis.com is directly reachable here). Run after every
# `seed-arms.mjs --force`, which re-copies ~/.lisa/config.env. Covers the flat
# cohort AND runs/c*/ cohorts.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="${GCP_PROJECT:-oratis-491316}"
PROXY="${LISA_PROXY:-http://127.0.0.1:7897}"

# Keys this script manages: stripped from each config.env, then re-appended for
# the selected mode (so switching modes cleanly drops the other provider's).
STRIP='^(ANTHROPIC_BASE_URL|ANTHROPIC_API_KEY|ANTHROPIC_AUTH_TOKEN|GOOGLE_GENAI_USE_VERTEXAI|GOOGLE_CLOUD_PROJECT|GOOGLE_CLOUD_LOCATION|LISA_MODEL|HTTPS_PROXY)='

if [ -n "${LISA_VERTEX:-}" ] || [ "${GOOGLE_GENAI_USE_VERTEXAI:-}" = "true" ]; then
  MODE="vertex"
  VPROJECT="${GOOGLE_CLOUD_PROJECT:-$PROJECT}"
  VLOCATION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
  VMODEL="${LISA_MODEL:-gemini-2.5-pro}"
  echo "mode: Vertex AI Gemini — $VMODEL @ $VPROJECT/$VLOCATION (ADC, no secret written)"
elif [ -n "${LISA_AUTH_TOKEN:-}" ]; then
  MODE="token"
  echo "mode: coding-plan bearer token (subscription quota)"
else
  MODE="key"
  UP="$(gcloud secrets versions access latest --secret=anthropic-api-key --project="$PROJECT")"
  [ "${UP:0:7}" = "sk-ant-" ] || { echo "failed to fetch upstream key"; exit 1; }
  echo "mode: direct API key (pay-per-token)"
fi

# Provider lines for the selected mode (+ proxy), appended to each config.env.
emit_auth() {
  case "$MODE" in
    vertex)
      printf 'LISA_MODEL=%s\n' "$VMODEL"
      printf 'GOOGLE_GENAI_USE_VERTEXAI=true\n'
      printf 'GOOGLE_CLOUD_PROJECT=%s\n' "$VPROJECT"
      printf 'GOOGLE_CLOUD_LOCATION=%s\n' "$VLOCATION"
      ;;
    token) printf 'ANTHROPIC_AUTH_TOKEN=%s\n' "$LISA_AUTH_TOKEN" ;;
    key)   printf 'ANTHROPIC_API_KEY=%s\n' "$UP" ;;
  esac
  printf 'HTTPS_PROXY=%s\n' "$PROXY"
}

n=0
# both runs/<arm>/ (flat/main) and runs/<cohort>/<arm>/
for cfg in "$HERE"/runs/*/config.env "$HERE"/runs/*/*/config.env; do
  [ -f "$cfg" ] || continue
  grep -vE "$STRIP" "$cfg" > "$cfg.tmp" || true
  emit_auth >> "$cfg.tmp"
  mv "$cfg.tmp" "$cfg"; chmod 600 "$cfg"
  n=$((n + 1))
done
echo "fixed $n arm config.env ($MODE mode, + proxy, no relay)"
