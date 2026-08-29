#user interface using Plotter object
#arnab.laha@cern.ch

from .plotter import Plotter


_plot = None

_style = {
    "experiment": "CMS",
    "lumi": 0,
    "year": 0,
    "energy": "13 TeV",
    "extraText": "Internal",
    "pubStyle": False,
}


def _apply_style(plot):
    plot.setExperiment(_style["experiment"])
    plot.setLumi(_style["lumi"])
    plot.setYear(_style["year"])
    plot.setEnergy(_style["energy"])
    plot.setExtraText(_style["extraText"])
    plot.setPubStyle(_style["pubStyle"])


def _get_plot():
    global _plot

    if _plot is None:
        figure()

    return _plot


def style(experiment="CMS", lumi=0, year=0, energy="13 TeV", extraText="Internal", pubStyle=False):
    global _style

    _style = {
        "experiment": experiment,
        "lumi": lumi,
        "year": year,
        "energy": energy,
        "extraText": extraText,
        "pubStyle": pubStyle,
    }

    if _plot is not None:
        _apply_style(_plot)


def figure(canvName="can", w=800, h=600):
    global _plot

    if _plot is not None: _plot.close()

    _plot = Plotter()
    _apply_style(_plot)
    _plot.figure(canvName, w, h)
    return _plot

def hist(histo, **kwargs):
    _get_plot().hist(histo, **kwargs)


def xaxis(label="X-axis", xrange=()):
    _get_plot().set_xaxis(label, xrange)


def yaxis(label="Events", yrange=(0.01, 1E8)):
    _get_plot().set_yaxis(label, yrange)


def ratio_axis(label="obs/exp", yrange=(0, 2)):
    _get_plot().set_yaxis_ratio(label, yrange)


def legend(pos=[0.70, 0.01, 0.92, 0.86], fontsize=0.03, col=1):
    _get_plot().legend(pos, fontsize, col)


def caption(text):
    _get_plot().set_extraTextCaption(text)


def draw(**kwargs):
    return _get_plot().Draw(**kwargs)

def savefig(filename):
    _get_plot().savefig(filename)

def printTable(data=None):
    return _get_plot().printTable(data=data)

def current():
    return _get_plot()

def close():
    global _plot
    if _plot is not None: _plot.close()
    _plot = None
