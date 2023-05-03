import type { IDataset } from "./dataset";
import type { IRun } from "./run";

export interface IExperiment {
  id: string;
  dataset: IDataset;
  task_name: string;
  step: string;
  created: Date;
  last_modified: Date;
  runs: IRun[];
}
