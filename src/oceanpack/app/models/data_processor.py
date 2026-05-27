# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-07-08
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
"""Data processing routines for computing derived oceanographic quantities such as CO2 concentration, pCO2, and fugacity."""

import logging

log = logging.getLogger(__name__)


class DataProcessor:
    """A class the processes the data from the Analyzer or the NetDI unit.
    This includes:
        - Compute CO2 concentration
        - Compute pCO2
        - Compute fugacity
        - ...
    """

    def __init__(self):
        self.ds = None

    def load_data(self, file):
        """Load raw data from `file`."""
        import xarray as xr

        self.ds = xr.open_dataset(file)

    def convert_coordinates(self):
        """Convert longitude and latitude from DDDMM.MMM format to decimal degrees."""
        from oceanpack.utils.helpers import convert_coordinates

        if not all(var in self.ds for var in ["Longitude", "Latitude"]):
            log.warning(
                "Longitude and Latitude variables not found. Skipping coordinate conversion."
            )
            return
        self.ds["lon"] = convert_coordinates(self.ds["Longitude"])
        self.ds["lat"] = convert_coordinates(self.ds["Latitude"])

    def compute_equilibrator_pressure(self):
        """Obtain pressure at the equilibrator/membrane."""
        from oceanpack.utils.helpers import pressure2atm

        df = self.ds[["CellPress", "DPressInt"]].to_pandas()
        pressure_equ = df["CellPress"] - df["DPressInt"].rolling("2min").mean()  # in mBar
        self.ds["PressEqu"] = pressure2atm(pressure_equ)  # in atm
        self.ds["PressEqu"].attrs["unit"] = "atm"
        self.ds["PressEqu"].attrs["long_name"] = "Pressure at equilibrator/membrane"

    def compute_pCO2_wet_equ(self):  # noqa: N802
        """Compute pCO2 at the equilibrator in wet air."""
        from oceanpack.utils.helpers import ppm2uatm

        self.ds["pCO2_wet_equ"] = ppm2uatm(self.ds["CO2"], self.ds["PressEqu"])
        self.ds["pCO2_wet_equ"].attrs["unit"] = "µatm"
        self.ds["pCO2_wet_equ"].attrs["long_name"] = "pCO2 at equilibrator/membrane in wet air"

    def compute_temperature_correction(self):
        """Correct pCO2 from equilibrator temperature to in-situ SST.

        Applies the Takahashi correction formula.
        T_equ is approximated by waterTemp (internal SBE45 temperature).

        .. note::
            If measurements were taken on a ship, the water intake path may introduce a
            lag between the actual SST and the registered ``SBE45Temp``. A lag analysis
            and time-series correction of the intake temperature should be considered
            before applying this correction in such cases.

        References
        ----------
        Takahashi et al. (2009), doi:10.1016/j.dsr2.2008.12.009
        """
        from oceanpack.utils.helpers import temperature_correction

        CO2_var = "pCO2_wet_equ"
        T_equ_var = "SBE45Temp"  # equilibrator temperature (approximated by internal SBE45)
        T_target_var = "SST"  # in-situ sea surface temperature (SST)
        for var in [CO2_var, T_target_var, T_equ_var]:
            if var not in self.ds.variables:
                log.warning(f"⚠️  {var} variable not found. Skipping temperature correction.")
                return
        CO2 = self.ds[CO2_var]
        T_target = self.ds[T_target_var]
        T_equ = self.ds[T_equ_var]
        self.ds["pCO2_wet_sst"] = temperature_correction(
            CO2=CO2, T_out=T_target, T_in=T_equ, method="Takahashi2009"
        )
        self.ds["pCO2_wet_sst"].attrs["unit"] = "µatm"
        self.ds["pCO2_wet_sst"].attrs["long_name"] = (
            "pCO2 at SST in wet air (temperature-corrected)"
        )


    def remove_non_operating_phases(self):
        """Set CO2 values in non-operating phases to NaN"""
        from oceanpack.utils.helpers import set_nonoperating_to_nan

        for var in self.ds.variables:
            if "CO2" in var and not var.endswith("original"):
                if f"{var}_original" not in self.ds.variables:
                    self.ds = self.ds.rename({var: f"{var}_original"})
                df = self.ds[[f"{var}_original", "STATUS"]].to_pandas()
                df = set_nonoperating_to_nan(
                    df, status_var="STATUS", col=f"{var}_original", buffer="20min"
                )
                self.ds[var] = df[f"{var}_original"]

    def to_netcdf(self, output_file):
        """Write the processed dataset to a netCDF file at `output_file`."""
        try:
            self.ds.load()
        finally:
            self.ds.close()
        self.ds.to_netcdf(output_file)


class DataMerger:
    """A class that merges multiple netCDF files into a single dataset. This is useful
    when data from multiple sources (e.g., GPS coordinates, SST from a different sensor, etc.)
    should be merged into a single dataset for further processing.
    """

    def __init__(self):
        self.merged = None

    def merge(self, files, tolerance: str = "2min"):
        """Merge multiple netCDF files into a single dataset."""
        from tqdm.auto import tqdm
        import xarray as xr

        all_ds = []
        for i, file in enumerate(tqdm(files)):
            ds = xr.open_dataset(file)
            if i > 0:
                ds = ds.sel(time=all_ds[0].time, method="nearest", tolerance=tolerance)
                # Remove duplicate variables
                for var in ds.variables:
                    if var in all_ds[0].variables:
                        ds = ds.drop_vars(var)
            all_ds.append(ds)
        log.info("Merge data sets")
        self.merged = xr.merge(all_ds, join="inner", combine_attrs="drop_conflicts")

    def select_variables(self):
        """Select the variables to be kept."""
        vars2keep = [
            "time",
            "CO2",
            "SBE45Temp",
            "SBE45Cond",
            "SBE45Sal",
            "AIN0_mA_Waterflow",
            "CellTemp",
            "CellPress",
            "DPressInt",
            "Latitude",
            "Longitude",
            "Speed",
            "Course",
            "Error",
            "ANA_state",
            "STATUS",
        ]
        vars2drop = [var for var in self.merged.variables if var not in vars2keep]
        log.info("Drop variables")
        self.merged = self.merged.drop_vars(vars2drop, errors="ignore")

    def to_netcdf(self, output_file):
        """Generate output file in netCDF format at `output_file`."""
        self.merged.to_netcdf(output_file)
