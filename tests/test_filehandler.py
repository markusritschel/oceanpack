import pandas as pd

from oceanpack.app.models.filehandler import AnalyzerFileHandler, FileHandlerInterface


class TestAnalyzerFileHandler:
    def test_read_file(self):
        analyzer_file = "tests/example_op.log"
        file_handler = AnalyzerFileHandler()
        result = file_handler.read_file(analyzer_file)
        assert isinstance(result, tuple)
        assert isinstance(result[0], pd.DataFrame)


class TestParseHeader:
    def test_psds0_line_breaks_immediately(self, tmp_path):
        f = tmp_path / "stream.log"
        f.write_bytes(b"$PSDS0,some,data\n")
        header = FileHandlerInterface.parse_header(f)
        assert "$PSDS0" in header

    def test_rate_line_breaks(self, tmp_path):
        f = tmp_path / "rate.log"
        f.write_bytes(b"@RATE,1\n")
        header = FileHandlerInterface.parse_header(f)
        assert "nrows" in header
        assert "$PSDS0" not in header

    def test_too_many_rows_returns_none(self, tmp_path):
        f = tmp_path / "noheader.log"
        f.write_bytes(b"garbage\n" * 20)
        result = FileHandlerInterface.parse_header(f)
        assert result is None

    def test_read_file_returns_empty_on_no_header(self, tmp_path):
        f = tmp_path / "noheader.log"
        f.write_bytes(b"garbage\n" * 20)
        data, meta = AnalyzerFileHandler.read_file(f)
        assert data.empty
        assert meta.empty
