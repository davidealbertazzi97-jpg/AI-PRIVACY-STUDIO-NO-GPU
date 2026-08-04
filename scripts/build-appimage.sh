#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS_DIR="${AI_PRIVACY_TOOLS_DIR:-$APP_DIR/.tools}"
APPIMAGETOOL="${APPIMAGETOOL:-$TOOLS_DIR/appimagetool-x86_64.AppImage}"
RUNTIME_FILE="${APPIMAGE_RUNTIME_FILE:-$TOOLS_DIR/runtime-x86_64}"
APPIMAGETOOL_VERSION="1.9.1"
APPIMAGETOOL_SHA256="ed4ce84f0d9caff66f50bcca6ff6f35aae54ce8135408b3fa33abfc3cb384eb0"
RUNTIME_SHA256="1cc49bcf1e2ccd593c379adb17c9f85a36d619088296504de95b1d06215aebbf"

mkdir -p "$TOOLS_DIR"
if [[ ! -f "$APPIMAGETOOL" ]]; then
  curl --fail --location --proto '=https' --tlsv1.2 \
    "https://github.com/AppImage/appimagetool/releases/download/${APPIMAGETOOL_VERSION}/appimagetool-x86_64.AppImage" \
    --output "$APPIMAGETOOL"
  chmod 0755 "$APPIMAGETOOL"
fi
echo "$APPIMAGETOOL_SHA256  $APPIMAGETOOL" | sha256sum --check -

if [[ ! -f "$RUNTIME_FILE" ]]; then
  curl --fail --location --proto '=https' --tlsv1.2 \
    "https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-x86_64" \
    --output "$RUNTIME_FILE"
fi
echo "$RUNTIME_SHA256  $RUNTIME_FILE" | sha256sum --check -

python3 "$APP_DIR/scripts/build-release-packages.py"
ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 \
  "$APPIMAGETOOL" --runtime-file "$RUNTIME_FILE" \
  "$APP_DIR/build/AppDir" \
  "$APP_DIR/dist/AI-Privacy-Studio-1.0.0-linux-x86_64.AppImage"

echo "Linux AppImage created successfully."
