# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-13
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
from abc import ABC, abstractmethod


class FileHandlerInterface(ABC):
    def __init__(self):
        pass

    @staticmethod
    @abstractmethod
    def read_file(file_path):
        pass


class InternalFileHandler(FileHandlerInterface):
    """File handler for log files created by OceanPack Analyzer or NetDI unit."""


class AnalyzerFileHandler(InternalFileHandler):
    """File handler for log files created by OceanPack Analyzer unit."""


class NetDIFileHandler(InternalFileHandler):
    """File handler for log files created by OceanPack NetDI unit."""


class StreamFileHandler(FileHandlerInterface):
    """File handler for log files created by OceanPack NetDI unit."""

