"""DashAI base class for dataloaders."""

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Final

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.utils import MultilingualString

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pandas import DataFrame

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class BaseDataLoader(ConfigObject):
    """Abstract class with base methods for DashAI dataloaders.

    Subclasses that handle self-describing formats (formats whose files carry
    explicit column-type metadata, e.g. ARFF, Parquet, Feather) may set
    ``SUPPORTS_NATIVE_TYPES = True`` and implement ``extract_native_types``
    to expose those native types directly, bypassing statistical type
    inference. Subclasses may also declare a ``NATIVE_TYPE_MAPPING`` class
    attribute as a convenient lookup from format-specific type names to
    DashAI type dicts (the same shape produced by ``DashAIPtype.infer_types``).
    """

    TYPE: Final[str] = "DataLoader"
    CATEGORY: Final = MultilingualString(
        en="File Uploading",
        es="Carga de Archivos",
        pt="Carregamento de Arquivos",
        de="Datei-Upload",
        zh="文件上传",
    )
    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset()
    SUPPORTS_NATIVE_TYPES: bool = False
    NATIVE_TYPE_MAPPING: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "category": cls.CATEGORY if cls.CATEGORY else "File Uploading",
            "supported_extensions": sorted(cls.SUPPORTED_EXTENSIONS),
            "supports_native_types": cls.SUPPORTS_NATIVE_TYPES,
        }

    def extract_native_types(
        self,
        filepath_or_buffer: str,
        params: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]] | None:
        """Extract column types from the file's own metadata, if available.

        Default implementation returns ``None``, meaning the format does not
        carry native type info. Subclasses for self-describing formats
        override this and return one entry per column with the same dict
        shape produced by ``DashAIPtype.infer_types`` (keys: ``type``,
        ``dtype``, plus ``categories``/``encoder`` for ``Categorical``).

        Parameters
        ----------
        filepath_or_buffer : str
            Path to the file already prepared on disk (post-ZIP extraction).
        params : Dict[str, Any]
            Dataloader parameters, same dict that ``load_preview`` receives.

        Returns
        -------
        Dict[str, Dict[str, Any]] | None
            Column name -> DashAI type dict, or ``None`` if the format does
            not provide native types.
        """
        return None

    @abstractmethod
    def load_data(
        self,
        filepath_or_buffer: str,
        temp_path: str,
        params: Dict[str, Any],
        n_sample: int | None = False,
    ) -> "DashAIDataset":
        """Load data abstract method.

        Parameters
        ----------
        filepath_or_buffer : str
            An URL where the dataset is located or a FastAPI/Uvicorn uploaded file
            object.
        temp_path : str
            The temporary path where the files will be extracted and then uploaded.
        params : Dict[str, Any]
            Dict with the dataloader parameters.
        n_sample : int | None
            Indicates how many rows load from the dataset, all rows if null.

        Returns
        -------
        DashAIDataset
            A DashAI Dataset with the loaded data.
        """
        raise NotImplementedError

    def load_preview(
        self,
        filepath_or_buffer: str,
        params: Dict[str, Any],
        n_rows: int = 10,
    ) -> "DataFrame":
        """
        Load a preview of the dataset using streaming.

        This is a default implementation that can be overridden by specific dataloaders
        for better performance.

        Parameters
        ----------
        filepath_or_buffer : str
            Path to the file or buffer to load.
        params : Dict[str, Any]
            Parameters for loading the data.
        n_rows : int, optional
            Number of rows to preview. Default is 10.

        Returns
        -------
        DataFrame
            A pandas DataFrame with the preview data.
        """
        raise NotImplementedError(
            "load_preview must be implemented by specific dataloader"
        )

    def prepare_files(self, file_path: str, temp_path: str) -> str:
        """Resolve a file path or URL into a local path suitable for loading.

        Downloads and extracts remote URLs via ``DownloadManager``, extracts
        ZIP archives to a temporary directory, or returns local file paths
        unchanged. The returned tuple distinguishes between directory results
        (multifile or extracted archives) and single-file results.

        Parameters
        ----------
        file_path : str
            Path to a local file, a ZIP archive, or an HTTP(S) URL.
        temp_path : str
            Temporary directory used for extraction of ZIP or URL downloads.

        Returns
        -------
        tuple of (str, str)
            ``(path, type_path)`` where ``type_path`` is ``"dir"`` for
            extracted archives/URLs or ``"file"`` for plain local files.
        """
        from datasets.download.download_manager import DownloadManager

        if file_path.startswith("http"):
            file_path = DownloadManager.download_and_extract(file_path, temp_path)
            return (file_path, "dir")

        if file_path.lower().endswith(".zip"):
            extracted_path = self.extract_files(
                file_path=file_path, temp_path=temp_path
            )
            return (extracted_path, "dir")

        else:
            return (file_path, "file")

    def extract_files(self, file_path: str, temp_path: str) -> str:
        """Extract a ZIP archive into a subdirectory of ``temp_path``.

        Parameters
        ----------
        file_path : str
            Path to the ZIP archive to extract.
        temp_path : str
            Base temporary directory; extraction target is
            ``<temp_path>/files/``.

        Returns
        -------
        str
            Path of the directory containing the extracted files
            (``<temp_path>/files/``).
        """
        import os
        import zipfile

        files_path = os.path.join(temp_path, "files")
        os.makedirs(files_path, exist_ok=True)
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(files_path)
        return files_path
