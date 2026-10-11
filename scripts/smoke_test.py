import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from emcorr import mc, options
here = os.path.join(os.path.dirname(__file__), "..")
df = mc.load_params(os.path.join(here, "config", "parameters.csv"))
cor = mc.load_corridors(os.path.join(here, "config", "corridors.yaml"))
years = np.arange(2025, 2061)
P = {k: np.atleast_1d(v) for k, v in mc.base_values(df).items()}
res = options.evaluate(P, cor, years)
print(f"{'option':16s}" + "".join(f"{'L'+str(l):>9s}" for l in range(4)))
for o in options.OPTIONS:
    print(f"{o:16s}" + "".join(f"{float(np.squeeze(res[o][l])):9.1f}" for l in range(4)))
Ps, U = mc.sample_lhs(df, 2000)
r = options.evaluate(Ps, cor, years)
print("\nLHS n=2000, layer 3 (median, P5-P95):")
for o in options.OPTIONS:
    v = np.asarray(r[o][3]) * np.ones(2000)
    print(f"{o:16s} {np.median(v):7.1f}  [{np.percentile(v,5):6.1f}, {np.percentile(v,95):6.1f}]")
