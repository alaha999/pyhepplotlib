from pathlib import Path
import ROOT
import math

ROOT.gROOT.SetBatch(True)

import pyplotlib.pyplot as plt
from dummy_data import make_histograms, make_overflow_histogram

OUT = Path(__file__).parent / "outputs"
OUT.mkdir(exist_ok=True)


def save(name):
    plt.savefig(OUT / name)
    print(f"[OK] {name}")
    
def case_01_minimal():
    _, _, signal, _ = make_histograms()
    plt.style("CMS", lumi=138, year=2018, energy="13 TeV", extraText="Internal")
    plt.figure()
    plt.hist(signal, label="Signal", color=ROOT.kBlue)
    plt.draw()
    save("01_minimal.png")


def case_02_overlay():
    _, _, signal, _ = make_histograms()
    signal2 = signal.Clone("h_signal_shifted")
    signal2.SetDirectory(0)
    signal2.Scale(0.55)
    plt.figure()
    plt.hist(signal, label="Signal A", color=ROOT.kBlue)
    plt.hist(signal2, label="Signal B", color=ROOT.kRed, lstyle=ROOT.kDashed)
    plt.xaxis("Observable [GeV]", (0, 400))
    plt.yaxis("Events", (0.1, 100))
    plt.legend(pos=[0.68, 0.55, 0.92, 0.85])
    plt.draw(logY=True)
    save("02_overlay.png")


def case_03_stack_data_ratio():
    qcd, top, signal, data = make_histograms()
    plt.figure()
    plt.hist(qcd, label="Multijet", color=ROOT.kAzure + 1, stack=True, fill=True)
    plt.hist(top, label="Top", color=ROOT.kOrange + 1, stack=True, fill=True)
    plt.hist(signal, label="Signal x 5", color=ROOT.kRed, scale=5)
    plt.hist(data, label="Data", color=ROOT.kBlack, isData=True)
    plt.xaxis("Observable [GeV]", (0, 400))
    plt.yaxis("Events", (0.1, 2e3))
    plt.ratio_axis("Data / MC", (0.5, 1.5))
    plt.draw(logY=True)
    save("03_stack_data_ratio.png")


def case_04_atlas_analysis():
    qcd, top, signal, data = make_histograms()
    plt.style("ATLAS", lumi=51.8, year=2023, energy="13.6 TeV", extraText="Internal", pubStyle=False)
    plt.figure()
    plt.hist(qcd, label="Multijet", color=ROOT.kAzure + 1, stack=True, fill=True)
    plt.hist(top, label="Top", color=ROOT.kOrange + 1, stack=True, fill=True)
    plt.hist(signal, label="Signal x 10", color=ROOT.kRed, scale=10)
    plt.hist(data, label="Data", color=ROOT.kBlack, isData=True)
    plt.xaxis("Jet p_{T} [GeV]", (50, 350))
    plt.yaxis("Events", (0.1, 2e3))
    plt.ratio_axis("Data / Pred.", (0.5, 1.5))
    plt.legend(pos=[0.69, 0.45, 0.93, 0.84], fontsize=0.03)
    plt.caption("Dummy signal region")
    plt.draw(logY=True, rebin=2)
    save("04_atlas_analysis.png")


def case_05_publication():
    qcd, top, signal, data = make_histograms()
    plt.style("ATLAS", lumi=51.8, year=2023, energy="13.6 TeV", extraText="", pubStyle=True)
    plt.figure()
    plt.hist(qcd, label="Multijet", color=ROOT.kAzure + 1, stack=True, fill=True)
    plt.hist(top, label="Top", color=ROOT.kOrange + 1, stack=True, fill=True)
    plt.hist(signal, label="Signal x 10", color=ROOT.kRed, scale=10)
    plt.hist(data, label="Data", color=ROOT.kBlack, isData=True)
    plt.xaxis("Observable [GeV]", (0, 400))
    plt.yaxis("Events", (0.1, 2e3))
    plt.ratio_axis("Data / Pred.", (0.5, 1.5))
    plt.legend(pos=[0.64, 0.50, 0.94, 0.84])
    plt.draw(logY=True, showStat=False)
    save("05_publication.png")

    
def case_06_rebin_overflow():
    h = make_overflow_histogram()

    plt.style("CMS", lumi=138, year=2018, energy="13 TeV", extraText="Internal", pubStyle=False)
    plt.figure()
    plt.hist(h, label="Background", color=ROOT.kBlue, stack=True, fill=True)
    plt.xaxis("Observable [GeV]", (30, 170))
    plt.yaxis("Events", (0.1, 500))
    plt.draw(logY=True, rebin=[30, 50, 70, 100, 130, 170], truncate_xrange=True)

    # For this test there is only one stacked background, so h_totbkg is
    # the final histogram after overflow folding, truncation and rebinning.
    h_final = plt.current().h_totbkg

    print("\n" + "=" * 72)
    print(" TEST 06 — ORIGINAL HISTOGRAM")
    print("=" * 72)
    print(f"{'Bin':<8} {'Range':<22} {'Content':>14} {'Error':>14}")
    print("-" * 72)

    nbins = h.GetNbinsX()
    print(f"{'UF':<8} {'Underflow':<22}{h.GetBinContent(0):>14.2f}{h.GetBinError(0):>14.2f}")

    for i in range(1, nbins + 1):
        low, high = h.GetXaxis().GetBinLowEdge(i), h.GetXaxis().GetBinUpEdge(i)
        print(f"{i:<8} {f'[{low:.0f}, {high:.0f})':<22}{h.GetBinContent(i):>14.2f}{h.GetBinError(i):>14.2f}")

    print(f"{'OF':<8} {'Overflow':<22}{h.GetBinContent(nbins + 1):>14.2f}{h.GetBinError(nbins + 1):>14.2f}")

    original_total = sum(h.GetBinContent(i) for i in range(nbins + 2))
    original_error = math.sqrt(sum(h.GetBinError(i)**2 for i in range(nbins + 2)))

    print("-" * 72)
    print(f"{'Total':<30}{original_total:>14.2f}{original_error:>14.2f}")
    print("=" * 72)

    print("\n" + "=" * 72)
    print(" TEST 06 — FINAL HISTOGRAM ACTUALLY PLOTTED")
    print(" Range: 30 <= x <= 170 | Rebin: [30, 50, 70, 100, 130, 170]")
    print("=" * 72)
    print(f"{'Bin':<8} {'Range':<22} {'Content':>14} {'Error':>14}")
    print("-" * 72)

    nbins_final = h_final.GetNbinsX()
    print(f"{'UF':<8} {'Underflow':<22}{h_final.GetBinContent(0):>14.2f}{h_final.GetBinError(0):>14.2f}")

    for i in range(1, nbins_final + 1):
        low, high = h_final.GetXaxis().GetBinLowEdge(i), h_final.GetXaxis().GetBinUpEdge(i)
        print(f"{i:<8} {f'[{low:.0f}, {high:.0f})':<22}{h_final.GetBinContent(i):>14.2f}{h_final.GetBinError(i):>14.2f}")

    print(f"{'OF':<8} {'Overflow':<22}{h_final.GetBinContent(nbins_final + 1):>14.2f}{h_final.GetBinError(nbins_final + 1):>14.2f}")

    final_total = sum(h_final.GetBinContent(i) for i in range(nbins_final + 2))
    final_error = math.sqrt(sum(h_final.GetBinError(i)**2 for i in range(nbins_final + 2)))

    print("-" * 72)
    print(f"{'Original total':<30}{original_total:>14.2f}{original_error:>14.2f}")
    print(f"{'Final total':<30}{final_total:>14.2f}{final_error:>14.2f}")
    print(f"{'Difference':<30}{final_total - original_total:>14.2f}")
    print("=" * 72)

    save("06_rebin_overflow.png")


if __name__ == "__main__":
    case_01_minimal()
    case_02_overlay()
    case_03_stack_data_ratio()
    case_04_atlas_analysis()
    case_05_publication()
    case_06_rebin_overflow()
    print(f"\ntest plots written to: {OUT}")
