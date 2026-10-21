"""Helpers that keep a copy of the file a document is parsed from."""

import hashlib
import shutil
from pathlib import Path
from typing import Tuple

from DashAI.back.core.schema_fields import schema_field, string_field
from DashAI.back.core.utils import MultilingualString


def source_directory_field():
    """Build the schema field for the directory a source file is copied into.

    Returns
    -------
    Any
        The annotated ``path`` field shared by the source storing units.
    """
    return schema_field(
        string_field(),
        placeholder="",
        description=MultilingualString(
            en="Directory the original file is copied into, so the document "
            "keeps its source even after the upload or the download is gone.",
            es="Directorio al que se copia el archivo original, para que el "
            "documento conserve su origen aunque la subida o la descarga ya no "
            "existan.",
            pt="Diretório para onde o ficheiro original é copiado, para que o "
            "documento mantenha a sua origem mesmo depois de o carregamento ou "
            "a descarga desaparecerem.",
            de="Verzeichnis, in das die Originaldatei kopiert wird, damit das "
            "Dokument seine Quelle behält, auch wenn der Upload oder der "
            "Download nicht mehr existiert.",
            zh="原始文件被复制到的目录，即使上传或下载内容已不存在，文档也能保留其来源。",
        ),
        alias=MultilingualString(
            en="Source directory",
            es="Directorio de origen",
            pt="Diretório de origem",
            de="Quellverzeichnis",
            zh="源文件目录",
        ),
    )


def sha256(path: Path) -> str:
    """Hash a file in 1 MiB chunks.

    Parameters
    ----------
    path : pathlib.Path
        The file to hash.

    Returns
    -------
    str
        The hexadecimal sha256 digest.
    """
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def store_source(source: str, directory: str, file_name: str) -> Tuple[str, str]:
    """Copy a file into a directory under a given name and hash the copy.

    A plain helper: takes and returns values, never touches the context.

    Parameters
    ----------
    source : str
        File to copy.
    directory : str
        Destination directory, created when missing.
    file_name : str
        Name of the copy.

    Returns
    -------
    Tuple[str, str]
        The path of the copy and its sha256 digest.
    """
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    stored = destination / file_name
    shutil.copyfile(source, stored)
    return str(stored), sha256(stored)
