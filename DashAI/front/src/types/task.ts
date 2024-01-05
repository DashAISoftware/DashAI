export interface ITask {
  class: string;
  name: string;
  help: string;
  description: string;
  type: string;
}

export interface ITaskMetadataParameters {
  inputs_columns: string[];
  outputs_columns: string[];
  inputs_cardinality: "n" | number;
  outputs_cardinality: "n" | number;
}
