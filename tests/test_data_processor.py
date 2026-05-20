# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2026-05-20
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
import numpy as np
import xarray as xr

from oceanpack.app.models.data_processor import DataProcessor


def _make_processor_for_pCO2():
    """Build a minimal DataProcessor with CO2 and PressEqu for pCO2 computation."""
    times = np.array(["2020-01-01"], dtype="datetime64[ns]")
    proc = DataProcessor()
    proc.ds = xr.Dataset(
        {
            "CO2": ("time", np.atleast_1d(400.0)),
            "PressEqu": ("time", np.atleast_1d(1.0)),
        },
        coords={"time": times},
    )
    proc.ds["PressEqu"].attrs["unit"] = "atm"
    return proc


def test_pCO2_wet_equ_unit_label():
    """pCO2_wet_equ must carry unit 'µatm', not 'atm'."""
    proc = _make_processor_for_pCO2()
    proc.compute_pCO2_wet_equ()

    unit = proc.ds["pCO2_wet_equ"].attrs.get("unit")
    assert unit == "µatm", f"Expected unit 'µatm', got '{unit}'"
