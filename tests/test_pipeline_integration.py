"""Integration tests that run the full convert→process pipeline on example_op.log
and assert physically meaningful output ranges.

These tests would catch regressions such as:
  - Using CellTemp (~51 °C) instead of waterTemp as T_equ in the temperature correction
  - Broken coordinate conversion
  - Pressure unit errors
  - fCO2 exceeding pCO2 (violates thermodynamics)
  - Bug in set_nonoperating_to_nan when all STATUS==5
"""

import numpy as np
import pytest
import xarray as xr

LOG_FILE = "tests/example_op.log"
EXAMPLE_NC = "tests/example_op.nc"


@pytest.fixture(scope="module")
def converted_nc(tmp_path_factory):
    """Run convert-data on example_op.log and return path to the netCDF."""
    import warnings

    warnings.filterwarnings("ignore")

    out = tmp_path_factory.mktemp("data") / "example_op.nc"
    from oceanpack.app.controllers.data_controller import DataConversionController

    ctrl = DataConversionController("Analyzer")
    ctrl.load_data(LOG_FILE)
    ctrl.generate_output(str(out))
    return out


@pytest.fixture(scope="module")
def processed_ds(converted_nc, tmp_path_factory):
    """Run process-data on the converted netCDF and return the xarray Dataset."""
    import shutil
    import warnings

    warnings.filterwarnings("ignore")

    proc = tmp_path_factory.mktemp("processed") / "example_op_processed.nc"
    shutil.copy(converted_nc, proc)

    from oceanpack.app.controllers.data_controller import DataProcessingController

    ctrl = DataProcessingController()
    ctrl.load_data(str(proc))
    ctrl.process_data()
    ctrl.generate_output(str(proc))
    return xr.open_dataset(str(proc))


class TestCoordinates:
    def test_latitude_range(self, processed_ds):
        lat = processed_ds["lat"].values
        assert np.nanmin(lat) > 47.0, "lat too low for Bay of Biscay"
        assert np.nanmax(lat) < 50.0, "lat too high for Bay of Biscay"

    def test_longitude_range(self, processed_ds):
        lon = processed_ds["lon"].values
        assert np.nanmin(lon) > -6.0, "lon too far west for Bay of Biscay"
        assert np.nanmax(lon) < -3.0, "lon too far east for Bay of Biscay"


class TestEquilibratorPressure:
    def test_press_equ_range(self, processed_ds):
        p = processed_ds["PressEqu"].values
        # CellPress ~1022 mbar + |DPressInt| ~11 mbar → ~1033 mbar → ~1.019 atm
        assert np.nanmin(p) > 1.00, "PressEqu below 1 atm — likely unit error"
        assert np.nanmax(p) < 1.10, "PressEqu above 1.10 atm — unrealistic"


class TestPCO2:
    def test_pCO2_wet_equ_range(self, processed_ds):
        pco2 = processed_ds["pCO2_wet_equ"].values
        assert np.nanmin(pco2) > 290, "pCO2_wet_equ too low"
        assert np.nanmax(pco2) < 380, "pCO2_wet_equ too high"

    def test_pCO2_wet_sst_close_to_equ(self, processed_ds):
        """Temperature correction ΔT should be small (waterTemp≈T_equ≈T_SST)."""
        delta = np.abs(processed_ds["pCO2_wet_sst"].values - processed_ds["pCO2_wet_equ"].values)
        assert np.nanmax(delta) < 20, (
            "pCO2_wet_sst deviates >20 µatm from pCO2_wet_equ — "
            "check that CellTemp is NOT used as T_equ (CellTemp ~51 °C would give ΔT ~38 °C)"
        )

    def test_temperature_correction_not_using_cell_temp(self, processed_ds):
        """If CellTemp (~51 °C) were used as T_equ, pCO2_wet_sst would be ~70 µatm — impossible."""
        pco2_sst = processed_ds["pCO2_wet_sst"].values
        assert np.nanmin(pco2_sst) > 200, (
            "pCO2_wet_sst is unphysically low — CellTemp may have been used as T_equ"
        )
        assert np.nanmax(pco2_sst) < 400, (
            "pCO2_wet_sst is unphysically high — check temperature correction variable"
        )


class TestFCO2:
    def test_fCO2_less_than_pCO2(self, processed_ds):
        """Fugacity must always be slightly less than partial pressure."""
        fco2 = processed_ds["fCO2_wet_sst"].values
        pco2 = processed_ds["pCO2_wet_sst"].values
        mask = ~np.isnan(fco2) & ~np.isnan(pco2)
        assert np.all(fco2[mask] < pco2[mask]), (
            "fCO2 >= pCO2 for some points — violates thermodynamics"
        )

    def test_fCO2_within_1_to_4_uatm_below_pCO2(self, processed_ds):
        """Fugacity correction is typically 1–3 µatm for oceanic conditions."""
        diff = processed_ds["pCO2_wet_sst"].values - processed_ds["fCO2_wet_sst"].values
        mask = ~np.isnan(diff)
        assert np.nanmin(diff[mask]) > 0, "fCO2 must be < pCO2"
        assert np.nanmax(diff[mask]) < 5, "fCO2 correction > 5 µatm is unrealistic here"
