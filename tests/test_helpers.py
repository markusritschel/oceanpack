# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-12
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
import warnings

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from oceanpack.utils.helpers import (
    _split_degrees_minutes,
    centered_bins,
    compress_xarray,
    compute_salinity,
    compute_water_vapor_pressure,
    convert_coordinates,
    find_nearest,
    fugacity,
    order_of_magnitude,
    ppm2uatm,
    pressure2atm,
    pressure2mbar,
    set_nonoperating_to_nan,
    temperature2C,
    temperature2K,
    temperature_correction,
)


def test_split_degrees_minutes_separates_ddmm_format():
    """4623.4231 in DDDMM.MMMM format → 46 degrees and 23.4231 minutes."""
    degrees, minutes = _split_degrees_minutes(4623.4231)
    assert degrees == 46.0
    assert minutes == pytest.approx(23.4231, rel=1e-9)


def test_convert_coordinates_dddmm_to_decimal_degrees():
    """4623.4231 (DDDMM.MMMM) → 46 + 23.4231 / 60 ≈ 46.390385 decimal degrees."""
    assert convert_coordinates(4623.4231) == pytest.approx(46.390385, rel=1e-6)


def test_compute_salinity_matches_ctd_reference_value():
    """PSS-78 formula must reproduce a known CTD measurement within 0.01 %."""
    salinity_ctd = 34.3684  # reference value from CTD sensor
    salinity_computed = compute_salinity(C=35.67560, T=8.0583, p=0.357)
    assert np.isclose(salinity_ctd, salinity_computed, rtol=1e-4), (
        "The calculated value deviates too much from the true value!"
        "Relative tolerance exceeds 1e-4."
    )


def test_compute_salinity_explicit_mscm_unchanged():
    """Explicit units='mS/cm' must produce the same result as the default (no units)."""
    sal_default = compute_salinity(C=35.67560, T=8.0583, p=0.357)
    sal_explicit = compute_salinity(C=35.67560, T=8.0583, p=0.357, units="mS/cm")
    assert sal_default == sal_explicit


def test_compute_salinity_sm_matches_mscm():
    """S/m input multiplied by 10 should give the same salinity as the mS/cm value."""
    sal_mscm = compute_salinity(C=35.67560, T=8.0583, p=0.357)
    sal_sm = compute_salinity(C=3.567560, T=8.0583, p=0.357, units="S/m")
    assert np.isclose(sal_mscm, sal_sm, rtol=1e-9)


def test_compute_salinity_sm_warns_without_units():
    """Values that look like S/m (OOM < 1) must raise a UserWarning when units are not given."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        compute_salinity(C=3.5676, T=8.0583, p=0.357)
    assert len(caught) == 1
    assert issubclass(caught[0].category, UserWarning)
    assert "S/m" in str(caught[0].message)


def test_compute_salinity_mscm_no_warning():
    """Values in the normal mS/cm range must not trigger a warning."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        compute_salinity(C=35.67560, T=8.0583, p=0.357)
    unit_warnings = [w for w in caught if issubclass(w.category, UserWarning)]
    assert len(unit_warnings) == 0


def test_compute_salinity_xarray_sm_autodetect():
    """xr.DataArray with units='S/m' should auto-convert and match the mS/cm result."""
    C_da = xr.DataArray(3.567560, attrs={"units": "S/m"})
    sal_auto = compute_salinity(C=C_da, T=8.0583, p=0.357)
    sal_expected = compute_salinity(C=35.67560, T=8.0583, p=0.357)
    assert np.isclose(sal_auto, sal_expected, rtol=1e-9)


def test_compute_salinity_xarray_mscm_autodetect():
    """xr.DataArray with units='mS/cm' should not convert and must match the plain float result."""
    C_da = xr.DataArray(35.67560, attrs={"units": "mS/cm"})
    sal_auto = compute_salinity(C=C_da, T=8.0583, p=0.357)
    sal_expected = compute_salinity(C=35.67560, T=8.0583, p=0.357)
    assert np.isclose(sal_auto, sal_expected, rtol=1e-9)


def test_compute_salinity_invalid_units():
    """An unrecognized units string must raise ValueError."""
    with pytest.raises(ValueError, match="Unknown conductivity units"):
        compute_salinity(C=35.67560, T=8.0583, p=0.357, units="kg/m3")


def test_compute_salinity_units_case_normalisation():
    """Upper-case variant 'S/M' should be treated identically to 'S/m'."""
    sal_lower = compute_salinity(C=3.567560, T=8.0583, p=0.357, units="S/m")
    sal_upper = compute_salinity(C=3.567560, T=8.0583, p=0.357, units="S/M")
    assert sal_lower == sal_upper


def test_compute_salinity_nan_conductivity():
    """NaN conductivity falls into the 'no finite values' branch and returns NaN."""
    import math
    result = compute_salinity(C=float("nan"), T=25.0, p=1013.25)
    assert math.isnan(result)


def test_compute_salinity_units_alias_siemens_meter():
    """Alias 'Siemens/Meter' should convert the same as 'S/m'."""
    sal_alias = compute_salinity(C=3.567560, T=8.0583, p=0.357, units="Siemens/Meter")
    sal_sm = compute_salinity(C=3.567560, T=8.0583, p=0.357, units="S/m")
    assert sal_alias == sal_sm


def test_compute_salinity_xarray_unrecognised_units():
    """A DataArray with an unknown units attribute must raise ValueError."""
    C_da = xr.DataArray(35.67560, attrs={"units": "kg/m3"})
    with pytest.raises(ValueError, match="Unknown conductivity units"):
        compute_salinity(C=C_da, T=8.0583, p=0.357)


def test_order_of_magnitude():
    """Returns floor(log10(x)): single-digit → 0, tens → 1, hundreds → 2, etc."""
    assert order_of_magnitude(0) == 0
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


def test_centered_bins_produces_half_step_boundaries():
    """Bin edges sit half a step below/above each centre; edge count equals N+1."""
    x = np.arange(-90, 91)
    bins = centered_bins(x)

    assert np.allclose(bins, np.arange(-90.5, 91, 1))
    assert len(bins) == len(x) + 1


# --- temperature2C ---

def test_temperature2C_from_kelvin():
    assert temperature2C(283.15) == pytest.approx(10.0)


def test_temperature2C_already_celsius():
    assert temperature2C(10.0) == 10.0


def test_temperature2C_series():
    """pd.Series path: values above threshold are shifted from K to °C."""
    s = pd.Series([283.15, 293.15])
    result = temperature2C(s)
    assert result.iloc[0] == pytest.approx(10.0)
    assert result.iloc[1] == pytest.approx(20.0)


# --- temperature2K with Series / DataArray ---

def test_temperature2K_series():
    s = pd.Series([10.0, 20.0])
    result = temperature2K(s)
    assert np.allclose(result.values, [283.15, 293.15])


def test_temperature2K_dataarray():
    da = xr.DataArray([10.0, 20.0])
    result = temperature2K(da)
    assert np.allclose(result.values, [283.15, 293.15])


# --- pressure2mbar ---

def test_pressure2mbar_hpa():
    assert pressure2mbar(1013) == 1013


def test_pressure2mbar_pa():
    assert pressure2mbar(101300) == pytest.approx(1013.0)


def test_pressure2mbar_atm():
    assert pressure2mbar(1.0) == pytest.approx(1013.25)


def test_pressure2mbar_invalid():
    with pytest.raises(ValueError, match="hPa, Pa or atm"):
        pressure2mbar(1e7)


def test_pressure2atm_invalid():
    with pytest.raises(ValueError, match="hPa, Pa or atm"):
        pressure2atm(1e7)


# --- ppm2uatm ---

def test_ppm2uatm_wet():
    result = ppm2uatm(400.0, 1013.25)
    assert result == pytest.approx(400.0, rel=1e-4)


def test_ppm2uatm_dry():
    """Dry-air xCO2 must be reduced by the water vapour pressure before becoming pCO2."""
    result = ppm2uatm(400.0, 1013.25, input="dry", T=20.0, S=35.0)
    assert result < 400.0


def test_ppm2uatm_invalid_input():
    with pytest.raises(ValueError, match=r"dry.*wet"):
        ppm2uatm(400.0, 1013.25, input="invalid")


# --- compute_water_vapor_pressure ---

def test_compute_water_vapor_pressure_range():
    pH2O = compute_water_vapor_pressure(T=20.0, S=35.0)
    assert 0.02 < pH2O < 0.04  # typical oceanic range in atm


# --- temperature_correction ---

def test_temperature_correction_takahashi1993():
    result = temperature_correction(400.0, T_out=20.0, T_in=18.0, method="Takahashi1993")
    expected = 400.0 * np.exp(0.0423 * (20.0 - 18.0))
    assert np.isclose(result, expected, rtol=1e-9)


def test_temperature_correction_kwargs_form():
    """T_out/T_in can be passed as T_insitu/T_equ keyword arguments."""
    result = temperature_correction(400.0, T_insitu=20.0, T_equ=18.0)
    expected = temperature_correction(400.0, T_out=20.0, T_in=18.0)
    assert np.isclose(result, expected, rtol=1e-9)


def test_temperature_correction_invalid_method():
    with pytest.raises(ValueError, match="Unknown method"):
        temperature_correction(400.0, T_out=20.0, T_in=18.0, method="BadMethod")


# --- fugacity ---

def test_fugacity_less_than_pCO2():
    """Virial correction always reduces fCO2 below pCO2."""
    f = fugacity(350.0, 1.0, 20.0, xCO2=350.0)
    assert f < 350.0


def test_fugacity_xCO2_term_has_negligible_effect():
    """Omitting the optional xCO2 virial term (sets it to 1) should shift fCO2 by less than 0.1 µatm."""
    f_with = fugacity(350.0, 1.0, 20.0, xCO2=350.0)
    f_without = fugacity(350.0, 1.0, 20.0)
    assert f_with < 350.0
    assert f_without < 350.0
    assert abs(f_with - f_without) < 0.1


# --- set_nonoperating_to_nan ---

def test_set_nonoperating_to_nan_sets_values():
    times = pd.date_range("2020-01-01", periods=10, freq="1min")
    status = [5, 5, 1, 1, 1, 5, 5, 5, 5, 5]  # non-operating at indices 2-4
    co2 = [400.0] * 10
    df = pd.DataFrame({"STATUS": status, "CO2": co2}, index=times)
    result = set_nonoperating_to_nan(df, col="CO2", status_var="STATUS", buffer="0min")
    assert np.isnan(result["CO2"].iloc[2])
    assert np.isnan(result["CO2"].iloc[3])
    assert not np.isnan(result["CO2"].iloc[0])


def test_set_nonoperating_to_nan_all_operating():
    """All-operating data must be returned unchanged."""
    times = pd.date_range("2020-01-01", periods=5, freq="1min")
    df = pd.DataFrame({"STATUS": [5] * 5, "CO2": [400.0] * 5}, index=times)
    result = set_nonoperating_to_nan(df, col="CO2", status_var="STATUS", buffer="0min")
    assert not result["CO2"].isna().any()


# --- compress_xarray ---

def test_compress_xarray_dataset():
    ds = xr.Dataset({"a": xr.DataArray([1.0, 2.0])})
    result = compress_xarray(ds)
    assert result["a"].encoding.get("zlib") is True


def test_compress_xarray_dataarray():
    da = xr.DataArray([1.0, 2.0])
    result = compress_xarray(da)
    assert result.encoding.get("zlib") is True
