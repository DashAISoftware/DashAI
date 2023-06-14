import type { IParameterJsonSchema } from "./configurableObject";

export interface IComponent {
  name: string;
  type: string;
  configurable_object: boolean;
  schema: IParameterJsonSchema;
  description: string;
}
