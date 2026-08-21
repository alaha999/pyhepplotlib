import ROOT

ROOT.gROOT.SetBatch(True)

from pyplotlib import Plotter
import pyplotlib.pyplot as plt
from dummy_data import make_histograms, make_overflow_histogram


def test_plotter_state_is_independent():
    h, _, _, _ = make_histograms()
    p1 = Plotter()
    p2 = Plotter()
    p1.figure()
    p2.figure()
    p1.hist(h)
    assert len(p1.histogram) == 1
    assert len(p2.histogram) == 0


def test_histogram_is_detached_and_original_is_untouched():
    h = make_overflow_histogram()
    original_bins = h.GetNbinsX()
    original_overflow = h.GetBinContent(original_bins + 1)

    p = Plotter()
    p.figure()
    stored = p.hist(h, stack=True, fill=True)

    assert stored is not h
    assert not stored.GetDirectory()

    p.Draw(rebin=2, logY=False)
    p.Draw(rebin=1, logY=False)

    assert h.GetNbinsX() == original_bins
    assert h.GetBinContent(original_bins + 1) == original_overflow
    assert stored.GetNbinsX() == original_bins


def test_global_style_persists_across_figures():
    plt.style("ATLAS", lumi=140, year=2018, energy="13 TeV", extraText="Internal", pubStyle=False)
    first = plt.figure()
    second = plt.figure()

    for p in (first, second):
        assert p.experiment == "ATLAS"
        assert p.lumi == 140
        assert p.year == 2018
        assert p.energy == "13 TeV"
        assert p.extraText == "Internal"


def test_draw_can_be_repeated_with_different_rebinning():
    qcd, top, _, data = make_histograms()
    p = Plotter()
    p.figure()
    p.hist(qcd, stack=True, fill=True)
    p.hist(top, stack=True, fill=True)
    p.hist(data, isData=True, color=ROOT.kBlack)

    p.Draw(rebin=1, logY=False)
    first_bins = p.h_totbkg.GetNbinsX()
    p.Draw(rebin=2, logY=False)
    second_bins = p.h_totbkg.GetNbinsX()
    p.Draw(rebin=1, logY=False)
    third_bins = p.h_totbkg.GetNbinsX()

    assert second_bins < first_bins
    assert third_bins == first_bins

def test_underflow_overflow_merge():
    from pyplotlib.utils import merge_underflow_overflow_in_range

    h = ROOT.TH1D(
        "h_underflow_overflow_test",
        "",
        5,
        0,
        50
    )
    h.SetDirectory(0)

    # Explicit values so the expected result is obvious
    h.SetBinContent(0, 10.0)   # underflow
    h.SetBinContent(1, 20.0)   # 0-10
    h.SetBinContent(2, 30.0)   # 10-20
    h.SetBinContent(3, 40.0)   # 20-30
    h.SetBinContent(4, 50.0)   # 30-40
    h.SetBinContent(5, 60.0)   # 40-50
    h.SetBinContent(6, 70.0)   # overflow

    # Simple errors for checking propagation
    for i in range(0, 7):
        h.SetBinError(i, h.GetBinContent(i) ** 0.5)

    print("\n" + "=" * 78)
    print(" UNDERFLOW / OVERFLOW MERGE TEST")
    print(" Visible range: 10 <= x <= 40")
    print("=" * 78)

    print(
        f"{'Bin':<10} "
        f"{'Range':<18} "
        f"{'Before':>12} "
        f"{'After':>12} "
        f"{'Expected':>12}"
    )
    print("-" * 78)

    before = {
        "UF": h.GetBinContent(0),
        "bin1": h.GetBinContent(1),
        "bin2": h.GetBinContent(2),
        "bin3": h.GetBinContent(3),
        "bin4": h.GetBinContent(4),
        "bin5": h.GetBinContent(5),
        "OF": h.GetBinContent(6),
    }

    total_before = sum(before.values())

    merge_underflow_overflow_in_range(
        h,
        xmin=10,
        xmax=40
    )

    after = {
        "UF": h.GetBinContent(0),
        "bin1": h.GetBinContent(1),
        "bin2": h.GetBinContent(2),
        "bin3": h.GetBinContent(3),
        "bin4": h.GetBinContent(4),
        "bin5": h.GetBinContent(5),
        "OF": h.GetBinContent(6),
    }

    expected = {
        "UF": 0.0,
        "bin1": 0.0,
        "bin2": 60.0,   # UF + bin1 + bin2 = 10 + 20 + 30
        "bin3": 40.0,
        "bin4": 180.0,  # bin4 + bin5 + OF = 50 + 60 + 70
        "bin5": 0.0,
        "OF": 0.0,
    }

    rows = [
        ("UF",   "underflow"),
        ("bin1", "[0, 10)"),
        ("bin2", "[10, 20)"),
        ("bin3", "[20, 30)"),
        ("bin4", "[30, 40)"),
        ("bin5", "[40, 50)"),
        ("OF",   "overflow"),
    ]

    for key, label in rows:
        print(
            f"{key:<10} "
            f"{label:<18} "
            f"{before[key]:>12.2f} "
            f"{after[key]:>12.2f} "
            f"{expected[key]:>12.2f}"
        )

    print("-" * 78)

    total_after = sum(after.values())

    print(
        f"{'Total':<29} "
        f"{total_before:>12.2f} "
        f"{total_after:>12.2f} "
        f"{total_before:>12.2f}"
    )

    print("=" * 78)

    for key in expected:
        assert after[key] == expected[key]

    assert total_after == total_before    
