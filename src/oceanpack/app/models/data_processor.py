# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-07-08
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
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
        import xarray as xr
        self.ds = xr.open_dataset(file)

    def convert_coordinates(self):
        from oceanpack.utils.helpers import convert_coordinates
        self.ds['lon'] = convert_coordinates(self.ds['Longitude'])
        self.ds['lat'] = convert_coordinates(self.ds['Latitude'])

    def compute_equilibrator_pressure(self):
        """Obtain pressure at the equilibrator/membrane."""
        from oceanpack.utils.helpers import pressure2atm
        df = self.ds[['CellPress', 'DPressInt']].to_pandas()
        pressure_equ = df['CellPress'] - df['DPressInt'].rolling('2min').mean()  # in mBar
        self.ds['PressEqu'] = pressure2atm(pressure_equ)  # in atm
        self.ds['PressEqu'].attrs['unit'] = 'atm'
        self.ds['PressEqu'].attrs['full_name'] = 'Pressure at equilibrator/membrane'

    def compute_pCO2_wet_equ(self):
        """Compute pCO2 at the equilibrator in wet air."""
        from oceanpack.utils.helpers import ppm2uatm
        self.ds['pCO2_wet_equ'] = ppm2uatm(self.ds['CO2'], self.ds['PressEqu'])

    def to_netcdf(self, output_file):
        self.ds.to_netcdf(output_file)


class DataMerger:
    def __init__(self):
        self.merged = None

    def merge(self, files, tolerance: str = '2min'):
        import xarray as xr
        from tqdm.auto import tqdm

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
            "ANA_state"
            "STATUS",
        ]
        vars2drop = [var for var in self.merged.variables if var not in vars2keep]
        log.info("Drop variables")
        self.merged = self.merged.drop_vars(vars2drop, errors="ignore")

    def to_netcdf(self, output_file):
        self.merged.to_netcdf(output_file)
