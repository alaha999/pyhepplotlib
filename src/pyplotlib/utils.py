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
