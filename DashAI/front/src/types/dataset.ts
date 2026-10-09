export interface IDataset {
  id: string;
  name: string;
  status: string;
  created: Date;
  last_modified: Date;
  file_path: string;
  total_rows?: number | null;
  total_columns?: number | null;
  folder_id?: number | null;
}

export interface DatasetPage {
  rows: Record<string, any>[];
  total: number;
}
