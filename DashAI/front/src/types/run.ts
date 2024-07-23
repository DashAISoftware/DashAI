export interface IRun {
  id: string;
  experiment_id: string;
  created: Date;
  last_modified: Date;
  model_name: string;
  parameters: object;
  optimizer_name: string;
  optimizer_parameters: object;
  plot_path: string;
  train_metrics: object;
  test_metrics: object;
  validation_metrics: object;
  artifacts: object;
  run_name: string;
  run_description: string;
  status: string;
  start_time: Date;
  end_time: Date;
}
