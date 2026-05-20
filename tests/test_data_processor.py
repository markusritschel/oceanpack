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
