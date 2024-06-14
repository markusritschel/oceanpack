# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-14
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
import logging
import numpy as np


log = logging.getLogger(__name__)


def convert_coordinates(x):
    """Convert coordinates from 'ddmm.mmmm' format into 'dd.dddd'.

    Example
    -------
    >>> x = (12.0, 45.5)
    >>> decimal_degrees(x)
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

    return salinity


