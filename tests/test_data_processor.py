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



def test_pCO2_wet_equ_unit_label():
    """pCO2_wet_equ must carry unit 'µatm', not 'atm'."""
    dp = DataProcessor()
    dp.ds = _make_ds()
    dp.compute_pCO2_wet_equ()
    assert dp.ds["pCO2_wet_equ"].attrs.get("unit") == "µatm"


def _make_processor(pCO2_wet_equ, SBE45Temp, SST):
    """Build a minimal DataProcessor with required variables for temperature correction."""
    times = np.array(["2020-01-01"], dtype="datetime64[ns]")
    proc = DataProcessor()
    proc.ds = xr.Dataset(
        {
            "pCO2_wet_equ": ("time", np.atleast_1d(pCO2_wet_equ)),
            "SBE45Temp": ("time", np.atleast_1d(SBE45Temp)),
            "SST": ("time", np.atleast_1d(SST)),
        },
        coords={"time": times},
    )
    return proc


def test_temperature_correction_normal_case():
    """pCO2_wet_sst should differ from pCO2_wet_equ when SST != T_equ."""
    sst = 20.0
    t_equ = 18.0
    pco2 = 400.0

    proc = _make_processor(pco2, t_equ, sst)
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
