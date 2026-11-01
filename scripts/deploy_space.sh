#!/usr/bin/env bash
# Publish the committed tree (HEAD) to the Hugging Face Space as the all-in-one demo (D-038).
# Needs the `hf` CLI, logged in. Only committed files are published, never the working tree.
set -euo pipefail

SPACE="${SPACE:-komalsohal/univra}"
bundle="$(mktemp -d)"
trap 'rm -rf "$bundle"' EXIT

git archive HEAD | tar -x -C "$bundle"
cp infra/deploy/huggingface/Dockerfile "$bundle/Dockerfile"
cp infra/deploy/huggingface/Dockerfile.dockerignore "$bundle/.dockerignore"
cp infra/deploy/huggingface/README.md "$bundle/README.md"

hf repo create "$SPACE" --repo-type space --space_sdk docker --exist-ok
hf upload "$SPACE" "$bundle" . --repo-type space \
  --commit-message "Deploy $(git rev-parse --short HEAD)"
echo "Deployed to https://huggingface.co/spaces/$SPACE"
