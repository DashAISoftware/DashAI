export interface IExplorer {
  id: string;
  dataset_id: number;
  created: Date;
  columns: object;
  exploration_type: string;
  parameters: object;
  name: string;
  delivery_time: Date | null;
  start_time: Date | null;
  end_time: Date | null;
  exploration_path: string | null;
  status: ExplorerStatus;
  pinned: boolean;
}

export enum ExplorerStatus {
  NOT_STARTED,
  DELIVERED,
  STARTED,
  FINISHED,
  ERROR,
}
