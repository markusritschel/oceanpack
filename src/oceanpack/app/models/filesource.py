# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-12
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
from enum import Enum, IntEnum
import pandas as pd
from tqdm.auto import tqdm
import logging

from pathlib import Path


log = logging.getLogger(__name__)


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
        self._metadata = None
        self.df = None

    @property
    def source_type(self) -> str:
        return self._source_type

    @source_type.setter
    def source_type(self, value: str):
        if not isinstance(value, str):
            raise TypeError("source_type must be of type str")
        if not FileSourceType.isvalid(value):
            valid_values = [m.value for m in FileSourceType]
            raise TypeError(f"source_type is unknown. Valid options are {valid_values}")
        self._source_type = FileSourceType.from_string(value)
        if self._source_type:
            self._filehandler = self._source_type.get_filehandler()

    def load_data(self, path: str):
        all_files = collect_files(path)

        if self._source_type:
            self._filehandler = self._source_type.get_filehandler()

        df_list = []
        for file in tqdm(all_files, unit='file'):
            data_, metadata_ = self._filehandler.read_file(file)
            if self._metadata is None:
                self._metadata = metadata_
            df_list.append(data_)

        self.df = pd.concat(df_list)


    def clean_data(self):
        df = self.df
        df = df.loc[df.index.dropna()]
        self.df = df[~df.index.duplicated(keep='first')]

    def process_data(self):
        df = self.df
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except Exception:
                log.warning(f'Cannot convert {col} to numeric')
        df.sort_index(axis=0, inplace=True, ascending=True)
        self.df = df

    def get_data(self):
        pass
    

def collect_files(path: str, suffix='log') -> list[Path]:
    """
    Collect files from a given path.

    Parameters
    ----------
    path : str
        The path to the file or directory.
    suffix : str, optional
        The file suffix to filter by. Defaults to 'log'.

    Returns
    -------
    list[Path]
        A list of paths to the detected files.
    """
    path = Path(path)
    if path.is_file():
        all_files = [path]
    elif path.is_dir():
        files = path.glob(f'**/*.{suffix}')
        all_files = list(files)
    return all_files
