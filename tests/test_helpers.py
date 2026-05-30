# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-12
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
import warnings

import numpy as np
import pytest
import xarray as xr

from oceanpack.utils.helpers import (
    _split_degrees_minutes,
    centered_bins,
    compute_salinity,
    convert_coordinates,
    find_nearest,
    order_of_magnitude,
    pressure2atm,
    temperature2K,
)


def test_coordinate_splitting():
    coord = 4623.4231
    assert _split_degrees_minutes(coord) == (46, 23.423099999999977), (
        "Coordinate conversion is erroneous"
    )
    assert convert_coordinates(coord) == 46.390385, "Coordinate conversion is erroneous"


def test_cond2sal_converter():
    # example values from a CTD
    salinity_ctd = 34.3684
    conductivity_ctd = 35.67560
    salinity_computed = compute_salinity(C=conductivity_ctd, T=8.0583, p=0.357)

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


def test_bin_creator():
    x = np.arange(-90, 91)
    bins = centered_bins(x)

    assert np.all(bins == np.arange(-90.5, 91, 1)), "Bins don't match!"
    assert len(bins) == len(x) + 1, "Bin edges must be one more than there are labels"
