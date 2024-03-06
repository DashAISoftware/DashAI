import type { IDataset } from "./dataset";
import type { IRun } from "./run";

export interface IExperiment {
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
}
