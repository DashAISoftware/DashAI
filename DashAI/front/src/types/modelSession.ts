import type { IDataset } from "./dataset";
import type { IRun } from "./run";

export interface IRawColumnRef {
  kind: "raw";
  name: string;
}

export interface IGroupColumnRef {
  kind: "group";
  step: number;
  // One type's columns of the step's output (mutually exclusive with name).
  slot?: string | null;
  // One column of the step's output whose name is known before fit.
  name?: string | null;
}

export type IColumnRef = IRawColumnRef | IGroupColumnRef;

export interface IConverterStep {
  converter: string;
  params: Record<string, unknown>;
  scope: IColumnRef[];
}

// Estimated dataset structure along a session's converter chain, as returned
// by the backend's infer_structure (DashAI/back/preprocessing/structure.py).
export interface IColumnItem {
  kind: "column";
  name: string;
  type: string | null;
  dtype: string | null;
  // null for an original dataset column; otherwise the step that created it.
  origin: number | null;
}

export interface IBlockItem {
  kind: "block";
  step: number;
  slot: string | null;
  label: string;
  type: string | null;
  dtype: string | null;
  // null when the column count is only known after fit.
  count: number | null;
}

export type IStateItem = IColumnItem | IBlockItem;

export interface IStructureMessage {
  code: string;
  params: Record<string, unknown>;
}

export interface IStepStructure {
  status: "ok" | "error" | "blocked";
  state: IStateItem[];
  added: IStateItem[];
  error: IStructureMessage | null;
  warnings: IStructureMessage[];
}

export interface IStructureResult {
  initial: IStateItem[];
  steps: IStepStructure[];
  final: IStateItem[];
  valid: boolean;
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
