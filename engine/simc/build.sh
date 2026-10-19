#!/usr/bin/env bash
# Build the pinned SimulationCraft CLI into engine/simc/bin/simc
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${ROOT}/SIMC_PIN"

BIN_DIR="${ROOT}/bin"
SRC_DIR="${ROOT}/src"
mkdir -p "${BIN_DIR}"

if [[ -x "${BIN_DIR}/simc" ]]; then
  echo "simc already present at ${BIN_DIR}/simc"
  "${BIN_DIR}/simc" 2>&1 | head -1 || true
  exit 0
fi

if [[ ! -d "${SRC_DIR}/.git" ]]; then
  git clone --depth 1 --branch "${BRANCH}" "${REPO_URL}" "${SRC_DIR}"
fi

cd "${SRC_DIR}"
git fetch --depth 1 origin "${COMMIT}"
git checkout "${COMMIT}"

cd "${SRC_DIR}/engine"
make clean >/dev/null 2>&1 || true
make SC_NO_NETWORKING=1 CXX=g++ -j"$(nproc)"
cp -f simc "${BIN_DIR}/simc"
echo "Built $(${BIN_DIR}/simc 2>&1 | head -1 || true)"
