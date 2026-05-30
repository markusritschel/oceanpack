import pytest

from oceanpack.app.models.filehandler import (
    AnalyzerFileHandler,
    InternalFileHandler,
    NetDIFileHandler,
    StreamFileHandler,
)
from oceanpack.app.models.filesource import FileSourceModel, FileSourceType, collect_files


class TestFileSourceTypeGetFilehandler:
    @pytest.mark.parametrize(
        ("source_type", "expected"),
        [
            (FileSourceType.ANALYZER, AnalyzerFileHandler),
            (FileSourceType.NETDI, NetDIFileHandler),
            (FileSourceType.STREAM, StreamFileHandler),
            (FileSourceType.INTERNAL, InternalFileHandler),
        ],
    )
    def test_returns_correct_handler(self, source_type, expected):
        assert source_type.get_filehandler() is expected


def test_filesource_type_from_string_invalid():
    with pytest.raises(ValueError, match="Invalid source type"):
        FileSourceType.from_string("Unknown")


class TestFileSourceModelSourceTypeSetter:
    def test_none_leaves_source_type_unset(self):
        model = FileSourceModel(None)
        assert model.source_type is None

    def test_non_string_raises_type_error(self):
        model = FileSourceModel(None)
        with pytest.raises(TypeError, match="must be of type str"):
            model.source_type = 42

    def test_unknown_string_raises_type_error(self):
        with pytest.raises(TypeError, match="source_type is unknown"):
            FileSourceModel("Unknown")


def test_collect_files_single_file():
    result = collect_files("tests/example_op.log")
    assert len(result) == 1
    assert result[0].name == "example_op.log"


def test_collect_files_directory(tmp_path):
    (tmp_path / "a.log").write_text("data")
    (tmp_path / "b.log").write_text("data")
    result = collect_files(str(tmp_path))
    assert len(result) == 2
    assert all(f.suffix == ".log" for f in result)
