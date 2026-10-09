export interface IDocumentResponse {
  id: number;
  file_name: string;
  file_type: string;
  file_hash: string;
  created: Date;
  last_modified: Date;
  optional_metadata: Record<string, any> | null;
  related_sessions: number[] | null;
  file_url: string;
  preview_url: string;
  extractor: { component: string; params: Record<string, any> } | null;
  default_extractor: { component: string; params: Record<string, any> } | null;
}
