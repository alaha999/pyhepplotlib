import ROOT
from array import array

from .styles import atlas_labels, cms_labels, legend_style, pad_style, ratio_style, stack_style
from .utils import (
    clone_histogram,
    mc_uncertainty_band_ratio,
    merge_underflow_overflow_in_range,
    root_value,
    truncate_histogram,
    unique_name,
)


class Plotter:
    def __init__(self):
        # Global-style settings: normally unchanged while making many plots.
        self.lumi = 0
        self.year = 0
        self.experiment = "CMS"
        self.extraText = "Internal"
        self.energy = "13 TeV"
        self.pubStyle = False

        self.debug = False
        self.print_info = False

        # Per-plot settings/state.
        self.canvas = None
        self.mainPad = None
        self.ratioPad = None
        self.histogram = []
        self.xlabel = "X"
        self.ylabel = "Events"
        self.xrange = None
        self.yrange = (0.01, 1E8)
        self.ylabel_ratio = "obs/exp"
        self.yrange_ratio = (0, 2)
        self.extraTextCaption = []

        self._legend_pos = [0.70, 0.01, 0.92, 0.86]
        self._legend_fontsize = 0.03
        self._legend_col = 1

        # Keep ROOT objects used by the current canvas alive until the next draw.
        # PyROOT canvases keep C++ pointers; Python must retain the owners.
        self._draw_objects = []

        self._reset_draw_state()

    def _reset_draw_state(self):
        self._draw_objects = []
        self.h_stack = None
        self.h_totbkg = None
        self.h_data = None
        self.h_err = None
        self.h_ratio = None
        self.yerr_ratio = None
        self.mainleg = None
        self.ratioleg = None
        # Statistics corresponding to the most recent successful Draw().
        self._last_draw_summary = None

    # Original configuration API kept for compatibility.
    def setPubStyle(self, pubStyle): self.pubStyle = pubStyle
    def setLumi(self, lumi): self.lumi = lumi
    def setYear(self, year): self.year = year
    def setExperiment(self, experiment): self.experiment = experiment
    def setExtraText(self, extraText): self.extraText = extraText
    def setEnergy(self, energy): self.energy = energy

    def set_xaxis(self, xlabel="X-axis", xrange=()):
        self.xlabel = xlabel
        if xrange:
            self.xrange = xrange

    def set_yaxis(self, ylabel="Y-axis", yrange=(0.01, 1E8)):
        self.ylabel = ylabel
        self.yrange = yrange

    def set_yaxis_ratio(self, ylabel="obs/exp", yrange=(0, 2)):
        self.ylabel_ratio = ylabel
        self.yrange_ratio = yrange

    def set_extraTextCaption(self, textCaption):
        self.extraTextCaption.append(textCaption)

    def show(self):
        print("plot settings")
        print("Experiment: ", self.experiment)
        print("ExtraText : ", self.extraText)
        print("Energy    : ", self.energy)
        print("Year      : ", self.year)
        print("Luminosity: ", self.lumi)
        print("PubStyle  : ", self.pubStyle)

    def figure(self, canvName="can", w=800, h=600):
        if self.pubStyle:
            w, h = 600, 600

        self.canvas = ROOT.TCanvas(unique_name(canvName), "canvas", w, h)
        ROOT.gStyle.SetOptStat(0)
        ratio_size = 0.30
        self.mainPad = ROOT.TPad(unique_name("mpad"), "mainpad", 0, ratio_size, 1, 1)
        ROOT.SetOwnership(self.mainPad, False)
        self.ratioPad = ROOT.TPad(unique_name("rpad"), "ratiopad", 0, 0, 1, ratio_size)
        ROOT.SetOwnership(self.ratioPad, False)
        pad_style(self.mainPad, self.ratioPad, self.pubStyle)

        self.histogram = []
        self.xlabel = "X"
        self.ylabel = "Events"
        self.xrange = None
        self.yrange = (0.01, 1E8)
        self.ylabel_ratio = "obs/exp"
        self.yrange_ratio = (0, 2)
        self.extraTextCaption = []
        self._legend_pos = [0.70, 0.01, 0.92, 0.86]
        self._legend_fontsize = 0.03
        self._legend_col = 1
        self._reset_draw_state()
        return self

    def legend(self, pos=None, fontsize=0.03, col=1):
        if pos is not None:
            self._legend_pos = list(pos)
        self._legend_fontsize = fontsize
        self._legend_col = col
        return self

    def _make_legend(self):
        x1, y1, x2, y2 = self._legend_pos
        self.mainleg = ROOT.TLegend(x1, y1, x2, y2)
        legend_style(self.mainleg)
        self.mainleg.SetTextSize(self._legend_fontsize)
        self.mainleg.SetTextFont(42)
        self.mainleg.SetNColumns(self._legend_col)
        self.mainleg.SetColumnSeparation(0.1)

        self.ratioleg = ROOT.TLegend(x1, y2 + 0.01, x2, y2 + 0.03)
        legend_style(self.ratioleg)
        self.ratioleg.SetTextSize(self._legend_fontsize)

    def hist(
        self,
        histo,
        color="ROOT.kBlue",
        label="name",
        stack=False,
        fill=False,
        lwidth=2,
        ls=0.7,
        lstyle="ROOT.kSolid",
        legendStyle="lf",
        scale=1.0,
        density=False,
        isData=False,
    ):
        # Store a detached private clone. The caller's TH1 is never modified.
        h = clone_histogram(histo)
        h.SetLineWidth(0 if stack else lwidth)
        h.SetLineColor(root_value(color))
        h.SetLineStyle(root_value(lstyle))
        if fill:
            h.SetFillColor(root_value(color))
        if isData:
            h.SetMarkerSize(ls)
            h.SetMarkerStyle(8)

        if density:
            integral = h.Integral()
            if integral:
                h.Scale(1.0 / integral)
        else:
            h.Scale(scale)

        if self.xrange is None:
            axis = h.GetXaxis()
            self.xrange = (axis.GetBinLowEdge(1), axis.GetBinUpEdge(h.GetNbinsX()))

        if self.debug:
            print(
                f"xmin={h.GetXaxis().GetBinLowEdge(1)}/nbins={h.GetNbinsX()}"
                f"/xmax={h.GetXaxis().GetBinUpEdge(h.GetNbinsX())}"
            )

        self.histogram.append([label, stack, isData, h, legendStyle])
        return h

    def _working_histograms(self, truncate_xrange, rebin):
        # Draw-time transformations operate on temporary clones. This makes
        # repeated Draw() calls safe and prevents rebin/overflow accumulation.
        work = []
        for label, stack, is_data, source, legend_style_name in self.histogram:
            h = clone_histogram(source)
            merge_underflow_overflow_in_range(h, self.xrange[0], self.xrange[1])

            if truncate_xrange:
                axis = h.GetXaxis()
                xmin = max(self.xrange[0], axis.GetBinLowEdge(1))
                xmax = min(self.xrange[1], axis.GetBinUpEdge(h.GetNbinsX()))
                h = truncate_histogram(h, xmin, xmax)

            if isinstance(rebin, int):
                if rebin > 1:
                    h.Rebin(rebin)
            else:
                bins = array("d", rebin)
                h = h.Rebin(len(bins) - 1, unique_name(h.GetName() + "_rebin"), bins)
                h.SetDirectory(0)

            work.append([label, stack, is_data, h, legend_style_name])
        return work

    def _create_placeholder(self, hist):
        h = clone_histogram(hist, unique_name("h_placeholder"))
        for i in range(1, h.GetNbinsX() + 1):
            h.SetBinContent(i, 1)
            h.SetBinError(i, 0)
        return h

    def _yield_and_error(self, hist):
        if hist is None: return None
        yld = sum(hist.GetBinContent(i) for i in range(1, hist.GetNbinsX() + 1))
        err = sum(hist.GetBinError(i)**2 for i in range(1, hist.GetNbinsX() + 1))**0.5
        return yld, err
    
    def printTable(self, data=None):
        from tabulate import tabulate

        if self._last_draw_summary is None: raise RuntimeError("Call Draw() before printTable().")

        s, rows = self._last_draw_summary, []

        for label, yld, err in s["backgrounds"] + s["signals"]:
            rows.append([label, f"{yld:.2f} ± {err:.2f}"])

        bkg_yld = None
        if s["total_background"] is not None:
            bkg_yld, err = s["total_background"]
            rows.append(["Total bkg", f"{bkg_yld:.2f} ± {err:.2f}"])

        show_data = data is not False
        data_yld = None

        if data is True and s["data"] is None: print("Warning: data=True requested, but no data histogram was drawn.")

        if show_data and s["data"] is not None:
            data_yld, err = s["data"]
            rows.append(["Data", f"{data_yld:.2f} ± {err:.2f}"])

        if show_data and data_yld is not None and bkg_yld is not None:
            rows.append(["Obs/Exp", f"{data_yld / bkg_yld:.3f}" if bkg_yld else "—"])

        if not rows: return print("No histograms are available for the yield table.")
        print(tabulate(rows, headers=["Process", "Yield"], tablefmt="github"))

    def Draw(
        self,
        logY=True,
        logX=False,
        ratio_logY=False,
        truncate_xrange=False,
        rebin=1,
        unc_fstyle=1003,
        unc_fcolor=ROOT.kGray,
        extraTextOffset=0.08,
        sigLegStyle="lf",
        sortLegend=True,
        showStat=False,
    ):
        if not self.histogram:
            raise RuntimeError("No histograms added. Call hist() first.")
        if self.canvas is None:
            self.figure()


        self.mainPad.Clear()
        self.ratioPad.Clear()
        self._reset_draw_state()
        
        self.mainPad.SetLogy(bool(logY))
        self.mainPad.SetLogx(bool(logX))
        self.ratioPad.SetLogx(bool(logX))
        self.ratioPad.SetLogy(bool(ratio_logY))

        work = self._working_histograms(truncate_xrange, rebin)
        self._draw_objects.extend(item[3] for item in work)
        backgrounds = [item for item in work if item[1]]
        data = [item for item in work if item[2] and not item[1]]
        signals = [item for item in work if not item[1] and not item[2]]

        backgrounds.sort(key=lambda item: item[3].Integral())
        if backgrounds:
            self.h_stack = ROOT.THStack(unique_name("stack"), "")
            for item in backgrounds:
                self.h_stack.Add(item[3])

            self.h_totbkg = clone_histogram(backgrounds[0][3], unique_name("total_background"))
            self.h_totbkg.Reset("ICES")
            for item in backgrounds:
                self.h_totbkg.Add(item[3])

            self.h_err = clone_histogram(self.h_totbkg, unique_name("MC_uncertainty"))
            self.h_err.SetFillColorAlpha(root_value(unc_fcolor) + 1, 0.6)
            self.h_err.SetFillStyle(unc_fstyle)
            self.h_err.SetMarkerStyle(0)
            self.h_err.SetLineWidth(0)

        if data:
            self.h_data = clone_histogram(data[0][3], unique_name("h_data"))
            for item in data[1:]:
                self.h_data.Add(item[3])

        #summary text to build the table        
        self._last_draw_summary = {
            "backgrounds": [(label, *self._yield_and_error(hist)) for label, _, _, hist, _ in backgrounds],
            "signals": [(label, *self._yield_and_error(hist)) for label, _, _, hist, _ in signals],
            "total_background": self._yield_and_error(self.h_totbkg),
            "data": self._yield_and_error(self.h_data),
        }
                
        self._make_legend()
        stack_legend = sorted(backgrounds, key=lambda item: item[3].Integral(), reverse=True) if sortLegend else backgrounds
        signal_legend = sorted(signals, key=lambda item: item[3].Integral(), reverse=True) if sortLegend else signals
        data_label = data[0][0] if data else "Data"

        if self.pubStyle and not showStat:
            if self.h_data is not None:
                self.mainleg.AddEntry(self.h_data, data_label, "ep")
            for label, _, _, hist, _ in stack_legend:
                self.mainleg.AddEntry(hist, label, "f")
            for label, _, _, hist, legstyle in signal_legend:
                self.mainleg.AddEntry(hist, label, sigLegStyle if legstyle == "lf" else legstyle)
            if self.h_err is not None:
                self.mainleg.AddEntry(self.h_err, "Uncertainty", "f")
        else:
            if self.h_data is not None and self.h_totbkg is not None and self.h_totbkg.Integral() and self.h_data.Integral():
                self.ratioleg.SetHeader(
                    f"obs/exp={self.h_data.Integral() / self.h_totbkg.Integral():.2f}, "
                    f"Exp={self.h_totbkg.Integral():.3e}"
                )
            if self.h_data is not None:
                self.mainleg.AddEntry(self.h_data, f"{data_label} [{self.h_data.Integral():.3e}]", "ep")
            for label, _, _, hist, _ in stack_legend:
                self.mainleg.AddEntry(hist, f"{label} [{hist.Integral():.3e}]", "f")
            for label, _, _, hist, legstyle in signal_legend:
                self.mainleg.AddEntry(hist, f"{label} [{hist.Integral():.3e}]", sigLegStyle if legstyle == "lf" else legstyle)
            if self.h_err is not None:
                self.mainleg.AddEntry(self.h_err, "Uncertainty", "f")

        # Explicitly attach pads to this canvas. This matters when many canvases
        # are produced sequentially and ROOT.gPad still points to an older pad.
        self.canvas.cd()
        self.mainPad.Draw()
        self.ratioPad.Draw()
        self.mainPad.cd()

        if self.h_stack is not None:
            self.h_stack.Draw("HIST")
            # THStack creates its internal axis histogram lazily during painting.
            # Force that paint before asking for GetXaxis()/GetYaxis().
            self.mainPad.Update()
            stack_style(self.h_stack, self.ylabel)
            self.h_stack.SetMinimum(self.yrange[0])
            self.h_stack.SetMaximum(self.yrange[1])
            self.h_stack.GetXaxis().SetRangeUser(*self.xrange)
            self.h_err.Draw("E2 SAME")

        for index, (_, _, _, hist, _) in enumerate(signals):
            stack_style(hist, self.ylabel)
            hist.GetXaxis().SetRangeUser(*self.xrange)
            hist.GetYaxis().SetRangeUser(*self.yrange)
            hist.Draw("HIST" if index == 0 and self.h_stack is None else "HIST SAME")

        if self.h_data is not None:
            self.h_data.SetBinErrorOption(ROOT.TH1.EBinErrorOpt.kPoisson)
            self.h_data.GetXaxis().SetRangeUser(*self.xrange)
            self.h_data.GetYaxis().SetRangeUser(*self.yrange)
            self.h_data.Draw("E1X0 SAME")            
            
        self.mainleg.Draw()
        if not self.pubStyle:
            self.ratioleg.Draw()

        self._draw_experiment_label(extraTextOffset)
        ROOT.gPad.RedrawAxis()
        self.mainPad.SetTickx(1)
        self.mainPad.SetTicky(1)
        self.mainPad.Update()

        if self.h_totbkg is None:
            self.h_totbkg = self._create_placeholder(work[0][3])

        self.ratioPad.cd()
        if self.h_data is not None:
            self.h_ratio = clone_histogram(self.h_data, unique_name("h_ratio"))
            self.h_ratio.Divide(self.h_totbkg)
        else:
            self.h_ratio = clone_histogram(self.h_totbkg, unique_name("h_ratio"))
            self.h_ratio.SetMarkerSize(0)
            self.h_ratio.SetFillColor(0)
            self.h_ratio.SetLineColor(ROOT.kGray + 1)
            self.h_ratio.SetLineStyle(ROOT.kDotted)
            for i in range(1, self.h_ratio.GetNbinsX() + 1):
                self.h_ratio.SetBinContent(i, 1)
                self.h_ratio.SetBinError(i, 0)

        ratio_style(self.h_ratio, self.xlabel, self.ylabel_ratio)
        self.h_ratio.GetXaxis().SetRangeUser(*self.xrange)
        self.h_ratio.GetYaxis().SetRangeUser(*self.yrange_ratio)
        self.h_ratio.GetXaxis().SetTickSize(0.08)

        if self.h_data is not None:
            for i in range(1, self.h_ratio.GetNbinsX() + 1):
                if not self.h_ratio.GetBinContent(i):
                    self.h_ratio.SetBinError(i, 0.000001)
                    self.h_ratio.SetBinContent(i, -10)

        self.yerr_ratio = mc_uncertainty_band_ratio(self.h_totbkg)
        ratio_style(self.yerr_ratio, self.xlabel, self.ylabel_ratio)
        self.yerr_ratio.SetLineWidth(100)
        self.yerr_ratio.SetMarkerSize(0)
        self.yerr_ratio.SetFillStyle(unc_fstyle)
        self.yerr_ratio.SetFillColor(root_value(unc_fcolor))
        self.yerr_ratio.GetYaxis().SetRangeUser(*self.yrange_ratio)
        self.yerr_ratio.GetXaxis().SetLimits(*self.xrange)

        self.h_ratio.DrawCopy("E1X0")
        self.yerr_ratio.Draw("E2 SAME")
        self.h_ratio.DrawCopy("E1X0 SAME")
        self.ratioPad.SetTickx(1)
        ROOT.gPad.RedrawAxis()
        self.ratioPad.Update()
        self.canvas.Update()
        self.canvas.Draw()
        return self.canvas

    def _draw_experiment_label(self, extraTextOffset):
        if self.experiment == "CMS":
            exp, extra, lumi = cms_labels()
            y = 0.925
            left = round(self.mainPad.GetLeftMargin(), 2)
            right = round(self.mainPad.GetRightMargin(), 2)
        elif self.experiment == "ATLAS":
            exp, extra, lumi = atlas_labels()
            y = 0.825
            left = round(self.mainPad.GetLeftMargin(), 2) + 0.03
            right = round(self.mainPad.GetRightMargin(), 2)
        else:
            return

        if self.pubStyle:
            extraTextOffset += 0.02
        exp.DrawLatex(left, y, self.experiment)
        extra.DrawLatex(left + extraTextOffset, y, str(self.extraText))
        self._draw_objects.extend([exp, extra, lumi])

        if self.experiment == "CMS":
            lumi.SetTextAlign(31)
            lumi.DrawLatex(1 - right, y, f"{self.lumi} fb^{{#minus1}} ({self.energy})")
        else:
            lumi.DrawLatex(left, y - 0.05, f"#sqrt{{s}} = {self.energy}, {self.lumi} fb^{{#minus1}}")

        for i, caption in enumerate(self.extraTextCaption):
            text = ROOT.TLatex()
            text.SetNDC(True)
            text.SetTextSize(0.042 if self.experiment == "ATLAS" else 0.044)
            text.SetTextFont(42)
            text.DrawLatex(left, y - (i + 2) * 0.05, caption)
            self._draw_objects.append(text)

        return self.canvas
            
    def savefig(self, filename):
        if self.canvas is None:
            raise RuntimeError("No canvas exists. Call figure() and Draw() first.")
        self.canvas.Print(str(filename))


    def close(self):
        if self.canvas: self.canvas.Close()
        
        self.mainPad = None
        self.ratioPad = None
        self.canvas = None
        self.histogram = []
        self._reset_draw_state()
