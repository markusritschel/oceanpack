import pandas as pd
import pytest
from oceanpack.app.models.filehandler import AnalyzerFileHandler

@pytest.fixture()
def analyzer_file():
    return '/home/markusritschel/PycharmProjects/EUREC4A/data/raw_data/NetDI/200117_001.log'

class TestAnalyzerFileHandler:
    def test_read_file(self, analyzer_file):
        file_handler = AnalyzerFileHandler()
        result = file_handler.read_file(analyzer_file)
        assert isinstance(result, tuple)
        assert isinstance(result[0], pd.DataFrame)
