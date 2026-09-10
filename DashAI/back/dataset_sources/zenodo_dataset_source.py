"""Zenodo dataset source for DashAI."""

import logging
import os
import re
from typing import Any, Final

import httpx

from DashAI.back.core.utils import MultilingualString
from DashAI.back.dataset_sources.base_dataset_source import (
    BaseDatasetSource,
    DatasetEntry,
    SearchPage,
)

log = logging.getLogger(__name__)

_ZENODO_API = "https://zenodo.org/api"


def _escape_lucene_phrase(s: str) -> str:
    """Escape backslash and double-quote inside a Lucene quoted-string phrase."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _strip_html(text: str) -> str:
    """Remove HTML tags from a string.

    Parameters
    ----------
    text : str
        Raw string possibly containing HTML markup.

    Returns
    -------
    str
        Plain text with HTML tags removed.
    """
    return re.sub(r"<[^>]+>", "", text)


class ZenodoDatasetSource(BaseDatasetSource):
    """Dataset source that fetches public datasets from Zenodo.

    Uses the Zenodo REST API, with no authentication required for public records.
    Pagination is page-based; the cursor encodes the current page number as a
    string.
    """

    DISPLAY_NAME: Final = MultilingualString(
        en="Zenodo",
        es="Zenodo",
        zh="Zenodo",
        de="Zenodo",
        pt="Zenodo",
    )
    DESCRIPTION: Final = MultilingualString(
        en=(
            "Zenodo is an open-access repository operated by CERN that hosts "
            "research datasets, papers, software, and other scientific outputs "
            "from researchers worldwide. It covers all disciplines and accepts "
            "any file format, making it a go-to archive for datasets published "
            "alongside academic papers. Every record gets a DOI, ensuring "
            "long-term citability. Search by keyword and download directly to "
            "dashAI. "
            "[https://zenodo.org](https://zenodo.org)"
        ),
        es=(
            "Zenodo es un repositorio de acceso abierto operado por el CERN que "
            "aloja datasets de investigación, artículos, software y otros "
            "resultados científicos de investigadores de todo el mundo. Cubre "
            "todas las disciplinas y acepta cualquier formato de archivo, siendo "
            "el archivo de referencia para datasets publicados junto a artículos "
            "académicos. Cada registro obtiene un DOI que garantiza su "
            "citabilidad a largo plazo. Busca por palabra clave y descarga "
            "directamente a dashAI. "
            "[https://zenodo.org](https://zenodo.org)"
        ),
        zh=(
            "Zenodo是由CERN运营的开放获取仓库，托管来自全球研究人员的研究数据集、"
            "论文、软件和其他科学成果。它涵盖所有学科并接受任何文件格式，"
            "是学术论文配套数据集的首选档案。每条记录都获得DOI，确保长期可引用性。"
            "按关键词搜索，直接下载到DashAI。"
            "[https://zenodo.org](https://zenodo.org)"
        ),
        de=(
            "Zenodo ist ein Open-Access-Repositorium des CERN, das "
            "Forschungsdatensätze, Artikel, Software und andere wissenschaftliche "
            "Ergebnisse von Forschenden weltweit bereitstellt. Es deckt alle "
            "Disziplinen ab und akzeptiert jedes Dateiformat, wodurch es zum "
            "bevorzugten Archiv für Datensätze wird, die zusammen mit "
            "wissenschaftlichen Publikationen veröffentlicht werden. Jeder "
            "Eintrag erhält einen DOI, der langfristige Zitierbarkeit sicherstellt. "
            "Suche nach Schlagworten und lade direkt in dashAI herunter. "
            "[https://zenodo.org](https://zenodo.org)"
        ),
        pt=(
            "Zenodo e um repositorio de acesso aberto operado pelo CERN que "
            "hospeda conjuntos de dados de pesquisa, artigos, software e outros "
            "resultados cientificos de pesquisadores de todo o mundo. Abrange "
            "todas as disciplinas e aceita qualquer formato de arquivo, sendo o "
            "arquivo de referencia para conjuntos de dados publicados junto a "
            "artigos academicos. Cada registro recebe um DOI, garantindo "
            "citabilidade a longo prazo. Busque por palavra-chave e baixe "
            "diretamente para o dashAI. "
            "[https://zenodo.org](https://zenodo.org)"
        ),
    )

    def search(
        self,
        query: str,
        limit: int = 20,
        cursor: str | None = None,
        **filters: Any,
    ) -> SearchPage:
        """Return public Zenodo datasets matching a query.

        Parameters
        ----------
        query : str
            Free text search string.
        limit : int, optional
            Maximum number of results per page, by default 20.
        cursor : str or None, optional
            Opaque pagination token (encodes the page number as a string).
            Pass ``None`` to fetch the first page.
        **filters : Any
            Supported keys:
              tags (list[str]): Filter by Zenodo keywords. Each tag is
                appended to the query using Lucene ``keywords:"<tag>"``
                syntax (AND logic).

        Returns
        -------
        SearchPage
            Matching datasets and cursor for the next page (or ``None``).
        """
        try:
            page = int(cursor) if cursor else 1
            tags: list[str] = filters.get("tags") or []
            keyword_clauses = " AND ".join(
                f'keywords:"{_escape_lucene_phrase(t)}"' for t in tags
            )
            if query and tags:
                zenodo_q = f"({query}) AND {keyword_clauses}"
            elif tags:
                zenodo_q = keyword_clauses
            else:
                zenodo_q = query
            params: dict[str, Any] = {
                "q": zenodo_q,
                "type": "dataset",
                "page": page,
                "size": limit,
                "status": "published",
            }
            resp = httpx.get(
                f"{_ZENODO_API}/records",
                params=params,
                timeout=15,
            )
            if resp.status_code != 200:
                log.warning("Zenodo API returned %s", resp.status_code)
                return SearchPage()

            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            entries = []
            for record in hits:
                metadata = record.get("metadata", {})
                files = record.get("files", [])
                size_bytes = sum(f.get("size", 0) for f in files) or None
                entries.append(
                    DatasetEntry(
                        id=str(record["id"]),
                        name=metadata.get("title", ""),
                        description=_strip_html(metadata.get("description", "") or ""),
                        tags=metadata.get("keywords", []) or [],
                        size_bytes=size_bytes,
                        url=record.get("links", {}).get("self_html", ""),
                        source=self.__class__.__name__,
                    )
                )

            has_next = "next" in data.get("links", {})
            next_cursor = str(page + 1) if has_next else None
            return SearchPage(entries=entries, next_cursor=next_cursor)
        except Exception:
            log.exception("Error searching Zenodo datasets")
            return SearchPage()

    def get_info(self, dataset_id: str) -> DatasetEntry | None:
        """Return full metadata for a single Zenodo record.

        Parameters
        ----------
        dataset_id : str
            Zenodo record ID (integer as string, e.g. ``"123456"``).

        Returns
        -------
        DatasetEntry or None
            Full metadata entry, or None on error.
        """
        try:
            resp = httpx.get(f"{_ZENODO_API}/records/{dataset_id}", timeout=15)
            resp.raise_for_status()
            record = resp.json()
            metadata = record.get("metadata", {})
            files = record.get("files", [])
            size_bytes = sum(f.get("size", 0) for f in files) or None
            return DatasetEntry(
                id=str(record["id"]),
                name=metadata.get("title", ""),
                description=_strip_html(metadata.get("description", "") or ""),
                tags=metadata.get("keywords", []) or [],
                size_bytes=size_bytes,
                url=record.get("links", {}).get("self_html", ""),
                source=self.__class__.__name__,
            )
        except Exception:
            log.debug("Could not fetch info for Zenodo record %s", dataset_id)
            return None

    def download_dataset(self, dataset_id: str, temp_path: str) -> str:
        """Download all files for a Zenodo record into a local directory.

        Parameters
        ----------
        dataset_id : str
            Zenodo record ID (integer as string, e.g. ``"123456"``).
        temp_path : str
            Local directory to download into.

        Returns
        -------
        str
            Path to the directory containing the downloaded files.

        Raises
        ------
        ValueError
            If the record has no downloadable files.
        """
        files_resp = httpx.get(
            f"{_ZENODO_API}/records/{dataset_id}/files",
            timeout=15,
        )
        files_resp.raise_for_status()
        files = files_resp.json().get("entries", [])

        if not files:
            raise ValueError(f"Zenodo record {dataset_id} has no downloadable files.")

        for file_entry in files:
            filename = file_entry.get("key")
            download_url = file_entry.get("links", {}).get("content")
            if not filename or not download_url:
                log.warning(
                    "Skipping malformed file entry in Zenodo record %s", dataset_id
                )
                continue
            file_resp = httpx.get(download_url, timeout=120, follow_redirects=True)
            file_resp.raise_for_status()
            out_path = os.path.join(temp_path, filename)
            with open(out_path, "wb") as f:
                f.write(file_resp.content)
            log.debug("Downloaded %s → %s", filename, out_path)

        return temp_path
