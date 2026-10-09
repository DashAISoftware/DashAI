import type { IParameterJsonSchema } from "./configurableObject";
import type { ITaskMetadataParameters } from "./task";

export interface IComponent {
  name: string;
  type: string;
  configurable_object: boolean;
  schema: IParameterJsonSchema;
  metadata: ITaskMetadataParameters;
  description: string;
  display_name?: string;
  color?: string;
  required_credentials?: string[];
  optional_credentials?: string[];
  credentials_satisfied?: boolean;
  downloaded?: boolean;
}
