#!/usr/bin/env bash
set -euo pipefail
TASK_HUB=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TASK_VERSION=${1:?Usage: install_godot.sh VERSION ABSOLUTE_OUTPUT}
TASK_OUTPUT=${2:?Usage: install_godot.sh VERSION ABSOLUTE_OUTPUT}
[[ "$TASK_VERSION" =~ ^4\.(6\.3|7\.2)$ && "$TASK_OUTPUT" = /* ]] || exit 1
TASK_TEMP=$(mktemp -d)
trap 'rm -rf "$TASK_TEMP"' EXIT
for TASK_FILE in "Godot_v${TASK_VERSION}-stable_linux.x86_64.zip" "Godot_v${TASK_VERSION}-stable_export_templates.tpz"; do
  curl --fail --silent --show-error --location --retry 2 --max-time 300 \
    "https://github.com/godotengine/godot-builds/releases/download/${TASK_VERSION}-stable/$TASK_FILE" \
    --output "$TASK_TEMP/$TASK_FILE"
done
(cd "$TASK_TEMP" && sha512sum --check "$TASK_HUB/toolchain/godot-${TASK_VERSION}.sha512")
unzip -q "$TASK_TEMP/Godot_v${TASK_VERSION}-stable_linux.x86_64.zip" -d "$TASK_TEMP/engine"
mkdir -p "$TASK_OUTPUT"
install -m 0755 "$TASK_TEMP/engine/Godot_v${TASK_VERSION}-stable_linux.x86_64" "$TASK_OUTPUT/godot"
# Install only the Windows x86_64 templates used by this profile.
unzip -q "$TASK_TEMP/Godot_v${TASK_VERSION}-stable_export_templates.tpz" \
  'templates/windows_debug_x86_64.exe' 'templates/windows_release_x86_64.exe' -d "$TASK_TEMP/export"
TASK_DATA=${XDG_DATA_HOME:-$HOME/.local/share}
mkdir -p "$TASK_DATA/godot/export_templates/${TASK_VERSION}.stable"
install -m 0644 "$TASK_TEMP/export/templates/"*.exe "$TASK_DATA/godot/export_templates/${TASK_VERSION}.stable/"
"$TASK_OUTPUT/godot" --headless --version
