# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-13
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
from oceanpack.app.views.data_view import DataView
from oceanpack.app.models.filesource import FileSourceModel


class DataController:
    def __init__(self, source_type: str = None):
        self.model = FileSourceModel(source_type)
        self.view = DataView()

    def load_data(self, path: str):
        self.model.load_data(path)
        self.model.clean_data()
        self.model.process_data()

    def display(self):
        self.view.display(self.model)

    def write_output(self, path):
        data = self.model.get_data()
        self.view.export_to_netcdf(data, path)
