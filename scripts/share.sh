#!/usr/bin/env bash
# Run the all-in-one demo image and share it at a public https link (Cloudflare quick tunnel).
# Voice keys (LiveKit Cloud, Deepgram, optional Anthropic) are read from .env when set. They go
# to the container through a temporary env file, never the command line, and are not printed.
set -euo pipefail

KEYS=(LIVEKIT_URL LIVEKIT_API_KEY LIVEKIT_API_SECRET DEEPGRAM_API_KEY ANTHROPIC_API_KEY)
envfile="$(mktemp)"
chmod 600 "$envfile"
trap 'rm -f "$envfile"' EXIT

found=()
if [ -f .env ]; then
  for key in "${KEYS[@]}"; do
    value="$(grep -E "^${key}=" .env | tail -1 | cut -d= -f2- | sed 's/[[:space:]]*#.*$//; s/[[:space:]]*$//')"
    if [ -n "$value" ]; then
      printf '%s=%s\n' "$key" "$value" >>"$envfile"
      found+=("$key")
    fi
  done
fi
echo "Keys from .env: ${found[*]:-none}"
# `make up` registers its own worker with the same LiveKit project. A separate agent name keeps
# calls from the public link on this container's worker, which knows their sessions.
echo "AGENT_NAME=voiceserve-share" >>"$envfile"

docker build -f infra/deploy/huggingface/Dockerfile -t univra-space:local .
docker rm -f univra-space >/dev/null 2>&1 || true
docker run -d --name univra-space --restart unless-stopped \
  -p 127.0.0.1:7860:7860 --env-file "$envfile" univra-space:local >/dev/null
rm -f "$envfile"

cloudflared="$(command -v cloudflared || echo "/c/Program Files (x86)/cloudflared/cloudflared.exe")"
exec "$cloudflared" tunnel --no-autoupdate --url http://localhost:7860
