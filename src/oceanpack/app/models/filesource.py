# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-12
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
from enum import Enum, IntEnum


class FileSourceType(Enum):
    """This class determines the file source."""

    ANALYZER = 'Analyzer'
    NETDI    = 'NetDI'
    STREAM   = 'Stream'

    @staticmethod
    def isvalid(source_type: str) -> bool:
        """Checks if the source type is valid."""
        source_types = [member.value for member in FileSourceType]
        return source_type in source_types
    
    def get_filehandler(self):
        """Get the file handler for the respective source."""
        if self == FileSourceType.ANALYZER:
            from .filehandler import AnalyzerFileHandler
            return AnalyzerFileHandler
        elif self == FileSourceType.NETDI:
            from .filehandler import NetDIFileHandler
            return NetDIFileHandler
        elif self == FileSourceType.STREAM:
            from .filehandler import StreamFileHandler
            return StreamFileHandler
        else:
            return None
    
    @classmethod
    def from_string(cls, value: str):
        for source in cls:
            if source.value == value:
                return source
        raise ValueError(f"Invalid source type: {value}")


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
