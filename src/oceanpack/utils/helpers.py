# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-14
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
import logging
import numpy as np
import pandas as pd
import xarray as xr
from copy import copy


log = logging.getLogger(__name__)


def convert_coordinates(x):
    """Convert coordinates from 'ddmm.mmmm' format into 'dd.dddd'.

    Example
    -------
    >>> x = (12.0, 45.5)
    >>> convert_coordinates(x)
    array([0.2       , 0.75833333])
    """
    sign = np.sign(x)
    x = np.abs(x)
    degrees, minutes = _split_degrees_minutes(x)
    return sign * (degrees + minutes / 60)


def _split_degrees_minutes(x):
    """Split degrees and minutes from 'ddmm.mmmm' format to ('dd', 'mm.mmmm').
    This is a helper function for converting (GPS) coordinates.

    Example
    -------
    >>> x = 1245.5000
    >>> _split_degrees_minutes(x)
    (12.0, 45.5)
    """
    degrees = x // 100
    minutes = x % 100

    return degrees, minutes


def compute_salinity(C, T, p):
    """Compute salinity from conductivity, according to :cite:t:`lewis_practical_1981`.
    
    Example
    -------
    >>> compute_salinity(C=52, T=25, p=1013)
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
    # maybe use units from log file for auto-conversion and print a hint or so (this could be already done during the read routine)

    rT = c0 + c1*T + c2*T**2 + c3*T**3 + c4*T**4

    alpha = (A1*p + A2*p**2 + A3*p**3) / (1 + B1*T + B2*T**2 + B3*R + B4*T*R)

    Rp = 1 + alpha

    RT = R / (rT*Rp)

    k = 0.0162  # TODO: check sign! +/-?

    ξ = np.sqrt(RT)
    ψ = b0 + b1*ξ + b2*ξ**2 + b3*ξ**3 + b4*ξ**4 + b5*ξ**5
    dSal = ψ*(T - 15) / (1 + k*(T - 15))

    salinity = a0 + a1*ξ + a2*ξ**2 + a3*ξ**3 + a4*ξ**4 + a5*ξ**5 + dSal

    return float(salinity)


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
        log.info("Pressure is assumed to be in hPa and was converted to atm")
    elif 4 <= np.nanmedian(np.rint(order_of_magnitude(p))) <= 5:
        p /= 101325
        log.info("Pressure is assumed to be in Pa and was converted to atm")
    elif -1 <= np.nanmedian(np.rint(order_of_magnitude(p))) <= 1:
        log.info("Pressure is assumed to be already in atm (no conversion)")
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
        log.info("Pressure is assumed to be already in mbar (no conversion)")
    elif 4 <= np.nanmedian(np.rint(order_of_magnitude(p))) <= 5:
        p /= 100
        log.info("Pressure is assumed to be in Pa and was converted to mbar (hPa)")
    elif -1 <= np.nanmedian(np.rint(order_of_magnitude(p))) <= 1:
        log.info("Pressure is assumed to be in atm and was converted to mbar (hPa)")
        p *= 1013.25
    else:
        raise IOError("Pressure must be given in hPa, Pa or atm")
    return p


def order_of_magnitude(x):
    """Determine the order of magnitude of the numeric input (:obj:`int`, :obj:`float`, :obj:`numpy.array` or :obj:`pandas.Series`).

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
    return np.array(oom).squeeze()




def temperature2K(T):
    """Convert temperatures given in °C into Kelvin.
    If `T` is a :obj:`pandas.Series` object, only values larger than 200 are converted. 
    All others are expected to be already in Kelvin.

    Examples
    --------
    >>> temperature2K(10)
    283.15
    """
    T = copy(T)
    if isinstance(T, pd.Series):
        if len(T[T > 200]) != 0:
            log.warning("Some values seem to be already in Kelvin")
        # TODO: do this in a better way
        T.loc[T < 200] += 273.15
    elif T < 200:
        T += 273.15
    return T


def temperature2C(T):
    """Convert temperatures given in Kelvin into °C.
    If `T` is a :obj:`pandas.Series` object, only values greater than 200 are converted. 
    All others are expected to be already in °C.

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
    xCO2: float or pandas.Series
        The measured CO2 concentration (in ppm)
    p_equ: float or pandas.Series
        The measured pressure (in hPa, Pa or atm) at the equilibrator (hint: you might want to smoothen your time series)
    input: str [default: "wet"]
        Either "wet" or "dry", specifying the type of air, in which the concentration is measured.
        If the CO2 concentration is measured in dry air, one must correct for the water vapor pressure.
        In this case, make sure to also provide T (temperature in Kelvin) and S (salinity in PSU) as arguments.
    T: float or pandas.Series [default: None]
        Temperature in Kelvin (needs to be provided if xCO2 is measured in dry air)
    S: float or pandas.Series [default: None]
        Salinity in PSU (needs to be provided if xCO2 is measured in dry air)
    """
    # Pa or hPa -> atm
    p_equ = pressure2atm(p_equ)

    if input == "dry":
        pH2O = compute_water_vapor_pressure(T, S)
    elif input == "wet":
        pH2O = 0
    else:
        raise IOError("Input must be either 'dry' or 'wet'.")

    pCO2_wet_equ = xCO2 * (p_equ - pH2O)
    
    return pCO2_wet_equ


def compute_water_vapor_pressure(T, S):
    """Compute the water vapor pressure by means of the temperature [K] and the salinity [PSU]
    following :cite:t:`weiss_nitrous_1980`.

    Parameters
    ----------
    S: float or pandas.Series
        Salinity in PSU
    T: float or pandas.Series
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
    CO2: float or pandas.Series
        The CO2 variable, which shall be corrected for temperature differences.
        Can be one out of the following:
        - xCO2 (mole fraction in ppm)
        - pCO2 (partial pressure in hPa, Pa, atm or µatm)
        - fCO2 (fugacity in hPa, Pa, atm or µatm)
    T_out: float or pandas.Series
        The temperature towards which the data shall be corrected. Typically, the in-situ temperature (°C or K), at which the water was sampled.
    T_in: float or pandas.Series
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
    """Calculate the fugacity of CO2. Can be done either before or after a :func:`temperature_correction`.
    The formulas follow :cite:t:`dickson_guide_2007`, mainly SOP 5, Chapter 8. "Calculation and expression of results".

    .. math::
       (fCO_2)^\\text{wet}_\\text{SST} = (pCO_2)^\\text{wet}_\\text{SST} \\cdot
            \\exp{\\Big(p_\\text{equ}\\cdot\\frac{\\left[ B(CO_2,SST) + 2\\,\\left(1-(xCO_2)^\\text{wet}_{SST}\\right)^2 \\, \\delta(CO_2,SST)\\right]}{R\\cdot SST}\\Big)}

    where :math:`SST` is the sea surface temperature in K, :math:`R` the gas constant and :math:`B(CO_2,SST)` and 
    :math:`\\delta(CO_2,SST)` are the virial coefficients for :math:`CO_2` (both in :math:`\\text{cm}^3\\,\\text{mol}^{-1}`), which are given as

    .. math::
       B(CO_2,T) = -1636.75 + 12.0408\\,T - 0.0327957\\,T^2 + 0.0000316528\\,T^3

    and

    .. math::
       \\delta(CO_2,T) = 57.7 - 0.188\\,T


    Parameters
    ----------
    pCO2: float or pandas.Series
        The partial pressure of CO2 (in µatm).
        Make sure you have converted xCO2 concentration (mole fraction in ppm) into partial pressure (in µatm).
    p_equ: float or pandas.Series
        The measured pressure (in hPa, Pa or atm) at the equilibrator (hint: you might want to smoothen your time series)
    SST: float or pandas.Series
        The in-situ measurement temperature (in °C or Kelvin)
    xCO2: float or pandas.Series (optional)
        CO2 concentration (mole fraction in ppm). If given, the δ_CO2 virial coefficient in the numerator in the exponential expression is multiplied by (1 - xCO2*1e-6). Else, this term is 1.
    """
    # Pa or hPa -> atm
    p_equ = pressure2atm(p_equ)

    # °C -> K
    SST = temperature2K(SST)

    # respectively in cm³/mol
    B_CO2 = -1636.75 + 12.0408*SST - 3.27957e-2*SST**2 + 3.16528e-5*SST**3
    δ_CO2 = 57.7 - 0.118*SST

    # gas constant
    R = 8.2057366080960e-2 	        # L⋅atm⋅K−1⋅mol−1
    R *= 1000                       # cm³⋅atm⋅K−1⋅mol−1

    if xCO2 is None:
        x_c = 1
    else:
        x_c = (1 - xCO2*1e-6)       # can be and is often neglected in literature

    A = p_equ*(B_CO2 + 2 * δ_CO2 * x_c**2)
    B = R*SST
    f = pCO2 * np.exp(A / B)        # same unit as pCO2 (µatm)

    return f


def set_nonoperating_to_nan(data, col='CO2', shift='30min', status_var='ANA_state'):
    """Set all values from each period, which is ranging from the begin of a certain phase 
    (indicated by the status flag) to the end of the phase, plus a given shift to NaN.
    """

    grouped_by_status = data.groupby((data[status_var] != data[status_var].shift()).cumsum())

    # get the first and last index of all periods which are not in operating status
    phase_start, phase_end = zip(*[(g.index[0], g.index[-1]) for i, g in grouped_by_status if g[status_var].unique() != 5])

    phase_start = pd.to_datetime(phase_start)
    phase_end = pd.to_datetime(phase_end)

    # add shift to the end
    phase_end_shift = phase_end + pd.to_timedelta(shift)

    # set all values in the respective column(s) to NaN
    for i, j in zip(phase_start, phase_end_shift):
        data.loc[i:j, col] = np.nan

    return data


def find_nearest(items: list, pivot: float) -> float:
    """Find the element inside `items` that is closest to the `pivot` element.

    Examples
    --------
    >>> result = find_nearest(np.array([2,4,5,7,9,10]), 4.6)
    >>> int(result)   # Account for type conflicts when testing with pytest
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


def compress_xarray(data: xr.Dataset | xr.DataArray, complevel: int = 5) -> xr.Dataset | xr.DataArray:
    """Compress :class:`xarray.Dataset` or :class:`xarray.DataArray`.
    
    Parameters
    ----------
    data:
        Data to compress.
    complevel:
        Compression level.
    
    Returns
    -------
    xarray.Dataset | xarray.DataArray
        Compressed data.
    """
    compression_dict = dict(zlib=True, complevel=complevel)
    if isinstance(data, xr.Dataset):
        for variable in data:
            data[variable].encoding.update(compression_dict)
    elif isinstance(data, xr.DataArray):
        data.encoding.update(compression_dict)
    return data
