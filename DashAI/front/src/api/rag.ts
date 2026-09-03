import api from "./api";
import { ISession } from "../types/session";
import { IGenerativeTask } from "../types/generativeTask";
import { IDocumentResponse } from "../types/documentResponse";
import { IComponent } from "../types/component";
import { RetrieverPresetRecipe } from "../types/retrieverPreset";
import {
  IRAGConfiguration,
  IRAGIndexStatus,
  IRAGPreset,
} from "../types/ragConfiguration";
import { getChildComponents } from "./component";

/** The generative task every RAG session belongs to. */
export const RAG_TASK_NAME = "RAGTask";

/** The generative model every RAG session runs on. */
export const RAG_MODEL_NAME = "RAGPipeline";

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
 * When the session already holds this exact file (same content hash), the
 * backend answers `409 Conflict`; the result is flagged as `duplicate` and
 * carries the document the session already has. There is nothing to confirm:
 * the file is in the session either way.
 */
export type AddDocumentResult =
  | {
      duplicate: false;
      document: IDocumentResponse;
    }
  | {
      duplicate: true;
      existingDocument: IDocumentResponse;
    };

/**
 * Uploads a document into a RAG session via multipart/form-data.
 * @param sessionId - The session that will own the document.
 * @param file - The File object to upload.
 * @param optional_metadata - Optional metadata (name, source, etc.).
 * @returns The upload result (created document or duplicate info).
 */
export const addDocument = async ({
  sessionId,
  file,
  optional_metadata,
}: {
  sessionId: number | string;
  file: File;
  optional_metadata?: Record<string, any>;
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
      `/v1/document/session/${sessionId}`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } },
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
      };
    }
    throw error;
  }
};

/** Fetches all available extractor components (children of BaseExtractor). @returns List of extractor components. */
export const getExtractorOptions = async (): Promise<IComponent[]> => {
  const response = await getChildComponents("BaseExtractor", false);
  if (!response) {
    throw new Error(`Failed to fetch extractor options`);
  }
  return response;
};

/** Fetches default prompt components (children of RAGGenerationPrompt). @returns List of default prompt components. */
export const getDefaultPrompts = async (): Promise<IComponent[]> => {
  return getChildComponents("RAGGenerationPrompt", false);
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
 * Persists an extractor choice for a document, re-extracting its text.
 *
 * The chunks and retrievers fitted over the previous extraction are discarded
 * server-side. The document belongs to one session, so nothing else is
 * affected and there is nothing to confirm.
 *
 * @param docId - The document ID.
 * @param extractorRef - The {component, params} for the extractor.
 * @returns The updated document response.
 */
export const updateDocumentExtractor = async (
  docId: number,
  extractorRef: { component: string; params?: Record<string, any> },
): Promise<IDocumentResponse> => {
  const response = await api.put(`/v1/document/${docId}/extractor`, {
    extractor: extractorRef,
  });
  if (response.status !== 200) {
    throw new Error(
      `Failed to update document extractor: ${response.statusText}`,
    );
  }
  return response.data;
};
