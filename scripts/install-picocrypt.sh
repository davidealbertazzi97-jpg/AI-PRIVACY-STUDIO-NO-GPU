#!/usr/bin/env bash
set -euo pipefail

app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
target="$app_dir/bin/picocrypt"
download="$target.download"
license_target="$app_dir/bin/PICOCRYPT-LICENSE-GPL-3.0.txt"
license_download="$license_target.download"
url="https://github.com/Picocrypt/CLI/releases/download/1.49/picocrypt-linux-amd64"
license_url="https://raw.githubusercontent.com/Picocrypt/CLI/1.49/LICENSE"
expected="9ecd432f96374944ae271b1a40cc21d844f6a6f7d6f115a3777338da3772a3e5"
license_expected="3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986"

mkdir -p -- "$app_dir/bin"
cleanup() {
  rm -f -- "$download" "$license_download"
}
trap cleanup EXIT

curl --fail --location --proto '=https' --tlsv1.2 --output "$download" "$url"
actual="$(sha256sum "$download" | cut -d' ' -f1)"
if [[ "$actual" != "$expected" ]]; then
  printf 'Checksum Picocrypt non valido: %s\n' "$actual" >&2
  exit 1
fi

curl \
  --fail \
  --location \
  --proto '=https' \
  --tlsv1.2 \
  --output "$license_download" \
  "$license_url"
license_actual="$(sha256sum "$license_download" | cut -d' ' -f1)"
if [[ "$license_actual" != "$license_expected" ]]; then
  printf 'Checksum licenza Picocrypt non valido: %s\n' "$license_actual" >&2
  exit 1
fi

chmod 0755 "$download"
mv -f -- "$download" "$target"
chmod 0644 "$license_download"
mv -f -- "$license_download" "$license_target"
"$target" 2>&1 | head -n 2 || true
