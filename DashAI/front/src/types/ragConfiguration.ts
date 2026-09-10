/** A single parameter of a RAG component, already paired with its label. */
export interface IRAGConfigParam {
  name: string;
  label: string;
  description: string | null;
  value: unknown;
  is_component: boolean;
}

/** One section of a session's configuration, resolved for display. */
export interface IRAGConfigSection {
  section_name: string;
  component: string;
  /** Friendly name; falls back to the class name only for unknown components. */
  display_name: string | null;
  description: string | null;
  registered: boolean;
  params: IRAGConfigParam[];
  /** Chunking / retrieval only: the preset this configuration corresponds to. */
  preset_key?: string | null;
  preset_display_name?: string | null;
  /** Chunking only: a human summary of the chunk size. */
  summary?: string;
  /** Retrieval only: how many chunks the configuration actually returns. */
  top_k?: number;
  /** Generation model only: availability, resolved server-side. */
  requires_download?: boolean;
  downloaded?: boolean;
  credentials_satisfied?: boolean;
  required_credentials?: string[];
}

/** How much of the model's context window the configuration already spends. */
export interface IRAGContextBudget {
  context_window: number;
  max_tokens: number;
  used_by_chunks: number;
  used_by_prompt: number;
  available: number;
  is_valid: boolean;
}

/** The full resolved configuration of a RAG session. */
export interface IRAGConfiguration {
  chunking_model: IRAGConfigSection;
  retriever_model: IRAGConfigSection;
  prompt: IRAGConfigSection;
  generation_model: IRAGConfigSection;
  context_budget: IRAGContextBudget;
}

/** Indexing state of one document within a session. */
export interface IRAGDocumentIndexState {
  document_id: number;
  file_name: string | null;
  chunks: number;
  indexed: boolean;
}

/** Whether a session's documents are indexed for its current configuration. */
export interface IRAGIndexStatus {
  status: "not_indexed" | "stale" | "indexed";
  chunk_set_id: number | null;
  total_chunks: number;
  retriever_ready: boolean;
  documents: IRAGDocumentIndexState[];
  /** Localized, ready to render as-is. */
  message: string;
}

/** A ready-to-apply component configuration offered as a named preset. */
export interface IRAGPreset {
  key: string;
  display_name: string;
  description: string;
  component: string;
  params: Record<string, unknown>;
}

/** The configuration a new session gets when the user picks nothing. */
export interface IRAGSessionDefaults {
  chunking_model: { component: string; display_name: string; params: object };
  retriever_model: { component: string; display_name: string; params: object };
  prompt: { component: string; display_name: string; params: object };
}
