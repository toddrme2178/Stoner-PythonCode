"""Example of nDimArrhenius Fit."""
from Stoner import Data
import Stoner.Fit as SF
from numpy import linspace, ones_like
from numpy.random import normal

# Make some data
V = linspace(-4, 4, 101)
I = SF.simmons(V, 2500, 3.2, 15.0) + normal(size=len(V), scale=5e-7)
dI = ones_like(V) * 500e-9

p0 = p0 = [2500, 3, 10.0]

d = Data(V, I, dI, setas="xye", column_headers=["Bias", "Current", "Noise"])

d.curve_fit(SF.simmons, p0=p0, result=True, header="curve_fit", maxfev=2000)
d.setas = "xyey"
d.plot(fmt=["r,", "b-"], capsize=1)
d.annotate_fit(
    SF.simmons,
    x=0.25,
    y=0.25,
    prefix="simmons",
    fontdict={"size": "x-small", "color": "blue"},
)

d.setas = "xye"
fit = SF.Simmons()
d.lmfit(SF.Simmons, p0=p0, result=True, header="lmfit", maxfev=2000)
d.setas = "x...y"
d.plot(fmt="g-", label="lmfit")
d.annotate_fit(
    fit,
    x=0.65,
    y=0.25,
    prefix="Simmons",
    fontdict={"size": "x-small", "color": "green"},
)

d.ylabel = "Current (A)"
d.xlabel = "Bias (V)"
d.title = "Simmons Model test"
d.yscale("symlog", linthreshy=1e-5)
d.tight_layout()
