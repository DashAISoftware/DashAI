from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.value_types import Float, Integer, Text


class _FloatIntConverter(BaseConverter):
    SCHEMA = None
    metadata = {
        "allowed_types": [Float, Integer],
        "allowed_dtypes": [],
        "restricted_dtypes": [],
    }

    def get_output_type(self, column_name=None):
        return None

    def fit(self, x, y=None):
        return self

    def transform(self, x, y=None):
        return x


class _DownloadableConverter(BaseConverter):
    SCHEMA = None
    metadata = {}
    REQUIRES_DOWNLOAD = True
    DOWNLOAD_SIZE_BYTES = 1234

    def get_output_type(self, column_name=None):
        return None

    def fit(self, x, y=None):
        return self

    def transform(self, x, y=None):
        return x


class _StarDtypeConverter(BaseConverter):
    SCHEMA = None
    metadata = {"allowed_types": [], "allowed_dtypes": ["*"]}

    def get_output_type(self, column_name=None):
        return None

    def fit(self, x, y=None):
        return self

    def transform(self, x, y=None):
        return x


class _EmptyMetaConverter(BaseConverter):
    SCHEMA = None
    metadata = {}

    def get_output_type(self, column_name=None):
        return None

    def fit(self, x, y=None):
        return self

    def transform(self, x, y=None):
        return x


class _NoneMetaConverter(BaseConverter):
    SCHEMA = None
    metadata = None

    def get_output_type(self, column_name=None):
        return None

    def fit(self, x, y=None):
        return self

    def transform(self, x, y=None):
        return x


def test_get_metadata_serializes_allowed_types_to_name_strings():
    meta = _FloatIntConverter.get_metadata()
    assert meta["allowed_types"] == ["Float", "Integer"]


def test_get_metadata_drops_restricted_dtypes():
    meta = _FloatIntConverter.get_metadata()
    assert "restricted_dtypes" not in meta


def test_get_metadata_normalizes_star_allowed_dtypes_to_empty_list():
    meta = _StarDtypeConverter.get_metadata()
    assert meta["allowed_dtypes"] == []


def test_get_metadata_empty_metadata_produces_empty_lists():
    meta = _EmptyMetaConverter.get_metadata()
    assert meta["allowed_types"] == []
    assert meta["allowed_dtypes"] == []
    assert "restricted_dtypes" not in meta


def test_get_metadata_none_metadata_produces_empty_lists():
    meta = _NoneMetaConverter.get_metadata()
    assert meta["allowed_types"] == []
    assert meta["allowed_dtypes"] == []
    assert "restricted_dtypes" not in meta


def test_get_metadata_plain_converter_not_downloadable():
    meta = _FloatIntConverter.get_metadata()
    assert meta["requires_download"] is False
    assert meta["download_size_bytes"] is None


def test_get_metadata_downloadable_converter_metadata():
    meta = _DownloadableConverter.get_metadata()
    assert meta["requires_download"] is True
    assert meta["download_size_bytes"] == 1234


def test_get_metadata_categorical_text_serialized_correctly():
    class _CatTextConverter(BaseConverter):
        SCHEMA = None
        metadata = {"allowed_types": [Categorical, Text], "allowed_dtypes": ["string"]}

        def get_output_type(self, column_name=None):
            return None

        def fit(self, x, y=None):
            return self

        def transform(self, x, y=None):
            return x

    meta = _CatTextConverter.get_metadata()
    assert meta["allowed_types"] == ["Categorical", "Text"]
    assert meta["allowed_dtypes"] == ["string"]
