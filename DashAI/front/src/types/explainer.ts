export interface IExplainer {
  id: string;
  name: string;
  run_id: number;
  explainer_name: string;
  dataset_id: number;
  explanation_path: string;
  plot_path: string;
  parameters: object;
  fit_parameters: object;
  created: Date;
  status: number;
}
