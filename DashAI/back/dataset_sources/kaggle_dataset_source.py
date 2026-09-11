"""Kaggle dataset source for DashAI."""

import io
import json
import logging
import tempfile
from contextlib import redirect_stdout
from typing import Any, Final

from DashAI.back.core.utils import MultilingualString
from DashAI.back.dataset_sources.base_dataset_source import (
    BaseDatasetSource,
    DatasetEntry,
    SearchPage,
)

log = logging.getLogger(__name__)

# How many datasets Kaggle puts on one search page. It pages by number, ignores
# ``page_size`` and never fills ``next_page_token``, so the cursor is the page
# number, as in the Zenodo source, and a page shorter than this is the last one.
_KAGGLE_PAGE_SIZE: Final[int] = 20


def _import_kaggle():
    """Import the ``kaggle`` module, suppressing its import time auth noise.

    ``kaggle`` authenticates at import time and prints an authentication help
    block when no credentials are available; that output is not useful to DashAI
    users, so it is suppressed.  The module level ``kaggle.api`` instance is used
    for all calls below.
    """
    with redirect_stdout(io.StringIO()):
        import kaggle

    return kaggle


class KaggleDatasetSource(BaseDatasetSource):
    """Dataset source that fetches public datasets from Kaggle.

    Uses the official ``kaggle`` library (module level ``kaggle.api``).  Public
    datasets can be searched and downloaded without authentication; a stored
    ``KaggleCredential`` is applied when downloading so private or consent gated
    datasets work too.
    """

    OPTIONAL_CREDENTIALS = ["KaggleCredential"]

    DISPLAY_NAME: Final = MultilingualString(
        en="Kaggle",
        es="Kaggle",
        zh="Kaggle",
        de="Kaggle",
        pt="Kaggle",
    )
    DESCRIPTION: Final = MultilingualString(
        en=(
            "Kaggle is the world's largest data science community and hosts a "
            "vast collection of public datasets across every domain: tabular, "
            "NLP, computer vision, and more. Datasets are contributed by "
            "companies, researchers, and community members, and many are "
            "actively maintained with regular updates. Search by name, "
            "download directly to DashAI, and start training in minutes. "
            "[https://www.kaggle.com/datasets](https://www.kaggle.com/datasets)"
        ),
        es=(
            "Kaggle es la comunidad de ciencia de datos más grande del mundo y "
            "aloja una amplia colección de datasets públicos de todos los "
            "dominios: tabulares, NLP, visión por computadora y más. Los "
            "datasets son aportados por empresas, investigadores y miembros de "
            "la comunidad, y muchos se mantienen activamente con actualizaciones "
            "regulares. Busca por nombre, descarga directamente a DashAI y "
            "comienza a entrenar en minutos. "
            "[https://www.kaggle.com/datasets](https://www.kaggle.com/datasets)"
        ),
        zh=(
            "Kaggle是全球最大的数据科学社区，托管着涵盖表格、NLP、计算机视觉等所有领域的大量公共数据集。"
            "数据集由公司、研究者和社区成员贡献，许多数据集定期更新并积极维护。"
            "按名称搜索，直接下载到DashAI，数分钟内开始训练。"
            "[https://www.kaggle.com/datasets](https://www.kaggle.com/datasets)"
        ),
        de=(
            "Kaggle ist die größte Data Science Community der Welt und hostet "
            "eine riesige Sammlung öffentlicher Datensätze aus allen Bereichen: "
            "tabellarisch, NLP, Computer Vision und mehr. Die Datensätze werden "
            "von Unternehmen, Forschern und Community Mitgliedern beigetragen, "
            "viele werden aktiv gepflegt und regelmäßig aktualisiert. Nach Name "
            "suchen, direkt in DashAI herunterladen und in Minuten mit dem "
            "Training beginnen. "
            "[https://www.kaggle.com/datasets](https://www.kaggle.com/datasets)"
        ),
        pt=(
            "Kaggle e a maior comunidade de ciencia de dados do mundo e hospeda "
            "uma vasta colecao de conjuntos de dados publicos de todos os "
            "dominios: tabulares, NLP, visao computacional e mais. Os conjuntos "
            "de dados sao contribuidos por empresas, pesquisadores e membros da "
            "comunidade, e muitos sao mantidos ativamente com atualizacoes "
            "regulares. Pesquise por nome, baixe diretamente para o DashAI e "
            "comece a treinar em minutos. "
            "[https://www.kaggle.com/datasets](https://www.kaggle.com/datasets)"
        ),
    )

    @staticmethod
    def _tag_names(tags: Any) -> list[str]:
        """Extract human readable tag names from a Kaggle tag list.

        Kaggle returns tags as a list of dicts with a ``name`` key; the helper
        tolerates strings and objects with a ``name`` attribute as well.
        """
        names: list[str] = []
        for tag in tags or []:
            if isinstance(tag, dict):
                name = tag.get("name")
            else:
                name = getattr(tag, "name", None) or str(tag)
            if name:
                names.append(str(name))
        return names

    @classmethod
    def _to_entry(cls, item: Any) -> DatasetEntry:
        """Map a kaggle ``ApiDataset`` object to a ``DatasetEntry``."""
        ref = item.ref or ""
        slug = ref.split("/")[-1]
        return DatasetEntry(
            id=ref,
            name=item.title or slug,
            description=(item.description or "") or (item.subtitle or ""),
            tags=cls._tag_names(item.tags),
            size_bytes=item.total_bytes,
            url=f"https://www.kaggle.com/datasets/{ref}",
            source=cls.__name__,
        )

    def search(
        self,
        query: str,
        limit: int = 20,
        cursor: str | None = None,
        **filters: Any,
    ) -> SearchPage:
        """Return Kaggle datasets matching a query.

        Parameters
        ----------
        query : str
            Free text search string.
        limit : int, optional
            Requested page size, by default 20. Passed to Kaggle, which today
            serves ``_KAGGLE_PAGE_SIZE`` datasets a page whatever is asked.
        cursor : str or None, optional
            Page number returned by the previous call as ``next_cursor``.
            ``None`` fetches the first page.
        **filters : Any
            Supported keys:
              sort_by (str): Kaggle dataset sort (e.g. ``"hottest"``).
              tags (list[str]): Comma-joined into Kaggle ``tag_ids``.
              file_type (str): Filter by file type.
              license_name (str): Filter by license.
              user (str): Only datasets owned by this username.

        Returns
        -------
        SearchPage
            Matching datasets and a cursor for the next page (or ``None``).
        """
        kaggle = _import_kaggle()
        try:
            page = int(cursor) if cursor else 1
            sort_by = filters.get("sort_by") or "hottest"
            tag_ids = filters.get("tags")
            if isinstance(tag_ids, list):
                tag_ids = ",".join(tag_ids)
            params: dict[str, Any] = {
                "search": query or None,
                "page": page,
                "page_size": limit,
                "sort_by": sort_by,
            }
            for key in ("tag_ids", "file_type", "license_name", "user"):
                value = {"tag_ids": tag_ids}.get(key, filters.get(key))
                if value:
                    params[key] = value
            response = kaggle.api.dataset_list_with_response(**params)
            entries = [self._to_entry(item) for item in (response.datasets or [])]
            # Kaggle answers with a full page or the tail of the results, never
            # with a token, so a full page is the only sign of a next one. The
            # entries are not trimmed to ``limit``: the next page starts where
            # this one ended, so anything cut here would never be served again.
            has_next = len(entries) >= min(limit, _KAGGLE_PAGE_SIZE)
            next_cursor = str(page + 1) if has_next else None
            return SearchPage(entries=entries, next_cursor=next_cursor)
        except Exception:
            log.exception("Error searching Kaggle datasets")
            return SearchPage()

    def get_info(self, dataset_id: str) -> "DatasetEntry | None":
        """Return full metadata for a single Kaggle dataset.

        Uses ``dataset_metadata`` (writes a JSON file into a temp dir) for the
        description and keywords, and ``dataset_list_files`` for the total size.

        Parameters
        ----------
        dataset_id : str
            Kaggle dataset identifier in ``"owner/dataset-name"`` form.

        Returns
        -------
        DatasetEntry or None
            Full metadata entry, or None on error.
        """
        kaggle = _import_kaggle()
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                meta_file = kaggle.api.dataset_metadata(dataset_id, tmp_dir)
                with open(meta_file, encoding="utf-8") as f:
                    info = json.load(f).get("info", {}) or {}
                files_response = kaggle.api.dataset_list_files(dataset_id)
                size_bytes = sum(
                    int(file.total_bytes or 0) for file in (files_response.files or [])
                )
            title = info.get("title") or dataset_id.split("/")[-1]
            return DatasetEntry(
                id=dataset_id,
                name=title,
                description=info.get("description") or "",
                tags=list(info.get("keywords") or []),
                size_bytes=size_bytes,
                url=f"https://www.kaggle.com/datasets/{dataset_id}",
                source=self.__class__.__name__,
            )
        except Exception:
            log.debug("Could not fetch info for Kaggle dataset %s", dataset_id)
            return None

    def download_dataset(self, dataset_id: str, temp_path: str) -> str:
        """Download a Kaggle dataset's files into ``temp_path``.

        Parameters
        ----------
        dataset_id : str
            Kaggle dataset identifier (e.g. ``"uciml/iris"``).
        temp_path : str
            Local directory to download into.

        Returns
        -------
        str
            Path to the directory containing the downloaded files.
        """
        self.get_credential("KaggleCredential").apply()

        kaggle = _import_kaggle()
        kaggle.api.dataset_download_files(
            dataset_id,
            path=temp_path,
            force=True,
            quiet=True,
            unzip=True,
        )
        return temp_path
