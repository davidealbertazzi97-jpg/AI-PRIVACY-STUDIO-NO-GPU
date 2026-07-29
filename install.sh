#!/usr/bin/env bash
set -euo pipefail

app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
uv_version="0.11.16"
system_name="$(uname -s)"
machine_name="$(uname -m)"

case "$system_name/$machine_name" in
  Linux/x86_64)
    uv_asset="uv-x86_64-unknown-linux-gnu.tar.gz"
    uv_sha256="74947fe2c03315cf07e82ab3acc703eddef01aba4d5232a98e4c6825ec116131"
    ;;
  Darwin/arm64)
    uv_asset="uv-aarch64-apple-darwin.tar.gz"
    uv_sha256="2b25be1af546be330b340b0a76b99f989daa6d92678fdffb87438e661e9d88fb"
    ;;
  *)
    printf 'Profilo completo non supportato: %s/%s.\n' \
      "$system_name" "$machine_name" >&2
    printf 'Sono supportati Linux x86-64 e macOS Apple Silicon.\n' >&2
    exit 1
    ;;
esac

uv_dir="$app_dir/.tools/uv"
uv_bin="$uv_dir/uv"
if [[ ! -x "$uv_bin" ]]; then
  temporary="$(mktemp -d)"
  cleanup() {
    rm -rf -- "$temporary"
  }
  trap cleanup EXIT
  archive="$temporary/$uv_asset"
  url="https://github.com/astral-sh/uv/releases/download/$uv_version/$uv_asset"
  printf 'Scarico uv %s e verifico SHA-256...\n' "$uv_version"
  if command -v curl >/dev/null 2>&1; then
    curl --fail --location --proto '=https' --tlsv1.2 \
      --output "$archive" "$url"
  elif command -v wget >/dev/null 2>&1; then
    wget --https-only --secure-protocol=TLSv1_2 \
      --output-document="$archive" "$url"
  else
    printf 'Serve curl o wget per il bootstrap verificato.\n' >&2
    exit 1
  fi
  if command -v sha256sum >/dev/null 2>&1; then
    actual="$(sha256sum "$archive" | cut -d' ' -f1)"
  elif command -v shasum >/dev/null 2>&1; then
    actual="$(shasum -a 256 "$archive" | cut -d' ' -f1)"
  elif command -v openssl >/dev/null 2>&1; then
    actual="$(openssl dgst -sha256 -r "$archive" | cut -d' ' -f1)"
  else
    printf 'Manca un programma locale per verificare SHA-256.\n' >&2
    exit 1
  fi
  if [[ "$actual" != "$uv_sha256" ]]; then
    printf 'Checksum uv non valido: %s\n' "$actual" >&2
    exit 1
  fi
  mkdir -p -- "$uv_dir"
  tar -xzf "$archive" -C "$uv_dir" --strip-components=1
  chmod 0755 "$uv_bin"
fi

"$uv_bin" python install 3.12
export PRIVACY_STUDIO_UV="$uv_bin"
exec "$uv_bin" run --isolated --no-project --python 3.12 \
  "$app_dir/scripts/bootstrap.py" "$@"
