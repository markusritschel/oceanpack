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

from copy import copy

import numpy as np
import pandas as pd


def __dm_split(x):
    """Split 'ddmm.mmmm' format in ('dd', 'mm.mmmm').
    >>> x = 1245.5000
    >>> __dm_split(x)
    (12.0, 45.5)
    """
    degrees = x // 100
    minutes = x % 100

    return degrees, minutes


def decimal_degrees(x):
    """Convert dd, mm.mmmm tuple into dd.dddd
    >>> x = (12.0, 45.5)
    >>> decimal_degrees(x)
    array([0.2       , 0.75833333])
    """
    sign = np.sign(x)
    x = np.abs(x)
    degrees, minutes = __dm_split(x)
    return sign*(degrees + minutes / 60)


def cond2sal(C, T, p):
    """Compute salinity from conductivity.
    According to Lewis and Perkin (1978): "The practical salinity scale 1978: conversion of existing data".
    >>> cond2sal(C=52, T=25, p=1013)
    34.206423378894655
    """
    p = p / 100  # convert hPa -> dbar

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

    c0 = 6.766098e-1
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

    rT = c0 + c1*T + c2*T**2 + c3*T**3 + c4*T**4

    alpha = (A1*p + A2*p**2 + A3*p**3) / (1 + B1*T + B2*T**2 + B3*R + B4*T*R)

    Rp = 1 + alpha

    RT = R / (rT*Rp)

    xi = np.sqrt(RT)
    psi = b0 + b1*xi + b2*xi**2 + b3*xi**3 + b4*xi**4 + b5*xi**5
    dSal = psi*(T - 15) / (1 - 0.0162*(T - 15))

    salinity = a0 + a1*xi + a2*xi**2 + a3*xi**3 + a4*xi**4 + a5*xi**5 + dSal

    return salinity


def order_of_magnitude(x, roundto=None):
    """Determine the order of magnitude of the numeric input (int, float or pd.Series).
    >>> order_of_magnitude(11)
    2.0
    >>> order_of_magnitude(234)
    3.0
    >>> order_of_magnitude(1, roundto=1)
    1.0
    >>> order_of_magnitude(.15)
    -0.0
    """
    if roundto:
        x = roundup(x, roundto)
        x += 1e-5  # to avoid for example 10 being of magnitude 0
    return np.ceil(np.log10(x))


def roundup(x, to=1):
    return np.ceil(x / to) // 1*to


def pressure2atm(p):
    """Converts pressure given in hPa, Pa or atm into atm"""
    p = copy(p)
    if np.ceil(order_of_magnitude(p).mean()) == 4:
        p /= 1013.25
    elif np.ceil(order_of_magnitude(p).mean()) == 6:
        p /= 101325
    elif -1 <= np.ceil(order_of_magnitude(p).mean()) <= 1:
        pass
    else:
        raise IOError("Pressure must be given in hPa, Pa or atm")
    return p


def temperature2K(T):
    """Converts temperature given in °C into Kelvin"""
    T = copy(T)
    if isinstance(T,pd.Series):
        T.loc[order_of_magnitude(T) < 3] += 273.15
    elif order_of_magnitude(T) < 3:
        T += 273.15
    return T


def ppm2µatm(xCO2,p_equ,input='wet',T=None,S=None):
    """Converts a mole fraction concentration (in ppm) into partial pressure (in µatm) following Dickson et al. (2007)

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

    if input=="wet":
        pH2O = 0
    elif input== "dry":
        pH2O = water_vapor_pressure(T,S)

    pCO2_wet_equ = xCO2 * (p_equ - pH2O)

    return pCO2_wet_equ


def water_vapor_pressure(T, S):
    """Computes the water vapor pressure by means of the temperature [K] and the salinity [PSU]
    following Weiss and Price (1980).

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


def temperature_correction(xCO2, T_insitu, T_equ, method='Takahashi2009'):
    """xCO2 can be one out of [xCO2 (mole fraction), pCO2 (partial pressure), fCO2 (fugacity)]

    Parameters
    ----------
    xCO2: float or pd.Series
        The CO2 variable, which shall be corrected for temperature differences.
        Can be one out of the following:
        - xCO2 (mole fraction in ppm)
        - pCO2 (partial pressure in hPa, Pa, atm or µatm)
        - fCO2 (fugacity in hPa, Pa, atm or µatm)
    T_insitu: float or pd.Series
        The in-situ temperature (°C or K), at which the water was sampled
    T_equ: float or pd.Series
        The temperature (°C or K) at the equilibrator, at which the water was measured
    method: str
        Either "Takahashi2009" or "Takahashi1993", describing the method of the respectively published paper by Takahashi et al.
    """
    if method=="Takahashi2009":
        xCO2_out = xCO2 * np.exp(0.0433*(T_insitu - T_equ) - 4.35e-5*(T_insitu**2 - T_equ**2))
    elif method=="Takahashi1993":
        xCO2_out = xCO2 * np.exp(0.0423*(T_insitu - T_equ))

    return xCO2_out


def fugacity(pCO2,p_equ,SST,xCO2=None):
    """Calculate the fugacity of CO2. Can be done either before or after a temperature correction.
    The formulas follow Dickson et al. (2007), mainly SOP 5, Chapter 8. "Calculation and expression of results"

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
