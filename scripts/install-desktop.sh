#!/usr/bin/env bash
set -euo pipefail

app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
config_dir="$HOME/.config/privacy-studio"
state_dir="$HOME/.local/state/privacy-studio"
applications_dir="$HOME/.local/share/applications"
icons_dir="$HOME/.local/share/icons/hicolor/scalable/apps"
unit_dir="$HOME/.config/systemd/user"
user_bin_dir="$HOME/.local/bin"
dashboard_dir="$HOME/Scrivania/PANNELLI DI CONTROLLO"
environment_file="$config_dir/environment"
gui_launcher="$user_bin_dir/privacy-studio"
service_launcher="$user_bin_dir/privacy-studio-service"

umask 077
mkdir -p -- \
  "$config_dir" \
  "$state_dir" \
  "$applications_dir" \
  "$icons_dir" \
  "$unit_dir" \
  "$user_bin_dir"

if [[ ! -s "$environment_file" ]]; then
  token="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
  printf 'PRIVACY_STUDIO_TOKEN=%s\nPRIVACY_STUDIO_PORT=8765\n' "$token" > "$environment_file"
fi
chmod 0600 "$environment_file"

gui_temp="$(mktemp "$state_dir/gui-launcher.XXXXXX")"
service_temp="$(mktemp "$state_dir/service-launcher.XXXXXX")"
desktop_temp="$(mktemp "$state_dir/desktop-entry.XXXXXX")"
unit_temp="$(mktemp "$state_dir/service-unit.XXXXXX")"
cleanup() {
  rm -f -- "$gui_temp" "$service_temp" "$desktop_temp" "$unit_temp"
}
trap cleanup EXIT

{
  printf '#!/usr/bin/env bash\n'
  printf 'set -euo pipefail\n'
  printf 'exec %q "$@"\n' "$app_dir/scripts/open.sh"
} > "$gui_temp"

{
  printf '#!/usr/bin/env bash\n'
  printf 'set -euo pipefail\n'
  printf 'app_dir=%q\n' "$app_dir"
  printf 'cd -- "$app_dir"\n'
  printf 'export LD_PRELOAD="$app_dir/bin/libprivacy_studio_netguard.so"\n'
  printf 'exec "$app_dir/.venv/bin/python" -m uvicorn app.main:app '
  printf '%s\n' \
    '--host 127.0.0.1 --port "${PRIVACY_STUDIO_PORT:-8765}" --no-access-log'
} > "$service_temp"

install -m 0755 "$gui_temp" "$gui_launcher"
install -m 0755 "$service_temp" "$service_launcher"

python3 - \
  "$app_dir/packaging/privacy-studio.desktop.in" \
  "$desktop_temp" \
  "@GUI_LAUNCHER@" \
  "$gui_launcher" <<'PY'
from pathlib import Path
import sys

template, output, marker, value = sys.argv[1:]
text = Path(template).read_text(encoding="utf-8")
Path(output).write_text(text.replace(marker, value), encoding="utf-8")
PY

python3 - \
  "$app_dir/packaging/privacy-studio.service.in" \
  "$unit_temp" \
  "@SERVICE_LAUNCHER@" \
  "$service_launcher" <<'PY'
from pathlib import Path
import sys

template, output, marker, value = sys.argv[1:]
text = Path(template).read_text(encoding="utf-8")
Path(output).write_text(text.replace(marker, value), encoding="utf-8")
PY

install -m 0644 "$unit_temp" "$unit_dir/privacy-studio.service"
install -m 0644 "$desktop_temp" "$applications_dir/privacy-studio.desktop"
install -m 0644 "$app_dir/static/icon.svg" \
  "$icons_dir/privacy-studio.svg"

if [[ -d "$dashboard_dir" ]]; then
  install -m 0755 "$desktop_temp" \
    "$dashboard_dir/Privacy Studio Locale.desktop"
  gio set "$dashboard_dir/Privacy Studio Locale.desktop" \
    metadata::trusted true 2>/dev/null || true
fi

systemctl --user daemon-reload
update-desktop-database "$applications_dir" 2>/dev/null || true
gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
printf 'Launcher Privacy Studio installato.\n'
