# -*- coding: utf-8 -*-
"""Code adapted from skimage module
"""
from __future__ import division

__all__ = ["convert"]

import numpy as np
from warnings import warn


dtype_range = {
    np.bool_: (False, True),
    np.bool8: (False, True),
    np.uint8: (0, 255),
    np.uint16: (0, 65535),
    np.int8: (-128, 127),
    np.int16: (-32768, 32767),
    np.int64: (-2 ** 63, 2 ** 63 - 1),
    np.uint64: (0, 2 ** 64 - 1),
    np.int32: (-2 ** 31, 2 ** 31 - 1),
    np.uint32: (0, 2 ** 32 - 1),
    np.float32: (-1.0, 1.0),
    np.float64: (-1.0, 1.0),
}

integer_types = (np.uint8, np.uint16, np.int8, np.int16)

_supported_types = (
    np.bool_,
    np.bool8,
    np.uint8,
    np.uint16,
    np.uint32,
    np.uint64,
    np.int8,
    np.int16,
    np.int32,
    np.int64,
    np.float32,
    np.float64,
)

dtype_range[np.float16] = (-1, 1)
_supported_types += (np.float16,)


def sign_loss(dtypeobj_in, dtypeobj):
    """Warn over loss of sign information when converting image."""
    warn(
        "Possible sign loss when converting negative image of type "
        "%s to positive image of type %s." % (dtypeobj_in, dtypeobj)
    )


def prec_loss(dtypeobj_in, dtypeobj):
    """Warn over precision loss when converting image."""
    warn("Possible precision loss when converting from " "%s to %s" % (dtypeobj_in, dtypeobj))


def _dtype(itemsize, *dtypes):
    """Return first of `dtypes` with itemsize greater than `itemsize."""
    try:
        ret = next(dt for dt in dtypes if itemsize < np.dtype(dt).itemsize)
    except StopIteration:
        ret = dtypes[0]
    return ret


def _dtype2(kind, bits, itemsize=1):
    """Return dtype of `kind` that can store a `bits` wide unsigned int."""
    c = lambda x, y: x <= y if kind == "u" else x < y
    s = next(i for i in (itemsize,) + (2, 4, 8) if c(bits, i * 8))
    return np.dtype(kind + str(s))


def _scale(a, n, m, dtypeobj_in, dtypeobj, copy=True):
    """cale unsigned/positive integers from n to m bits

    Numbers can be represented exactly only if m is a multiple of n
    Output array is of same kind as input."""
    kind = a.dtype.kind
    if n > m and a.max() < 2 ** m:
        mnew = int(np.ceil(m / 2) * 2)
        if mnew > m:
            dtype = "int%s" % mnew
        else:
            dtype = "uint%s" % mnew
        n = int(np.ceil(n / 2) * 2)
        msg = "Downcasting %s to %s without scaling because max " "value %s fits in %s" % (
            a.dtype,
            dtype,
            a.max(),
            dtype,
        )
        warn(msg)
        return a.astype(_dtype2(kind, m))
    elif n == m:
        return a.copy() if copy else a
    elif n > m:
        # downscale with precision loss
        prec_loss(dtypeobj_in, dtypeobj)
        if copy:
            b = np.empty(a.shape, _dtype2(kind, m))
            np.floor_divide(a, 2 ** (n - m), out=b, dtype=a.dtype, casting="unsafe")
            return b
        else:
            a //= 2 ** (n - m)
            return a
    elif m % n == 0:
        # exact upscale to a multiple of n bits
        if copy:
            b = np.empty(a.shape, _dtype2(kind, m))
            np.multiply(a, (2 ** m - 1) // (2 ** n - 1), out=b, dtype=b.dtype)
            return b
        else:
            a = np.array(a, _dtype2(kind, m, a.dtype.itemsize), copy=False)
            a *= (2 ** m - 1) // (2 ** n - 1)
            return a
    else:
        # upscale to a multiple of n bits,
        # then downscale with precision loss
        prec_loss(dtypeobj_in, dtypeobj)
        o = (m // n + 1) * n
        if copy:
            b = np.empty(a.shape, _dtype2(kind, o))
            np.multiply(a, (2 ** o - 1) // (2 ** n - 1), out=b, dtype=b.dtype)
            b //= 2 ** (o - m)
            return b
        else:
            a = np.array(a, _dtype2(kind, o, a.dtype.itemsize), copy=False)
            a *= (2 ** o - 1) // (2 ** n - 1)
            a //= 2 ** (o - m)
            return a


def convert(image, dtype, force_copy=False, uniform=False, normalise=True):
    """
    Convert an image to the requested data-type.

    Warnings are issued in case of precision loss, or when negative values
    are clipped during conversion to unsigned integer types (sign loss).

    Floating point values are expected to be normalized and will be clipped
    to the range [0.0, 1.0] or [-1.0, 1.0] when converting to unsigned or
    signed integers respectively.

    Numbers are not shifted to the negative side when converting from
    unsigned to signed integer types. Negative values will be clipped when
    converting to unsigned integers.

    Parameters
    ----------
    image : ndarray
        Input image.
    dtype : dtype
        Target data-type.
    force_copy : bool
        Force a copy of the data, irrespective of its current dtype.
    uniform : bool
        Uniformly quantize the floating point range to the integer range.
        By default (uniform=False) floating point values are scaled and
        rounded to the nearest integers, which minimizes back and forth
        conversion errors.
    normalise : bool
        When converting from int types to float normalise the resulting array
        by the maximum allowed value of the int type.

    References
    ----------
    (1) DirectX data conversion rules.
        http://msdn.microsoft.com/en-us/library/windows/desktop/dd607323%28v=vs.85%29.aspx
    (2) Data Conversions.
        In "OpenGL ES 2.0 Specification v2.0.25", pp 7-8. Khronos Group, 2010.
    (3) Proper treatment of pixels as integers. A.W. Paeth.
        In "Graphics Gems I", pp 249-256. Morgan Kaufmann, 1990.
    (4) Dirty Pixels. J. Blinn.
        In "Jim Blinn's corner: Dirty Pixels", pp 47-57. Morgan Kaufmann, 1998.

    """
    image = np.asarray(image)
    dtypeobj = np.dtype(dtype)
    dtypeobj_in = image.dtype
    dtype = dtypeobj.type
    dtype_in = dtypeobj_in.type

    if dtype_in == dtype:
        if force_copy:
            image = image.copy()
        return image

    if not (dtype_in in _supported_types and dtype in _supported_types):
        raise ValueError("can not convert %s to %s." % (dtypeobj_in, dtypeobj))

    kind = dtypeobj.kind
    kind_in = dtypeobj_in.kind
    itemsize = dtypeobj.itemsize
    itemsize_in = dtypeobj_in.itemsize

    if kind == "b":
        # to binary image
        if kind_in in "fi":
            sign_loss(dtype_in, dtypeobj)
        prec_loss(dtypeobj_in, dtypeobj)
        return image > dtype_in(dtype_range[dtype_in][1] / 2)

    if kind_in == "b":
        # from binary image, to float and to integer
        result = image.astype(dtype)
        if kind != "f":
            result *= dtype(dtype_range[dtype][1])
        return result

    if kind in "ui":
        imin = np.iinfo(dtype).min
        imax = np.iinfo(dtype).max
    if kind_in in "ui":
        imin_in = np.iinfo(dtype_in).min
        imax_in = np.iinfo(dtype_in).max

    if kind_in == "f":
        if np.min(image) < -1.0 or np.max(image) > 1.0:
            raise ValueError("Images of type float must be between -1 and 1.")
        if kind == "f":
            # floating point -> floating point
            if itemsize_in > itemsize:
                prec_loss(dtypeobj_in, dtypeobj)
            return image.astype(dtype)

        # floating point -> integer
        prec_loss(dtypeobj_in, dtypeobj)
        # use float type that can represent output integer type
        image = np.array(image, _dtype(itemsize, dtype_in, np.float32, np.float64))
        if not uniform:
            if kind == "u":
                image *= imax
            else:
                image *= imax - imin
                image -= 1.0
                image /= 2.0
            np.rint(image, out=image)
            np.clip(image, imin, imax, out=image)
        elif kind == "u":
            image *= imax + 1
            np.clip(image, 0, imax, out=image)
        else:
            image *= (imax - imin + 1.0) / 2.0
            np.floor(image, out=image)
            np.clip(image, imin, imax, out=image)
        return image.astype(dtype)

    if kind == "f":
        # integer -> floating point
        if itemsize_in >= itemsize:
            prec_loss(dtypeobj_in, dtypeobj)
        # use float type that can exactly represent input integers
        image = np.array(image, _dtype(itemsize_in, dtype, np.float32, np.float64))
        if normalise:  # normalise floats by maximum value of int type
            if kind_in == "u":
                image /= imax_in
                # DirectX uses this conversion also for signed ints
                # if imin_in:
                #    np.maximum(image, -1.0, out=image)
            else:
                image *= 2.0
                image += 1.0
                image /= imax_in - imin_in
        return image.astype(dtype)

    if kind_in == "u":
        if kind == "i":
            # unsigned integer -> signed integer
            image = _scale(image, 8 * itemsize_in, 8 * itemsize - 1, dtypeobj_in, dtypeobj)
            return image.view(dtype)
        else:
            # unsigned integer -> unsigned integer
            return _scale(image, 8 * itemsize_in, 8 * itemsize, dtypeobj_in, dtypeobj)

    if kind == "u":
        # signed integer -> unsigned integer
        sign_loss(dtype_in, dtypeobj)
        image = _scale(image, 8 * itemsize_in - 1, 8 * itemsize, dtypeobj_in, dtypeobj)
        result = np.empty(image.shape, dtype)
        np.maximum(image, 0, out=result, dtype=image.dtype, casting="unsafe")
        return result

    # signed integer -> signed integer
    if itemsize_in > itemsize:
        return _scale(image, 8 * itemsize_in - 1, 8 * itemsize - 1, dtypeobj_in, dtypeobj)
    image = image.astype(_dtype2("i", itemsize * 8))
    image -= imin_in
    image = _scale(image, 8 * itemsize_in, 8 * itemsize, dtypeobj_in, dtypeobj, copy=False)
    image += imin
    return image.astype(dtype)
