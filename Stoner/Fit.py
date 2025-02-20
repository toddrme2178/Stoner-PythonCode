"""Stoner.Fit: Functions and lmfit.Models for fitting data.

Functions should accept an array of x values and a number of parmeters,
they should then return an array of y values the same size as the x array.

Models are subclasses of lmfit.Model that represent the corresponding function

Please do keep documentation up to date, see other functions for documentation examples.

All the functions here defined for scipy.optimize.curve\_fit to call themm
i.e. the parameters are expanded to separate arguements.
"""
__all__ = [
    "Arrhenius",
    "BDR",
    "BlochGrueneisen",
    "FMR_Power",
    "FluchsSondheimer",
    "FowlerNordheim",
    "Ic_B_Airy",
    "Inverse_Kittel",
    "KittelEquation",
    "Langevin",
    "Linear",
    "Lorentzian_diff",
    "ModArrhenius",
    "NDimArrhenius",
    "PowerLaw",
    "Quadratic",
    "RSJ_Noiseless",
    "RSJ_Simple",
    "Simmons",
    "StretchedExp",
    "Strijkers",
    "TersoffHammann",
    "VFTEquation",
    "WLfit",
    "arrhenius",
    "bdr",
    "blochGrueneisen",
    "cfg_data_from_ini",
    "cfg_model_from_ini",
    "fluchsSondheimer",
    "fmr_power",
    "fowlerNordheim",
    "ic_B_airy",
    "inverse_kittel",
    "kittelEquation",
    "langevin",
    "linear",
    "lorentzian_diff",
    "make_model",
    "modArrhenius",
    "nDimArrhenius",
    "powerLaw",
    "quadratic",
    "rsj_noiseless",
    "rsj_simple",
    "simmons",
    "stretchedExp",
    "strijkers",
    "tersoffHammann",
    "vftEquation",
    "wlfit",
]

import Stoner.Core as _SC_
from .compat import string_types
from . import Data
from functools import wraps
import numpy as _np_
from collections import Mapping
from io import IOBase

try:
    from lmfit import Model
    from lmfit.models import LinearModel as _Linear  # NOQA pylint: disable=unused-import
    from lmfit.models import PowerLawModel as _PowerLaw  # NOQA pylint: disable=unused-import
    from lmfit.models import QuadraticModel as _Quadratic  # NOQA pylint: disable=unused-import
    from lmfit.models import update_param_vals
except ImportError:
    Model = object
    _Linear = object
    _PowerLaw = object
    _Quadratic = object
    update_param_vals = None

try:
    from configparser import ConfigParser as SafeConfigParser

except ImportError:
    SafeConfigParser = None

from Stoner.analysis.fitting.models.generic import (
    Linear,
    Lorentzian_diff,
    PowerLaw,
    Quadratic,
    StretchedExp,
    linear,
    lorentzian_diff,
    powerLaw,
    quadratic,
    stretchedExp,
)


from Stoner.analysis.fitting.models.thermal import (
    Arrhenius,
    ModArrhenius,
    NDimArrhenius,
    VFTEquation,
    arrhenius,
    modArrhenius,
    nDimArrhenius,
    vftEquation,
)

from Stoner.analysis.fitting.models.magnetism import (
    FMR_Power,
    Inverse_Kittel,
    KittelEquation,
    Langevin,
    fmr_power,
    inverse_kittel,
    kittelEquation,
    langevin,
)

from Stoner.analysis.fitting.models.tunnelling import (
    BDR,
    FowlerNordheim,
    Simmons,
    TersoffHammann,
    bdr,
    fowlerNordheim,
    simmons,
    tersoffHammann,
)

from Stoner.analysis.fitting.models.e_transport import (
    BlochGrueneisen,
    FluchsSondheimer,
    WLfit,
    blochGrueneisen,
    fluchsSondheimer,
    wlfit,
)

from Stoner.analysis.fitting.models.superconductivity import (
    RSJ_Noiseless,
    RSJ_Simple,
    Strijkers,
    Ic_B_Airy,
    rsj_noiseless,
    rsj_simple,
    strijkers,
    ic_B_airy,
)


def _get_model_(model):
    """Utility meothd to manage creating an lmfit.Model.

    Args:
        model (str, callable, Model): The model to be setup.

    Returns:
        An llmfit.Model instance

    model can be of several different types that determine what to do:

    -   A string. In which ase it should be a fully qualified name of a function or class to be imported.
        The part after the final period will be assumed to be the name and the remainder the module to be
        imported.
    -   A callable object. In this case the callable will be passed to the constructor of Model and a fresh
        Model instance is constructed
    -   A subclass of lmfit.Model - in whcih case it is instantiated.
    -   A Model instance - in which case no further action is necessary.

    """
    if isinstance(model, string_types):  # model is a string, so we;ll try importing it now
        parts = model.split(".")
        model = parts[-1]
        module = ".".join(parts[:-1])
        model = __import__(module, globals(), locals(), (model)).__getattribute__(model)
    if type(model).__name__ == "type" and issubclass(
        model, Model
    ):  # ok perhaps we've got a model class rather than an instance
        model = model()
    if not isinstance(model, Model) and callable(model):  # Ok, wrap the callable in a model
        model = Model(model)
    if not isinstance(model, Model):
        raise TypeError("model {} is not an instance of llmfit.Model".format(model.__name__))
    return model


def make_model(model_func):
    """A decorator that turns a function into an lmfit model.

    Notes:
        The function being wrapped into the model should have the form::

            def model_func(x_data,*parameters):
                ....

        (i.e. similar to what :py:func:`scipy.optimize.curve_fit` expects). The resulting
        class is a sub-class of :py:class:`lmfit.Model` but also adds a class method
        :py:method:`_ModelDectorator.guesser` which can be used as a decorator to convert another function into
        a :py:meth:`lmfit.Model.guess` method. If using this decorator, the function that does the guessing should
        take the form::

            def guesser_function(y_data,x=x_data,**kargs):
                return (param_1,param_2,....,pram_n)

        Similarly, the class provides a :py:meth:`_ModelDecorator.hinter` decorator which can be used to mark a function
        as something that can generate prameter hints for the model. In this case the function should take the form::

            def hinter(**kwargs):
                return {"param_1":{"max":max_val,"min":min_value,"value":start_value},"param_2":{.....}}

        Finally the new model_func class can be instantiated or just passed to :py:meth:`Data.lmfit` etc. directly.
    """

    class _ModelDecorator(Model):

        __doc__ = model_func.__doc__

        def __init__(self, *args, **kargs):
            super(_ModelDecorator, self).__init__(model_func, *args, **kargs)
            if hasattr(self, "_limits"):
                for param, limit in self._limits().items():
                    self.set_param_hint(param, **limit)
            self.__name__ = self.func.__name__

        def guess(self, y, x=None):
            """A default parameter guess method that just guesses 1.0 for everything like :py:func:`scipy.optimize.curve_fit` does."""
            return _np_.ones(len(self.param_names))

        @classmethod
        def hinter(cls, func):
            """Use the given function to determine the parameter hints.

            Args:
                func (callable): A fimction that rturns a dictionary of dictionaries

            Returns:
                The wrapped hinter function.

            Notes:
                This decorator will modify the instance attributes so that the instance has a method to generate parameter hints.

                func should only take keyword arguments as by default it will be called with no arguments during model initialisation.
            """

            @wraps(func)
            def _limits_proxy(self, **kargs):
                limits = func(**kargs)
                for param in limits:
                    if param not in self.param_names:
                        raise RuntimeError("Unrecognised parameter in hinter function: {}".format(param))
                    if not isinstance(limits[param], Mapping):
                        raise RuntimeError("Parameter hint for {} was not a mapping".format(param))
                return limits

            cls._limits = _limits_proxy
            return _limits_proxy

        @classmethod
        def guesser(cls, func):
            """Use the given function as the guess method.

            Args:
                func (callable): A function that guesses the parameter values

            Returns:
                The wrapped guess function.

            Notes:
                This decorator will modify the instance attributes so that the instance has a working guess method.

                func should take at least one positional argument, being the y-data values used to guess parameters.
                It should return a list, tuple of guesses parameter values with one entry for each parameter in the model.
            """

            @wraps(func)
            def guess_proxy(self, *args, **kargs):
                """A magic proxy call around a function to guess initial prameters."""
                guesses = func(*args, **kargs)
                pars = {x: y for x, y in zip(self.param_names, guesses)}
                pars = self.make_params(**pars)
                return update_param_vals(pars, self.prefix, **kargs)

            cls.guess = guess_proxy
            return guess_proxy

    return _ModelDecorator


def cfg_data_from_ini(inifile, filename=None, **kargs):
    """Read an inifile and load and configure a DataFile from it.

    Args:
        inifile (str or file): Path to the ini file to be read.

    Keyword Arguments:
        filename (strig,boolean or None): File to load that contains the data.
        **kargs: All other keywords are passed to the Data constructor

    Returns:
        An instance of :py:class:`Stoner.Core.Data` with data loaded and columns configured.

    The inifile should contain a [Data] section that contains the following keys:

    -  **type (str):** optional name of DataFile subclass to import.
    -  **filename (str or boolean):** optionally used if *filename* parameter is None.
    - **xcol (column index):** defines the x-column data for fitting.
    - **ycol (column index):** defines the y-column data for fitting.
    - **yerr (column index):** Optional column with uncertainity values for the data
    """
    if SafeConfigParser is None:
        raise RuntimeError("Need to have ConfigParser module installed for this to work.")
    config = SafeConfigParser()
    if isinstance(inifile, string_types):
        config.read(inifile)
    elif isinstance(inifile, IOBase):
        config.readfp(inifile)
    if not config.has_section("Data"):
        raise RuntimeError("Configuration file lacks a [Data] section to describe data.")

    if config.has_option("Data", "type"):
        typ = config.get("Data", "type").split(".")
        typ_mod = ".".join(typ[:-1])
        typ = typ[-1]
        typ = __import__(typ_mod, fromlist=[typ]).__getattribute__(typ)
    else:
        typ = None
    data = Data(**kargs)
    if filename is None:
        if not config.has_option("Data", "filename"):
            filename = False
        else:
            filename = config.get("Data", "filename")
            if filename in ["False", "True"]:
                filename = bool(filename)
    data.load(filename, auto_load=False, filetype=typ)
    cols = {"x": 0, "y": 1, "e": None}  # Defaults

    for c in ["x", "y", "e"]:
        if not config.has_option("Data", c):
            pass
        else:
            try:
                cols[c] = config.get("Data", c)
                cols[c] = int(cols[c])
            except ValueError:
                pass
        if cols[c] is None:
            del cols[c]

    data.setas(**cols)  # pylint: disable=not-callable
    return data


def cfg_model_from_ini(inifile, model=None, data=None):
    r"""Utility function to configure an lmfit Model from an inifile.

    Args:
        inifile (str or file): Path to the ini file to be read.

    Keyword Arguments:
        model (str, callable, lmfit.Model instance or sub-class or None): What to use as a model function.
        data (DataFile): if supplied, the details of the parameter hints and labels and units are included in the data's metadata.

    Returns:
        An llmfit.Model,, a 2D array of starting values for each parameter

    model can be of several different types that determine what to do:

    -   A string. In which ase it should be a fully qualified name of a function or class to be imported.
        The part after the final period will be assumed to be the name and the remainder the module to be
        imported.
    -   A callable object. In this case the callable will be passed to the constructor of Model and a fresh
        Model instance is constructed
    -   A subclass of lmfit.Model - in whcih case it is instantiated.
    -   A Model instance - in which case no further action is necessary.

    The returned model is configured with parameter hints for fitting with. The second return value is
    a 2D array which lists the starting values for one or more fits. If the inifile describes mapping out
    the :math:`\Chi^2` as a function of the parameters, then this array has a separate row for each iteration.
    """
    config = SafeConfigParser()
    if isinstance(inifile, string_types):
        config.read(inifile)
    elif isinstance(inifile, IOBase):
        config.readfp(inifile)

    if model is None:  # Check to see if config file specified a model
        try:
            model = config.get("Options", "model")
        except Exception:
            raise RuntimeError("Model is notspecifed either as keyword argument or in inifile")
    model = _get_model_(model)
    if config.has_option("option", "prefix"):
        prefix = config.get("option", "prefix")
    else:
        prefix = model.__class__.__name__
    prefix += ":"
    vals = []
    for p in model.param_names:
        if not config.has_section(p):
            raise RuntimeError("Config file does not have a section for parameter {}".format(p))
        keys = {
            "vary": bool,
            "value": float,
            "min": float,
            "max": float,
            "expr": str,
            "step": float,
            "label": str,
            "units": str,
        }
        kargs = dict()
        for k in keys:
            if config.has_option(p, k):
                if keys[k] == bool:
                    kargs[k] = config.getboolean(p, k)
                elif keys[k] == float:
                    kargs[k] = config.getfloat(p, k)
                elif keys[k] == str:
                    kargs[k] = config.get(p, k)
        if isinstance(data, _SC_.DataFile):  # stuff the parameter hint data into metadata
            for k in keys:  # remove keywords not needed
                if k in kargs:
                    data["{}{} {}".format(prefix, p, k)] = kargs[k]
            if "lmfit.prerfix" in data:
                data["lmfit.prefix"].append(prefix)
            else:
                data["lmfit.prefix"] = [prefix]
        if "step" in kargs:  # We use step for creating a chi^2 mapping, but not for a parameter hint
            step = kargs.pop("step")
            if "vary" in kargs and "min" in kargs and "max" in kargs and not kargs["vary"]:  # Make chi^2?
                vals.append(_np_.arange(kargs["min"], kargs["max"] + step / 10, step))
            else:  # Nope, just make a single value step here
                vals.append(_np_.array(kargs["value"]))
        else:  # Nope, just make a single value step here
            vals.append(_np_.array(kargs["value"]))
        kargs = {k: kargs[k] for k in kargs if k in ["value", "max", "min", "vary"]}
        model.set_param_hint(p, **kargs)  # set the model parameter hint
    msh = _np_.meshgrid(*vals)  # make a mesh of all possible parameter values to test
    msh = [m.ravel() for m in msh]  # tidy it up and combine into one 2D array
    msh = _np_.column_stack(msh)
    return model, msh
