#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${1:-}"
DEST="${ROOT}/packages/game-data/presets/12.1.5"
mkdir -p "${DEST}"

if [[ -z "${SRC}" ]]; then
  echo "Usage: $0 /path/to/simc/profiles/MID2 [/path/to/simc/profiles/MID1]" >&2
  exit 1
fi

cp -f "${SRC}"/MID2_*.simc "${DEST}/" 2>/dev/null || true

# Optional MID1 fallbacks for specs without MID2 profiles on the pin.
if [[ -n "${2:-}" ]]; then
  for f in \
    MID1_Druid_Balance.simc \
    MID1_Druid_Guardian.simc \
    MID1_Evoker_Devastation.simc
  do
    if [[ -f "${2}/${f}" ]]; then
      cp -f "${2}/${f}" "${DEST}/"
    fi
  done
fi

echo "Imported presets into ${DEST}"
ls "${DEST}" | wc -l
