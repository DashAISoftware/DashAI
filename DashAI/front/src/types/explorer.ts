export interface IExplorer {
  id: string;
  dataset_id: number;
  created: Date;
  columns: object;
  exploration_type: string;
  parameters: object;
  name: string;
  delivery_time: Date;
  start_time: Date;
  end_time: Date;
  exploration_path: string;
  status: string;
  pinned: boolean;
}
