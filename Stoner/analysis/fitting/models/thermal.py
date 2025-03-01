#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:py:class:`lmfit.Model` model classes and functions for various thermal physics models.
"""

__all__ = [
    "Arrhenius",
    "ModArrhenius",
    "Model",
    "NDimArrhenius",
    "VFTEquation",
    "arrhenius",
    "modArrhenius",
    "nDimArrhenius",
    "np",
    "vftEquation",
]


import numpy as np
import scipy.constants as consts

try:
    from lmfit import Model
    from lmfit.models import update_param_vals
except ImportError:
    Model = object
    update_param_vals = None


def arrhenius(x, A, DE):
    r"""Arrhenius Equation without T dependendent prefactor.

    Args:
        x (array): temperatyre data in K
        A (float): Prefactor - temperature independent. See :py:func:modArrhenius for temperaure dependent version.
        DE (float): Energy barrier in *eV*.

    Return:
        Typically a rate corresponding to the given temperature values.

    The Arrhenius function is defined as :math:`\tau=A\exp\left(\frac{-\Delta E}{k_B x}\right)` where
    :math:`k_B` is Boltzmann's constant.

    Example:
        .. plot:: samples/Fitting/Arrhenius.py
            :include-source:
            :outname: arrhenius

    """
    _kb = consts.physical_constants["Boltzmann constant"][0] / consts.physical_constants["elementary charge"][0]
    return A * np.exp(-DE / (_kb * x))


def nDimArrhenius(x, A, DE, n):
    r"""Arrhenius Equation without T dependendent prefactor for various dimensions.

    Args:
        x (array): temperatyre data in K
        A (float): Prefactor - temperature independent. See :py:func:modArrhenius for temperaure dependent version.
        DE (float): Energy barrier in *eV*.
        n (float): The dimensionalirty of the model

    Return:
        Typically a rate corresponding to the given temperature values.

    The Arrhenius function is defined as :math:`\tau=A\exp\left(\frac{-\Delta E}{k_B x^n}\right)` where
    :math:`k_B` is Boltzmann's constant.

    Example:
        .. plot:: samples/Fitting/nDimArrhenius.py
            :include-source:
            :outname: nDimarrehenius
    """
    return arrhenius(x ** n, A, DE)


def modArrhenius(x, A, DE, n):
    r"""Arrhenius Equation with a variable T power dependent prefactor.

    Args:
        x (array): temperatyre data in K
        A (float): Prefactor - temperature independent. See :py:func:modArrhenius for temperaure dependent version.
        DE (float): Energy barrier in *eV*.
        n (float): The exponent of the temperature pre-factor of the model

    Return:
        Typically a rate corresponding to the given temperature values.

    The modified Arrhenius function is defined as :math:`\tau=Ax^n\exp\left(\frac{-\Delta E}{k_B x}\right)` where
    :math:`k_B` is Boltzmann's constant.

    Example:
        .. plot:: samples/Fitting/modArrhenius.py
            :include-source:
            :outname: modarrhenius
    """
    return (x ** n) * arrhenius(x, A, DE)


def vftEquation(x, A, DE, x_0):
    r"""Vogel-Flucher-Tammann (VFT) Equation without T dependendent prefactor.

    Args:
        x (float): Temperature in K
        A (float): Prefactror (not temperature dependent)
        DE (float): Energy barrier in eV
        x_0 (float): Offset temeprature in K

    Return:
        Rates according the VFT equation.

    The VFT equation is defined as as rr`\tau = A\exp\left(\frac{DE}{x-x_0}\right)` and represents
    a modifed form of the Arrenhius distribution with a freezing point of :math:`x_0`.

    Example:
        .. plot:: samples/Fitting/vftEquation.py
            :include-source:
            :outname: vft
    """
    _kb = consts.physical_constants["Boltzmann constant"][0] / consts.physical_constants["elementary charge"][0]
    return A * np.exp(-DE / (_kb * (x - x_0)))


class Arrhenius(Model):

    r"""Arrhenius Equation without T dependendent prefactor.

    Args:
        x (array): temperatyre data in K
        A (float): Prefactor - temperature independent. See :py:func:modArrhenius for temperaure dependent version.
        DE (float): Energy barrier in *eV*.

    Return:
        Typically a rate corresponding to the given temperature values.

    The Arrhenius function is defined as :math:`\tau=A\exp\left(\frac{-\Delta E}{k_B x}\right)` where
    :math:`k_B` is Boltzmann's constant.

    Example:
        .. plot:: samples/Fitting/Arrhenius.py
            :include-source:
            :outname: arrhenius-class
    """

    display_names = ["A", r"\Delta E"]

    def __init__(self, *args, **kwargs):
        """Configure default function to fit."""
        super(Arrhenius, self).__init__(arrhenius, *args, **kwargs)

    def guess(self, data, x=None, **kwargs):
        """Estimate fitting parameters from data."""
        _kb = consts.physical_constants["Boltzmann constant"][0] / consts.physical_constants["elementary charge"][0]

        d1, d2 = 1.0, 0.0
        if x is not None:
            d1, d2 = np.polyfit(-1.0 / x, np.log(data), 1)
        pars = self.make_params(A=np.exp(d2), DE=_kb * d1)
        return update_param_vals(pars, self.prefix, **kwargs)


class NDimArrhenius(Model):

    r"""Arrhenius Equation without T dependendent prefactor for various dimensions.

    Args:
        x (array): temperatyre data in K
        A (float): Prefactor - temperature independent. See :py:func:modArrhenius for temperaure dependent version.
        DE (float): Energy barrier in *eV*.
        n (float): The dimensionalirty of the model

    Return:
        Typically a rate corresponding to the given temperature values.

    The Arrhenius function is defined as :math:`\tau=A\exp\left(\frac{-\Delta E}{k_B x^n}\right)` where
    :math:`k_B` is Boltzmann's constant.

    Example:
        .. plot:: samples/Fitting/nDimArrhenius.py
            :include-source:
            :outname: nDimarrhenius-class
    """

    display_names = ["A", r"\Delta E", "n"]

    def __init__(self, *args, **kwargs):
        """Configure Initial fitting function."""
        super(NDimArrhenius, self).__init__(nDimArrhenius, *args, **kwargs)

    def guess(self, data, x=None, **kwargs):
        """Guess paramneters from a set of data."""
        _kb = consts.physical_constants["Boltzmann constant"][0] / consts.physical_constants["elementary charge"][0]

        d1, d2 = 1.0, 0.0
        if x is not None:
            d1, d2 = np.polyfit(-1.0 / x, np.log(data), 1)
        pars = self.make_params(A=np.exp(d2), DE=_kb * d1, n=1.0)
        return update_param_vals(pars, self.prefix, **kwargs)


class ModArrhenius(Model):

    r"""Arrhenius Equation with a variable T power dependent prefactor.

    Args:
        x (array): temperatyre data in K
        A (float): Prefactor - temperature independent. See :py:func:modArrhenius for temperaure dependent version.
        DE (float): Energy barrier in *eV*.
        n (float): The exponent of the temperature pre-factor of the model

    Return:
        Typically a rate corresponding to the given temperature values.

    The Arrhenius function is defined as :math:`\tau=Ax^n\exp\left(\frac{-\Delta E}{k_B x}\right)` where
    :math:`k_B` is Boltzmann's constant.

    Example:
        .. plot:: samples/Fitting/modArrhenius.py
            :include-source:
            :outname: modarrhenius-class
    """

    display_names = ["A", r"\Delta E", "n"]

    def __init__(self, *args, **kwargs):
        """Configure Initial fitting function."""
        super(ModArrhenius, self).__init__(modArrhenius, *args, **kwargs)

    def guess(self, data, x=None, **kwargs):
        """Guess paramneters from a set of data."""
        _kb = consts.physical_constants["Boltzmann constant"][0] / consts.physical_constants["elementary charge"][0]

        d1, d2 = 1.0, 0.0
        if x is not None:
            d1, d2 = np.polyfit(-1.0 / x, np.log(data), 1)
        pars = self.make_params(A=np.exp(d2), DE=_kb * d1, n=1.0)
        return update_param_vals(pars, self.prefix, **kwargs)


class VFTEquation(Model):

    r"""Vogel-Flucher-Tammann (VFT) Equation without T dependendent prefactor.

    Args:
        x (array): Temperature in K
        A (float): Prefactror (not temperature dependent)
        DE (float): Energy barrier in eV
        x_0 (float): Offset temeprature in K

    Return:
        Rates according the VFT equation.

    The VFT equation is defined as as :math:`\tau = A\exp\left(\frac{DE}{x-x_0}\right)` and represents
    a modifed form of the Arrenhius distribution with a freezing point of :math:`x_0`.

    See :py:func:`Stoner.Fit.vftEquation` for an example.

    Example:
        .. plot:: samples/Fitting/vftEquation.py
            :include-source:
            :outname: vft-class
    """

    display_names = ["A", r"\Delta E", "x_0"]

    def __init__(self, *args, **kwargs):
        """Configure Initial fitting function."""
        super(VFTEquation, self).__init__(vftEquation, *args, **kwargs)

    def guess(self, data, x=None, **kwargs):
        """Guess paramneters from a set of data."""
        _kb = consts.physical_constants["Boltzmann constant"][0] / consts.physical_constants["elementary charge"][0]

        d1, d2, x0 = 1.0, 0.0, 1.0
        if x is not None:
            x0 = x[np.argmin(np.abs(data))]
            d1, d2 = np.polyfit(-1.0 / (x - x0), np.log(data), 1)
        pars = self.make_params(A=np.exp(d2), dE=_kb * d1, x_0=x0)
        return update_param_vals(pars, self.prefix, **kwargs)
