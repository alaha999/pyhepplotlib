import ROOT
ROOT.gROOT.SetBatch(True)

import pyplotlib.pyplot as plt
from dummy_data import make_histograms


GREEN = "\033[92m"
RESET = "\033[0m"


def ok(message):
    print(f"{GREEN}OK{RESET} - {message}")


# --------------------------------------------------
# 1. Normal table
# --------------------------------------------------

qcd, top, signal, data = make_histograms()

plt.figure()
plt.hist(qcd, label="Multijet", stack=True, fill=True)
plt.hist(top, label="Top", stack=True, fill=True)
plt.hist(signal, label="Signal")
plt.hist(data, label="Data", isData=True)

plt.draw()
plt.printTable()

ok("normal table")


# --------------------------------------------------
# 2. Blinded table
# --------------------------------------------------

qcd, top, signal, data = make_histograms()

plt.figure()
plt.hist(qcd, label="Multijet", stack=True, fill=True)
plt.hist(top, label="Top", stack=True, fill=True)
plt.hist(signal, label="Signal")
plt.hist(data, label="Data", isData=True)

plt.draw()
plt.printTable(data=False)

ok("blinded table")


# --------------------------------------------------
# 3. No data
# --------------------------------------------------

qcd, top, signal, _ = make_histograms()

plt.figure()
plt.hist(qcd, label="Multijet", stack=True, fill=True)
plt.hist(top, label="Top", stack=True, fill=True)
plt.hist(signal, label="Signal")

plt.draw()
plt.printTable()

ok("table without data")


# --------------------------------------------------
# 4. Signal only
# --------------------------------------------------

_, _, signal, _ = make_histograms()

plt.figure()
plt.hist(signal, label="Signal")

plt.draw()
plt.printTable()

ok("signal-only table")


# --------------------------------------------------
# 5. Guard before draw
# --------------------------------------------------

qcd, _, _, _ = make_histograms()

plt.figure()
plt.hist(qcd, label="Multijet", stack=True)

try:
    plt.printTable()
except RuntimeError:
    ok("printTable refuses before draw()")
else:
    raise RuntimeError("printTable() should fail before draw()")


print(f"\n{GREEN}OK - ALL TESTS FINISHED{RESET}\n")
