import api from "./api";
import { ISession } from "../types/session";
import { IGenerativeTask } from "../types/generativeTask";
import { IDocumentResponse } from "../types/documentResponse";
import { IComponent } from "../types/component";
import { IRAGPrompt } from "../types/ragPrompt";
import { RetrieverPresetRecipe } from "../types/retrieverPreset";
import {
  IRAGConfiguration,
  IRAGIndexStatus,
  IRAGPreset,
  IRAGSessionDefaults,
} from "../types/ragConfiguration";
import { getChildComponents } from "./component";

/** The generative task every RAG session belongs to. */
export const RAG_TASK_NAME = "RAGTask";

/** The generative model every RAG session runs on. */
export const RAG_MODEL_NAME = "RAGPipeline";

/**
 * Creates a new RAG prompt via the API.
 * @param prompt - The prompt data (class_name, name, optional parameters).
 * @returns The created prompt metadata containing the new ID.
 */
export const createRAGPrompt = async (prompt: {
  class_name: string;
  name: string;
  parameters?: Record<string, any>;
}): Promise<{ id: number }> => {
  const response = await api.post("/v1/prompt/", prompt);
  if (response.status !== 201) {
    throw new Error(`Failed to create RAG prompt: ${response.statusText}`);
  }
  return response.data;
};

/** Fetches the RAG sessions. Filtering happens server-side. @returns List of RAG sessions. */
export const getRAGSessions = async (): Promise<ISession[]> => {
  const response = await api.get<ISession[]>("/v1/generative-session/", {
    params: { task_name: RAG_TASK_NAME },
  });
  if (response.status !== 200) {
    throw new Error(`Failed to fetch RAG sessions: ${response.statusText}`);
  }

  return response.data;
};

/** Fetches a single RAG session by ID. @param sessionId - The session ID. @returns The session object. */
export const getRAGSession = async (sessionId: number): Promise<ISession> => {
  const response = await api.get<ISession>(
    `/v1/generative-session/${sessionId}`,
  );
  if (response.status !== 200) {
    throw new Error(`Failed to fetch RAG session: ${response.statusText}`);
  }

  return response.data;
};

/**
 * Creates a new RAG session with the given data, forcing task_name to "RAGTask".
 * @param sessionData - Session creation payload (without id/created/last_modified).
 * @returns The created session.
 */
export const createRAGSession = async (
  sessionData: Omit<ISession, "id" | "created" | "last_modified">,
): Promise<ISession> => {
  const transformedSession: Omit<ISession, "id" | "created" | "last_modified"> =
    {
      name: sessionData.name,
      description: sessionData.description,
      task_name: RAG_TASK_NAME,
      model_name: RAG_MODEL_NAME,
      display_name: "",
      parameters: sessionData.parameters,
    };

  const response = await api.post<ISession>(
    "/v1/generative-session/",
    transformedSession,
  );

  if (response.status !== 201) {
    throw new Error(`Failed to create RAG session: ${response.statusText}`);
  }

  return response.data;
};

/** Updates an existing RAG session. @param sessionId - The session ID. @param sessionData - Partial fields to update. @returns The updated session. */
export const updateRAGSession = async (
  sessionId: number,
  sessionData: Partial<ISession>,
): Promise<ISession> => {
  const response = await api.put<ISession>(
    `/v1/generative-session/${sessionId}`,
    sessionData,
  );
  if (response.status !== 200) {
    throw new Error(`Failed to update RAG session: ${response.statusText}`);
  }

  return response.data;
};

/** Deletes a RAG session by ID. @param sessionId - The session ID. */
export const deleteRAGSession = async (sessionId: number): Promise<void> => {
  const response = await api.delete(`/v1/generative-session/${sessionId}`);
  if (response.status !== 204) {
    throw new Error(`Failed to delete RAG session: ${response.statusText}`);
  }
};

/** Updates only the parameters of an existing RAG session. @param sessionId - The session ID. @param newParams - The new parameters payload. @returns The updated session. */
export const updateGenerativeSessionParams = async (
  sessionId: number,
  newParams: Record<string, any>,
): Promise<ISession> => {
  const response = await api.put<ISession>(
    `/v1/generative-session/${sessionId}/parameters`,
    newParams,
  );
  if (response.status !== 200) {
    throw new Error(
      `Failed to update RAG session parameters: ${response.statusText}`,
    );
  }
  return response.data;
};

/** Fetches all available retriever paradigms (children of RetrieverModel). @returns List of retriever paradigm components. */
export const getRetrievalParadigm = async (): Promise<IComponent[]> => {
  const response = await getChildComponents("RetrieverModel", true);
  if (!response) {
    throw new Error(`Failed to fetch retrieval options`);
  }
  return response;
};

/** Fetches child components (specific retrievers) for a given retrieval paradigm. @param retrievalParadigm - Parent paradigm name. @returns List of retriever components. */
export const getRetrieverComponents = async (
  retrievalParadigm: string,
): Promise<IComponent[]> => {
  const response = await getChildComponents(retrievalParadigm, true);

  if (!response) {
    throw new Error(`Failed to fetch retriever components`);
  }

  return response;
};

/**
 * Fetches resolved retriever preset recipes for a given top-K.
 * @param topK - Number of chunks to configure.
 * @returns List of preset recipes ({ key, description, component, params }).
 */
export const getRetrieverPresets = async (
  topK: number,
): Promise<RetrieverPresetRecipe[]> => {
  const response = await api.get("/v1/rag/retriever-presets", {
    params: { top_k: topK },
  });
  if (response.status !== 200) {
    throw new Error(
      `Failed to fetch retriever presets: ${response.statusText}`,
    );
  }
  return response.data;
};

/**
 * Fetches resolved chunking preset recipes.
 * Names and summaries are localized by the backend, so they render as-is.
 * @returns List of chunking presets.
 */
export const getChunkingPresets = async (): Promise<IRAGPreset[]> => {
  const response = await api.get<IRAGPreset[]>("/v1/rag/chunking-presets");
  if (response.status !== 200) {
    throw new Error(`Failed to fetch chunking presets: ${response.statusText}`);
  }
  return response.data;
};

/**
 * Fetches the configuration a new RAG session gets when the user picks none.
 * This is the very same dict the backend applies on create, so showing it is
 * an honest preview rather than a client-side guess.
 * @returns The resolved defaults for chunking, retrieval and prompt.
 */
export const getSessionDefaults = async (): Promise<IRAGSessionDefaults> => {
  const response = await api.get<IRAGSessionDefaults>(
    "/v1/rag/session-defaults",
  );
  if (response.status !== 200) {
    throw new Error(`Failed to fetch session defaults: ${response.statusText}`);
  }
  return response.data;
};

/**
 * Fetches a session's configuration already resolved into friendly labels.
 * @param sessionId - The RAG session ID.
 * @returns Display names, preset labels, labelled parameters and the context budget.
 */
export const getSessionConfiguration = async (
  sessionId: number,
): Promise<IRAGConfiguration> => {
  const response = await api.get<IRAGConfiguration>(
    `/v1/rag/sessions/${sessionId}/configuration`,
  );
  if (response.status !== 200) {
    throw new Error(
      `Failed to fetch session configuration: ${response.statusText}`,
    );
  }
  return response.data;
};

/**
 * Fetches whether a session's documents are indexed for its current config.
 * Read-only: it never triggers indexing, it only reports what the chat job
 * would find.
 * @param sessionId - The RAG session ID.
 * @returns The indexing status, with a localized message ready to render.
 */
export const getSessionIndexStatus = async (
  sessionId: number,
): Promise<IRAGIndexStatus> => {
  const response = await api.get<IRAGIndexStatus>(
    `/v1/rag/sessions/${sessionId}/index-status`,
  );
  if (response.status !== 200) {
    throw new Error(`Failed to fetch index status: ${response.statusText}`);
  }
  return response.data;
};

/** Fetches generator components related to TextToTextGenerationTask. @returns List of generator components. */
export const getGeneratorComponents = async (): Promise<IGenerativeTask[]> => {
  const response = await api.get(
    `/v1/component/?related_component=TextToTextGenerationTask`,
  );

  if (response.status !== 200) {
    throw new Error(
      `Failed to fetch generator components: ${response.statusText}`,
    );
  }

  return response.data;
};

/** Fetches chunking model components (children of BaseChunkingModel). @returns List of chunking components. */
export const getChunkingComponents = async (): Promise<IComponent[]> => {
  const response = await getChildComponents("BaseChunkingModel", false);
  if (!response) {
    throw new Error(`Failed to fetch chunking components`);
  }
  return response;
};

/** Fetches all uploaded documents. @returns List of document responses. */
export const loadDocuments = async (): Promise<IDocumentResponse[]> => {
  const response = await api.get<IDocumentResponse[]>("/v1/document/");
  if (response.status !== 200) {
    throw new Error(`Failed to load documents: ${response.statusText}`);
  }
  return response.data;
};

/** Fetches documents scoped to a specific RAG session. @param sessionId - The session ID. @returns List of document responses. */
export const getSessionDocuments = async (
  sessionId: number,
): Promise<IDocumentResponse[]> => {
  const response = await api.get<IDocumentResponse[]>(
    `/v1/document/session/${sessionId}`,
  );
  if (response.status !== 200) {
    throw new Error(`Failed to load session documents: ${response.statusText}`);
  }
  return response.data;
};

/** Deletes a document by ID. @param documentId - The document ID. */
export const deleteDocument = async (documentId: number): Promise<void> => {
  const response = await api.delete(`/v1/document/${documentId}`);
  if (response.status !== 204) {
    throw new Error(`Failed to delete document: ${response.statusText}`);
  }
};

/**
 * Result of a document upload attempt.
 *
 * When the uploaded file already exists (same content hash) and `force` was
 * not used, the backend answers `409 Conflict`; the result is flagged as
 * `duplicate` and carries the existing document plus the affected sessions so
 * the UI can ask for confirmation before forcing the update.
 */
export type AddDocumentResult =
  | {
      duplicate: false;
      document: IDocumentResponse;
    }
  | {
      duplicate: true;
      existingDocument: IDocumentResponse;
      affectedSessions: { id: number; name: string }[];
    };

/**
 * Uploads a document file with optional metadata via multipart/form-data.
 * @param file - The File object to upload.
 * @param optional_metadata - Optional metadata (name, source, etc.).
 * @param force - If true, overwrite the existing document when a duplicate
 *   (same content hash) is detected.
 * @returns The upload result (created document or duplicate info).
 */
export const addDocument = async ({
  file,
  optional_metadata,
  force = false,
}: {
  file: File;
  optional_metadata?: Record<string, any>;
  force?: boolean;
}): Promise<AddDocumentResult> => {
  if (optional_metadata) {
    optional_metadata.last_modified = file.lastModified;
  }
  const metadata = {
    file_name: file.name,
    last_modified: file.lastModified,
    optional_metadata,
  };

  const formData = new FormData();
  formData.append("file", file);
  formData.append("metadata", JSON.stringify(metadata));

  try {
    const response = await api.post<IDocumentResponse>(
      "/v1/document/",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
        params: force ? { force: "true" } : undefined,
      },
    );

    if (response.status !== 201 && response.status !== 200) {
      throw new Error(`Failed to upload document: ${response.statusText}`);
    }

    return { duplicate: false, document: response.data };
  } catch (error: unknown) {
    // Check if this is an axios error with a 409 response
    if (
      error &&
      typeof error === "object" &&
      "response" in error &&
      error.response &&
      typeof error.response === "object" &&
      "status" in error.response &&
      error.response.status === 409 &&
      "data" in error.response
    ) {
      const detail = (error.response.data as any)?.detail;
      return {
        duplicate: true,
        existingDocument: detail?.existing_document,
        affectedSessions: detail?.affected_sessions ?? [],
      };
    }
    throw error;
  }
};

/** Class name prefix that identifies non-generation prompt types. */
const AUGMENTATION_PROMPT_CLASS_PREFIX = "Augmentation";

/**
 * Checks whether a prompt's class_name corresponds to a generation prompt
 * (i.e. NOT an augmentation prompt).
 *
 * @param className - The prompt component class name to test.
 * @returns `true` if the class is a generation prompt, `false` if it is an augmentation prompt.
 */
export function isGenerationPromptClass(className: string): boolean {
  return !className.includes(AUGMENTATION_PROMPT_CLASS_PREFIX);
}

/** Fetches default prompt components (children of RAGGenerationPrompt). @returns List of default prompt components. */
export const getDefaultPrompts = async (): Promise<IComponent[]> => {
  return getChildComponents("RAGGenerationPrompt", false);
};

/** Fetches all saved RAG prompts (user-created). @returns List of RAG prompts. */
export const getRAGPrompts = async (): Promise<IRAGPrompt[]> => {
  const response = await api.get<IRAGPrompt[]>("/v1/prompt/");
  if (response.status !== 200) {
    throw new Error(`Failed to fetch RAG prompts: ${response.statusText}`);
  }
  return response.data;
};

/**
 * Fetches custom (non-Default) prompt components for the given parent types.
 * @param types - Array of parent component type names to fetch children from.
 * @returns List of custom prompt components (excluding Default* classes).
 */
export const getCustomPrompts = async (
  types: string[] = ["RAGGenerationPrompt", "AugmentationPrompt"],
): Promise<IComponent[]> => {
  let allChildren: IComponent[] = [];
  for (const type of types) {
    const response = await api.get<IComponent[]>(
      `/v1/component/${type}/children`,
      { params: { recursive: false } },
    );
    if (response.status !== 200) {
      throw new Error(
        `Failed to fetch ${type} children: ${response.statusText}`,
      );
    }
    const filtered = response.data.filter(
      (child) =>
        !(
          child.name &&
          typeof child.name === "string" &&
          child.name.includes("Default")
        ),
    );
    allChildren.push(...filtered);
  }
  return allChildren;
};

/** Fetches all available extractor components (children of BaseExtractor). @returns List of extractor components. */
export const getExtractorOptions = async (): Promise<IComponent[]> => {
  const response = await getChildComponents("BaseExtractor", false);
  if (!response) {
    throw new Error(`Failed to fetch extractor options`);
  }
  return response;
};

/**
 * Extracts text from a document using a specified extractor.
 * @param docId - The document ID.
 * @param extractorRef - Optional {component, params} for the extractor to use.
 * @param persist - If false, preview mode (no persistence/invalidation). Defaults to true.
 * @returns Extracted text with metadata.
 */
export const extractDocumentText = async (
  docId: number,
  extractorRef?: { component: string; params?: Record<string, any> },
  persist: boolean = true,
): Promise<{
  text: string;
  extractor: { component: string; params: Record<string, any> };
  char_count: number;
  cached?: boolean;
  created?: boolean;
  updated?: boolean;
}> => {
  const response = await api.post(`/v1/document/${docId}/extract`, {
    extractor: extractorRef,
    persist,
  });
  if (response.status !== 200) {
    throw new Error(`Failed to extract document text: ${response.statusText}`);
  }
  return response.data;
};

/**
 * Persists an extractor choice for a document and optionally invalidates RAG artifacts.
 * @param docId - The document ID.
 * @param extractorRef - The {component, params} for the extractor.
 * @param force - If true, bypass confirmation and invalidate artifacts.
 * @returns The updated document response.
 */
export const updateDocumentExtractor = async (
  docId: number,
  extractorRef: { component: string; params?: Record<string, any> },
  force: boolean = false,
): Promise<IDocumentResponse> => {
  const response = await api.put(`/v1/document/${docId}/extractor`, {
    extractor: extractorRef,
    force,
  });
  if (response.status !== 200) {
    throw new Error(
      `Failed to update document extractor: ${response.statusText}`,
    );
  }
  return response.data;
};
