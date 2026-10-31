# pyhepplotlib

A small PyROOT histogram plotting library with a minimal `matplotlib`-style interface and the original `Plotter` API underneath.

*External dependency*
- ROOT/pyROOT
- tabulate package for pretty printing


## Quick start

*Minimal histogram plotting*

```python
import pyplotlib.pyplot as plt
plt.style("CMS", lumi=138, year=2018, energy="13 TeV", extraText="Internal")
plt.figure()
plt.hist(h_signal, label="Signal", color=ROOT.kBlue)
plt.draw()
plt.savefig("minimal_histogram_test.png")
```
![Test 01: minimal](tests/outputs/01_minimal.png)

*For a normal analysis plot, complexity is added only when needed:*

```python
import ROOT
import pyplotlib.pyplot as plt

# Global analysis style: persists across figures.
plt.style("ATLAS", lumi=51.8, year=2023, energy="13.6 TeV", extraText="", pubStyle=True)

plt.figure()
plt.hist(qcd, label="Multijet", color=ROOT.kAzure + 1, stack=True, fill=True)
plt.hist(top, label="Top", color=ROOT.kOrange + 1, stack=True, fill=True)
plt.hist(signal, label="Signal x 10", color=ROOT.kRed, scale=10)
plt.hist(data, label="Data", color=ROOT.kBlack, isData=True)
plt.xaxis("Observable [GeV]", (0, 400))
plt.yaxis("Events", (0.1, 2e4))
plt.ratio_axis("Data / Pred.", (0.5, 1.5))
plt.legend(pos=[0.64, 0.50, 0.94, 0.84])
plt.caption("e#mu SR")
plt.draw(logY=True, showStat=False)
save("jet_pt.png")
```
For uncommon advanced settings you can access the current engine:

```python
p = plt.current()
p.debug = True
p.print_info = True
```

![Test 02: ATLAS pub](tests/outputs/05_publication.png)


Another way of plotting is using the original object-oriented API instead of the matplotlib-style wrapper:

```python
from pyplotlib import Plotter

p = Plotter()
p.setExperiment("ATLAS")
p.figure()
p.hist(h1)
p.Draw()
p.savefig("plot.pdf")
```

*For more test plots checkout the `tests/README.md` gallery*
## Plot Gallery

The following examples demonstrate the plotting functionality, from minimal histograms to full analysis-style figures.

<table>
<tr>
<td width="50%" align="center">
  <a href="tests/outputs/01_minimal.png">
    <img src="tests/outputs/01_minimal.png" width="100%" alt="Minimal ROOT Histogram">
  </a>
  <br>
  <b>01 — Minimal ROOT Histogram</b>
  <br>
  Basic histogram plotting using <code>plt.hist(h)</code>.
</td>
<td width="50%" align="center">
  <a href="tests/outputs/02_overlay.png">
    <img src="tests/outputs/02_overlay.png" width="100%" alt="Histogram Overlay">
  </a>
  <br>
  <b>02 — Histogram Overlay</b>
  <br>
  Multiple histograms, line styles, axis ranges, and logarithmic scales.
</td>
</tr>

<tr>
<td width="50%" align="center">
  <a href="tests/outputs/03_stack_data_ratio.png">
    <img src="tests/outputs/03_stack_data_ratio.png" width="100%" alt="Stack and Ratio">
  </a>
  <br>
  <b>03 — Stack + Data/MC Ratio</b>
  <br>
  Stacked backgrounds, scaled signals, observed data, and MC uncertainty.
</td>
<td width="50%" align="center">
  <a href="tests/outputs/04_atlas_analysis.png">
    <img src="tests/outputs/04_atlas_analysis.png" width="100%" alt="ATLAS Analysis">
  </a>
  <br>
  <b>04 — ATLAS Analysis Style</b>
  <br>
  ATLAS labels, luminosity, custom legends, captions, and ratio ranges.
</td>
</tr>

<tr>
<td width="50%" align="center">
  <a href="tests/outputs/05_publication.png">
    <img src="tests/outputs/05_publication.png" width="100%" alt="Publication Style">
  </a>
  <br>
  <b>05 — Publication Style</b>
  <br>
  Clean publication-style figures with statistical yields hidden.
</td>
<td width="50%" align="center">
  <a href="tests/outputs/03_pietest_atlas.pdf">
    <img src="tests/outputs/03_pietest_atlas.png" width="100%" alt="ATLAS Pie Chart">
  </a>
  <br>
  <b>07 — ATLAS Pie Chart</b>
  <br>
  Background composition visualized as a pie chart.
</td>
</tr>
</table>

---


***ToDo***

This is rough to-do list for me in my free time:
- [ ] 2D histogram     
- [ ] TEfficiency plots     
- [ ] TGraph for limit plots (Yeah, I am sad, I want to make p-value discovery plots. Should I include it first? xD)
- [ ] yaml config based plotting wrapper for extensive analysis level collaboration and plotting     
- [x] github CI/CD pipeline
- [x] Pie chart


## Installation

Open a terminal and go to your work dir. Then follow these steps for a system wide setup:

```bash
git clone https://github.com/alaha999/pyhepplotlib.git
source setup.sh
source run-test.sh
```
If everything went fine, you should see example plots in `tests/outputs/`

Now you can start doing your own plotting by calling (from anywhere in your system),

```bash
import pyplotlib.pyplot as plt
plt.style("CMS", lumi=138, year=2018, energy="13 TeV", extraText="Internal")
plt.figure()
plt.hist(h_signal, label="Signal", color=ROOT.kBlue)  #preparing a histogram h_signal is up to you!
plt.draw()
plt.savefig("minimal_histogram_test.png")
```

## Repo structure

Repo structure for visualisation

```text
.
├── LICENSE
├── pyproject.toml
├── README.md
├── run-test.sh
├── setup.sh
├── src
│   └── pyplotlib
│       ├── __init__.py
│       ├── plotter.py
│       ├── pyplot.py
│       ├── styles.py
│       └── utils.py
└── tests
    ├── dummy_data.py
    ├── gallery.ipynb
    ├── outputs
    │   ├── 01_minimal.png
    │   ├── 02_overlay.png
    │   ├── 03_stack_data_ratio.png
    │   ├── 04_atlas_analysis.png
    │   ├── 05_publication.png
    │   └── 06_rebin_overflow.png
    ├── README.md
    ├── test_core.py
    └── test_gallery.py

```

## Notes

This library is an evolution of a library that I wrote and used in my PhD for plotting purposes. Obviously, the pyplot wrapper was not written at that time. I used to work with Plotter API. Here is the latest github repo of that (with many improvements that my PhD's version xD): `https://github.com/alaha999/plotter`.

Now, I have written the wrapper with the help of AI along with a few optimisations. It feels more like `matplotlib style` now and have an easy `user interface`. Hope it benefits if you are interested.

Feel free to contact me for anything! <br>

*Email:* `arnab.laha@cern.ch`

