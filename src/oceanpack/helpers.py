#!/usr/bin/env python
# -*- coding utf-8 -*-
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  kontakt@markusritschel.de
# Date:   23/04/2020
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
from __future__ import absolute_import, division, print_function, with_statement

import logging
from copy import copy
import filecmp
import numpy as np
import pandas as pd

from functools import wraps as _wraps

logger = logging.getLogger(__name__)

def __dm_split(x):
    """Split degrees and minutes from 'ddmm.mmmm' format to ('dd', 'mm.mmmm').
    This is a helper function for converting (GPS) coordinates.

    Example
    -------
    >>> x = 1245.5000
    >>> __dm_split(x)
    (12.0, 45.5)
    """
    degrees = x // 100
    minutes = x % 100

    return degrees, minutes


def decimal_degrees(x):
    """Convert coordinates from 'ddmm.mmmm' format into 'dd.dddd'.

    Example
    -------
    >>> x = (12.0, 45.5)
    >>> decimal_degrees(x)
    array([0.2       , 0.75833333])
    """
    sign = np.sign(x)
    x = np.abs(x)
    degrees, minutes = __dm_split(x)
    return sign * (degrees + minutes / 60)


# TODO: compare with "1978 Practical Salinity Scale Equations, from IEEE Journal of Oceanic Engineering, Vol. OE-5, No. 1, January 1980, page 14"
def cond2sal(C, T, p):
    """Compute salinity from conductivity, according to :cite:t:`lewis_practical_1981`.
    
    Example
    -------
    >>> cond2sal(C=52, T=25, p=1013)
    34.20810771080768
    """
    p = pressure2mbar(p) / 100  # convert hPa (mbar) -> dbar
    T = temperature2C(T)

    a0 = 0.008
    a1 = -0.1692
    a2 = 25.3851
    a3 = 14.0941
    a4 = -7.0261
    a5 = 2.7081

    b0 = 0.0005
    b1 = -0.0056
    b2 = -0.0066
    b3 = -0.0375
    b4 = 0.0636
    b5 = -0.0144

    c0 = 6.766097e-1
    c1 = 2.00564e-2
    c2 = 1.104259e-4
    c3 = -6.9698e-7
    c4 = 1.0031e-9

    A1 = 2.070e-5
    A2 = -6.370e-10
    A3 = 3.989e-15
    B1 = 3.426e-2
    B2 = 4.464e-4
    B3 = 4.215e-1
    B4 = -3.107e-3

    R = C / 42.914  # units: mS/cm
    # TODO: check input units of Conductivity! "If you are working in conductivity units of Siemens/meter (S/m), multiply your conductivity values by 10 before using the PSS 1978 equations. "
    # TODO: maybe use units from log file for auto-conversion and print a hint or so (this could be already done during the read routine)

    rT = c0 + c1*T + c2*T**2 + c3*T**3 + c4*T**4

    alpha = (A1*p + A2*p**2 + A3*p**3) / (1 + B1*T + B2*T**2 + B3*R + B4*T*R)

    Rp = 1 + alpha

    RT = R / (rT*Rp)

    k = 0.0162  # TODO: check sign! +/-?

    xi = np.sqrt(RT)
    psi = b0 + b1*xi + b2*xi**2 + b3*xi**3 + b4*xi**4 + b5*xi**5
    dSal = psi*(T - 15) / (1 + k*(T - 15))

    salinity = a0 + a1*xi + a2*xi**2 + a3*xi**3 + a4*xi**4 + a5*xi**5 + dSal

    return salinity


def order_of_magnitude(x):
    """Determine the order of magnitude of the numeric input (`int`, `float`, :meth:`numpy.array` or :meth:`pandas.Series`).

    Examples
    --------
    >>> order_of_magnitude(11)
    array(1.)
    >>> order_of_magnitude(234)
    array(2.)
    >>> order_of_magnitude(1)
    array(0.)
    >>> order_of_magnitude(.15)
    array(-1.)
    >>> order_of_magnitude(np.array([24.13, 254.2]))
    array([1., 2.])
    >>> order_of_magnitude(pd.Series([24.13, 254.2]))
    array([1., 2.])
    """
    x = np.asarray(x)
    if np.all(x == 0):
        return None
    x = x[x != 0]
    oom = np.floor(np.log10(x))
    # oom = (np.int32(np.log10(np.abs(x))) + 1)
    return np.array(oom)


def roundup(x, to=1):
    return np.ceil(x / to) // 1*to


def pressure2atm(p):
    """Convert pressure given in hPa, Pa or atm into atm.

    Examples
    --------
    >>> pressure2atm(1013.25)
    1.0
    >>> pressure2atm(101325)
    1.0
    >>> pressure2atm(2)
    2
    >>> pressure2atm(pd.Series([1013.25, 1024.0]))
    0    1.000000
    1    1.010609
    dtype: float64
    """
    p = copy(p)
    if 2 <= np.nanmedian(np.rint(order_of_magnitude(p))) <= 3:
        p /= 1013.25
        logger.info("Pressure is assumed to be in hPa and was converted to atm")
    elif 4 <= np.nanmedian(np.rint(order_of_magnitude(p))) <= 5:
        p /= 101325
        logger.info("Pressure is assumed to be in Pa and was converted to atm")
    elif -1 <= np.nanmedian(np.rint(order_of_magnitude(p))) <= 1:
        logger.info("Pressure is assumed to be already in atm (no conversion)")
    else:
        raise IOError("Pressure must be given in hPa, Pa or atm")
    return p


def pressure2mbar(p):
    """Convert pressure given in hPa, Pa or atm into mbar (or hPa).

    Examples
    --------
    >>> pressure2mbar(1013)
    1013
    >>> pressure2mbar(101300)
    1013.0
    >>> pressure2mbar(1.0)
    1013.25
    >>> pressure2mbar(pd.Series([1.013, 2.034]))
    0    1026.42225
    1    2060.95050
    dtype: float64
    """
    p = copy(p)
    if 2 <= np.nanmedian(np.rint(order_of_magnitude(p))) <= 3:
        logger.info("Pressure is assumed to be already in mbar (no conversion)")
    elif 4 <= np.nanmedian(np.rint(order_of_magnitude(p))) <= 5:
        p /= 100
        logger.info("Pressure is assumed to be in Pa and was converted to mbar (hPa)")
    elif -1 <= np.nanmedian(np.rint(order_of_magnitude(p))) <= 1:
        logger.info("Pressure is assumed to be in atm and was converted to mbar (hPa)")
        p *= 1013.25
    else:
        raise IOError("Pressure must be given in hPa, Pa or atm")
    return p


def temperature2K(T):
    """Convert temperatures given in °C into Kelvin.
    If `T` is a :meth:`pandas.Series` object, only values larger than 200 are converted. All others are expected to be
    already in Kelvin.

    Examples
    --------
    >>> temperature2K(10)
    283.15
    """
    T = copy(T)
    if isinstance(T, pd.Series):
        if len(T[T > 200]) != 0:
            logger.warning("Some values seem to be already in Kelvin")
        # TODO: do this in a better way
        T.loc[T < 200] += 273.15
    elif T < 200:
        T += 273.15
    return T


def temperature2C(T):
    """Convert temperatures given in Kelvin into °C.
    If `T` is a :meth:`pandas.Series` object, only values less than 200 are converted. All others are expected to be
    already in °C.

    Examples
    --------
    >>> temperature2C(283.15)
    10.0
    """
    T = copy(T)
    if isinstance(T, pd.Series):
        T.loc[T > 200] -= 273.15
    elif T > 200:
        T -= 273.15
    return T


def ppm2uatm(xCO2,p_equ,input='wet',T=None,S=None):
    """Convert mole fraction concentration (in ppm) into partial pressure (in µatm) following :cite:t:`dickson_guide_2007`

    .. math::
        pCO_2 = xCO_2 \\cdot p_\\text{equ}

    Parameters
    ----------
    xCO2: float or pd.Series
        The measured CO2 concentration (in ppm)
    p_equ: float or pd.Series
        The measured pressure (in hPa, Pa or atm) at the equilibrator (hint: you might want to smoothen your time series)
    input: str [default: "wet"]
        Either "wet" or "dry", specifying the type of air, in which the concentration is measured.
        If the CO2 concentration is measured in dry air, one must correct for the water vapor pressure.
        In this case, make sure to also provide T (temperature in Kelvin) and S (salinity in PSU) as arguments.
    T: float or pd.Series [default: None]
        Temperature in Kelvin (needs to be provided if xCO2 is measured in dry air)
    S: float or pd.Series [default: None]
        Salinity in PSU (needs to be provided if xCO2 is measured in dry air)
    """
    # Pa or hPa -> atm
    p_equ = pressure2atm(p_equ)
    
    if input == "wet":
        pH2O = 0
    elif input == "dry":
        pH2O = water_vapor_pressure(T, S)
    else:
        raise IOError("Input must be either 'dry' or 'wet'.")
    
    pCO2_wet_equ = xCO2 * (p_equ - pH2O)
    
    return pCO2_wet_equ


def water_vapor_pressure(T, S):
    """Compute the water vapor pressure by means of the temperature [K] and the salinity [PSU]
    following :cite:t:`weiss_nitrous_1980`.

    Parameters
    ----------
    S: float or pd.Series
        Salinity in PSU
    T: float or pd.Series
        Temperature (°C gets converted into Kelvin)
    """
    # °C -> K
    T = temperature2K(T)

    pH2O = np.exp(24.4543 - 67.4509*(100/T) - 4.8489*np.log(T/100) - 0.000544*S)
    return pH2O


def temperature_correction(CO2, T_out=None, T_in=None, method='Takahashi2009', **kwargs):
    """Apply a temperature correction. This might be necessary when the temperatures at the water intake 
    (often outside the ship) and at the OceanPack CTD differ. The correction used here follows :cite:t:`takahashi_climatological_2009`:

    .. math::
        {(xCO_2)}_{SST} = {(xCO_2)}_{T_\\text{equ}} \\cdot \\exp{\\Big(0.0433\\cdot(SST - T_\\text{equ}) - 4.35\\times 10^{-5}\\cdot(SST^2 - T_\\text{equ}^2)\\Big)}

    for correcting the temperature at the equilibrator :math:`T_\\text{equ}` to the SST.

    `CO2` can be one out of [xCO2 (mole fraction), pCO2 (partial pressure), fCO2 (fugacity)].

    Parameters
    ----------
    CO2: float or pd.Series
        The CO2 variable, which shall be corrected for temperature differences.
        Can be one out of the following:
        - xCO2 (mole fraction in ppm)
        - pCO2 (partial pressure in hPa, Pa, atm or µatm)
        - fCO2 (fugacity in hPa, Pa, atm or µatm)
    T_out: float or pd.Series
        The temperature towards which the data shall be corrected. Typically, the in-situ temperature (°C or K), at which the water was sampled.
    T_in: float or pd.Series
        The temperature from which the data shall be corrected. Typically, the temperature (°C or K) at the equilibrator, at which the water was measured.
    method: str
        Either "Takahashi2009" or "Takahashi1993", describing the method of the respectively published paper by Takahashi et al.
    """
    if T_out is None: T_out = kwargs.pop('T_insitu')
    if T_in is None: T_in = kwargs.pop('T_equ')
    if method=="Takahashi2009":
        CO2_out = CO2 * np.exp(0.0433*(T_out - T_in) - 4.35e-5*(T_out**2 - T_in**2))
    elif method=="Takahashi1993":
        CO2_out = CO2 * np.exp(0.0423*(T_out - T_in))
    else:
        raise IOError("Unknown method for temperature conversion.")

    return CO2_out


def fugacity(pCO2, p_equ, SST, xCO2=None):
    """Calculate the fugacity of CO2. Can be done either before or after a :func:`.temperature correction`.
    The formulas follow :cite:t:`dickson_guide_2007`, mainly SOP 5, Chapter 8. "Calculation and expression of results"

    .. math::
       (fCO_2)^\\text{wet}_\\text{SST} = (pCO_2)^\\text{wet}_\\text{SST} \\cdot
            \\exp{\\Big(p_\\text{equ}\\cdot\\frac{\\left[ B(CO_2,SST) + 2\\,\\left(1-(xCO_2)^\\text{wet}_{SST}\\right)^2 \\, \\delta(CO_2,SST)\\right]}{R\\cdot SST}\\Big)}

    where :math:`SST` is the sea surface temperature in K, :math:`R` the gas constant and :math:`B(CO_2,SST)` and 
    :math:`\delta(CO_2,SST)` are the virial coefficients for :math:`CO_2` (both in :math:`\\text{cm}^3\\,\\text{mol}^{-1}`), which are given as

    .. math::
       B(CO_2,T) = -1636.75 + 12.0408\\,T - 0.0327957\\,T^2 + 0.0000316528\\,T^3

    and

    .. math::
       \\delta(CO_2,T) = 57.7 - 0.188\\,T


    Parameters
    ----------
    pCO2: float or pd.Series
        The partial pressure of CO2 (in µatm).
        Make sure you have converted xCO2 concentration (mole fraction in ppm) into partial pressure (in µatm).
    p_equ: float or pd.Series
        The measured pressure (in hPa, Pa or atm) at the equilibrator (hint: you might want to smoothen your time series)
    SST: float or pd.Series
        The in-situ measurement temperature (in °C or Kelvin)
    xCO2: float or pd.Series (optional)
        CO2 concentration (mole fraction in ppm). If given, the d_CO2 virial coefficient in the numerator in the
        exponential expression is multiplied by (1 - xCO2*1e-6). Else, this term is 1.
    """
    # Pa or hPa -> atm
    p_equ = pressure2atm(p_equ)

    # °C -> K
    SST = temperature2K(SST)

    # respectively in cm³/mol
    B_CO2 = -1636.75 + 12.0408*SST - 3.27957e-2*SST**2 + 3.16528e-5*SST**3
    d_CO2 = 57.7 - 0.118*SST

    # gas constant
    R = 8.2057366080960e-2 	        # L⋅atm⋅K−1⋅mol−1
    R *= 1000                       # cm³⋅atm⋅K−1⋅mol−1

    if xCO2 is None:
        x_c = 1
    else:
        x_c = (1 - xCO2*1e-6)       # can be and is often neglected in literature

    A = p_equ*(B_CO2 + 2 * d_CO2 * x_c**2)
    B = R*SST
    f = pCO2 * np.exp(A / B)        # same unit as pCO2 (µatm)

    return f


def set_nonoperating_to_nan(data, col='CO2', shift='30min', status_var='ANA_state'):
    """Set all values from each period, which is ranging from the begin of a certain phase (indicated by the ANA_state flag)
    to the end of the phase, plus a given shift to NaN."""

    grouped_by_status = data.groupby((data[status_var] != data[status_var].shift()).cumsum())

    # get the first and last index of all periods which are not in operating status
    phase_start, phase_end = zip(*[(g.index[0], g.index[-1]) for i, g in grouped_by_status if g[status_var].unique() != 5])

    phase_start = pd.to_datetime(phase_start)
    phase_end = pd.to_datetime(phase_end)

    # add shift to the end
    phase_end_shift = phase_end + pd.to_timedelta(shift)

    # data['takeOut'] = np.repeat(0, len(data))

    # set all values in the respective column(s) to NaN
    for i, j in zip(phase_start, phase_end_shift):
        data.loc[i:j, col] = np.nan
        # data.loc[i:j, 'takeOut'] = True

    return data


def nearest(items: list, pivot: float) -> float:
    """Find the element inside `items` that is closest to the `pivot` element.

    Examples
    --------
    >>> nearest(np.array([2,4,5,7,9,10]), 4.6)
    5
    """
    return min(items, key=lambda x: abs(x - pivot))


def centered_bins(x):
    """Create centered bin boundaries from a given array with the values of the array as centers.

    Example
    -------
    >>> x = np.arange(-3, 4)
    >>> x
    array([-3, -2, -1,  0,  1,  2,  3])
    >>> centered_bins(x)
    array([-3.5, -2.5, -1.5, -0.5,  0.5,  1.5,  2.5,  3.5])
    """
    x = np.array(x)
    x = np.append(x, x[-1] + np.diff(x[-2:]))

    differences = np.gradient(x, 2)

    return x - differences


def grid_dataframe(points, vals, xi, export_grid=False):
    """Bin the values with `points` coordinates by the given target coordinates `xi` and put the average of each bin
    onto the target grid.

    Parameters
    ----------
    points : tuple[list, list]
        A tuple `(x, y)` consisting of two lists holding the respective x and y coordinates of the source data.
    values : list
        The actual data values that are meant to be regridded
    xi : tuple[list, list]
        A tuple `(x, y)` consisting of two lists holding the target coordinates.

    Example
    -------
    >>> df = pd.DataFrame({'lon': np.linspace(0, 40, 100),
    >>>                    'lat': np.sin(np.linspace(0, 3, 100))*10 + 40,
    >>>                    'data': np.linspace(240,200,100)})
    >>> xi = np.linspace(-5, 45, 40)
    >>> yi = np.linspace(35, 53, 50)
    >>> gridded = grid_dataframe((df.lon, df.lat), df.data, (xi, yi))
    >>> plt.pcolormesh(xi, yi, gridded, shading='auto', cmap='Greens_r')
    >>> plt.scatter(df.lon, df.lat, c=df.data, marker='.', lw=.75, cmap='Reds', label='raw data')
    >>> plt.xlabel('Longitude')
    >>> plt.ylabel('Latitude')
    >>> plt.legend()
    >>> plt.show()

    .. image:: ../_static/grid_dataframe_plot.png
       :width: 450px
       :alt: eample plot
       :align: left
    """
    x, y = points
    X, Y = xi
    xx, yy = np.meshgrid(*xi)
    target = np.empty(xx.shape) * np.nan

    # flatten target and grid components
    xx_ = xx.ravel()
    yy_ = yy.ravel()
    target_ = target.ravel()

    df = pd.DataFrame({'vals': vals, 'x': x, 'y': y})

    df['x_binned'] = pd.cut(df.x, bins=centered_bins(X), labels=X)
    df['y_binned'] = pd.cut(df.y, bins=centered_bins(Y), labels=Y)

    df['points'] = df[['x_binned', 'y_binned']].apply(tuple, axis=1)

    df_ = df.groupby('points').mean()

    for idx, row in df_.iterrows():
        target_[(xx_ == idx[0]) & (yy_ == idx[1])] = row.vals

    target = target_.reshape(xx.shape)

    return (xx, yy, target) if export_grid else target


def check_input_for_duplicates(func):
    """A decorator that checks a list of file paths (the first and only argument of the wrapped function) for duplicates.
    For example, when you call the function :func:`oceanpack.io_routines.read_oceanpack` with a list of many files, the
    decorator checks the input for duplicates before the read-in routine actually processes the files.
    The decorator makes use of the :func:`os.stat` signatures (file type, size, and modification time) to compare files
    pair-wise.

    Detected duplicates are dropped from the list such that the function can deal with the cleaned-up list.
    """
    # The functools._wraps decorator ensures that `func` can still be parsed by Sphinx. Usually, decorated functions can not be parsed by Sphinx.
    @_wraps(func)
    def wrapper(file_list):
        if not isinstance(file_list, list) or len(file_list) <= 1:
            return func(file_list)
        remove_idx = []
        for i, f1 in enumerate(file_list):
            for f2 in file_list[i + 1:]:
                res = filecmp.cmp(f1,f2, shallow=True)  # Note: shallow=False would compare the actual file contents
                if res:
                    remove_idx.append(i)
        filtered_file_list = [i for j, i in enumerate(file_list) if j not in remove_idx]
        remove_files = [i for j, i in enumerate(file_list) if j in remove_idx]
        if remove_idx:
            logger.info("Found and ignored %s duplicates in file list.", len(remove_idx))
            for entry in remove_files:
                logger.debug("Ignored %s", entry)
        return func(filtered_file_list)

    return wrapper

