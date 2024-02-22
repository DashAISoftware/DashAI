import type { PluginStatus } from "../pages/plugins/constants/pluginStatus";

interface Tag {
  id: number;
  name: string;
  plugin_id: number;
}
export interface IPlugin {
  id: number;
  name: string;
  author: string;
  tags: Tag[];
  status: PluginStatus;
  summary: string;
  description: string;
  description_content_type: string;
  created: Date;
  last_modified: Date;
}
