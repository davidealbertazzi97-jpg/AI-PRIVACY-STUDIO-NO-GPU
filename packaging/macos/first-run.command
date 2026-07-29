#!/bin/sh
set -eu

INSTALL_ROOT="$HOME/Library/Application Support/AI Privacy Studio/app"
cd -- "$INSTALL_ROOT"

printf '\nAI Privacy Studio — installation / installazione\n\n'
./install.sh

if [ -f .pending-bundle-version ]; then
  mv -f -- .pending-bundle-version .bundle-version
fi

printf '\nInstallation complete. Starting the app.\n'
printf 'Installazione completata. Avvio dell’app.\n\n'
exec ./start.sh
