#!/usr/bin/env bash
# Start-up for the all-in-one demo image (D-038). Every boot gets a fresh database, which the
# API seeds with synthetic data; the internal service key is generated unless provided.
set -euo pipefail

export PGDATA=/tmp/pgdata
if [ ! -s "$PGDATA/PG_VERSION" ]; then
  initdb -D "$PGDATA" -U voiceserve --auth=trust --encoding=UTF8 >/dev/null
  pg_ctl -D "$PGDATA" -o "-c listen_addresses=127.0.0.1 -k /tmp" -w start >/dev/null
  createdb -h 127.0.0.1 -U voiceserve voiceserve
  psql -h 127.0.0.1 -U voiceserve -d voiceserve -qc "CREATE EXTENSION IF NOT EXISTS vector"
  pg_ctl -D "$PGDATA" -w stop >/dev/null
fi

random_key() { head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n'; }
export INTERNAL_API_KEY="${INTERNAL_API_KEY:-$(random_key)}"
# Voice needs LiveKit Cloud here (a Space can't open WebRTC media ports); browsers and the
# worker use the same LiveKit URL.
export LIVEKIT_URL="${LIVEKIT_URL:-}"
export LIVEKIT_PUBLIC_URL="${LIVEKIT_PUBLIC_URL:-$LIVEKIT_URL}"

exec supervisord -n -c /app/deploy/supervisord.conf
