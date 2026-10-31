import ROOT
import math
from array import array

from .styles import atlas_labels, cms_labels, legend_style, pad_style, ratio_style, stack_style, hist2d_style, scale_axis_fonts
from .utils import (
    clone_histogram,
    mc_uncertainty_band_ratio,
    merge_underflow_overflow_in_range,
    root_value,
    truncate_histogram,
    unique_name,
    rebin_histogram_2d,
    full_integral_2d,
    axis_edges_2d,
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
        self.histogram2d = None
        self.xlabel = "X"
        self.ylabel = "Events"
        self.zlabel = "Events"        
        self.xrange = None
        self.yrange = (0.01, 1E8)
        self.zrange = None                
        self.ylabel_ratio = "obs/exp"
        self.yrange_ratio = (0, 2)
        self.extraTextCaption = []

        self._legend_pos = [0.70, 0.01, 0.99, 0.86]
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
        
    def set_zaxis(self, zlabel="Events", zrange=None):
        self.zlabel = zlabel
        self.zrange = zrange
        
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

    def figure(self, canvName="can", w=800, h=700):
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
        self._legend_pos = [0.70, 0.01, 0.99, 0.86]
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

    def _font_scale(self):
        # Applied on Draw; stable for normal canvas sizes.
        if self.canvas is None:
            return 1.0
        return max(1.0, min(1.5, min(self.canvas.GetWw() / 800., self.canvas.GetWh() / 600.)))

    def _make_legend(self, n_entries=0, header=False):
        pos = self._legend_pos
        if len(pos) == 4:  # Legacy: [x1, y1, x2, top]
            x1, _, x2, top = pos
        elif len(pos) == 3:  # [x1, top, x2]
            x1, top, x2 = pos
        else:
            raise ValueError("legend pos must have 3 or 4 coordinates")

        # The full box must be set in the TLegend constructor. Resizing it
        # with SetY1NDC() after creation can leave the painted entries packed
        # into the original 0.1-high box on some ROOT versions.
        rows = math.ceil(n_entries / max(1, self._legend_col)) + int(header)
        row_height = 0.055
        available = max(0.02, top - 0.03)
        height = min(available, rows * row_height + 0.012)
        self._legend_top = top
        self.mainleg = ROOT.TLegend(x1, top - height, x2, top)
        legend_style(self.mainleg)
        self.mainleg.SetTextFont(42)
        self.mainleg.SetTextSize(self._legend_fontsize)
        self.mainleg.SetNColumns(self._legend_col)
        self.mainleg.SetColumnSeparation(0.05)
        self.mainleg.SetMargin(0.16)
        self.ratioleg = None

    def _draw_frame_edges(self, pad):
        """Redraw thick frame edges above stack bars and error bands."""
        pad.cd()
        left, right = pad.GetLeftMargin(), 1.0 - pad.GetRightMargin()
        bottom, top = pad.GetBottomMargin(), 1.0 - pad.GetTopMargin()
        for x1, y1, x2, y2 in (
            (left, bottom, left, top), (right, bottom, right, top),
            (left, bottom, right, bottom), (left, top, right, top),
        ):
            edge = ROOT.TLine()
            edge.SetLineWidth(pad.GetFrameLineWidth())
            edge.SetLineColor(ROOT.kBlack)
            edge.SetNDC(True)
            edge.DrawLineNDC(x1, y1, x2, y2)
            self._draw_objects.append(edge)

    @staticmethod
    def _full_yield(hist):
        # Include underflow and overflow; independent of variable binning.
        return sum(hist.GetBinContent(i) for i in range(hist.GetNbinsX() + 2))

    def _source_yields(self):
        # Kept before rebin/truncation; hist() already applied scaling/density.
        return {label: self._full_yield(h) for label, _, _, h, _ in self.histogram}

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

    ##2D histograms
    def hist2d(
        self,
        histo,
        rebinx=1,
        rebiny=1,
        cmap="viridis",
        fold=True,
        label=None,
        scale=1.0,
    ):
        if self.histogram:
            raise RuntimeError("Cannot mix 1D and 2D histograms.")

        if self.histogram2d is not None:
            raise RuntimeError("Only one TH2 per figure is supported.")

        histograms = (
            histo if isinstance(histo, (list, tuple))
            else [histo]
        )

        if not histograms:
            raise ValueError("No TH2 histogram provided.")

        for hist in histograms:
            if not hist.InheritsFrom("TH2"):
                raise TypeError("hist2d() requires ROOT.TH2.")

        h = clone_histogram(histograms[0])

        for other in histograms[1:]:

            if (
                    axis_edges_2d(h.GetXaxis()) != axis_edges_2d(other.GetXaxis())
                    or axis_edges_2d(h.GetYaxis()) != axis_edges_2d(other.GetYaxis())
            ):
                raise ValueError("TH2 binning mismatch.")

            h.Add(other)

        h.Scale(scale)

        self.histogram2d = {
            "source": h,
            "rebinx": rebinx,
            "rebiny": rebiny,
            "cmap": cmap,
            "fold": fold,
            "label": label,
        }

        return h
    
    @staticmethod
    def _fold_flow_bins(h):
        """Fold ROOT under/overflow into the first/last visible bins."""
        n = h.GetNbinsX()
        for flow, target in ((0, 1), (n + 1, n)):
            h.SetBinContent(target, h.GetBinContent(target) + h.GetBinContent(flow))
            h.SetBinError(target, (h.GetBinError(target)**2 + h.GetBinError(flow)**2)**0.5)
            h.SetBinContent(flow, 0.)
            h.SetBinError(flow, 0.)

    def _working_histograms(self, truncate_xrange, rebin):
        # All transformations operate on private clones (safe for repeated draws).
        work = []
        for label, stack, is_data, source, legend_style_name in self.histogram:
            expected = self._full_yield(source)
            h = clone_histogram(source)
            merge_underflow_overflow_in_range(h, self.xrange[0], self.xrange[1])

            if truncate_xrange:
                axis = h.GetXaxis()
                xmin = max(self.xrange[0], axis.GetBinLowEdge(1))
                xmax = min(self.xrange[1], axis.GetBinUpEdge(h.GetNbinsX()))
                h = truncate_histogram(h, xmin, xmax)

            if isinstance(rebin, int):
                if rebin < 1:
                    raise ValueError("rebin must be a positive integer or bin edges")
                if rebin > 1:
                    rebinned = h.Rebin(rebin)
                    if rebinned:
                        h = rebinned
            else:
                bins = array("d", rebin)
                if len(bins) < 2 or any(b >= c for b, c in zip(bins, bins[1:])):
                    raise ValueError("rebin edges must be strictly increasing")
                h = h.Rebin(len(bins) - 1, unique_name(h.GetName() + "_rebin"), bins)
                h.SetDirectory(0)

            # ROOT may move a non-divisible remainder or bins outside explicit
            # rebin edges into flow bins. Put those contents back on the plot.
            self._fold_flow_bins(h)
            actual = self._full_yield(h)
            tolerance = 1e-9 * max(1., sum(abs(source.GetBinContent(i)) for i in range(source.GetNbinsX() + 2)))
            if not math.isfinite(actual) or not math.isfinite(expected) or abs(actual - expected) > tolerance:
                raise RuntimeError(
                    f"Histogram '{label}' yield changed during plotting: "
                    f"{expected:.12g} -> {actual:.12g}"
                )
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

        for label, yld, err, _ in s["backgrounds"] + s["signals"]:
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

        # Source yields are invariant under display ranges and rebinning.
        source_yields = [self._full_yield(item[3]) for item in self.histogram]
        work = self._working_histograms(truncate_xrange, rebin)
        work_index = {id(item): i for i, item in enumerate(work)}
        yield_by_hist = {id(item[3]): y for item, y in zip(work, source_yields)}
        def display_yield(item):
            return yield_by_hist[id(item[3])]
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
        # Keep the table consistent with the legend (including flow bins).
        def source_summary(item):
            source = self.histogram[work_index[id(item)]][3]
            return (display_yield(item), sum(source.GetBinError(i)**2 for i in range(source.GetNbinsX() + 2))**0.5)

        def combine_summary(items):
            if not items:
                return None
            yields_errors = [source_summary(item) for item in items]
            return (sum(v for v, _ in yields_errors), sum(e*e for _, e in yields_errors)**0.5)

        self._last_draw_summary = {
            "backgrounds": [(item[0], *source_summary(item), item[3].GetFillColor()) for item in backgrounds],
            "signals": [(item[0], *source_summary(item), item[3].GetFillColor()) for item in signals],
            "total_background": combine_summary(backgrounds),
            "data": combine_summary(data),
        }
                
        n_entries = (int(self.h_data is not None) + len(backgrounds)
                     + len(signals) + int(self.h_err is not None))
        has_header = (not (self.pubStyle and not showStat)
                      and bool(data and backgrounds)
                      and sum(display_yield(item) for item in backgrounds) != 0)
        self._make_legend(n_entries, header=has_header)
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
            if self.h_data is not None:
                self.mainleg.AddEntry(self.h_data, f"{data_label} [{sum(display_yield(item) for item in data):.3e}]", "ep")
            for item in stack_legend:
                label, _, _, hist, _ = item
                self.mainleg.AddEntry(hist, f"{label} [{display_yield(item):.3e}]", "f")
            for item in signal_legend:
                label, _, _, hist, legstyle = item
                self.mainleg.AddEntry(hist, f"{label} [{display_yield(item):.3e}]", sigLegStyle if legstyle == "lf" else legstyle)
            if self.h_err is not None:
                self.mainleg.AddEntry(self.h_err, "Uncertainty", "f")
            obs = sum(display_yield(item) for item in data)
            exp = sum(display_yield(item) for item in backgrounds)
            if data and backgrounds and exp:
                self.mainleg.SetHeader(f"Obs/Exp={obs / exp:.2f}, Exp={exp:.3e}")

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
            scale_axis_fonts(self.h_stack, self._font_scale())
            self.h_stack.SetMinimum(self.yrange[0])
            self.h_stack.SetMaximum(self.yrange[1])
            self.h_stack.GetXaxis().SetRangeUser(*self.xrange)
            self.h_err.Draw("E2 SAME")

        for index, (_, _, _, hist, _) in enumerate(signals):
            stack_style(hist, self.ylabel)
            scale_axis_fonts(hist, self._font_scale())
            hist.GetXaxis().SetRangeUser(*self.xrange)
            hist.GetYaxis().SetRangeUser(*self.yrange)
            hist.Draw("HIST" if index == 0 and self.h_stack is None else "HIST SAME")

        if self.h_data is not None:
            self.h_data.SetBinErrorOption(ROOT.TH1.EBinErrorOpt.kPoisson)
            self.h_data.GetXaxis().SetRangeUser(*self.xrange)
            self.h_data.GetYaxis().SetRangeUser(*self.yrange)
            if self.h_stack is None and not signals:
                stack_style(self.h_data, self.ylabel)
                scale_axis_fonts(self.h_data, self._font_scale())
                self.h_data.Draw("E1X0")
            else:
                self.h_data.Draw("E1X0 SAME")            
            
        # Do not resize legend text after filling it: width estimates can
        # shrink names and yields until they are effectively invisible.
        self.mainleg.Draw()

        self._draw_experiment_label(extraTextOffset)
        ROOT.gPad.RedrawAxis()
        self._draw_frame_edges(self.mainPad)
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
        scale_axis_fonts(self.h_ratio, self._font_scale(), ratio=True)
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
        self._draw_frame_edges(self.ratioPad)
        self.ratioPad.Update()
        self.canvas.Update()
        self.canvas.Draw()
        return self.canvas

    ##Draw2D
    def Draw2D(
        self,
        logX=False,
        logY=False,
        logZ=False,
        option="COLZ",
        extraTextOffset=0.16,
    ):
        cfg = self.histogram2d
        
        if cfg is None:
            raise RuntimeError("No TH2 histogram registered.")

        pad = self.canvas
        pad.cd()
        pad.Clear()
        
        self._reset_draw_state()
        # Match the existing main-pad styling
        pad.SetLeftMargin(self.ratioPad.GetLeftMargin())
        pad.SetRightMargin(0.18)  # Space for Z color bar
        pad.SetTopMargin(0.11)
        pad.SetBottomMargin(0.14)
        
        pad.SetFrameLineWidth(self.ratioPad.GetFrameLineWidth())
        pad.SetFrameLineColor(ROOT.kBlack)

        pad.SetTickx(1)
        pad.SetTicky(1)
        
        pad.SetLogx(logX)
        pad.SetLogy(logY)
        pad.SetLogz(logZ)
        
        palettes = {
            "viridis": ROOT.kViridis,
            "bird": ROOT.kBird,
            "rainbow": ROOT.kRainBow,
            "cool": ROOT.kCool,
        }

        palette = palettes.get(cfg["cmap"].lower())

        if palette is None:
            raise ValueError(f"Unknown palette: {cfg['cmap']}")

        ROOT.gStyle.SetPalette(palette)

        # Rebin and fold on a private histogram.
        yrange = (
            None if self.yrange == (0.01, 1E8)
            else self.yrange
        )
        
        h = rebin_histogram_2d(
            cfg["source"],
            rebinx=cfg["rebinx"],
            rebiny=cfg["rebiny"],
            xrange=self.xrange,
            yrange=yrange,
            fold=cfg["fold"],
        )

        self._draw_objects.append(h)
        
        hist2d_style(
            h,
            self.xlabel,
            self.ylabel,
            self.zlabel,
        )

        if self.xrange is not None:
            h.GetXaxis().SetRangeUser(*self.xrange)

        if yrange is not None:
            h.GetYaxis().SetRangeUser(*yrange)

        if self.zrange is not None:
            h.SetMinimum(self.zrange[0])
            h.SetMaximum(self.zrange[1])

        h.Draw(option)
        
        pad.Update()
        
        if cfg["label"]:
            x1, _, x2, ytop = self._legend_pos
            legend = ROOT.TLegend(x1, ytop - 0.055, x2, ytop)
            legend_style(legend)
            legend.SetTextSize(self._legend_fontsize)
            legend.SetTextFont(42)
            # No box, background, or symbols
            legend.SetBorderSize(0)
            legend.SetFillStyle(0)
            # Text-only entry: no histogram object
            legend.AddEntry(0, cfg["label"], "")

            legend.Draw()
            self._draw_objects.append(legend)
        
        # Reuse the existing experiment/caption method.
        # Pass the canvas explicitly without changing its implementation.
        self._draw_experiment_label(
            extraTextOffset,
            pad=pad,
        )

        pad.RedrawAxis()
        pad.Modified()
        pad.Update()

        return self.canvas
    
    def _draw_experiment_label(self, extraTextOffset=0.18,pad=None):
        pad = pad or self.mainPad
        
        if self.experiment == "CMS":
            exp, extra, lumi = cms_labels()
            y = 0.925
            left = round(pad.GetLeftMargin(), 2)
            right = round(pad.GetRightMargin(), 2)
        elif self.experiment == "ATLAS":
            exp, extra, lumi = atlas_labels()
            y = 0.825
            left = round(pad.GetLeftMargin(), 2) + 0.03
            right = round(pad.GetRightMargin(), 2)
        else:
            return

        #Internal, Simulation Internal Text Position
        # Minimum spacing between experiment and extra text
        min_offset = 0.09 if self.experiment == "ATLAS" else 0.08
        offset = max(extraTextOffset, min_offset)
        if self.pubStyle:
            extraTextOffset += 0.02
        exp.DrawLatex(left, y, self.experiment)
        extra.DrawLatex(left + offset, y, str(self.extraText))

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

    def pieChart(self,
                 savefig=None,
                 title="",
                 labelSize=0.035,
                 radius=0.25,
                 angle=0,
                 w=600,
                 h=600,
                 extraTextOffset=0.18,
                 option=""):
        if self._last_draw_summary is None: raise RuntimeError("Call Draw() before pieChart().")

        bkgs = [x for x in self._last_draw_summary["backgrounds"] if x[1] > 0]
        if not bkgs: raise RuntimeError("No positive background yields available for pieChart().")

        values = array("d", [x[1] for x in bkgs])

        canvas = ROOT.TCanvas(unique_name("pie_canvas"), title, w, h)
        canvas.SetLeftMargin(self.mainPad.GetLeftMargin())
        canvas.SetRightMargin(self.mainPad.GetRightMargin())
        canvas.SetTopMargin(self.mainPad.GetTopMargin())
        canvas.SetBottomMargin(self.mainPad.GetBottomMargin())
        
        pie = ROOT.TPie(unique_name("pie"), title, len(values), values)
        pie.SetLabelFormat("%txt (%perc)")
        pie.SetRadius(radius)
        pie.SetAngularOffset(angle)

        pie.SetTextSize(labelSize)

        for i, (label, _, _, color) in enumerate(bkgs):
            pie.GetSlice(i).SetTitle(label)
            pie.GetSlice(i).SetFillColor(color)

        pie.Draw(option)
        self._draw_experiment_label(extraTextOffset,pad=canvas)
        canvas.Update()

        if savefig: canvas.SaveAs(savefig)

        return canvas
            
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
