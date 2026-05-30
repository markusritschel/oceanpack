# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-12
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
"""File source model and source type enumeration for managing OceanPack log file ingestion."""

from enum import Enum
import logging
from pathlib import Path

import pandas as pd
from tqdm.auto import tqdm

log = logging.getLogger(__name__)


class FileSourceType(Enum):
    """Enumeration class of supported data source types, each mapping to a dedicated file handler."""

    INTERNAL = "Internal"
    ANALYZER = "Analyzer"
    NETDI = "NetDI"
    STREAM = "Stream"

    @staticmethod
    def isvalid(source_type: str) -> bool:
        """Checks if the source type is valid.
        Return True if the given string matches one of the known source type values.
        """
        source_types = [member.value for member in FileSourceType]
        return source_type in source_types
    
    def get_filehandler(self):
        """Return the file handler class associated with the determined source type."""
        if self == FileSourceType.ANALYZER:
            from .filehandler import AnalyzerFileHandler
            return AnalyzerFileHandler
        elif self == FileSourceType.NETDI:
            from .filehandler import NetDIFileHandler
            return NetDIFileHandler
        elif self == FileSourceType.STREAM:
            from .filehandler import StreamFileHandler
            return StreamFileHandler
        elif self == FileSourceType.INTERNAL:
            from .filehandler import InternalFileHandler
            return InternalFileHandler
        else:
            return None
    
    @classmethod
    def from_string(cls, value: str):
        """Determines the source type from a string.
        Looks up and returns the enum member whose value matches the given string.
        """
        for source in cls:
            if source.value == value:
                return source
        raise ValueError(f"Invalid source type: {value}")

    @classmethod
    def from_header(cls, file_path):
        """Infer the source type by inspecting the file header content and the parent directory name."""
        from .filehandler import FileHandlerInterface
        print('Try to estimate source type from header...')
        file_path = Path(file_path)
        header = FileHandlerInterface.parse_header(file_path)
        if header is None:
            raise ValueError("Could not determine source type from header. Please specify using the respective option.")
        elif '$PSDS0' in header:
            return FileSourceType.STREAM
        elif 'names' in header:
            if 'analyzer' in file_path.parent.as_posix().lower():
                print("Found 'Analyzer' in file path. Use 'Analyzer' as source type.")
                return FileSourceType.ANALYZER
            elif 'netdi' in file_path.parent.as_posix().lower():
                print("Found 'NetDI' in file path. Use 'NetDI' as source type.")
                return FileSourceType.NETDI
            else:
                print("Use 'Internal' as source type.")
                return FileSourceType.INTERNAL
        else:
            raise ValueError("Could not determine source type from header. Please specify using the respective option.")


class FileSourceModel:
    """Orchestrates reading, cleaning, and processing of OceanPack log files.

    Resolves the appropriate file handler for the configured source type, reads all
    log files into a pandas DataFrame, and exposes the result as an xarray Dataset.
    The source type can be set explicitly or inferred automatically from the file header.
    """

    def __init__(self, source_type: FileSourceType = None) -> None:
        """Initialize the model, optionally setting the source type and resolving the file handler."""
        self._filehandler = None
        self._source_type = None
        self.source_type = source_type
        self._metadata = None
        self.df = None
        self.ds = None
        self.history = ''

    @property
    def source_type(self) -> FileSourceType | None:
        """The active source type used to select the file handler."""
        return self._source_type

    @source_type.setter
    def source_type(self, value: str):
        """Validate and set the source type, resolving the corresponding file handler."""
        if value is None:
            log.warning("Source type not specified. Need to estimate from header during execution of `load_data`.")
            return None
        elif not isinstance(value, str):
            raise TypeError("source_type must be of type str")
        
        if not FileSourceType.isvalid(value):
            valid_values = [m.value for m in FileSourceType]
            raise TypeError(f"source_type is unknown. Valid options are {valid_values}")
        self._source_type = FileSourceType.from_string(value)
        if self._source_type:
            self._filehandler = self._source_type.get_filehandler()

    def load_data(self, path: str):
        """Collect all log files at the given path and read them into a single DataFrame."""
        all_files = collect_files(path)

        if self._source_type is None:
            self._source_type = FileSourceType.from_header(all_files[0])

        if self._source_type:
            self._filehandler = self._source_type.get_filehandler()

        df_list = []
        for file in tqdm(all_files, unit='file'):
            data_, metadata_ = self._filehandler.read_file(file)
            if self._metadata is None:
                self._metadata = metadata_
            df_list.append(data_)

        self.df = pd.concat(df_list)
        self.history += f'{len(all_files)} files loaded; '

    def clean_data(self):
        """Drops rows with a missing index value and removes duplicate timestamps, keeping the first occurrence."""
        df = self.df
        df = df.loc[df.index.dropna()]
        self.df = df[~df.index.duplicated(keep='first')]
        self.history += 'Removed duplicates; '

    def process_data(self):
        """Casts all columns to numeric, drops any that cannot be converted, sorts by index, and builds the xarray Dataset."""
        df = self.df
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except Exception:
                log.warning(f'Cannot convert {col} to numeric values. Variable will be dropped.')
                df.drop(col, axis=1, inplace=True)
        df.sort_index(axis=0, inplace=True, ascending=True)
        self.history += 'Converted data to numeric values; '
        self.df = df
        self._pandas_to_xarray()
        self._add_metadata_to_xarray()


    def _pandas_to_xarray(self):
        """Converts the internal DataFrame to an xarray Dataset and stores it in ``self.ds``."""
        ds = self.df.to_xarray()
        ds.attrs['source_type'] = self.source_type.value
        self.ds = ds
        self.history += 'Converted pd.DataFrame to xr.Dataset; '

    def _add_metadata_to_xarray(self):
        """Attaches per-variable metadata from the parsed file header as xarray variable attributes."""
        meta = self._metadata.set_index('name')
        for var in self.ds.variables:
            if str(var) in meta.index.values:
                for col in meta.columns:
                    if value := meta.loc[var, col]:
                        self.ds[var].attrs[col] = value


    def to_netcdf(self, output_file):
        """Writes the xarray Dataset to a NetCDF file at the specified path."""
        self.ds.to_netcdf(output_file)


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
