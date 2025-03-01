"""Demo of new Stoner.Analysis.AnalyseFile.lmfit
"""
from __future__ import print_function
from Stoner import __home__
from os.path import join
from Stoner.Fit import cfg_data_from_ini, cfg_model_from_ini

config = join(__home__, "..", "scripts", "PCAR-chi^2.ini")
datafile = join(__home__, "..", "sample-data", "PCAR Co Data.csv")

d = cfg_data_from_ini(config, datafile)
model, p0 = cfg_model_from_ini(config, data=d)

fit = d.lmfit(model, p0=p0, result=True, header="Fit", output="data")

fit.plot(multiple="panels", capsize=3)
fit.yscale = "log"  # Adjust y scale for chi^2
fit.tight_layout()
