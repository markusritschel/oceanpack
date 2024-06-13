# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-13
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
import logging
from abc import ABC, abstractmethod

import pandas as pd

log = logging.getLogger(__name__)


class FileHandlerInterface(ABC):
    def __init__(self):
        pass

    @staticmethod
    @abstractmethod
    def read_file(file_path):
        pass


class InternalFileHandler(FileHandlerInterface):
    """File handler for log files created by OceanPack Analyzer or NetDI unit.

    Methods
    -------
    read_file(file_path)
        Reads the log file and returns a data and metadata as :class:`pandas.DataFrame`, respectively.
    """
    @staticmethod
    def read_file(file_path) -> pd.DataFrame:
        """
        Reads the log file and returns a data and metadata as :class:`pandas.DataFrame`, respectively.

        Parameters
        ----------
        file_path : str
            The path to the log file.

        Returns
        -------
        df : pandas DataFrame
            The data from the log file as a DataFrame.
        meta : pandas DataFrame
            The metadata associated with the log file.
        """
        header = InternalFileHandler.parse_header(file_path)
        if not header:
            return pd.DataFrame(), pd.DataFrame()
        
        names = header['names']
        units = header['units']
        sensors = header['sensors']

        data = pd.read_csv(file_path, sep=',', skiprows=header['nrows'], names=names,
                         encoding='iso-8859-1',
                         usecols=range(len(names)),
                        )
        data = data.where(data['@NAME']=='@DATA')
        data.index = pd.to_datetime(data['DATE'] + ' ' + data['TIME'])
        data.index.name = 'time'
        data.drop(['@NAME', 'DATE', 'TIME', 'DATE_TIME'], axis=1, inplace=True, errors='ignore')

        metadata = pd.DataFrame.from_records(list(zip(names, units, sensors))[1:], 
                                             columns=['name', 'unit', 'device'])

        return data, metadata


    @staticmethod
    def parse_header(file_path):
        header_dict = {}
        with open(file_path, 'r', encoding='Windows 1252') as f:
            header_dict['nrows'] = 0
            while True:
                line = f.readline()
                header_dict['nrows'] += 1
                if line.startswith('@RATE') : 
                    break

                elif line.startswith('@NAME'):
                    names = line.strip().split(',')
                    header_dict['names'] = [x.replace('/', '_') for x in names]

                elif line.startswith('@UNIT'):
                    header_dict['units'] = line.strip().split(',')

                elif line.startswith('@SENSOR'):
                    header_dict['sensors'] = line.strip().split(',')

                if header_dict['nrows'] > 15:
                    log.warning(f'Could not find header in file {file_path}. Skip file.')
                    return None
        return header_dict



class AnalyzerFileHandler(InternalFileHandler):
    """File handler for log files created by OceanPack Analyzer unit."""


class NetDIFileHandler(InternalFileHandler):
    """File handler for log files created by OceanPack NetDI unit."""


class StreamFileHandler(FileHandlerInterface):
    """File handler for log files created by OceanPack NetDI unit."""

