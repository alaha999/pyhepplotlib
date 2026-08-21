#pyplotlib

A small PyROOT histogram plotting library with a minimal `matplotlib`-style interface and the original `Plotter` API underneath.

> **ROOT/PyROOT is an external runtime dependency.** Activate your ROOT, ATLAS, CMS, conda-ROOT, or other PyROOT environment before importing `pyplotlib`.

## Quick start

```python
import pyplotlib.pyplot as plt

plt.hist(h1)
```

For a normal analysis plot, complexity is added only when needed:

```python
import ROOT
import pyplotlib.pyplot as plt

# Global analysis style: persists across figures.
plt.style("ATLAS", lumi=140, year=2018, energy="13 TeV", extraText="Internal", pubStyle=False)

plt.figure()
plt.hist(h_qcd, color=ROOT.kAzure+1, label="Multijet", stack=True, fill=True)
plt.hist(h_top, color=ROOT.kOrange+1, label="Top", stack=True, fill=True)
plt.hist(h_sig, color=ROOT.kRed, label="Signal", scale=10)
plt.hist(h_data, color=ROOT.kBlack, label="Data", isData=True)

plt.xaxis("Jet p_{T} [GeV]", (200, 1500))
plt.yaxis("Events", (0.1, 1e7))
plt.ratio_axis("Data / MC", (0.5, 1.5))
plt.legend(pos=[0.68, 0.45, 0.93, 0.87], fontsize=0.03, col=1)
plt.caption("Example selection")

# These are the original Plotter.Draw options.
plt.draw(logY=True, rebin=2, unc_fstyle=1003, sortLegend=True)
plt.savefig("jet_pt.png")
```

`plt.draw(...)` deliberately forwards the existing `Plotter.Draw()` options rather than creating a separate function for every rendering switch.

For uncommon advanced settings you can access the current engine:

```python
p = plt.current()
p.debug = True
p.print_info = True
```

The original object-oriented API is still available:

```python
from pyplotlib import Plotter

p = Plotter()
p.setExperiment("ATLAS")
p.figure()
p.hist(h1)
p.Draw()
p.savefig("plot.pdf")
```

## Install from a GitHub repository

Assume your repository is:

```text
https://github.com/YOUR-USERNAME/pyplotlib.git
```

### 1. Activate an environment containing PyROOT

For example, use the ROOT/ATLAS/CMS environment you normally use and first verify:

```bash
python -c "import ROOT; print(ROOT.gROOT.GetVersion())"
```

### 2. Install directly from GitHub

FILL ME

