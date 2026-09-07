export interface RetrieverPresetRecipe {
  key: string;
  /** Friendly, localized name supplied by the backend. */
  display_name: string;
  description: string;
  component: string;
  params: Record<string, unknown>;
}
