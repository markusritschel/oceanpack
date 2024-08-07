# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-13
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
import logging
from oceanpack.app.models.data_processor import DataMerger, DataProcessor
from oceanpack.app.views.data_view import DataConversionView
from oceanpack.app.models.filesource import FileSourceModel


log = logging.getLogger(__name__)


class DataConversionController:
    """A class that controlls the conversion from raw log files retrieved from the OceanPack to
    netCDF format."""
    def __init__(self, source_type: str = None):
        self.model = FileSourceModel(source_type)
        self.view = DataConversionView()

    def load_data(self, path: str):
        self.model.load_data(path)
        self.model.clean_data()
        self.model.process_data()

    def display(self):
        self.view.display(self.model)

    def generate_output(self, path):
        self.model.to_netcdf(path)


class DataMergeController:
    def __init__(self):
        self.model = DataMerger()

    def merge(self, files, tolerance: str = '2min', **kwargs):
        self.model.merge(files, tolerance=tolerance)
        if kwargs.pop('keep_all') is False:
            log.info("Remove variables that are not important for further analysis.")
            self.model.select_variables()

    def generate_output(self, path):
        self.model.to_netcdf(path)


class DataProcessingController:
    """A class that controls the processing of variables in a netCDF file."""
    def __init__(self):
        self.model = DataProcessor()

    def load_data(self, path):
        self.model.load_data(path)

    def process_data(self):
        self.model.convert_coordinates()
        self.model.remove_non_operating_phases()
        self.model.compute_equilibrator_pressure()
        self.model.compute_pCO2_wet_equ()

    def generate_output(self, path):
        self.model.to_netcdf(path)

