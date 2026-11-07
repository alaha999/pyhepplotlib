import ROOT
import math
import random
from pathlib import Path
import pyplotlib.pyplot as plt
from pyplotlib.utils import rebinned_hist, efficiency_graph

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kWarning
random.seed(42)

OUTPUT = Path(__file__).resolve().parent / "outputs"
OUTPUT.mkdir(parents=True, exist_ok=True)

plt.style(experiment="ATLAS", lumi=140, energy="13 TeV", extraText="Internal", pubStyle=True)


def save(name):
    filename = OUTPUT / name
    plt.savefig(str(filename))
    print(f"[OK] Saved: {filename}")


def make_efficiency_histograms():
    h_total = ROOT.TH1D("total", "", 40, 0, 400)
    h_pass70 = ROOT.TH1D("pass70", "", 40, 0, 400)
    h_pass85 = ROOT.TH1D("pass85", "", 40, 0, 400)

    for h in (h_total, h_pass70, h_pass85):
        h.Sumw2()
        h.SetDirectory(0)

    for _ in range(30000):
        pt = random.uniform(0, 400)
        weight = random.uniform(0.5, 1.5)
        eff70 = 0.45 + 0.30 * (1 - math.exp(-pt / 100))
        eff85 = 0.65 + 0.25 * (1 - math.exp(-pt / 120))
        score = random.random()

        h_total.Fill(pt, weight)
        if score < eff70: h_pass70.Fill(pt, weight)
        if score < eff85: h_pass85.Fill(pt, weight)

    return h_total, h_pass70, h_pass85


def make_limit_graphs():
    n = 21
    expected, observed = ROOT.TGraph(n), ROOT.TGraph(n)
    band1, band2 = ROOT.TGraphAsymmErrors(n), ROOT.TGraphAsymmErrors(n)

    for i in range(n):
        mass = 500 + 25 * i
        median = 10.0 * math.exp(-(mass - 500) / 300) + 0.02
        obs = median * (1.0 + 0.12 * math.sin(i * 0.45) + 0.05 * math.cos(i * 0.9))

        expected.SetPoint(i, mass, median)
        observed.SetPoint(i, mass, obs)

        band1.SetPoint(i, mass, median)
        band2.SetPoint(i, mass, median)

        band1.SetPointError(i, 0, 0, median * 0.20, median * 0.30)
        band2.SetPointError(i, 0, 0, median * 0.40, median * 0.65)

    return expected, observed, band1, band2

h_total, h_pass70, h_pass85 = make_efficiency_histograms()
expected, observed, band1, band2 = make_limit_graphs()


# ============================================================
# 01. Basic weighted efficiency
# ============================================================

plt.figure()
plt.graph(h_pass70, h_total, color="ROOT.kBlue", label="70% WP")
plt.graph(h_pass85, h_total, color="ROOT.kRed", label="85% WP")
plt.xaxis("Jet p_{T} [GeV]")
plt.yaxis("Tagging efficiency")
plt.legend(pos=[0.60, 0.70, 0.88, 0.85])
plt.draw(mode="efficiency", error="bayesian", drawstyle="errors", ratio=False)
save("01_graph_efficiency.png")


# ============================================================
# 02. Efficiency with ratio panel
# ============================================================

plt.figure()
plt.graph(h_pass70, h_total, color="ROOT.kBlue", label="70% WP")
plt.graph(h_pass85, h_total, color="ROOT.kRed", label="85% WP")
plt.xaxis("Jet p_{T} [GeV]")
plt.yaxis("Tagging efficiency")
plt.ratio_axis("Efficiency / 70% WP")
plt.legend(pos=[0.60, 0.70, 0.88, 0.85])
plt.draw(mode="efficiency", error="normal", drawstyle="errors", ratio=True, reference=0)
save("02_graph_efficiency_ratio.png")


# ============================================================
# 03. Efficiency with fixed rebinning
# ============================================================

plt.figure()
plt.graph(h_pass70, h_total, color="ROOT.kBlue", label="70% WP")
plt.graph(h_pass85, h_total, color="ROOT.kRed", label="85% WP")
plt.xaxis("Jet p_{T} [GeV]")
plt.yaxis("Tagging efficiency")
plt.legend(pos=[0.60, 0.70, 0.88, 0.85])
plt.draw(mode="efficiency", error="normal", drawstyle="errors", rebin=4)
save("03_graph_efficiency_rebin.png")


# ============================================================
# 04. Efficiency with variable-width rebinning
# ============================================================

bins = [0, 20, 40, 60, 100, 150, 200, 300, 400]

plt.figure()
plt.graph(h_pass70, h_total, color="ROOT.kBlue", label="70% WP")
plt.graph(h_pass85, h_total, color="ROOT.kRed", label="85% WP")
plt.xaxis("Jet p_{T} [GeV]")
plt.yaxis("Tagging efficiency")
plt.legend(pos=[0.60, 0.70, 0.88, 0.85])
plt.draw(mode="efficiency", error="normal", drawstyle="errors", rebin=bins)
save("04_graph_efficiency_variablebin.png")


# ============================================================
# Numerical checks
# ============================================================

assert h_total.GetNbinsX() == 40
assert h_pass70.GetNbinsX() == 40
assert h_pass85.GetNbinsX() == 40
assert rebinned_hist(h_total, 4).GetNbinsX() == 10
assert rebinned_hist(h_total, bins).GetNbinsX() == 8

g_eff = efficiency_graph(h_pass70, h_total, error="normal")
assert g_eff.GetN() == 40
assert all(0 <= g_eff.GetPointY(i) <= 1 for i in range(g_eff.GetN()))
print("[OK] Numerical checks passed.")


# ============================================================
# 05. Generic ROOT TGraph plotting
# ============================================================

plt.figure()
plt.graph(expected, color="ROOT.kBlack", label="Expected", lstyle="ROOT.kDashed", lwidth=3)
plt.graph(observed, color="ROOT.kRed", label="Observed", lwidth=3)
plt.xaxis("Mass [GeV]")
plt.yaxis("95% CL upper limit")
plt.legend(pos=[0.60, 0.70, 0.88, 0.85])
plt.draw(mode="graph", drawstyle="line")
save("05_graph_limit.png")


# ============================================================
# 06. Limit plot with uncertainty bands
# ============================================================

plt.figure()
plt.graph(band2, color="ROOT.kYellow", label="Expected #pm2#sigma", fill=True, drawstyle="band",fillalpha=1.0)
plt.graph(band1, color="ROOT.kGreen", label="Expected #pm1#sigma", fill=True, drawstyle="band",fillalpha=1.0)
plt.graph(expected, color="ROOT.kBlack", label="Expected", lstyle="ROOT.kDashed", lwidth=3)
plt.graph(observed, color="ROOT.kBlack", label="Observed", lstyle="ROOT.kSolid", lwidth=3)
plt.xaxis("Mass [GeV]",xrange=(495,1005))
plt.yaxis("95% CL upper limit #sigma [pb]")
plt.legend(pos=[0.57, 0.60, 0.88, 0.85])
plt.draw(mode="graph", drawstyle="line", logY=False)
save("06_graph_limit_band.png")


# ============================================================
# 07. Asymmetric error bars
# ============================================================

graph = ROOT.TGraphAsymmErrors(10)

for i in range(10):
    x, y = 10 + i * 10, 0.3 + 0.05 * i
    graph.SetPoint(i, x, y)
    graph.SetPointError(i, 2, 2, 0.03 + i * 0.002, 0.08 + i * 0.004)

plt.figure()
plt.graph(graph, color="ROOT.kBlue", label="Asymmetric uncertainties", markerstyle=20, markersize=1.0)
plt.xaxis("Observable")
plt.yaxis("Measurement")
plt.legend(pos=[0.50, 0.75, 0.88, 0.85])
plt.draw(mode="graph", drawstyle="errors")
save("07_graph_asymmetric.png")

plt.close()
