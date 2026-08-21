import ROOT


def pad_style(pad, rpad, pubstyle=False):
    left, right = 0.12, 0.30
    if pubstyle:
        left, right = 0.12, 0.05

    pad.SetLeftMargin(left)
    pad.SetRightMargin(right)
    pad.SetTopMargin(0.09)
    pad.SetBottomMargin(0.01)
    pad.SetTickx(1)
    pad.SetTicky(1)

    rpad.SetLeftMargin(left)
    rpad.SetRightMargin(right)
    rpad.SetTopMargin(0.04)
    rpad.SetBottomMargin(0.35)
    rpad.SetTickx(1)
    rpad.SetTicky(1)


def stack_style(h, ylabel="Events"):
    h.GetYaxis().SetTitle(ylabel)
    h.GetYaxis().CenterTitle()
    h.GetXaxis().SetTitleFont(43)
    h.GetXaxis().SetTitleSize(20)
    h.GetXaxis().SetTitleOffset(0.8)
    h.GetXaxis().SetLabelFont(43)
    h.GetXaxis().SetLabelSize(0)
    h.GetXaxis().SetNdivisions(513)
    h.GetXaxis().SetTickSize(0.05)
    h.GetYaxis().SetTitleFont(43)
    h.GetYaxis().SetTitleSize(18)
    h.GetYaxis().SetTitleOffset(1.7)
    h.GetYaxis().SetLabelFont(43)
    h.GetYaxis().SetLabelSize(15)
    h.GetYaxis().SetNdivisions(510)
    h.GetYaxis().SetTickSize(0.02)
    h.SetTitle("")


def ratio_style(h, xlabel="X", ylabel="obs/exp"):
    h.GetXaxis().SetTitle(xlabel)
    h.GetYaxis().SetTitle(ylabel)
    h.GetXaxis().CenterTitle()
    h.GetYaxis().CenterTitle()
    h.GetXaxis().SetTitleFont(43)
    h.GetXaxis().SetTitleSize(20)
    h.GetXaxis().SetTitleOffset(1.2)
    h.GetXaxis().SetLabelFont(43)
    h.GetXaxis().SetLabelSize(14)
    h.GetXaxis().SetNdivisions(513)
    h.GetYaxis().SetTitleFont(43)
    h.GetYaxis().SetTitleSize(18)
    h.GetYaxis().SetTitleOffset(1.6)
    h.GetYaxis().SetLabelFont(43)
    h.GetYaxis().SetLabelSize(14)
    h.GetYaxis().SetNdivisions(503)
    h.SetTitle("")


def legend_style(legend):
    legend.SetTextFont(41)
    legend.SetFillStyle(0)
    legend.SetBorderSize(0)
    legend.SetTextSize(0.04)


def cms_labels():
    experiment = ROOT.TLatex()
    experiment.SetNDC(True)
    experiment.SetTextSize(0.07)
    experiment.SetTextFont(61)

    extra = ROOT.TLatex()
    extra.SetNDC(True)
    extra.SetTextFont(52)
    extra.SetTextSize(0.044)

    lumi = ROOT.TLatex()
    lumi.SetNDC(True)
    lumi.SetTextAlign(31)
    lumi.SetTextFont(42)
    lumi.SetTextSize(0.044)
    return experiment, extra, lumi


def atlas_labels():
    experiment = ROOT.TLatex()
    experiment.SetNDC(True)
    experiment.SetTextSize(0.055)
    experiment.SetTextFont(72)

    extra = ROOT.TLatex()
    extra.SetNDC(True)
    extra.SetTextFont(42)
    extra.SetTextSize(0.053)

    lumi = ROOT.TLatex()
    lumi.SetNDC(True)
    lumi.SetTextFont(42)
    lumi.SetTextSize(0.044)
    return experiment, extra, lumi
