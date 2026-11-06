import ROOT
import pyplotlib.pyplot as plt

ROOT.gROOT.SetBatch(True)

# Create example histograms
h1 = ROOT.TH1D("h1", "", 40, 0, 200)
h2 = ROOT.TH1D("h2", "", 40, 0, 200)
h3 = ROOT.TH1D("h3", "", 40, 0, 200)

rng = ROOT.TRandom3(42)

for _ in range(10000):
    h1.Fill(rng.Gaus(80, 20))
    h2.Fill(rng.Gaus(100, 25))
    h3.Fill(rng.Gaus(120, 30))

# Plot
plt.style(experiment="ATLAS", lumi=140, extraText=" ",pubStyle=True)
plt.figure(w=800, h=700)

for h, color, label, linestyle in [
    (h1, ROOT.kRed + 1,   "Sample A", ROOT.kSolid),
    (h2, ROOT.kBlue + 1,  "Sample B", ROOT.kSolid),
    (h3, ROOT.kGreen + 2, "Sample C", ROOT.kSolid),
]:
    plt.hist(
        h,
        label=label,
        color=color,
        density=True,
        stack=False,
        fill=False,
        lwidth=3,
        lstyle=linestyle,
        legendStyle="lep",
    )

plt.xaxis("Observable [GeV]", (0, 200))
plt.yaxis("Normalized events", (0, 0.12))

plt.legend(pos=[0.64, 0.50, 0.94, 0.84])
plt.draw(logY=False,drawOption="HIST E")

plt.savefig("tests/outputs/normalized_overlay.png")
