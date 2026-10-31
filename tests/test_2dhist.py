"""Standalone pyhepplotlib TH2 gallery and basic conservation checks.

Run from the repository root:
    python tests/test_2dhist.py

Outputs are written to tests/outputs/.
"""

from pathlib import Path
import math

import ROOT
import pyplotlib.pyplot as plt

ROOT.gROOT.SetBatch(True)
ROOT.TH1.AddDirectory(False)
ROOT.gErrorIgnoreLevel = ROOT.kWarning

OUT = Path(__file__).resolve().parent / "outputs"
OUT.mkdir(parents=True, exist_ok=True)


def make_histograms():
    """Two TH2D samples with identical binning and intentionally populated flows."""
    qcd = ROOT.TH2D("h2_qcd_test", "QCD", 40, 0, 400, 40, -4, 4)
    top = ROOT.TH2D("h2_top_test", "Top", 40, 0, 400, 40, -4, 4)
    qcd.Sumw2()
    top.Sumw2()
    rng = ROOT.TRandom3(42)

    for _ in range(18000):
        qcd.Fill(rng.Gaus(120, 55), rng.Gaus(-0.5, 1.0), 1.0)
    for _ in range(8000):
        top.Fill(rng.Gaus(240, 60), rng.Gaus(0.7, 0.85), 1.5)

    # Exercise underflow, overflow, and diagonal corner cells explicitly.
    for h in (qcd, top):
        h.Fill(-30, 0.0, 2.0)      # X underflow
        h.Fill(450, 0.0, 3.0)      # X overflow
        h.Fill(100, -6, 4.0)      # Y underflow
        h.Fill(100, 6, 5.0)       # Y overflow
        h.Fill(-30, 6, 6.0)       # corner
        h.Fill(450, -6, 7.0)      # corner
    return qcd, top


def total(h):
    return sum(
        h.GetBinContent(ix, iy)
        for ix in range(h.GetNbinsX() + 2)
        for iy in range(h.GetNbinsY() + 2)
    )


def make_plot(name, hist, *, rebinx=1, rebiny=1, fold=True,
              xrange=None, yrange=None, cmap="viridis", logz=True):
    plt.figure(name, w=800, h=750)
    plt.hist2d(hist, rebinx=rebinx, rebiny=rebiny, fold=fold,
               cmap=cmap, label="QCD + t#bar{t}")
    plt.xaxis("X [GeV]", xrange or (0, 400))
    plt.yaxis("Y [GeV]", yrange or (-4, 4))
    plt.zaxis("Events")
    plt.legend(pos=[0.60, 0.01, 0.92, 0.85], fontsize=0.035)
    plt.caption("Simulation")
    plt.draw(logZ=logz)
    plt.savefig(str(OUT / f"{name}.png"))
    plt.close()
    print(f"Saved: {OUT / (name + '.png')}")


def main():
    plt.style(experiment="ATLAS", lumi=140, year="Run 2",
              energy="13 TeV", extraText="Internal")
    qcd, top = make_histograms()
    qcd_before, top_before = total(qcd), total(top)

    # 01: minimal API, ROOT TH2 addition, default rebinning and folding.
    make_plot("2d_01_minimal", [qcd , top])

    # 02: integer rebinning on each axis.
    make_plot("2d_02_integer_rebin", [qcd, top], rebinx=2, rebiny=4,cmap="bird")

    # 03: non-uniform edges aligned with the original bin boundaries.
    make_plot("2d_03_variable_rebin", [qcd , top],
              rebinx=[0, 40, 100, 200, 300, 400],
              rebiny=[-4, -2, -1, 0, 1, 2, 4],cmap="cool")

    # 04: restricted ranges; contents outside both axes fold to edge bins.
    make_plot("2d_04_range_fold", [qcd , top],
              xrange=(50, 350), yrange=(-2, 2),
              rebinx=2, rebiny=2, fold=True, cmap="cool")

    # The plotting layer must never modify user input histograms.
    assert math.isclose(total(qcd), qcd_before, rel_tol=1e-12)
    assert math.isclose(total(top), top_before, rel_tol=1e-12)
    print("PASS: input TH2 histograms remain unchanged")


if __name__ == "__main__":
    main()
