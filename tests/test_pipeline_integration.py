"""Integration tests that run the full convert→process pipeline on example_op.log
and assert physically meaningful output ranges.

These tests would catch regressions such as:
  - Using CellTemp (~51 °C) instead of waterTemp as the equilibrator temperature
  - Broken coordinate conversion, or coordinates still labelled with the raw NMEA unit
  - Pressure unit errors and a flipped DPressInt sign convention
  - fCO2 exceeding pCO2 (violates thermodynamics)
  - Bug in set_nonoperating_to_nan when all STATUS==5
  - Shipping a temperature-corrected variable when no independent SST was available
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

    def test_coordinates_are_labelled_as_decimal_degrees(self, processed_ds):
        """The raw NMEA unit must not survive the conversion — a consumer that trusts
        'ddmm.mmmm' and re-converts 48.1 lands at 0.8 °N, ~5250 km away."""
        assert processed_ds["lat"].attrs["unit"] == "degrees_north"
        assert processed_ds["lon"].attrs["unit"] == "degrees_east"


class TestEquilibratorPressure:
    def test_press_equ_matches_the_documented_sign_convention(self, processed_ds, converted_nc):
        """PressEqu = CellPress − rolling_mean(DPressInt), as documented in docs/cli.md.

        DPressInt is negative (median −11.4 mbar) throughout this file, so the documented
        subtraction puts the equilibrator *above* the measurement cell and the opposite
        convention puts it below. The two are disjoint on this dataset — 1.0202–1.0361 atm
        against 0.9977–1.0133 atm — so these bounds fail if the sign is flipped.

        NOTE: which convention the HWHSC sensor actually reports is an open question on this
        dataset (see docs/cli.md); this test pins the behaviour the code and the docs agree
        on today. If the convention is revised, the formula, docs/cli.md and these bounds
        must move together.
        """
        raw = xr.open_dataset(converted_nc)
        cell_press_atm = raw["CellPress"].values / 1013.25
        p = processed_ds["PressEqu"].values
        assert np.nanmin(p) > 1.015, "PressEqu too low — DPressInt sign may be flipped"
        assert np.nanmax(p) < 1.045, "PressEqu too high — check the DPressInt correction"
        assert np.all(p > cell_press_atm), (
            "PressEqu must exceed CellPress while DPressInt is negative — sign flipped"
        )


class TestPCO2:
    def test_pCO2_wet_equ_range(self, processed_ds):
        pco2 = processed_ds["pCO2_wet_equ"].values
        assert np.nanmin(pco2) > 290, "pCO2_wet_equ too low"
        assert np.nanmax(pco2) < 380, "pCO2_wet_equ too high"

    def test_no_temperature_corrected_variable_without_an_independent_sst(self, processed_ds):
        """An Analyzer log carries only the internal CTD, which sits at the equilibrator.

        Correcting waterTemp to waterTemp is exp(0) = 1, so the pipeline must not emit a
        variable whose name and long_name claim a correction that never happened.
        """
        assert "pCO2_wet_sst" not in processed_ds
        assert "fCO2_wet_sst" not in processed_ds
        assert "fCO2_wet_equ" in processed_ds

    def test_pCO2_refers_to_an_ocean_temperature(self, processed_ds):
        """Guards against CellTemp (~51 °C, the heated LI-840 detector) being used as the
        equilibrator temperature — the ΔT of ~38 °C would give pCO2 ~70 µatm."""
        temp_var = processed_ds["pCO2_wet_equ"].attrs["temperature_variable"]
        temp = processed_ds[temp_var].values
        assert -2 < np.nanmin(temp) < np.nanmax(temp) < 40, (
            f"{temp_var} is outside the ocean temperature range — CellTemp used by mistake?"
        )


class TestFCO2:
    def test_fCO2_less_than_pCO2(self, processed_ds):
        """Fugacity must always be slightly less than partial pressure."""
        fco2 = processed_ds["fCO2_wet_equ"].values
        pco2 = processed_ds["pCO2_wet_equ"].values
        mask = ~np.isnan(fco2) & ~np.isnan(pco2)
        assert np.all(fco2[mask] < pco2[mask]), (
            "fCO2 >= pCO2 for some points — violates thermodynamics"
        )

    def test_fCO2_within_1_to_4_uatm_below_pCO2(self, processed_ds):
        """Fugacity correction is typically 1–3 µatm for oceanic conditions."""
        diff = processed_ds["pCO2_wet_equ"].values - processed_ds["fCO2_wet_equ"].values
        mask = ~np.isnan(diff)
        assert np.nanmin(diff[mask]) > 0, "fCO2 must be < pCO2"
        assert np.nanmax(diff[mask]) < 5, "fCO2 correction > 5 µatm is unrealistic here"


class TestTemperatureCorrectionPath:
    """The correction is off by default on Analyzer logs, so exercise it explicitly with an
    independent intake temperature merged in — otherwise the code path ships untested."""

    @pytest.fixture(scope="class")
    def processor_with_intake_sst(self, converted_nc, tmp_path_factory):
        import shutil
        import warnings

        warnings.filterwarnings("ignore")
        proc = tmp_path_factory.mktemp("sst") / "with_sst.nc"
        shutil.copy(converted_nc, proc)

        from oceanpack.app.models.data_processor import DataProcessor

        model = DataProcessor()
        model.load_data(str(proc))
        # a hull intake 0.5 K colder than the equilibrator — a realistic underway ΔT
        model.ds["SST_intake"] = model.ds["waterTemp"] - 0.5
        model.convert_coordinates()
        model.remove_non_operating_phases()
        model.compute_equilibrator_pressure()
        model.compute_pCO2_wet_equ()
        model.compute_temperature_correction(sst_var="SST_intake")
        model.compute_fCO2()
        return model

    def test_correction_is_applied_and_matches_takahashi(self, processor_with_intake_sst):
        ds = processor_with_intake_sst.ds
        ratio = (ds["pCO2_wet_sst"] / ds["pCO2_wet_equ"]).values
        # Takahashi (2009) for ΔT = −0.5 K at the median waterTemp of 13.108 °C:
        #   exp(0.0433*(-0.5) - 4.35e-5*(12.608**2 - 13.108**2))
        #   = exp(-0.02165 + 0.000559323) = 0.9791302
        # The tolerance covers the T² term across the transect (12.67–13.45 °C, spread 3.3e-5).
        assert np.allclose(ratio, 0.9791302, atol=3e-5), (
            "temperature correction does not follow the Takahashi (2009) factor"
        )
        assert np.nanmax(np.abs(ratio - 1.0)) > 1e-3, "correction is a no-op"

    def test_fCO2_follows_the_corrected_pCO2(self, processor_with_intake_sst):
        ds = processor_with_intake_sst.ds
        assert "fCO2_wet_sst" in ds
        assert ds["fCO2_wet_sst"].attrs["temperature_variable"] == "SST_intake"
        assert np.all(ds["fCO2_wet_sst"].values < ds["pCO2_wet_sst"].values)

    def test_correcting_a_temperature_to_itself_is_rejected(self, converted_nc, tmp_path_factory):
        import shutil

        proc = tmp_path_factory.mktemp("degenerate") / "degenerate.nc"
        shutil.copy(converted_nc, proc)

        from oceanpack.app.models.data_processor import DataProcessor

        model = DataProcessor()
        model.load_data(str(proc))
        model.compute_equilibrator_pressure()
        model.compute_pCO2_wet_equ()
        with pytest.raises(ValueError, match="no-op"):
            model.compute_temperature_correction(sst_var=DataProcessor.T_EQU_VAR)
