import os
import ROOT
ROOT.gROOT.SetBatch(True)

import pyplotlib.pyplot as plt
from dummy_data import make_histograms


GREEN = "\033[92m"
RESET = "\033[0m"

OUTPUT_DIR = "tests/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def ok(message):
    print(f"{GREEN}OK{RESET} - {message}")


# --------------------------------------------------
# 1. Normal pie chart
# --------------------------------------------------

qcd, top, signal, data = make_histograms()

plt.figure()
plt.hist(qcd, label="Multijet", stack=True, fill=True, color="ROOT.kAzure+1")
plt.hist(top, label="Top", stack=True, fill=True, color="ROOT.kOrange+1")
plt.hist(signal, label="Signal")
plt.hist(data, label="Data", isData=True)

plt.draw()
plt.pieChart(extraTextOffset=0.135,savefig=f"{OUTPUT_DIR}/01_pietest.pdf")

ok("normal pie chart")


# --------------------------------------------------
# 2. Custom cosmetics
# --------------------------------------------------

qcd, top, signal, data = make_histograms()

plt.figure()
plt.hist(qcd, label="Multijet", stack=True, fill=True, color="ROOT.kAzure+1")
plt.hist(top, label="Top", stack=True, fill=True, color="ROOT.kOrange+1")
plt.hist(signal, label="Signal")
plt.hist(data, label="Data", isData=True)

plt.draw()
plt.pieChart(
    savefig=f"{OUTPUT_DIR}/02_pietest_custom.png",
    title="Background composition",
    labelSize=0.045,
    radius=0.36,
    angle=25,
    w=800,
    h=700,
)

ok("custom pie chart")


# --------------------------------------------------
# 3. Experiment label / style
# --------------------------------------------------

plt.style(
    "ATLAS",
    lumi=140,
    year=2018,
    energy="13 TeV",
    extraText="Internal",
    pubStyle=False,
)

qcd, top, signal, data = make_histograms()

plt.figure()
plt.hist(qcd, label="Multijet", stack=True, fill=True, color="ROOT.kAzure+1")
plt.hist(top, label="Top", stack=True, fill=True, color="ROOT.kOrange+1")
plt.hist(signal, label="Signal")
plt.hist(data, label="Data", isData=True)

plt.draw()
plt.pieChart(savefig=f"{OUTPUT_DIR}/03_pietest_atlas.pdf")

ok("pie chart with experiment label")


# --------------------------------------------------
# 4. No backgrounds -> should fail cleanly
# --------------------------------------------------

_, _, signal, data = make_histograms()

plt.figure()
plt.hist(signal, label="Signal")
plt.hist(data, label="Data", isData=True)

plt.draw()

try:
    plt.pieChart()
except RuntimeError:
    ok("pieChart refuses plot without backgrounds")
else:
    raise RuntimeError("pieChart() should fail when no backgrounds exist")


# --------------------------------------------------
# 5. pieChart before draw -> should fail cleanly
# --------------------------------------------------

qcd, _, _, _ = make_histograms()

plt.figure()
plt.hist(qcd, label="Multijet", stack=True, fill=True)

try:
    plt.pieChart()
except RuntimeError:
    ok("pieChart refuses before draw()")
else:
    raise RuntimeError("pieChart() should fail before draw()")


print(f"\n{GREEN}OK - ALL PIE CHART TESTS FINISHED{RESET}\n")
