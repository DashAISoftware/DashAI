/**
 * Represents a RAG prompt as returned by the /v1/prompt/ API.
 *
 * Supports both single-template (via `template`) and multi-template
 * (via `templates` keyed by language code) prompt shapes.
 */
export interface IRAGPrompt {
  /** Unique identifier for the prompt. */
  id: number;
  /** Fully qualified component class name (e.g. "CustomRAGGenerationPrompt"). */
  class_name: string;
  /** Human-readable display name. */
  name: string;
  /** ISO timestamp of creation. */
  created?: string;
  /** ISO timestamp of last modification. */
  last_modified?: string;
  /** Parameter bag containing the template(s) and language. */
  parameters: {
    /** Single template string (used for custom/simple prompts). */
    template?: string;
    /** Multi-language template dictionary keyed by language code (used for default prompts). */
    templates?: Record<string, string>;
    /** The language code for the active template. */
    language?: string;
  };
}
