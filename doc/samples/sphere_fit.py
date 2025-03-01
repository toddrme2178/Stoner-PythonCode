"""Fit a sphere with curve_fit."""
from Stoner import Data
from numpy import sin, cos, pi, column_stack, zeros_like, ones_like, meshgrid, linspace
from numpy.random import normal, uniform
import matplotlib.pyplot as plt


def transform(r, q, p):
    """Converts from spherical to cartesian co-ordinates."""
    x = r * sin(q) * cos(p)
    y = r * sin(q) * sin(p)
    z = r * cos(q)
    return x, y, z


def sphere(coords, a, b, c, r):
    """Returns zero if (x,y,z) lies on a sphere centred at (a,b,c) with radius r."""
    x, y, z = coords
    return (x - a) ** 2 + (y - b) ** 2 + (z - c) ** 2 - r ** 2


# Create some points approximately spherical distribution
p = uniform(low=-pi / 2, high=pi / 2, size=250)
q = uniform(low=-pi, high=pi, size=250)
r = normal(loc=3.0, size=250, scale=0.5)

x, y, z = transform(r, q, p)

x += 3.0
y -= 4.0
z += 2.0

# Construct the  DataFile object
d = Data(column_stack((x, y, z)), setas="xyz", filename="Best fit sphere")
d.template.fig_width = 5.2
d.template.fig_height = 5.0  # Square aspect ratio
d.plot_xyz(plotter="scatter")

# curve_fit does the hard work
popt, pcov = d.curve_fit(sphere, (0, 1, 2), zeros_like(d.x))

# This manually constructs the best fit sphere
a, b, c, r = popt
p = linspace(-pi / 2, pi / 2, 16)
q = linspace(-pi, pi, 31)
P, Q = meshgrid(p, q)
R = ones_like(P) * r
x, y, z = transform(R, Q, P)
x += a
y += b
z += c

ax = plt.gca(projection="3d")
ax.plot_surface(x, y, z, rstride=1, cstride=1, color=(1.0, 0.0, 0.0, 0.25), linewidth=0)
plt.draw()
