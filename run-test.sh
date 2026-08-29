#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo " pyplotlib tests"
echo "============================================================"

# Basic environment sanity
echo "[INFO] Checking ROOT..."
python3 - <<'PY'
import ROOT
print(f"[OK] ROOT version: {ROOT.gROOT.GetVersion()}")
PY

echo "[INFO] Checking pyplotlib..."
python3 - <<'PY'
import pyplotlib.pyplot as plt
print("[OK] pyplotlib import successful")
PY

# Core regression tests
echo
echo "[INFO] Running core tests..."
python3 -m pytest -vv -s tests/test_core.py

# printTable test
echo
echo "[INFO] Running print table test..."
python3 tests/test_print_table.py

# Visual gallery tests
echo
echo "[INFO] Generating plot gallery..."
rm -f tests/outputs/*.png
python3 tests/test_gallery.py

# Check PNGs were actually produced
echo
echo "[INFO] Checking generated plots..."

nplots=$(find tests/outputs -maxdepth 1 -name "*.png" | wc -l)

if [[ "$nplots" -eq 0 ]]; then
    echo "[ERROR] No PNG plots were produced."
    exit 1
fi

echo "[OK] Generated $nplots plot(s):"
find tests/outputs -maxdepth 1 -name "*.png" -printf "  %f\n" | sort


echo
echo "============================================================"
echo " All tests completed successfully"
echo "============================================================"
echo
echo "Visual gallery:"
echo "  tests/README.md"
echo
echo "Generated images:"
echo "  tests/outputs/"
