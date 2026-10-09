import { getDatasetTypesByFilePath } from "../../api/datasets";
import { getNotebookColumns } from "../../api/notebook";

export const isDocumentNotebook = (notebook) =>
  notebook?.data_kind === "document";

export function fetchNotebookColumnTypes(notebook) {
  return isDocumentNotebook(notebook)
    ? getNotebookColumns(notebook.id)
    : getDatasetTypesByFilePath(notebook.file_path);
}
