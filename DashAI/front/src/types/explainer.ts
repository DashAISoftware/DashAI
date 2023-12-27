export interface IExplainer {
  id: string;
  run_id: string;
  dataset_id: string;
  created_at: Date;
  explainer_name: string;
  explainer_path: string;
}
