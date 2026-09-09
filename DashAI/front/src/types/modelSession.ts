import type { IDataset } from "./dataset";
import type { IRun } from "./run";

export interface IRawColumnRef {
  kind: "raw";
  name: string;
}

export interface IGroupColumnRef {
  kind: "group";
  step: number;
}

export type IColumnRef = IRawColumnRef | IGroupColumnRef;

export interface IConverterStep {
  converter: string;
  params: Record<string, unknown>;
  scope: IColumnRef[];
}

export type IPreprocessingStatus = "ready" | "pending" | "failed";

export interface IModelSession {
  id: string;
  dataset: IDataset;
  task_name: string;
  input_columns: string;
  output_columns: string;
  splits: string;
  step: string;
  created: Date;
  last_modified: Date;
  runs: IRun[];
  preprocessing?: IConverterStep[];
  input_column_refs?: IColumnRef[];
  preprocessing_status?: IPreprocessingStatus;
  preprocessing_error?: string | null;
  preprocessing_job_id?: string | null;
}
