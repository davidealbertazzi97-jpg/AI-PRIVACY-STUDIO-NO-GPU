#!/usr/bin/env bash
set -euo pipefail

app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
compiler="$(command -v cc || true)"
target="$app_dir/bin/libprivacy_studio_netguard.so"

if [[ -z "$compiler" ]]; then
  printf 'Manca un compilatore C per il guard di rete del browser.\n' >&2
  exit 1
fi

mkdir -p -- "$app_dir/bin"
"$compiler" \
  -shared \
  -fPIC \
  -O2 \
  -Wall \
  -Wextra \
  -Werror \
  -o "$target" \
  "$app_dir/native/netguard.c"
chmod 0755 "$target"
printf 'Guard di rete browser pronto.\n'
