"""OpenML dataset source for DashAI."""

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Any, Final

import httpx
import openml

from DashAI.back.core.utils import MultilingualString
from DashAI.back.dataset_sources.base_dataset_source import (
    BaseDatasetSource,
    DatasetEntry,
    SearchPage,
)

log = logging.getLogger(__name__)

# get_dataset is thread-safe because ``oslo.concurrency`` is installed (OpenML
# uses its interprocess file locks internally), so calls can be fanned out
# across threads without an extra lock.  The lru_cache on top means repeated
# lookups never touch the network.
#
# Bound the fan-out so a large page does not open dozens of sockets at once.
_MAX_META_WORKERS: Final = 8


@lru_cache(maxsize=1024)
def _fetch_dataset_meta(dataset_id: int) -> tuple[str, tuple[str, ...]]:
    """Fetch description and tags for one OpenML dataset (cached).

    Metadata only - never downloads the data file.  Results are memoized in
    process via ``lru_cache``; OpenML additionally caches the description XML on
    disk, so a cold miss here is still cheap on the second process run.

    Parameters
    ----------
    dataset_id : int
        OpenML dataset ID.

    Returns
    -------
    tuple of (str, tuple of str)
        ``(description, tags)``.  Tags are a tuple so the result stays hashable
        and cacheable.

    Raises
    ------
    Exception
        Propagates any OpenML error so the failure is NOT cached; the caller is
        responsible for isolating it.
    """
    dataset = openml.datasets.get_dataset(
        dataset_id,
        download_data=False,
        download_qualities=False,
        download_features_meta_data=False,
    )
    return (dataset.description or "", tuple(dataset.tag or ()))


class OpenMLDatasetSource(BaseDatasetSource):
    """Dataset source that fetches public datasets from OpenML.

    Uses the OpenML Python library - no authentication required.
    """

    DISPLAY_NAME: Final = MultilingualString(
        en="OpenML",
        es="OpenML",
        zh="OpenML",
        de="OpenML",
        pt="OpenML",
    )
    DESCRIPTION: Final = MultilingualString(
        en=(
            "OpenML is an open science platform dedicated to reproducible machine "
            "learning research. It hosts thousands of curated, benchmark-ready "
            "datasets widely used in academic papers and competitions, covering "
            "classification, regression, and clustering tasks. Datasets are "
            "standardized and versioned, making them ideal for comparing models "
            "and reproducing published results. Search by name and download "
            "directly to dashAI. "
            "[https://www.openml.org](https://www.openml.org)"
        ),
        es=(
            "OpenML es una plataforma de ciencia abierta dedicada a la "
            "investigación reproducible en aprendizaje automático. Aloja miles de "
            "datasets curados y listos para benchmarking, ampliamente utilizados "
            "en artículos académicos y competiciones, cubriendo tareas de "
            "clasificación, regresión y agrupamiento. Los datasets están "
            "estandarizados y versionados, lo que los hace ideales para comparar "
            "modelos y reproducir resultados publicados. Busca por nombre y "
            "descarga directamente a dashAI. "
            "[https://www.openml.org](https://www.openml.org)"
        ),
        zh=(
            "OpenML是一个致力于可重现机器学习研究的开放科学平台。"
            "它托管了数千个精心整理的基准就绪数据集，广泛用于学术论文和竞赛，"
            "涵盖分类、回归和聚类任务。数据集经过标准化和版本控制，"
            "非常适合比较模型和重现已发布结果。按名称搜索，直接下载到DashAI。"
            "[https://www.openml.org](https://www.openml.org)"
        ),
        de=(
            "OpenML ist eine Open-Science-Plattform für reproduzierbare "
            "maschinelle Lernforschung. Sie hostet Tausende kuratierter, "
            "benchmark-fähiger Datensätze, die in wissenschaftlichen Arbeiten "
            "und Wettbewerben weit verbreitet sind und Klassifikations-, "
            "Regressions- sowie Clustering-Aufgaben abdecken. Datensätze sind "
            "standardisiert und versioniert, was sie ideal zum Vergleich von "
            "Modellen und zur Reproduktion veröffentlichter Ergebnisse macht. "
            "Nach Namen suchen und direkt in dashAI herunterladen. "
            "[https://www.openml.org](https://www.openml.org)"
        ),
        pt=(
            "OpenML é uma plataforma de ciência aberta dedicada à pesquisa "
            "reproduzível em aprendizado de máquina. Hospeda milhares de "
            "conjuntos de dados curados e prontos para benchmarking, amplamente "
            "utilizados em artigos acadêmicos e competições, cobrindo tarefas de "
            "classificação, regressão e agrupamento. Os conjuntos de dados são "
            "padronizados e versionados, tornando-os ideais para comparar modelos "
            "e reproduzir resultados publicados. Pesquise por nome e baixe "
            "diretamente para o dashAI. "
            "[https://www.openml.org](https://www.openml.org)"
        ),
    )

    def search(
        self,
        query: str,
        limit: int = 20,
        cursor: str | None = None,
        **filters: Any,
    ) -> SearchPage:
        """Return active OpenML datasets matching a name query.

        Parameters
        ----------
        query : str
            Dataset name search string.
        limit : int, optional
            Maximum number of results, by default 20.
        cursor : str or None, optional
            Opaque pagination token (encodes the numeric offset).  ``None``
            fetches the first page.
        **filters : Any
            Supported keys:
              tags (list[str]): Filter by OpenML tag. Only the first tag is
                used; OpenML's API accepts a single ``tag`` parameter.

        Returns
        -------
        SearchPage
            Matching datasets and cursor for the next page (or ``None``).
        """
        try:
            offset = int(cursor) if cursor else 0
            list_kwargs: dict[str, Any] = {
                "offset": offset,
                "size": limit + 1,
                "status": "active",
                "output_format": "dataframe",
            }
            if query:
                list_kwargs["data_name"] = query
            tags: list[str] = filters.get("tags") or []
            if tags:
                list_kwargs["tag"] = tags[0]
                if len(tags) > 1:
                    log.warning(
                        "OpenML supports only one tag filter; using %r, ignoring %r",
                        tags[0],
                        tags[1:],
                    )

            result = openml.datasets.list_datasets(**list_kwargs)

            rows = result.to_dict("records")

            def _meta(did: str) -> tuple[str, tuple[str, ...]] | None:
                """Fetch enrichment for one id, isolating failures as None."""
                try:
                    return _fetch_dataset_meta(int(did))
                except Exception:
                    # One bad dataset must not break the whole page.
                    log.warning("Could not enrich OpenML dataset %s", did)
                    return None

            # Fan out the per-dataset metadata fetches across threads.  Safe to
            # parallelize because oslo.concurrency makes get_dataset thread-safe;
            # executor.map preserves input order.
            ids = [str(row.get("did", "")) for row in rows]
            workers = min(_MAX_META_WORKERS, len(ids)) or 1
            with ThreadPoolExecutor(max_workers=workers) as pool:
                metas = list(pool.map(_meta, ids))

            entries = []
            for row, did, meta in zip(rows, ids, metas, strict=False):
                description = ""
                dataset_tags: list[str] = []
                if meta is not None:
                    description, real_tags = meta
                    dataset_tags = list(real_tags)
                entries.append(
                    DatasetEntry(
                        id=did,
                        name=row.get("name", "") or "",
                        description=description,
                        tags=dataset_tags,
                        size_bytes=None,
                        url=f"https://www.openml.org/d/{did}",
                        source=self.__class__.__name__,
                    )
                )
            has_next = len(entries) > limit
            if has_next:
                entries = entries[:limit]
            next_cursor = str(offset + limit) if has_next else None
            return SearchPage(entries=entries, next_cursor=next_cursor)
        except Exception:
            log.exception("Error searching OpenML datasets")
            return SearchPage()

    def download_dataset(self, dataset_id: str, temp_path: str) -> str:
        """Download an OpenML dataset's raw data file from its source URL.

        Resolves the dataset's data URL via the OpenML library, then downloads
        that file (typically ARFF) into ``temp_path``.

        Parameters
        ----------
        dataset_id : str
            OpenML dataset ID (integer as string, e.g. ``"61"``).
        temp_path : str
            Local directory to download into.

        Returns
        -------
        str
            Path to the downloaded data file inside ``temp_path``.
        """
        dataset = openml.datasets.get_dataset(
            int(dataset_id),
            download_data=False,
            download_qualities=False,
            download_features_meta_data=False,
        )
        url = dataset.url
        if not url:
            raise FileNotFoundError(
                f"OpenML returned no data URL for dataset '{dataset_id}'."
            )

        resp = httpx.get(url, timeout=120, follow_redirects=True)
        resp.raise_for_status()

        ext = os.path.splitext(url.split("?")[0])[1] or ".dat"
        out_path = os.path.join(temp_path, f"openml_{dataset_id}{ext}")
        with open(out_path, "wb") as f:
            f.write(resp.content)
        return out_path
