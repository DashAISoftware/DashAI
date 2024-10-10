export interface IExplorer {
  id: string;
  exploration_id: number;
  created: Date;
  last_modified: Date;
  columns: object;
  exploration_type: string;
  parameters: object;
  exploration_path: string | null;
  name: string;
  delivery_time: Date | null;
  start_time: Date | null;
  end_time: Date | null;
  status: ExplorerStatus;
}

export enum ExplorerStatus {
  NOT_STARTED,
  DELIVERED,
  STARTED,
  FINISHED,
  ERROR,
}

export interface IExplorerResults {
  type: string;
  data: object;
  config: object;
}
