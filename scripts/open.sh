#!/usr/bin/env bash
set -euo pipefail

app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
environment_file="$HOME/.config/privacy-studio/environment"
if [[ ! -r "$environment_file" ]]; then
  notify-send "Privacy Studio" "Installazione incompleta: manca la configurazione locale."
  exit 1
fi

token="$(sed -n 's/^PRIVACY_STUDIO_TOKEN=//p' "$environment_file" | head -n 1)"
port="$(sed -n 's/^PRIVACY_STUDIO_PORT=//p' "$environment_file" | head -n 1)"
if [[ -z "$token" ]]; then
  notify-send "Privacy Studio" "Configurazione locale non valida."
  exit 1
fi
if [[ ! "$port" =~ ^[0-9]+$ ]] || ((port < 1024 || port > 65535)); then
  notify-send "Privacy Studio" "Porta locale non valida nella configurazione."
  exit 1
fi

systemctl --user start privacy-studio.service
for _ in $(seq 1 80); do
  if curl --silent --fail --max-time 1 \
    "http://127.0.0.1:$port/health" >/dev/null; then
    url="http://127.0.0.1:$port/?token=$token"
    browser=""
    for candidate in chromium chromium-browser google-chrome google-chrome-stable; do
      if command -v "$candidate" >/dev/null 2>&1; then
        browser="$(command -v "$candidate")"
        break
      fi
    done
    if [[ -z "$browser" ]]; then
      notify-send \
        "Privacy Studio" \
        "Installa Chromium o Google Chrome per usare il browser isolato."
      exit 1
    fi
    browser_profile="$HOME/.local/state/privacy-studio/chrome-profile"
    netguard="$app_dir/bin/libprivacy_studio_netguard.so"
    mkdir -p -- "$browser_profile"
    chmod 0700 "$browser_profile"
    if [[ ! -r "$netguard" ]]; then
      notify-send \
        "Privacy Studio" \
        "Manca il guard di rete locale. Esegui scripts/install-netguard.sh."
      exit 1
    fi
    setsid -f env "LD_PRELOAD=$netguard" "$browser" \
        --app="$url" \
        --class=PrivacyStudio \
        --user-data-dir="$browser_profile" \
        --no-first-run \
        --disable-background-networking \
        --disable-component-update \
        --disable-default-apps \
        --disable-sync \
        --disable-client-side-phishing-detection \
        --disable-domain-reliability \
        --disable-breakpad \
        --disable-crash-reporter \
        --metrics-recording-only \
        --disable-ipv6 \
        --proxy-server=http://127.0.0.1:9 \
        --proxy-bypass-list=127.0.0.1,localhost \
        --host-resolver-rules="MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost" \
        --disable-features=AutofillServerCommunication,DnsOverHttps,InterestFeedContentSuggestions,MediaRouter,NetworkTimeServiceQuerying,OptimizationHints,Translate \
        >/dev/null 2>&1
    exit 0
  fi
  sleep 0.25
done

notify-send "Privacy Studio" "Il servizio locale non si è avviato. Controlla i log."
exit 1
