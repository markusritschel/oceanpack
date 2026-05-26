# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2026-05-19
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
import numpy as np
import xarray as xr

from oceanpack.app.models.data_processor import DataProcessor
from oceanpack.utils.helpers import fugacity


def _make_ds(**overrides):
    """Minimal xarray Dataset for DataProcessor.compute_fugacity() tests."""
    defaults = dict(
        pCO2_wet_equ=350.0,  # µatm
        PressEqu=1.0,  # atm
        SBE45Temp=20.0,  # °C
        CO2=350.0,  # ppm (xCO2)
    )
    defaults.update(overrides)
    return xr.Dataset({k: xr.DataArray([v]) for k, v in defaults.items()})


class TestComputeFugacity:
    def test_output_variable_created(self):
        dp = DataProcessor()
        dp.ds = _make_ds()
        dp.compute_fugacity()
        assert 'fCO2_wet_SST' in dp.ds

    def test_attrs(self):
        dp = DataProcessor()
        dp.ds = _make_ds()
        dp.compute_fugacity()
        assert dp.ds['fCO2_wet_SST'].attrs['unit'] == 'µatm'
        assert (
            dp.ds['fCO2_wet_SST'].attrs['long_name']
            == 'Fugacity of CO2 in wet air at SST'
        )

    def test_matches_helper_directly(self):
        """Result must equal calling the fugacity() helper with the same inputs."""
        pCO2, p_equ, SST, xCO2 = 350.0, 1.0, 20.0, 350.0
        dp = DataProcessor()
        dp.ds = _make_ds(pCO2_wet_equ=pCO2, PressEqu=p_equ, SBE45Temp=SST, CO2=xCO2)
        dp.compute_fugacity()
        expected = fugacity(pCO2, p_equ, SST, xCO2=xCO2)
        assert np.isclose(float(dp.ds['fCO2_wet_SST'].values[0]), expected, rtol=1e-9)

    def test_fugacity_less_than_pCO2(self):
        """fCO2 must be slightly smaller than pCO2 (virial correction is always negative)."""
        dp = DataProcessor()
        dp.ds = _make_ds()
        dp.compute_fugacity()
        assert float(dp.ds['fCO2_wet_SST'].values[0]) < 350.0

    def test_dickson_sop24_example(self):
        """Verify against Dickson et al., 2007 (SOP 24) example.

        Typical example values: pCO2=348.7 µatm, p_equ=1 atm, SST=29°C,
        xCO2=348.7 ppm.  Expected fCO2 is approximately 347.6 µatm.
        """
        pCO2, p_equ, SST, xCO2 = 348.7, 1.0, 29.0, 348.7
        dp = DataProcessor()
        dp.ds = _make_ds(pCO2_wet_equ=pCO2, PressEqu=p_equ, SBE45Temp=SST, CO2=xCO2)
        dp.compute_fugacity()
        result = float(dp.ds['fCO2_wet_SST'].values[0])
        assert result < pCO2, "fCO2 should be less than pCO2"
        assert np.isclose(result, 347.6, atol=1.0), (
            f"Expected ~347.6 µatm, got {result:.3f}"
        )

    def test_uses_pCO2_wet_SST_when_available(self):
        """When pCO2_wet_SST (temperature-corrected) is present, it should be used."""
        pCO2_sst = 345.0
        ds = _make_ds(pCO2_wet_equ=350.0, PressEqu=1.0, SBE45Temp=20.0, CO2=350.0)
        ds['pCO2_wet_SST'] = xr.DataArray([pCO2_sst])
        dp = DataProcessor()
        dp.ds = ds
        dp.compute_fugacity()
        result = float(dp.ds['fCO2_wet_SST'].values[0])
        expected = fugacity(pCO2_sst, 1.0, 20.0, xCO2=350.0)
        assert np.isclose(result, expected, rtol=1e-9)


def test_pCO2_wet_equ_unit_label():
    """pCO2_wet_equ must carry unit 'µatm', not 'atm'."""
    dp = DataProcessor()
    dp.ds = _make_ds()
    dp.compute_pCO2_wet_equ()
    assert dp.ds['pCO2_wet_equ'].attrs.get('unit') == 'µatm'


def _make_processor(pCO2_wet_equ, SBE45Temp, CellTemp):
    """Build a minimal DataProcessor with required variables for temperature correction."""
    times = np.array(["2020-01-01"], dtype="datetime64[ns]")
    proc = DataProcessor()
    proc.ds = xr.Dataset(
        {
            "pCO2_wet_equ": ("time", np.atleast_1d(pCO2_wet_equ)),
            "SBE45Temp": ("time", np.atleast_1d(SBE45Temp)),
            "CellTemp": ("time", np.atleast_1d(CellTemp)),
        },
        coords={"time": times},
    )
    return proc


def test_temperature_correction_normal_case():
    """pCO2_wet_sst should differ from pCO2_wet_equ when SST != T_equ."""
    sst = 20.0
    t_equ = 18.0
    pco2 = 400.0

    proc = _make_processor(pco2, sst, t_equ)
    proc.compute_temperature_correction()

    expected = pco2 * np.exp(0.0433 * (sst - t_equ) - 4.35e-5 * (sst**2 - t_equ**2))
    result = float(proc.ds["pCO2_wet_sst"].values[0])

    assert np.isclose(result, expected, rtol=1e-10), (
        f"Temperature correction result {result} does not match expected {expected}"
    )


def test_temperature_correction_sst_equals_tequ():
    """When SST == T_equ the correction factor is 1 and output equals input."""
    temp = 15.0
    pco2 = 380.0

    proc = _make_processor(pco2, temp, temp)
    proc.compute_temperature_correction()

    result = float(proc.ds["pCO2_wet_sst"].values[0])
    assert np.isclose(result, pco2, rtol=1e-12), (
        "When SST equals T_equ, pCO2_wet_sst must equal pCO2_wet_equ"
    )


def test_temperature_correction_output_attributes():
    """Output variable must carry correct unit and long_name attributes."""
    proc = _make_processor(400.0, 20.0, 18.0)
    proc.compute_temperature_correction()

    attrs = proc.ds["pCO2_wet_sst"].attrs
    assert attrs.get("unit") == "µatm"
    assert "long_name" in attrs
