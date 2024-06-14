# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-12
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
import numpy as np

from oceanpack.utils.helpers import (_split_degrees_minutes, convert_coordinates, 
                                     compute_salinity, order_of_magnitude,
                                     pressure2atm, temperature2K, 
                                     find_nearest, centered_bins)


def test_coordinate_splitting():
    coord = 4623.4231
    assert _split_degrees_minutes(coord) == (46, 23.423099999999977), "Coordinate conversion is erroneous"
    assert convert_coordinates(coord) == 46.390385, "Coordinate conversion is erroneous"


def test_cond2sal_converter():
    # example values from a CTD
    salinity_ctd = 34.3684
    conductivity_ctd = 35.67560
    salinity_computed = compute_salinity(C=conductivity_ctd, T=8.0583, p=0.357)

    assert np.isclose(salinity_ctd, salinity_computed, rtol=1e-4), \
        "The calculated value deviates too much from the true value!" \
        "Relative tolerance exceeds 1e-4."


def test_order_of_magnitude():
    assert order_of_magnitude(0) == None
    assert order_of_magnitude(2) == 0
    assert order_of_magnitude(10) == 1
    assert order_of_magnitude(300) == 2
    assert order_of_magnitude(988) == 2
    assert order_of_magnitude(1234) == 3


def test_pressure2atm():
    assert pressure2atm(1018) == 1.004687885516901, "Conversion from hPa to atm not correct"
    assert pressure2atm(101800) == 1.004687885516901, "Conversion from Pa to atm not correct"
    assert pressure2atm(1.005) == 1.005, "atm units should be passed through"


def test_temperature2K():
    assert temperature2K(13) == 286.15, "Temperature correction not correct"
    assert temperature2K(286.15) == 286.15, "Temperature in Kelvin should not be altered"


def test_find_nearest():
    items = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    pivot1 = 4.2
    pivot2 = 4.8

    assert find_nearest(items, pivot1) == 4, "Should find 4 as the nearest element for 4.2"
    assert find_nearest(items, pivot2) == 5, "Should find 5 as the nearest element for 4.8"


def test_bin_creator():
    x = np.arange(-90, 91)
    bins = centered_bins(x)

    assert np.alltrue(bins == np.arange(-90.5, 91, 1)), "Bins don't match!"
    assert len(bins) == len(x) + 1, "Bin edges must be one more than there are labels"


