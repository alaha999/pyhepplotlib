import ROOT
from array import array
import math

_name_id = 0


def unique_name(prefix):
    global _name_id
    _name_id += 1
    return f"{prefix}_{_name_id}"


def clone_histogram(histo, name=None):
    h = histo.Clone(name or unique_name(histo.GetName()))
    if hasattr(h, "SetDirectory"):
        h.SetDirectory(0)
    return h


def root_value(value):
    """Resolve ROOT constants without eval(). Integers are returned unchanged."""
    if not isinstance(value, str):
        return value

    expr = value.replace("ROOT.", "").replace(" ", "")
    sign = 1
    offset = 0
    base = expr

    if "+" in expr:
        base, tail = expr.rsplit("+", 1)
        offset = int(tail)
    elif "-" in expr[1:]:
        base, tail = expr.rsplit("-", 1)
        sign = -1
        offset = int(tail)

    if not hasattr(ROOT, base):
        raise ValueError(f"Unknown ROOT value: {value}")
    return getattr(ROOT, base) + sign * offset

def merge_underflow_overflow_in_range(h, xmin=None, xmax=None):
    axis = h.GetXaxis()
    nbins = h.GetNbinsX()

    first_bin = 1
    last_bin = nbins

    if xmin is not None:
        first_bin = max(1, axis.FindBin(xmin))

    if xmax is not None:
        last_bin = min(nbins, axis.FindBin(xmax - 1e-9))

    if first_bin > last_bin: raise ValueError("Invalid visible x-range.")

    if first_bin == last_bin:
        content = sum(h.GetBinContent(i) for i in range(0, nbins + 2))
        error = sum(h.GetBinError(i)**2 for i in range(0, nbins + 2))**0.5

        h.Reset()
        h.SetBinContent(first_bin, content)
        h.SetBinError(first_bin, error)
        return
    
    low_content = sum(h.GetBinContent(i) for i in range(0, first_bin + 1))
    low_error = sum(h.GetBinError(i)**2 for i in range(0, first_bin + 1))**0.5

    high_content = sum(h.GetBinContent(i) for i in range(last_bin, nbins + 2))
    high_error = sum(h.GetBinError(i)**2 for i in range(last_bin, nbins + 2))**0.5

    for i in range(0, first_bin):
        h.SetBinContent(i, 0)
        h.SetBinError(i, 0)

    for i in range(last_bin + 1, nbins + 2):
        h.SetBinContent(i, 0)
        h.SetBinError(i, 0)

    h.SetBinContent(first_bin, low_content)
    h.SetBinError(first_bin, low_error)

    h.SetBinContent(last_bin, high_content)
    h.SetBinError(last_bin, high_error)


def truncate_histogram(h_orig, xmin, xmax, new_name=None):
    axis = h_orig.GetXaxis()
    nbins_orig = h_orig.GetNbinsX()

    bin_low = max(1, axis.FindBin(xmin))
    bin_high = min(nbins_orig, axis.FindBin(xmax))
    if xmax == axis.GetBinLowEdge(bin_high):
        bin_high -= 1
    bin_high = max(bin_low, bin_high)

    edges = [axis.GetBinLowEdge(bin_low)]
    edges += [axis.GetBinUpEdge(b) for b in range(bin_low, bin_high + 1)]

    h_new = ROOT.TH1D(
        new_name or unique_name(h_orig.GetName() + "_trimmed"),
        h_orig.GetTitle(),
        len(edges) - 1,
        array("d", edges),
    )
    h_new.SetDirectory(0)

    h_new.SetLineColor(h_orig.GetLineColor())
    h_new.SetFillColor(h_orig.GetFillColor())
    h_new.SetMarkerColor(h_orig.GetMarkerColor())
    h_new.SetMarkerStyle(h_orig.GetMarkerStyle())
    h_new.SetMarkerSize(h_orig.GetMarkerSize())
    h_new.SetLineStyle(h_orig.GetLineStyle())
    h_new.SetLineWidth(h_orig.GetLineWidth())
    h_new.SetFillStyle(h_orig.GetFillStyle())
    h_new.GetXaxis().SetTitle(axis.GetTitle())
    h_new.GetYaxis().SetTitle(h_orig.GetYaxis().GetTitle())

    for target_bin, source_bin in enumerate(range(bin_low, bin_high + 1), start=1):
        h_new.SetBinContent(target_bin, h_orig.GetBinContent(source_bin))
        h_new.SetBinError(target_bin, h_orig.GetBinError(source_bin))

    return h_new


def mc_uncertainty_band_ratio(h_mc):
    unc_band = ROOT.TGraphAsymmErrors()
    unc_band.SetName(unique_name("unc_band_ratio"))
    unc_band.SetTitle("Ratio panel Uncertainty Band")

    for i in range(1, h_mc.GetNbinsX() + 1):
        mc_val = h_mc.GetBinContent(i)
        mc_err = h_mc.GetBinError(i)
        x = h_mc.GetBinCenter(i)
        width = h_mc.GetBinWidth(i) / 2.0
        rel_err = mc_err / mc_val if mc_val > 0 else 0.0
        unc_band.SetPoint(i - 1, x, 1.0)
        unc_band.SetPointError(i - 1, width, width, rel_err, rel_err)

    return unc_band


def axis_edges_2d(axis):
    """All actual axis edges, including variable-width ROOT axes."""
    return [axis.GetBinLowEdge(i) for i in range(1, axis.GetNbins() + 2)]


def _rebin_edges_2d(axis, spec):
    edges = axis_edges_2d(axis)
    if isinstance(spec, int) and not isinstance(spec, bool):
        if spec == 1:
            return edges
        if spec < 1:
            raise ValueError('rebinx/rebiny must be positive')
        return [edges[i] for i in range(0, len(edges) - 1, spec)] + [edges[-1]]
    try:
        requested = [float(v) for v in spec]
    except (TypeError, ValueError) as exc:
        raise ValueError("Rebinning requires a positive integer or bin-edge sequence") from exc
    if len(requested) < 2 or any(not math.isfinite(v) for v in requested) or any(a >= b for a, b in zip(requested, requested[1:])):
        raise ValueError('Rebin edges must be finite and strictly increasing')
    for edge in requested:
        if not any(math.isclose(edge, orig, rel_tol=1e-10, abs_tol=1e-10) for orig in edges):
            raise ValueError(f'Rebin edge {edge:g} is not a source bin boundary')
    return requested


def full_integral_2d(h):
    return sum(h.GetBinContent(ix, iy)
               for ix in range(h.GetNbinsX() + 2)
               for iy in range(h.GetNbinsY() + 2))


def rebin_histogram_2d(source, rebinx=1, rebiny=1, xrange=None, yrange=None, fold=True):
    """Rebin TH2 without splitting source bins; optionally fold all exterior cells.

    Ranges select visible source bins (as ROOT SetRangeUser does). When fold=True
    overflow, underflow and out-of-range bins are folded to those boundaries.
    """
    xedges = _rebin_edges_2d(source.GetXaxis(), rebinx)
    yedges = _rebin_edges_2d(source.GetYaxis(), rebiny)
    if xrange is not None and not xrange[0] < xrange[1]:
        raise ValueError('xrange must be increasing')
    if yrange is not None and not yrange[0] < yrange[1]:
        raise ValueError('yrange must be increasing')
    dest = ROOT.TH2D(unique_name('h2_rebin'), source.GetTitle(),
                     len(xedges)-1, array('d', xedges),
                     len(yedges)-1, array('d', yedges))
    dest.SetDirectory(0)
    dest.Sumw2()
    # Retain axis titles and style-relevant information.
    dest.GetXaxis().SetTitle(source.GetXaxis().GetTitle())
    dest.GetYaxis().SetTitle(source.GetYaxis().GetTitle())

    def destination_bins(axis, out_axis, wanted):
        low = 1 if wanted is None else max(1, min(out_axis.GetNbins(), out_axis.FindFixBin(wanted[0])))
        high = out_axis.GetNbins() if wanted is None else max(1, min(out_axis.GetNbins(), out_axis.FindFixBin(math.nextafter(wanted[1], -math.inf))))
        if low > high:
            raise ValueError('Plot range does not contain any output bins')
        indices = []
        n = axis.GetNbins()
        for i in range(n+2):
            if i == 0:
                j = 0
            elif i == n+1:
                j = out_axis.GetNbins()+1
            else:
                j = out_axis.FindFixBin(axis.GetBinCenter(i))
            if fold:
                j = min(high, max(low, j))
            indices.append(j)
        return indices

    xmap = destination_bins(source.GetXaxis(), dest.GetXaxis(), xrange)
    ymap = destination_bins(source.GetYaxis(), dest.GetYaxis(), yrange)
    for ix in range(source.GetNbinsX()+2):
        for iy in range(source.GetNbinsY()+2):
            dx, dy = xmap[ix], ymap[iy]
            content = source.GetBinContent(ix, iy)
            error = source.GetBinError(ix, iy)
            dest.SetBinContent(dx, dy, dest.GetBinContent(dx, dy) + content)
            dest.SetBinError(dx, dy, math.hypot(dest.GetBinError(dx, dy), error))

    dest.SetEntries(source.GetEntries())
    expected, observed = full_integral_2d(source), full_integral_2d(dest)
    tol = 1e-9 * max(1.0, sum(abs(source.GetBinContent(ix, iy))
                                for ix in range(source.GetNbinsX()+2)
                                for iy in range(source.GetNbinsY()+2)))
    if not all(math.isfinite(x) for x in (expected, observed)) or abs(expected-observed) > tol:
        raise RuntimeError(f'2D yield changed during rebin/folding: {expected} -> {observed}')
    return dest

#############################
# TGraph, Efficiency Helper #
#############################

def hist_to_graph(hist):
    """Convert TH1 to TGraphAsymmErrors."""

    graph = ROOT.TGraphAsymmErrors(hist.GetNbinsX())
    graph.SetName(unique_name("hist_graph"))

    for i in range(1, hist.GetNbinsX() + 1):

        x = hist.GetBinCenter(i)
        y = hist.GetBinContent(i)

        ex = hist.GetBinWidth(i) / 2.0
        ey = hist.GetBinError(i)

        graph.SetPoint(i - 1, x, y)
        graph.SetPointError(i - 1, ex, ex, ey, ey)

    return graph

def as_asymm_graph(source):
    """Convert a ROOT graph to TGraphAsymmErrors."""

    if source.InheritsFrom("TH1"):
        return hist_to_graph(source)

    if not source.InheritsFrom("TGraph"):
        raise TypeError("Expected TH1 or TGraph")

    graph = ROOT.TGraphAsymmErrors(source.GetN())
    graph.SetName(unique_name("asymm_graph"))

    is_asymm = source.InheritsFrom("TGraphAsymmErrors")
    is_symm = source.InheritsFrom("TGraphErrors")

    for i in range(source.GetN()):

        x = source.GetPointX(i)
        y = source.GetPointY(i)

        if is_asymm:

            exlow = source.GetErrorXlow(i)
            exhigh = source.GetErrorXhigh(i)

            eylow = source.GetErrorYlow(i)
            eyhigh = source.GetErrorYhigh(i)

        elif is_symm:

            exlow = exhigh = source.GetErrorX(i)
            eylow = eyhigh = source.GetErrorY(i)

        else:

            exlow = exhigh = 0.0
            eylow = eyhigh = 0.0

        graph.SetPoint(i, x, y)

        graph.SetPointError(
            i, exlow, exhigh, eylow, eyhigh
        )

    return graph

def rebinned_hist(hist, rebin=1):
    """Rebin a private histogram clone."""

    from array import array
    from math import isclose

    h = clone_histogram(hist)

    if rebin is None:
        return h

    if isinstance(rebin, int):

        if rebin == 1:
            return h

        if rebin < 1:
            raise ValueError("Rebin factor must be positive")

        if h.GetNbinsX() % rebin != 0:
            raise ValueError(
                "Rebin factor must divide the number of bins"
            )

        h.Rebin(rebin)
        return h

    # Variable-width binning
    edges = [float(x) for x in rebin]

    if len(edges) < 2:
        raise ValueError("At least two bin edges required")

    if any(b <= a for a, b in zip(edges, edges[1:])):
        raise ValueError("Bin edges must be increasing")

    axis = h.GetXaxis()

    original_edges = [axis.GetBinLowEdge(1)]

    original_edges += [
        axis.GetBinUpEdge(i)
        for i in range(1, h.GetNbinsX() + 1)
    ]

    # Require full histogram coverage
    if not isclose(edges[0], original_edges[0], abs_tol=1e-9):
        raise ValueError("First bin edge does not match")

    if not isclose(edges[-1], original_edges[-1], abs_tol=1e-9):
        raise ValueError("Last bin edge does not match")

    # Avoid splitting original bins
    for edge in edges:

        if not any(
            isclose(edge, old, abs_tol=1e-9)
            for old in original_edges
        ):
            raise ValueError(
                f"New bin edge {edge} is not an original bin edge"
            )

    hnew = h.Rebin(
        len(edges) - 1,
        unique_name("rebinned"),
        array("d", edges)
    )

    hnew.SetDirectory(0)

    return hnew


def efficiency_graph(passed, total, error="normal"):
    """Calculate efficiency using ROOT."""

    if passed.GetDimension() != 1 or total.GetDimension() != 1:
        raise ValueError("Efficiency requires 1D histograms")

    if not ROOT.TEfficiency.CheckBinning(passed, total):
        raise ValueError(
            "Numerator and denominator binning differs"
        )

    if not ROOT.TEfficiency.CheckConsistency(
        passed, total, "w"
    ):
        raise ValueError(
            "Invalid numerator/denominator histograms"
        )

    # Reject negative weighted bins
    for i in range(total.GetNbinsX() + 2):

        if total.GetBinContent(i) < 0:
            raise ValueError("Negative total bin content")

        if passed.GetBinContent(i) < 0:
            raise ValueError("Negative passed bin content")

    methods = {
        "normal": "n",
        "bayesian": "b(1,1) mode",
        "cp": "cp",
    }

    if error not in methods:
        raise ValueError(f"Unknown error method: {error}")

    # Clopper-Pearson requires unweighted binomial counts
    if error == "cp":

        for hist in (passed, total):

            for i in range(hist.GetNbinsX() + 2):

                content = hist.GetBinContent(i)
                variance = hist.GetBinError(i)**2

                if abs(content - round(content)) > 1e-8:
                    raise ValueError(
                        "Clopper-Pearson requires unweighted counts"
                    )

                if abs(variance - content) > 1e-8:
                    raise ValueError(
                        "Clopper-Pearson requires unweighted counts"
                    )

    graph = ROOT.TGraphAsymmErrors()
    graph.SetName(unique_name("efficiency_graph"))

    graph.Divide(
        passed,
        total,
        methods[error] + " cl=0.683"
    )

    return graph

def graph_ratio(numerator, denominator, reference=False):
    """Calculate graph ratio with asymmetric errors."""

    from math import sqrt, isclose

    if numerator.GetN() != denominator.GetN():
        raise ValueError(
            "Graphs must have the same number of points"
        )

    graph = ROOT.TGraphAsymmErrors()
    graph.SetName(unique_name("graph_ratio"))

    for i in range(numerator.GetN()):

        x = numerator.GetPointX(i)
        y = numerator.GetPointY(i)

        xr = denominator.GetPointX(i)
        d = denominator.GetPointY(i)

        if not isclose(x, xr, rel_tol=1e-7, abs_tol=1e-9):
            raise ValueError("Graph X coordinates do not match")

        if d == 0:
            continue

        exlow = numerator.GetErrorXlow(i)
        exhigh = numerator.GetErrorXhigh(i)

        if reference:

            ratio = 1.0
            eylow = 0.0
            eyhigh = 0.0

        else:
            ratio = y / d
            # Independent-error approximation
            eylow  = sqrt((numerator.GetErrorYlow(i) / d)**2 +(y * denominator.GetErrorYhigh(i)/ (d*d))**2)            
            eyhigh = sqrt((numerator.GetErrorYhigh(i) / d)**2+(y * denominator.GetErrorYlow(i)/ (d*d))**2)

            
        j = graph.GetN()
        graph.SetPoint(j, x, ratio)
        graph.SetPointError(j, exlow, exhigh, eylow, eyhigh)

    return graph

def graph_bounds(
    graphs,
    logY=False,
    efficiency=False,
    ratio=False
):
    """Determine axis limits including graph uncertainties."""

    xs = []
    ys = []

    for graph in graphs:

        for i in range(graph.GetN()):

            x = graph.GetPointX(i)
            y = graph.GetPointY(i)

            xs.extend([
                x - graph.GetErrorXlow(i),
                x + graph.GetErrorXhigh(i)
            ])

            ys.extend([
                y - graph.GetErrorYlow(i),
                y + graph.GetErrorYhigh(i)
            ])

    if not xs:
        raise ValueError("Cannot determine bounds of empty graphs")

    xmin = min(xs)
    xmax = max(xs)

    if xmin == xmax:
        xmin -= 0.5
        xmax += 0.5

    # Logarithmic Y axis
    if logY:

        positive = [v for v in ys if v > 0]

        if not positive:
            raise ValueError("No positive Y values for log scale")

        ymin = min(positive)
        ymax = max(positive)

        return (
            (xmin, xmax),
            (ymin / 1.7, max(ymax * 2.0, ymin * 1.1))
        )

    # Efficiency axis
    if efficiency:

        ymin = min(0.0, min(ys))
        ymax = max(1.05, max(ys) * 1.08)

        return (xmin, xmax), (ymin, ymax)

    # General graphs
    ymin = min(ys)
    ymax = max(ys)

    if ratio:
        ymin = min(ymin, 1.0)
        ymax = max(ymax, 1.0)

    delta = ymax - ymin

    if delta == 0:
        delta = max(abs(ymax) * 0.1, 0.1)

    ymin -= 0.1 * delta
    ymax += 0.15 * delta

    return (xmin, xmax), (ymin, ymax)
