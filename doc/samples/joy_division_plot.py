# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 15:01:49 2019

Demonstrate a waterfall plot styled after the famous album cover from Joy Division

@author: phygbu
"""

from Stoner import Data, DataFolder
from Stoner.formats.instruments import RigakuFile
from Stoner.plot.utils import joy_division
from numpy import log10


class RigakuFolder(DataFolder):

    """Quick subclass of DataFolder that knows how to extract multiple files from a single Rigaku file."""

    def load_files(self, filename):
        """Open the ras file and keep reading files."""

        with open(filename, "rb") as data:
            data.read()
            end = data.tell()
            data.seek(0)
            while data.tell() < end:
                d = RigakuFile()
                d._load(data)
                self += Data(d)

        return self


# Create a blank DataFolder subclass and then load the files into it.
fldr = RigakuFolder()
fldr.load_files(
    "L2_2 5mm length limiting slit Offspec RSM 0p05 2t step_0SecsAnneal.ras"
)
# The last file is impy to get rid of it.
# \Make the third column of data be the 2 theta angle
dels = []
for ix, d in enumerate(fldr):
    if len(d) == 0:
        dels.append(ix)
        continue
    d.setas = "xzy"
    d.y *= d["axis.position"][0]

for ix in sorted(dels, reverse=True):
    del fldr[ix]
# stack all the files together
for d in fldr[1:]:
    fldr[0] += d

total = fldr[0]

total.setas = "xzy"
total.z = log10(total.z)
total.column_headers = [
    r"$\omega(^\circ)$",
    r"$2\theta (^\circ)5",
    r"$\log_{10}(Counts)$",
]
# Do the plot
total.plot(plotter=joy_division, griddata=False, projection=None)
