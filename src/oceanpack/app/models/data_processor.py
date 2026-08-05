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
    #: Variable holding the temperature at the equilibrator/membrane. In the Analyzer this is
    #: the internal CTD (SS_CTD48), which sits at the equilibrator. `CellTemp` is the heated
    #: LI-840 detector cell (~51 °C) and must never be used here.
    T_EQU_VAR = 'waterTemp'

    def __init__(self):
        self.ds = None

    def load_data(self, file):
        import xarray as xr
        # read everything into memory and close the file handle: `process-data` writes its
        # output back over its input, which fails on an open netCDF
        with xr.open_dataset(file) as ds:
            self.ds = ds.load()

    def convert_coordinates(self):
        from oceanpack.utils.helpers import convert_coordinates
        self.ds['lon'] = convert_coordinates(self.ds['Longitude'])
        self.ds['lat'] = convert_coordinates(self.ds['Latitude'])
        # xarray propagates the attributes of the source variable, whose `unit` still
        # describes the raw NMEA format the values have just been converted away from.
        self.ds['lon'].attrs['unit'] = 'degrees_east'
        self.ds['lat'].attrs['unit'] = 'degrees_north'
        self.ds['lon'].attrs['long_name'] = 'Longitude'
        self.ds['lat'].attrs['long_name'] = 'Latitude'

    def compute_equilibrator_pressure(self):
        """Obtain pressure at the equilibrator/membrane."""
        from oceanpack.utils.helpers import pressure2atm
        df = self.ds[['CellPress', 'DPressInt']].to_pandas()
        pressure_equ = df['CellPress'] - df['DPressInt'].rolling('2min').mean()  # in mBar
        self.ds['PressEqu'] = pressure2atm(pressure_equ)  # in atm
        self.ds['PressEqu'].attrs['unit'] = 'atm'
        self.ds['PressEqu'].attrs['long_name'] = 'Pressure at equilibrator/membrane'

    def compute_pCO2_wet_equ(self):
        """Compute pCO2 at the equilibrator in wet air."""
        from oceanpack.utils.helpers import ppm2uatm
        self.ds['pCO2_wet_equ'] = ppm2uatm(self.ds['CO2'], self.ds['PressEqu'])
        self.ds['pCO2_wet_equ'].attrs['unit'] = 'uatm'
        self.ds['pCO2_wet_equ'].attrs['long_name'] = 'pCO2 at equilibrator/membrane in wet air'
        self.ds['pCO2_wet_equ'].attrs['temperature_variable'] = self.T_EQU_VAR
        self.ds['pCO2_wet_equ'].attrs['device'] = 'LI840'

    def compute_temperature_correction(self, sst_var: str | None = None):
        """Correct pCO2 from the equilibrator temperature to the in-situ SST
        (:func:`~oceanpack.utils.helpers.temperature_correction`, Takahashi et al. 2009).

        The correction is only meaningful when the in-situ SST comes from a *different*
        sensor than the equilibrator temperature — typically a hull-intake thermosalinograph
        upstream of the OceanPack. Analyzer logs do not carry such a record: their only water
        temperature is the internal CTD (`waterTemp`, SS_CTD48), which sits at the
        equilibrator. Passing it as both arguments would make the Takahashi factor exp(0) = 1
        and ship an identity under a "temperature-corrected" label, so when no separate SST
        variable is given, **no correction is applied and no `pCO2_wet_sst` is written**:
        `pCO2_wet_equ` already refers to the temperature the sample was measured at.

        To enable the correction, merge a hull-intake temperature record into the dataset
        (e.g. via ``merge-data``) and pass its variable name as `sst_var`.

        Parameters
        ----------
        sst_var: str, optional
            Name of the variable holding the in-situ sea surface temperature. Must be a
            different variable than :attr:`T_EQU_VAR`.
        """
        from oceanpack.utils.helpers import temperature_correction
        if sst_var is None:
            log.info("No in-situ SST variable given — skipping the temperature correction. "
                     "pCO2_wet_equ refers to the equilibrator temperature (%s).", self.T_EQU_VAR)
            return
        if sst_var == self.T_EQU_VAR:
            raise ValueError(
                f"sst_var={sst_var!r} is the equilibrator temperature ({self.T_EQU_VAR}); "
                "correcting a temperature to itself is a no-op. Pass an independent in-situ "
                "temperature record or omit sst_var."
            )
        self.ds['pCO2_wet_sst'] = temperature_correction(
            self.ds['pCO2_wet_equ'], T_out=self.ds[sst_var], T_in=self.ds[self.T_EQU_VAR]
        )
        self.ds['pCO2_wet_sst'].attrs = {
            'unit': 'uatm',
            'long_name': f'pCO2 in wet air, corrected from {self.T_EQU_VAR} to {sst_var}',
            'temperature_variable': sst_var,
            'method': 'Takahashi2009',
            'device': 'LI840',
        }

    def compute_fCO2(self):
        """Compute the fugacity of CO2 from the most corrected pCO2 available.

        Uses `pCO2_wet_sst` if :meth:`compute_temperature_correction` produced one, else
        `pCO2_wet_equ`, and names the output accordingly (`fCO2_wet_sst` / `fCO2_wet_equ`)
        so that the variable name states which temperature the fugacity refers to.
        """
        from oceanpack.utils.helpers import fugacity
        pco2_var = 'pCO2_wet_sst' if 'pCO2_wet_sst' in self.ds else 'pCO2_wet_equ'
        fco2_var = pco2_var.replace('pCO2', 'fCO2')
        temp_var = self.ds[pco2_var].attrs['temperature_variable']
        # pandas Series rather than DataArrays: temperature2K branches on a scalar comparison
        df = self.ds[[pco2_var, 'PressEqu', temp_var, 'CO2']].to_pandas()
        self.ds[fco2_var] = fugacity(df[pco2_var], df['PressEqu'], df[temp_var], xCO2=df['CO2'])
        self.ds[fco2_var].attrs = {
            'unit': 'uatm',
            'long_name': f'fCO2 in wet air at {temp_var}',
            'temperature_variable': temp_var,
            'device': 'LI840',
        }

    def remove_non_operating_phases(self):
        """Set CO2 values in non-operating phases to NaN.

        Only the raw analyzer channels are masked — they all start with 'CO2' (`CO2`,
        `CO2abs`, `CO2raw`, `CO2ref`, `CO2kzero`, `CO2kspan*`). Matching 'CO2' anywhere in
        the name would also catch the derived `pCO2_*` / `fCO2_*`, which `process-data`
        writes back into its own input file: on a second run they would be renamed to
        `*_original` too, changing the output contract on every run.
        """
        from oceanpack.utils.helpers import set_nonoperating_to_nan
        for var in self.ds.variables:
            if var.startswith('CO2') and not var.endswith('original'):
                if f'{var}_original' not in self.ds.variables:
                    self.ds = self.ds.rename({var: f'{var}_original'})
                df = self.ds[[f'{var}_original', 'STATUS']].to_pandas()
                df = set_nonoperating_to_nan(df, status_var='STATUS',
                                             col=f'{var}_original',
                                             buffer="20min")
                self.ds[var] = df[f'{var}_original']
                # assigning a pandas Series drops the attributes of the source variable
                self.ds[var].attrs = dict(self.ds[f'{var}_original'].attrs)

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
            "ANA_state",
            "STATUS",
        ]
        vars2drop = [var for var in self.merged.variables if var not in vars2keep]
        log.info("Drop variables")
        self.merged = self.merged.drop_vars(vars2drop, errors="ignore")

    def to_netcdf(self, output_file):
        self.merged.to_netcdf(output_file)
