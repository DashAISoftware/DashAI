export enum PluginStatus {
  REGISTERED = 0,
  DOWNLOADED = 1,
  INSTALLED = 2,
  ERROR = 3,
}

interface ITag {
  id: number;
  name: string;
  plugin_id: number;
}
export interface IPlugin {
  id: number;
  name: string;
  author: string;
  tags: ITag[];
  status: PluginStatus;
  summary: string;
  description: string;
  description_content_type: string;
  created: Date;
  last_modified: Date;
}
