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

