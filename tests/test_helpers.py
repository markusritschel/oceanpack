# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-12
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
import numpy as np
import pandas as pd
import pytest

from oceanpack.utils.helpers import (_split_degrees_minutes, convert_coordinates,
                                     compute_salinity, order_of_magnitude,
                                     pressure2atm, temperature2K,
                                     find_nearest, centered_bins,
                                     fugacity, set_nonoperating_to_nan,
                                     temperature_correction)


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

    assert np.all(bins == np.arange(-90.5, 91, 1)), "Bins don't match!"
    assert len(bins) == len(x) + 1, "Bin edges must be one more than there are labels"


def test_temperature_correction_takahashi2009():
    """Reference value computed by hand from Takahashi et al. (2009), temperatures in °C:

        exp(0.0433*(15 - 20) - 4.35e-5*(15² - 20²))
      = exp(-0.2165 + 0.0076125) = exp(-0.2088875) = 0.81148652...
      400 µatm * 0.81148652 = 324.594609 µatm
    """
    corrected = temperature_correction(400.0, T_out=15.0, T_in=20.0)

    assert np.isclose(corrected, 324.5946091, rtol=1e-9), \
        "Takahashi (2009) temperature correction does not match the reference value"
    # cooling by 5 K must lower pCO2 by ~4 %/K — the published rule of thumb is 4.23 %/K at
    # the derivative, 4.09 %/K averaged over this span once the T² term is included
    assert 0.039 < (1 - (corrected/400.0)**(1/5)) < 0.043


def test_temperature_correction_takahashi1993():
    """exp(0.0423*(15 - 20)) = exp(-0.2115) = 0.80936928...; 400 * that = 323.747712 µatm"""
    corrected = temperature_correction(400.0, T_out=15.0, T_in=20.0, method='Takahashi1993')

    assert np.isclose(corrected, 323.7477124, rtol=1e-9), \
        "Takahashi (1993) temperature correction does not match the reference value"


def test_temperature_correction_is_directional():
    """Warming raises pCO2, cooling lowers it, and T_out == T_in leaves the value untouched."""
    assert temperature_correction(400.0, T_out=25.0, T_in=20.0) > 400.0
    assert temperature_correction(400.0, T_out=15.0, T_in=20.0) < 400.0
    assert temperature_correction(400.0, T_out=20.0, T_in=20.0) == 400.0


def test_temperature_correction_rejects_unknown_method():
    with pytest.raises(IOError, match="Unknown method"):
        temperature_correction(400.0, T_out=15.0, T_in=20.0, method='Takahashi2029')


def test_fugacity_reference_value():
    """Reference value computed by hand from Weiss (1974) / Dickson et al. (2007), SOP 5,
    for pCO2 = 400 µatm, xCO2 = 400 ppm, p_equ = 1 atm and SST = 25 °C (298.15 K):

        B(CO2,T) = -1636.75 + 12.0408*T - 0.0327957*T² + 3.16528e-5*T³ = -123.19517 cm³/mol
        δ(CO2,T) = 57.7 - 0.118*T                                     =   22.51830 cm³/mol
        A        = p_equ * (B + 2*δ*(1 - 400e-6)²)                    =  -78.19459 cm³·atm/mol
        R*T      = 82.05736608 * 298.15                               = 24465.30 cm³·atm/mol
        fCO2     = 400 * exp(A / (R*T)) = 400 * 0.99680897 = 398.723589 µatm

    B(25 °C) = -123.2 cm³/mol reproduces the value published by Weiss (1974), which is what
    makes this an independent check rather than a restatement of the implementation.
    """
    f = fugacity(400.0, p_equ=1.0, SST=25.0, xCO2=400.0)

    assert np.isclose(f, 398.7235891, rtol=1e-8), \
        "Fugacity does not match the Weiss (1974) virial reference value"


def test_fugacity_is_a_small_negative_correction():
    """Near 1 atm the fugacity sits ~0.3 % below the partial pressure (Dickson SOP 5)."""
    for sst in (0.0, 13.0, 25.0):
        f = fugacity(400.0, p_equ=1.0, SST=sst)
        assert 0.995 < f/400.0 < 0.998, f"fCO2/pCO2 = {f/400.0} is outside the expected range"


def test_fugacity_accepts_pressure_in_mbar_and_pascal():
    """p_equ is normalised to atm internally, so the unit it is passed in must not matter."""
    reference = fugacity(400.0, p_equ=1.0, SST=13.0)

    assert np.isclose(fugacity(400.0, p_equ=1013.25, SST=13.0), reference, rtol=1e-12)
    assert np.isclose(fugacity(400.0, p_equ=101325.0, SST=13.0), reference, rtol=1e-12)


def test_fugacity_xCO2_term_is_a_second_order_effect():
    """Omitting xCO2 drops the (1 - xCO2)² factor — a common simplification in the
    literature, and worth well under 0.01 µatm at oceanic concentrations."""
    with_x = fugacity(400.0, p_equ=1.0, SST=13.0, xCO2=400.0)
    without_x = fugacity(400.0, p_equ=1.0, SST=13.0)

    assert with_x != without_x
    assert abs(with_x - without_x) < 0.01


def _status_frame(status_values):
    index = pd.date_range("2019-05-09 13:00", periods=len(status_values), freq="1min")
    return pd.DataFrame({"CO2": 320.0, "STATUS": status_values}, index=index)


def test_set_nonoperating_to_nan_keeps_fully_operational_data():
    """STATUS == 5 throughout means there is no non-operating phase to mask; the early
    return must leave every value in place (it used to raise on an empty zip)."""
    df = _status_frame([5] * 60)

    result = set_nonoperating_to_nan(df, col="CO2", status_var="STATUS", buffer="20min")

    assert result["CO2"].notna().all()


def test_set_nonoperating_to_nan_masks_phase_plus_buffer():
    """A calibration phase (STATUS != 5) and the following buffer must be masked."""
    df = _status_frame([5] * 20 + [1] * 5 + [5] * 35)

    result = set_nonoperating_to_nan(df, col="CO2", status_var="STATUS", buffer="10min")

    assert result["CO2"].iloc[:20].notna().all(), "data before the phase must survive"
    assert result["CO2"].iloc[20:25].isna().all(), "the non-operating phase must be masked"
    assert result["CO2"].iloc[25:35].isna().all(), "the buffer after the phase must be masked"
    assert result["CO2"].iloc[35:].notna().all(), "data past the buffer must survive"


