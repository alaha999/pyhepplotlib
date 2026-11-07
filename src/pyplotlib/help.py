import inspect
from . import pyplot
from .plotter import Plotter


# Public API groups (for display only)
GROUPS = {
    "FIGURE": ["figure", "savefig", "close"],
    "PLOTTING": ["hist", "hist2d", "graph", "draw"],
    "AXES & STYLE": ["xaxis", "yaxis", "ratio_axis", "legend", "caption", "style"],
    "UTILITIES": ["printTable", "pieChart", "current", "options"],
}

# Public name -> internal Plotter method
ALIASES = {
    "draw": ["Draw", "Draw2D", "DrawGraph"],
    "xaxis": ["set_xaxis"],
    "yaxis": ["set_yaxis"],
    "ratio_axis": ["set_yaxis_ratio"],
    "caption": ["set_extraTextCaption"],
}


def discover():
    """Discover public functions from pyplot.py."""
    return {
        name: func for name, func in inspect.getmembers(pyplot, inspect.isfunction)
        if not name.startswith("_") and func.__module__ == pyplot.__name__
    }


def print_parameters(func):
    """Display arguments and default values vertically."""
    params = list(inspect.signature(func).parameters.values())

    if params and params[0].name == "self":
        params = params[1:]

    if not params:
        print("    No arguments")
        return

    print(f"    {'Parameter':<22} {'Default'}")
    print("    " + "-" * 44)

    for param in params:
        default = "required" if param.default is inspect.Parameter.empty else repr(param.default)
        print(f"    {param.name:<22} {default}")


def options(method=None):
    """Display available pyhepplotlib functions and their parameters."""
    functions = discover()

    if method is None:
        print("\n" + "=" * 60)
        print("                  pyhepplotlib API")
        print("=" * 60)

        shown = set()

        for group, names in GROUPS.items():
            available = [name for name in names if name in functions]
            if not available: continue

            print(f"\n  {group}")
            print("  " + "-" * 45)

            for name in available:
                print(f"    plt.{name}()")
                shown.add(name)

        # Automatically include newly introduced functions
        remaining = sorted(set(functions) - shown)

        if remaining:
            print("\n  OTHER")
            print("  " + "-" * 45)
            for name in remaining:
                print(f"    plt.{name}()")

        print("\n" + "-" * 60)
        print("  Use plt.options('function') to see available arguments.")
        print("=" * 60 + "\n")
        return

    if method not in functions:
        raise ValueError(f"Unknown function '{method}'. Available: {', '.join(sorted(functions))}")

    print("\n" + "=" * 60)
    print(f"  plt.{method}()")
    print("=" * 60)

    names = ALIASES.get(method, [method])
    found = False

    for name in names:
        func = getattr(Plotter, name, None)
        if func is None: continue

        found = True
        print(f"\n  {name}()")
        print_parameters(func)

        doc = inspect.getdoc(func)
        if doc:
            print(f"\n    Description: {doc.splitlines()[0]}")

    # Public-only functions (e.g. style())
    if not found:
        print_parameters(functions[method])
        doc = inspect.getdoc(functions[method])
        if doc:
            print(f"\n    Description: {doc.splitlines()[0]}")

    print("\n" + "=" * 60 + "\n")
