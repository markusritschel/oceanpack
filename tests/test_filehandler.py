import pandas as pd
import pytest
from oceanpack.app.models.filehandler import AnalyzerFileHandler

class TestAnalyzerFileHandler:
    def test_read_file(self):
        analyzer_file = 'tests/example_op.log'
        file_handler = AnalyzerFileHandler()
        result = file_handler.read_file(analyzer_file)
        assert isinstance(result, tuple)
        assert isinstance(result[0], pd.DataFrame)

