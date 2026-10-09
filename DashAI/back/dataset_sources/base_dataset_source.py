"""Base classes for DashAI dataset sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Final

from DashAI.back.config_object import ConfigObject
from DashAI.back.core.utils import MultilingualString


@dataclass
class DatasetEntry:
    """Represents a single dataset retrieved from an external source.

    Parameters
    ----------
    id : str
        Source specific unique identifier (e.g. ``"owner/name"`` for HuggingFace).
    name : str
        Human readable dataset name.
    description : str
        Short description of the dataset.
    tags : list[str]
        List of topic/task tags.
    size_bytes : int or None
        Total compressed size in bytes, or None if unknown.
    url : str
        Link to the dataset page on the source website.
    source : str
        Class name of the DatasetSource that produced this entry.
    """

    id: str
    name: str
    description: str
    tags: list[str]
    size_bytes: int | None
    url: str
    source: str


@dataclass
class SearchPage:
    """Result of a paginated dataset search.

    Parameters
    ----------
    entries : list[DatasetEntry]
        Datasets returned by this page.
    next_cursor : str or None
        Opaque token to pass to the next ``search()`` call to get the following
        page.  ``None`` means there are no further results.
    """

    entries: list[DatasetEntry] = field(default_factory=list)
    next_cursor: str | None = None


class BaseDatasetSource(ConfigObject, ABC):
    """Abstract base class for all DashAI dataset sources.

    Subclasses connect to external dataset repositories (HuggingFace Hub,
    OpenML, Kaggle, etc.) and expose a uniform interface for searching,
    previewing, and downloading datasets.
    """

    TYPE: Final[str] = "DatasetSource"
    DISPLAY_NAME: Final = MultilingualString(en="", es="", zh="", pt="", de="")
    DESCRIPTION: Final = MultilingualString(en="", es="", zh="", pt="", de="")

    @abstractmethod
    def search(
        self,
        query: str,
        limit: int = 20,
        cursor: str | None = None,
        **filters: Any,
    ) -> SearchPage:
        """Return datasets matching a query string.

        Parameters
        ----------
        query : str
            Free text search string.
        limit : int, optional
            Maximum number of results, by default 20.
        cursor : str or None, optional
            Opaque pagination token returned by the previous call.  Pass
            ``None`` (default) to fetch the first page.
        **filters : Any
            Source specific filter keyword arguments.

        Returns
        -------
        SearchPage
            Matching datasets and an optional cursor for the next page.
        """
        ...

    def get_info(self, dataset_id: str) -> DatasetEntry | None:
        """Return full metadata for a single dataset, including description and tags.

        The default implementation returns None (no enrichment).
        Sources that require extra requests to retrieve description/tags
        should override this method.

        Parameters
        ----------
        dataset_id : str
            Source specific dataset identifier.

        Returns
        -------
        DatasetEntry or None
            Full metadata entry, or None if not available.
        """
        return None

    @abstractmethod
    def download_dataset(self, dataset_id: str, temp_path: str) -> str:
        """Download the full dataset to a local directory.

        Parameters
        ----------
        dataset_id : str
            Source specific dataset identifier.
        temp_path : str
            Local directory path to download into.

        Returns
        -------
        str
            Path to the downloaded file inside ``temp_path``.
        """
        ...
