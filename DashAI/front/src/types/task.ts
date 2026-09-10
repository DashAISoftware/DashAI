export interface ITask {
  class: string;
  name: string;
  help: string;
  description: string;
  type: string;
}
export interface ITaskColumnGroup {
  types: string[];
  min: number;
  max: "n" | number;
}

export interface ITaskMetadataParameters {
  inputs?: ITaskColumnGroup[];
  outputs?: ITaskColumnGroup[];
  inputs_columns: string[];
  outputs_columns: string[];
  inputs_cardinality: "n" | number;
  outputs_cardinality: "n" | number;
  requires_download?: boolean;
  download_size_bytes?: number | null;
}
