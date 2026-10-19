#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${1:-}"
DEST="${ROOT}/packages/game-data/presets/12.1.5"
mkdir -p "${DEST}"

if [[ -z "${SRC}" ]]; then
  echo "Usage: $0 /path/to/simc/profiles/MID1" >&2
  exit 1
fi

cp -f "${SRC}"/MID1_*.simc "${DEST}/"
echo "Imported presets into ${DEST}"
ls "${DEST}" | wc -l
