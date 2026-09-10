"""DashAI ARFF Dataloader."""

import glob
import shutil
from typing import TYPE_CHECKING, Any, Dict

from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dataloaders.classes.dataloader import BaseDataLoader

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ARFFDataloaderSchema(BaseSchema):
    """Schema for ARFFDataLoader hyperparameters.

    ARFF files are self-describing; no parameters are required.
    """


class ARFFDataLoader(BaseDataLoader):
    """Data loader that ingests tabular data from ARFF files into DashAI datasets.

    Reads Weka ARFF files using scipy, decodes nominal attributes from bytes
    to UTF-8 strings, and converts the result into DashAI datasets. Handles
    multifile uploads via ZIP archives containing train/test/val split folders.
    """

    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".arff", ".zip"})
    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]
    SCHEMA = ARFFDataloaderSchema
    SUPPORTS_NATIVE_TYPES: bool = True
    NATIVE_TYPE_MAPPING: Dict[str, Dict[str, Any]] = {
        "numeric": {"type": "Float", "dtype": "float64"},
        "real": {"type": "Float", "dtype": "float64"},
        "integer": {"type": "Integer", "dtype": "int64"},
        "nominal": {
            "type": "Categorical",
            "dtype": "string",
            "encoder": "one_hot",
        },
        "string": {"type": "Text", "dtype": "string", "encoding": "utf-8"},
        "date": {"type": "Text", "dtype": "string", "encoding": "utf-8"},
    }

    DESCRIPTION: str = MultilingualString(
        en=(
            "Data loader for tabular data in ARFF files "
            "(Weka Attribute-Relation File Format). "
            "ARFF files are self-describing and require no additional parameters."
        ),
        es=(
            "Cargador de datos para datos tabulares en archivos ARFF "
            "(formato Weka Attribute-Relation File Format). "
            "Los archivos ARFF son autodescriptivos y no requieren "
            "parámetros adicionales."
        ),
        pt=(
            "Carregador de dados para dados tabulares em arquivos ARFF "
            "(formato Weka Attribute-Relation File Format). "
            "Os arquivos ARFF são autodescritivos e não requerem "
            "parâmetros adicionais."
        ),
        de=(
            "Datenlader für tabellarische Daten in ARFF-Dateien "
            "(Weka Attribute-Relation File Format). "
            "ARFF-Dateien sind selbstbeschreibend und erfordern keine zusätzlichen "
            "Parameter."
        ),
        zh=(
            "ARFF文件（Weka属性关系文件格式）表格数据加载器。"
            "ARFF文件是自描述的，不需要额外参数。"
        ),
    )
    DISPLAY_NAME: str = MultilingualString(
        en="ARFF Data Loader",
        es="Cargador de Datos ARFF",
        pt="Carregador de Dados ARFF",
        de="ARFF Datenlader",
        zh="ARFF数据加载器",
    )

    def _load_arff_raw(self, filepath: str):
        """Read raw scipy ARFF ``(data, meta)`` tuple.

        Centralises the scipy call so the metadata object (discarded by
        ``_read_arff_file``) is available to ``extract_native_types``.

        Raises
        ------
        datasets.builder.DatasetGenerationError
            If the file cannot be parsed as valid ARFF.
        """
        from datasets.builder import DatasetGenerationError
        from scipy.io import arff

        try:
            return arff.loadarff(filepath)
        except Exception as e:
            raise DatasetGenerationError from e

    def _read_arff_file(self, filepath: str):
        """Read an ARFF file and return a pandas DataFrame.

        Parameters
        ----------
        filepath : str
            Path to the ARFF file.

        Returns
        -------
        pd.DataFrame
            DataFrame with nominal columns decoded from bytes to UTF-8.

        Raises
        ------
        datasets.builder.DatasetGenerationError
            If the file cannot be parsed as valid ARFF.
        """
        import pandas as pd

        data, _ = self._load_arff_raw(filepath)
        arff_df = pd.DataFrame(data)
        for col in arff_df.columns:
            if arff_df[col].dtype == object:
                arff_df[col] = arff_df[col].str.decode("utf-8")
        return arff_df

    @staticmethod
    def _decode_if_bytes(value: Any) -> Any:
        """Return ``value`` UTF-8 decoded if it is bytes, otherwise unchanged."""
        return value.decode("utf-8") if isinstance(value, bytes) else value

    def extract_native_types(
        self,
        filepath_or_buffer: str,
        params: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        """Build the DashAI column-type map from the ARFF header itself.

        Reads the scipy metadata object and converts each declared attribute
        kind (``numeric``, ``integer``, ``real``, ``nominal``, ``string``,
        ``date``) into the same dict shape used by
        ``DashAIPtype.infer_types``. For ``nominal`` attributes the
        category list comes straight from the ARFF header (e.g.
        ``@attribute color {red, green, blue}``), no statistical guess.

        Parameters
        ----------
        filepath_or_buffer : str
            Path to a single ARFF file already on disk.
        params : Dict[str, Any]
            Unused (ARFF needs no parameters).

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Column name -> DashAI type dict.
        """
        _, meta = self._load_arff_raw(filepath_or_buffer)

        native_types: Dict[str, Dict[str, Any]] = {}
        for col_name in meta.names():
            kind, values = meta[col_name]
            kind_key = kind.lower() if isinstance(kind, str) else "string"

            if kind_key in self.NATIVE_TYPE_MAPPING:
                info = self.NATIVE_TYPE_MAPPING[kind_key].copy()
            else:
                info = {"type": "Text", "dtype": "string"}

            if kind_key == "nominal" and values is not None:
                info["categories"] = [self._decode_if_bytes(v) for v in values]

            info["inference_reason"] = {
                "source": "arff_metadata",
                "native_type": kind_key,
                "final_type": info.get("type"),
                "is_categorical": kind_key == "nominal",
            }

            native_types[col_name] = info

        return native_types

    def load_data(
        self,
        filepath_or_buffer: str,
        temp_path: str,
        params: Dict[str, Any],
        n_sample: int | None = None,
    ) -> "DashAIDataset":
        """Load uploaded ARFF files into a DatasetDict.

        Parameters
        ----------
        filepath_or_buffer : str
            Path or URL to an ARFF file or a ZIP archive with split folders.
        temp_path : str
            Temporary directory for file extraction.
        params : Dict[str, Any]
            Dataloader parameters (unused; ARFF is self-describing).
        n_sample : int | None
            Maximum rows to load, or None for all.

        Returns
        -------
        DashAIDataset
            Dataset with loaded data.
        """
        import pandas as pd
        from datasets import Dataset, DatasetDict

        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset

        prepared_path = self.prepare_files(filepath_or_buffer, temp_path)

        if prepared_path[1] == "file":
            arff_df = self._read_arff_file(prepared_path[0])
            if n_sample is not None:
                arff_df = arff_df.head(n_sample)
            dataset_dict = DatasetDict(
                {"train": Dataset.from_pandas(arff_df, preserve_index=False)}
            )
        else:
            train_files = glob.glob(prepared_path[0] + "/train/*")
            test_files = glob.glob(prepared_path[0] + "/test/*")
            val_files = glob.glob(prepared_path[0] + "/val/*") + glob.glob(
                prepared_path[0] + "/validation/*"
            )
            try:
                train_df = pd.concat(
                    [self._read_arff_file(f) for f in sorted(train_files)]
                )
                test_df = pd.concat(
                    [self._read_arff_file(f) for f in sorted(test_files)]
                )
                val_df = pd.concat([self._read_arff_file(f) for f in sorted(val_files)])
                if n_sample is not None:
                    train_df = train_df.head(n_sample)
                    test_df = test_df.head(n_sample)
                    val_df = val_df.head(n_sample)
                dataset_dict = DatasetDict(
                    {
                        "train": Dataset.from_pandas(train_df, preserve_index=False),
                        "test": Dataset.from_pandas(test_df, preserve_index=False),
                        "validation": Dataset.from_pandas(val_df, preserve_index=False),
                    }
                )
            finally:
                shutil.rmtree(prepared_path[0])
        return to_dashai_dataset(dataset_dict)

    def load_preview(
        self,
        filepath_or_buffer: str,
        params: Dict[str, Any],
        n_rows: int = 100,
    ):
        """Load a preview of the ARFF dataset.

        Parameters
        ----------
        filepath_or_buffer : str
            Path to the ARFF file.
        params : Dict[str, Any]
            Unused parameters.
        n_rows : int, optional
            Maximum rows to return. Default is 100.

        Returns
        -------
        pd.DataFrame
            Preview DataFrame.
        """
        arff_df = self._read_arff_file(filepath_or_buffer)
        return arff_df.head(n_rows)
