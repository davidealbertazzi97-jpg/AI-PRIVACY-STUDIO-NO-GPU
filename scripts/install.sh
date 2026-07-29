#!/usr/bin/env bash
set -euo pipefail

app_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

"$app_dir/scripts/check-prerequisites.sh"
"$app_dir/scripts/install-core.sh"
"$app_dir/scripts/install-picocrypt.sh"
"$app_dir/scripts/install-netguard.sh"
"$app_dir/scripts/install-ai.sh"
"$app_dir/scripts/prefetch-models.sh"
"$app_dir/scripts/install-paddle.sh"
"$app_dir/scripts/install-glm.sh"
"$app_dir/scripts/install-desktop.sh"

printf 'Privacy Studio è installato. Aprilo dal menu applicazioni o dalla dashboard.\n'
