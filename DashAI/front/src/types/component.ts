import type { IParameterJsonSchema } from "./configurableObject";
import type { ITaskMetadataParameters } from "./task";

export interface IComponent {
  name: string;
  type: string;
  configurable_object: boolean;
  schema: IParameterJsonSchema;
  metadata: ITaskMetadataParameters;
  description: string;
}
