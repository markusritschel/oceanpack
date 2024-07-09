# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-13
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
from oceanpack.app.views.data_view import DataConversionView
from oceanpack.app.models.filesource import FileSourceModel


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
