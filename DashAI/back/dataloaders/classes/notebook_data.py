"""Where a notebook keeps its data and how tools read it.

A dataset notebook works on a copy of a dataset in ``<file_path>/dataset``;
a document notebook works on a copy of a document in ``<file_path>/document``.
These helpers are the only place that knows the two layouts.
"""

import os
import shutil
import time
from typing import TYPE_CHECKING, Any, Dict, List

from DashAI.back.core.data_kinds import DOCUMENT

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


def notebook_data_path(notebook: Any) -> str:
    """Return the directory of a notebook's working copy.

    Parameters
    ----------
    notebook : Notebook
        The notebook record.

    Returns
    -------
    str
        ``<file_path>/document`` for a document notebook, otherwise
        ``<file_path>/dataset``.
    """
    folder = "document" if notebook.data_kind == DOCUMENT else "dataset"
    return os.path.join(notebook.file_path, folder)


def original_data_path(notebook: Any) -> str:
    """Return the directory the working copy was made from.

    Parameters
    ----------
    notebook : Notebook
        The notebook record.

    Returns
    -------
    str
        The stored document directory for a document notebook, otherwise the
        dataset folder that is copied over the notebook folder.
    """
    if notebook.data_kind == DOCUMENT:
        return os.path.join(notebook.document.file_path, "document")
    return notebook.dataset.file_path


def get_notebook_columns_spec(notebook: Any) -> Dict[str, Dict[str, Any]]:
    """Return the columns tools are checked against.

    Parameters
    ----------
    notebook : Notebook
        The notebook record.

    Returns
    -------
    Dict[str, Dict[str, Any]]
        The dataset columns, or one column per content type, with its item
        count and element kinds, for a document.
    """
    if notebook.data_kind == DOCUMENT:
        from DashAI.back.dataloaders.classes.document_items import (
            get_document_columns_spec,
        )

        return get_document_columns_spec(notebook_data_path(notebook))
    from DashAI.back.dataloaders.classes.dashai_dataset import get_columns_spec

    return get_columns_spec(notebook_data_path(notebook))


def restore_notebook_data(notebook: Any) -> None:
    """Replace the working copy with the original data.

    A document copy is removed first so no converted file survives. A
    dataset copy is overwritten in place and its ``data.arrow`` touched,
    because ``copytree`` keeps the source mtime and the API cache keys on it.

    Parameters
    ----------
    notebook : Notebook
        The notebook record.
    """
    if notebook.data_kind == DOCUMENT:
        working = notebook_data_path(notebook)
        shutil.rmtree(working, ignore_errors=True)
        shutil.copytree(original_data_path(notebook), working)
        return
    shutil.copytree(
        original_data_path(notebook), notebook.file_path, dirs_exist_ok=True
    )
    arrow_path = os.path.join(notebook.file_path, "dataset", "data.arrow")
    if os.path.exists(arrow_path):
        now = time.time()
        os.utime(arrow_path, (now, now))


def load_explorer_input(
    notebook: Any, columns: List[Dict[str, Any]]
) -> "DashAIDataset":
    """Load the dataset an explorer runs on.

    Parameters
    ----------
    notebook : Notebook
        The notebook record.
    columns : List[Dict[str, Any]]
        The explorer's selected columns, each with ``"columnName"``. On a
        document the name is a content type, and ``"kinds"`` and
        ``"positions"`` may narrow the items to some element kinds or to
        exact items.

    Returns
    -------
    DashAIDataset
        The working dataset, or the selected document items: their content
        in a column named after the content type, then the ``kind``,
        ``page`` and ``position`` item columns. Explorers keep only the
        columns they select unless they ask for the item columns.

    Raises
    ------
    ValueError
        If a document explorer selects other than exactly one content type.
    """
    if notebook.data_kind == DOCUMENT:
        from DashAI.back.dataloaders.classes.dashai_document import load_document
        from DashAI.back.dataloaders.classes.document_items import (
            items_with_details,
            selection_from_columns,
        )

        selection = selection_from_columns(columns)
        if len(selection) != 1:
            raise ValueError(
                "An explorer on a document runs on exactly one content type."
            )
        ((type_name, item_filter),) = selection.items()
        document = load_document(notebook_data_path(notebook))
        return items_with_details(document, type_name, item_filter)
    from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset

    return load_dataset(notebook_data_path(notebook))
