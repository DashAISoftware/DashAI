"""HuggingFace Hub dataset source for DashAI."""

import logging
from itertools import islice
from typing import Any, Final

from DashAI.back.core.utils import MultilingualString
from DashAI.back.dataset_sources.base_dataset_source import (
    BaseDatasetSource,
    DatasetEntry,
    SearchPage,
)

log = logging.getLogger(__name__)


class HuggingFaceDatasetSource(BaseDatasetSource):
    """Dataset source that fetches public datasets from HuggingFace Hub.

    Uses ``huggingface_hub.HfApi``, with no authentication required for public
    datasets.  ``HfApi.list_datasets`` exposes an iterator rather than native
    cursors, so pagination is implemented by treating the cursor as a numeric
    offset and slicing the iterator.
    """

    OPTIONAL_CREDENTIALS = ["HuggingFaceCredential"]

    DISPLAY_NAME: Final = MultilingualString(
        en="HuggingFace Hub",
        es="HuggingFace Hub",
        zh="HuggingFace Hub",
        de="HuggingFace Hub",
        pt="HuggingFace Hub",
    )
    DESCRIPTION: Final = MultilingualString(
        en=(
            "HuggingFace Hub is the largest open repository of machine learning "
            "datasets, hosting hundreds of thousands of community-contributed "
            "collections across NLP, computer vision, audio, and tabular tasks. "
            "Datasets range from classic benchmarks to cutting-edge research "
            "splits, and many include multiple configurations or language "
            "variants. Search by name, download directly to dashAI, "
            "and start training in minutes. "
            "[https://huggingface.co/datasets](https://huggingface.co/datasets)"
        ),
        es=(
            "HuggingFace Hub es el repositorio abierto más grande de datasets "
            "para aprendizaje automático, con cientos de miles de colecciones "
            "aportadas por la comunidad para tareas de NLP, visión por "
            "computadora, audio y datos tabulares. Los datasets van desde "
            "benchmarks clásicos hasta particiones de investigación de vanguardia, "
            "y muchos incluyen múltiples configuraciones o variantes de idioma. "
            "Busca por nombre, descarga directamente a dashAI y comienza "
            "a entrenar en minutos. "
            "[https://huggingface.co/datasets](https://huggingface.co/datasets)"
        ),
        zh=(
            "HuggingFace Hub是最大的机器学习数据集开放仓库，托管了数十万个社区贡献的"
            "NLP、计算机视觉、音频和表格任务数据集。数据集涵盖经典基准到前沿研究划分，"
            "许多包含多种配置或语言变体。按名称搜索，直接下载到DashAI，数分钟内开始训练。"
            "[https://huggingface.co/datasets](https://huggingface.co/datasets)"
        ),
        de=(
            "HuggingFace Hub ist das größte offene Repository für maschinelles "
            "Lernen und hostet Hunderttausende von Community-Beiträgen zu NLP-, "
            "Computer-Vision-, Audio- und tabellarischen Aufgaben. Die Datensätze "
            "reichen von klassischen Benchmarks bis hin zu aktuellen "
            "Forschungsaufteilungen, viele mit mehreren Konfigurationen oder "
            "Sprachvarianten. Nach Name suchen, direkt in dashAI herunterladen "
            "und in Minuten mit dem Training beginnen. "
            "[https://huggingface.co/datasets](https://huggingface.co/datasets)"
        ),
        pt=(
            "HuggingFace Hub e o maior repositorio aberto de conjuntos de dados "
            "para aprendizado de maquina, hospedando centenas de milhares de "
            "colecoes contribuidas pela comunidade para tarefas de NLP, visao "
            "computacional, audio e dados tabulares. Os conjuntos de dados variam "
            "de benchmarks classicos a divisoes de pesquisa de ponta, e muitos "
            "incluem multiplas configuracoes ou variantes de idioma. Pesquise por "
            "nome, baixe diretamente para o dashAI e comece a treinar em minutos. "
            "[https://huggingface.co/datasets](https://huggingface.co/datasets)"
        ),
    )

    def search(
        self,
        query: str,
        limit: int = 20,
        cursor: str | None = None,
        **filters: Any,
    ) -> SearchPage:
        """Return public HuggingFace datasets matching a query.

        Parameters
        ----------
        query : str
            Search string passed to ``HfApi.list_datasets``.
        limit : int, optional
            Maximum number of results, by default 20.
        cursor : str or None, optional
            Pagination cursor returned by the previous call (encoded numeric
            offset).  ``None`` fetches the first page.
        **filters : Any
            Supported keys:
              tags (list[str]): Filter by HuggingFace tag strings.
                Passed directly as the ``filter`` argument to ``list_datasets``.

        Returns
        -------
        SearchPage
            Matching datasets and cursor for the next page (or ``None``).
        """
        from huggingface_hub import HfApi

        try:
            offset = int(cursor) if cursor else 0
            tags: list[str] = filters.get("tags") or []

            iterator = HfApi().list_datasets(
                search=query or None,
                full=True,
                limit=offset + limit + 1,
                filter=tags if tags else None,
            )
            window = list(islice(iterator, offset, offset + limit + 1))
            has_next = len(window) > limit
            page = window[:limit]

            entries = [
                DatasetEntry(
                    id=item.id,
                    name=item.id.split("/")[-1],
                    description=getattr(item, "description", "") or "",
                    tags=list(getattr(item, "tags", []) or []),
                    size_bytes=None,
                    url=f"https://huggingface.co/datasets/{item.id}",
                    source=self.__class__.__name__,
                )
                for item in page
            ]

            next_cursor = str(offset + limit) if has_next else None
            return SearchPage(entries=entries, next_cursor=next_cursor)
        except Exception:
            log.exception("Error searching HuggingFace datasets")
            return SearchPage()

    def get_info(self, dataset_id: str) -> "DatasetEntry | None":
        """Return full metadata for a single HuggingFace dataset, including size.

        Parameters
        ----------
        dataset_id : str
            HuggingFace dataset identifier in ``"namespace/repo"`` form.

        Returns
        -------
        DatasetEntry or None
            Full metadata entry, or None on error.
        """
        try:
            from huggingface_hub import HfApi

            item = HfApi().dataset_info(dataset_id)
            return DatasetEntry(
                id=dataset_id,
                name=dataset_id.split("/")[-1],
                description=item.description or "",
                tags=list(item.tags or []),
                size_bytes=item.used_storage,
                url=f"https://huggingface.co/datasets/{dataset_id}",
                source=self.__class__.__name__,
            )
        except Exception:
            log.debug("Could not fetch info for HuggingFace dataset %s", dataset_id)
            return None

    def download_dataset(self, dataset_id: str, temp_path: str) -> str:
        """Download the raw dataset files from HuggingFace Hub.

        Parameters
        ----------
        dataset_id : str
            HuggingFace dataset identifier (e.g. ``"stanfordnlp/imdb"``).
        temp_path : str
            Local directory to download into.

        Returns
        -------
        str
            Path to the directory containing the downloaded files.
        """
        from huggingface_hub import snapshot_download

        # Apply the HuggingFace credential if one is stored; this is a no-op for
        # public datasets and only matters for gated/private ones.
        self.get_credential("HuggingFaceCredential").apply()

        snapshot_download(
            repo_id=dataset_id,
            repo_type="dataset",
            local_dir=temp_path,
            ignore_patterns=["*.md", "*.gitattributes", ".gitattributes"],
        )
        return temp_path
