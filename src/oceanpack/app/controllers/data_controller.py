# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-13
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
"""Controllers that coordinate loading, processing, and exporting of OceanPack sensor data."""

import logging

from oceanpack.app.models.data_processor import DataMerger, DataProcessor
from oceanpack.app.models.filesource import FileSourceModel
from oceanpack.app.views.data_view import DataConversionView

log = logging.getLogger(__name__)


class DataConversionController:
    """A class that controlls the conversion from raw log files retrieved from the OceanPack to
    netCDF format.
    """

    def __init__(self, source_type: str | None = None):
        self.model = FileSourceModel(source_type)
        self.view = DataConversionView()

    def load_data(self, path: str):
        """Load raw data from `path`, clean it and run initial processing."""
        self.model.load_data(path)
        self.model.clean_data()
        self.model.process_data()

    def display(self):
        """Render the current model using the view."""
        self.view.display(self.model)

    def generate_output(self, path):
        """Generate output file in netCDF format at `path`."""
        self.model.to_netcdf(path)


class DataMergeController:
    """A class that controls the merging of multiple netCDF files into a single dataset. This is useful
    when data from multiple sources (e.g., GPS coordinates, SST from a different sensor, etc.) should be 
    merged into a single dataset for further processing.
    """

    def __init__(self):
        self.model = DataMerger()

    def merge(self, files, tolerance: str = '2min', **kwargs):
        """Merge multiple netCDF files into a single dataset.
        The `tolerance` parameter determines the maximum time difference allowed when aligning timestamps 
        across input files. The `keep_all` parameter determines whether to keep all variables from the 
        input files or to select only a subset of important variables after merging.
        """
        self.model.merge(files, tolerance=tolerance)
        if kwargs.pop('keep_all') is False:
            log.info("Remove variables that are not important for further analysis.")
            self.model.select_variables()

    def generate_output(self, path):
        """Generate output file in netCDF format at `path`."""
        self.model.to_netcdf(path)


class DataProcessingController:
    """A class that controls the processing of variables in a netCDF file."""

    def __init__(self):
        self.model = DataProcessor()

    def load_data(self, path):
        """Load raw data from `path`."""
        self.model.load_data(path)

    def process_data(self):
        """Run the processing steps to compute additional variables such as fCO2 at SST, equilibrator pressure, etc."""
        self.model.convert_coordinates()
        self.model.remove_non_operating_phases()
        self.model.compute_equilibrator_pressure()
        self.model.compute_pCO2_wet_equ()
        self.model.compute_temperature_correction()

    def generate_output(self, path):
        """Generate output file in netCDF format at `path`."""
        self.model.to_netcdf(path)
