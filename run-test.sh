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
rm -f tests/outputs/*
python3 tests/test_gallery.py

# pieChart test
echo
echo "[INFO] Running pieChart test..."
python3 tests/test_pie_chart.py

echo
echo "============================================================"
echo " All tests completed successfully"
echo "============================================================"
echo
