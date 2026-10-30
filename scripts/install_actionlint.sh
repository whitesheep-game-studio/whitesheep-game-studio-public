#!/usr/bin/env bash
set -euo pipefail
TASK_OUTPUT=${1:?Usage: install_actionlint.sh ABSOLUTE_OUTPUT}
[[ "$TASK_OUTPUT" = /* ]] || exit 1
TASK_TEMP=$(mktemp -d)
trap 'rm -rf "$TASK_TEMP"' EXIT
curl --fail --silent --show-error --location --retry 2 --max-time 120 \
  https://github.com/rhysd/actionlint/releases/download/v1.7.7/actionlint_1.7.7_linux_amd64.tar.gz \
  --output "$TASK_TEMP/actionlint.tar.gz"
echo '023070a287cd8cccd71515fedc843f1985bf96c436b7effaecce67290e7e0757  actionlint.tar.gz' \
  | (cd "$TASK_TEMP" && sha256sum --check)
mkdir -p "$TASK_OUTPUT"
tar -xzf "$TASK_TEMP/actionlint.tar.gz" -C "$TASK_OUTPUT" actionlint
"$TASK_OUTPUT/actionlint" --version
