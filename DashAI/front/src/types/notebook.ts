export type NotebookDataKind = "dataset" | "document";

export interface INotebook {
  id: string;
  dataset_id: string | null;
  document_id: number | null;
  data_kind: NotebookDataKind;
  created: Date;
  last_modified: Date;
  file_path: string;
  name: string;
  description: string;
}

export interface INotebookCreate {
  name: string;
  description?: string;
  dataset_id?: number;
  document_id?: number;
}
