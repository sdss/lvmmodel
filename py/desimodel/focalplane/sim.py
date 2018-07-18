# See LICENSE.rst for BSD 3-clause license info
# -*- coding: utf-8 -*-
"""
desimodel.focalplane.sim
========================

Tools for generating simulated random distortion fields.
"""

import numpy as np
import astropy.units as u

# Default RMS offset for static centroid offsets used below.
# This value is copied from cell B52 of the Throughput sheet
# from DESI-0347-v13, labeled "FVC corrector optics figure error".
# Define this here to avoid a problem with Sphinx compilation.
try:
    default_offset = 8.0 * u.um
except TypeError:  # pragma: no cover
    default_offset = 8.0


def generate_random_vector_field(rms, exponent, n, seed=None, smoothing=0.02):
    """Generate a pair dx, dy of 2D Gaussian random field.

    The random field is generated with a power spectrum P(k) ~ r ** exponent
    and normalized to the specified RMS value.  Smoothing is applied to minimize
    grid artifacts.

    Parameters
    ----------
    rms : :class:`float` or astropy quantity
        Desired RMS of the generated field values.
    exponent : :class:`float`
        Exponent of the power spectrum scaling with radius.
    n : :class:`int`
        Size of the generated array along each axis.
    seed : :class:`int`
        Random number seed to use. Generated fields should be portable
        across python versions and platforms.
    smoothing : :class:`float`
        Length scale for smoothing the generated field expressed
        as a fraction of the full width of the field.  Implemented
        as a Gaussian convolution.  No smoothing is applied when
        smoothing is zero.

    Returns
    -------
    tuple
        Tuple dx, dy of 2D arrays containing the generated Gaussian
        random field values. Arrays will have the same units as the
        rms parameter, if any.
    """
    A = np.zeros((n, n), complex)
    kvec = np.fft.fftfreq(n)
    kx, ky = np.meshgrid(kvec, kvec, sparse=True, copy=False)
    ksq = kx ** 2 + ky ** 2
    m = ksq > 0
    gen = np.random.RandomState(seed=seed)
    phase = 2 * np.pi * gen.uniform(size=(n, n))
    A[m] = (ksq[m] ** (exponent / 2) * gen.normal(size=(n, n))[m] *
            np.exp(1.j * phase[m]))
    if smoothing > 0:
        var = (n * smoothing) ** 2 / 2
        A[m] *= np.exp(-ksq[m] * var) / (2 * np.pi)
    offsets = np.fft.ifft2(A)

    # Rescale to the specified RMS radial offset.
    rescale = rms / np.sqrt(np.var(offsets.real) + np.var(offsets.imag))
    dx = offsets.real * rescale
    dy = offsets.imag * rescale

    return dx, dy


def generate_random_centroid_offsets(rms_offset=default_offset, seed=123):
    """Generate random centroid offsets.

    Calls :func:`generate_random_vector_field` to generate offsets with
    a power spectrum exponent of -1 in the expected format.

    The arrays in the files ``$DESIMODEL/data/throughput/DESI-0347_static_offset_<n>.fits``
    were generated by this method with seeds n=1,2,3.

    The default RMS offset value is taken from cell B52 of the Throughput sheet
    from DESI-0347-v13, labeled "FVC corrector optics figure error".

    Parameters
    ----------
    rms_offset : :class:`astropy.Quantity` instance.
        RMS that the generated offsets should have, including units.
    seed : :class:`int`
        Random number seed to use. Generated offsets should be portable
        across python versions and platforms.

    Returns
    -------
    tuple
        Tuple dx, dy of centroid offset arrays with units.
    """
    return generate_random_vector_field(
        rms_offset, exponent=-1.0, n=256, seed=seed, smoothing=0.02)

