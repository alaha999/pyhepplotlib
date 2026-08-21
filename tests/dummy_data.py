import ROOT
import math


def _make_hist(name, scale, slope, bump=0.0):
    h = ROOT.TH1D(name, "", 40, 0, 400)
    h.SetDirectory(0)
    h.Sumw2()
    for i in range(1, h.GetNbinsX() + 1):
        x = h.GetBinCenter(i)
        value = scale * math.exp(-x / slope)
        if bump:
            value += bump * math.exp(-0.5 * ((x - 210) / 28) ** 2)
        h.SetBinContent(i, value)
        h.SetBinError(i, math.sqrt(max(value, 0)))
    return h


def make_histograms():
    qcd = _make_hist("h_qcd", 850, 105)
    top = _make_hist("h_top", 230, 155)
    signal = _make_hist("h_signal", 4, 180, bump=38)

    data = qcd.Clone("h_data")
    data.SetDirectory(0)
    data.Add(top)
    # Deterministic data-like deviations so the gallery is reproducible.
    for i in range(1, data.GetNbinsX() + 1):
        value = max(0, round(data.GetBinContent(i) * (1 + 0.035 * math.sin(i * 0.8))))
        data.SetBinContent(i, value)
        data.SetBinError(i, math.sqrt(value))

    return qcd, top, signal, data


def make_overflow_histogram():
    h = ROOT.TH1D("h_overflow", "", 20, 0, 200)
    h.SetDirectory(0)
    h.Sumw2()
    for i in range(1, h.GetNbinsX() + 1):
        value = 120 * math.exp(-h.GetBinCenter(i) / 90)
        h.SetBinContent(i, value)
        h.SetBinError(i, math.sqrt(value))
    h.SetBinContent(0, 15)
    h.SetBinError(0, math.sqrt(15))
    h.SetBinContent(h.GetNbinsX() + 1, 25)
    h.SetBinError(h.GetNbinsX() + 1, 5)
    return h
