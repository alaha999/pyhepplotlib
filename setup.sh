#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo " pyplotlib setup"
echo "============================================================"

echo "[INFO] Python: $(python3 --version)"

echo "[INFO] Checking PyROOT..."
python3 - <<'PY'
import ROOT
print(f"[OK] ROOT version: {ROOT.gROOT.GetVersion()}")
PY

# Read local version from pyproject.toml without Python dependencies
LOCAL_VERSION=$(grep -m1 '^version *= *' pyproject.toml | sed -E 's/version *= *"([^"]+)"/\1/')

if [[ -z "$LOCAL_VERSION" ]]; then
    echo "[ERROR] Could not determine local version from pyproject.toml"
    exit 1
fi

# Check installed version
INSTALLED_VERSION=$(python3 -m pip show pyplotlib-hep 2>/dev/null | awk '/^Version:/ {print $2}')

echo "[INFO] Repository version: $LOCAL_VERSION"

if [[ -z "$INSTALLED_VERSION" ]]; then
    echo "[INFO] pyplotlib is not installed."
    echo "[INFO] Installing in editable mode..."
    python3 -m pip install -e .

elif [[ "$INSTALLED_VERSION" == "$LOCAL_VERSION" ]]; then
    echo "[OK] pyplotlib $INSTALLED_VERSION is already installed."
    echo "[INFO] Skipping installation."

else
    echo "[WARNING] Installed version : $INSTALLED_VERSION"
    echo "[WARNING] Repository version: $LOCAL_VERSION"

    read -rp "Install repository version $LOCAL_VERSION instead? [y/N] " answer

    if [[ "$answer" =~ ^[Yy]$ ]]; then
        python3 -m pip install -e .
    else
        echo "[INFO] Keeping pyplotlib $INSTALLED_VERSION."
        exit 0
    fi
fi

# pytest only if missing
if python3 -c "import pytest" >/dev/null 2>&1; then
    echo "[OK] pytest already available."
else
    echo "[INFO] Installing pytest..."
    python3 -m pip install -q pytest
fi

echo "[INFO] Checking pyplotlib import..."
python3 - <<'PY'
import pyplotlib.pyplot as plt
print("[OK] import pyplotlib.pyplot as plt")
PY

echo
echo "============================================================"
echo " Setup complete"
echo "============================================================"
echo "Next run:"
echo "  ./run-test.sh"
