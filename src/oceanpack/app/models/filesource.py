# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-12
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
class FileSourceModel:
    def __init__(self, source_type: FileSourceType = None) -> None:
        self._filehandler = None
        self._source_type = None
        self.source_type = source_type

    @property
    def source_type(self) -> str:
        return self._source_type

    def load_data(self, path: str):
        pass
    def clean_data(self):
        pass
    def process_data(self):
        pass
    def get_data(self):
        pass
