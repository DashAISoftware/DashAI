export interface IRun {
  id: string;
  model_session_id: string;
  evaluation_strategy: string;
  created: Date;
  last_modified: Date;
  model_name: string;
  parameters: object;
  optimizer_name: string;
  optimizer_parameters: object;
  plot_history_path: string;
  plot_slice_path: string;
  plot_contour_path: string;
  plot_importance_path: string;
  goal_metric: string;
  plot_path: string;
  train_metrics: object;
  test_metrics: object;
  validation_metrics: object;
  full_metrics: object;
  artifacts: object;
  run_name: string;
  run_description: string;
  status: string;
  start_time: Date;
  end_time: Date;
  nested?: object;
}
