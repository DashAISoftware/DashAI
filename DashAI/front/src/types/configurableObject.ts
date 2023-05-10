
export type IPropertiesObject = Record<string, { oneOf: IOneOfItem[] }>;
export type IDefaultValues = Record<string, any>

export interface IOneOfItem {
    default?: any;
    parent?: string;
    description: string;
    type: string;
  };

  export interface IParameterJsonSchema {
    additionalProperties: boolean;
    error_msg: string;
    description: string;
    properties?: IPropertiesObject;
    type:string;
  }