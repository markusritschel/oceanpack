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


