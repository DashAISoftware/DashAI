import * as Yup from "yup";
import type { RAGProgressPayload } from "../../types/process";

/**
 * Strips trailing "Task" and "Generation" suffixes from a task name
 * to produce a human-readable base used for auto-naming sessions.
 */
export function formatTaskNameForSession(taskName: string): string {
  if (!taskName) return "";
  return taskName.replace(/Task$/, "").replace(/Generation$/, "");
}

export type SchemaProperty = {
  type: string | string[];
  title?: string;
  nullable?: boolean;
  minimum?: number;
  maximum?: number;
  minLength?: number;
  maxLength?: number;
  default?: any;
  placeholder?: any;
  [key: string]: any;
};

export type SchemaProperties = {
  [key: string]: SchemaProperty;
};

/**
 * Preprocesses the schema properties to handle nullable types.
 * If a property has an `anyOf` with two items, where the second is `null`,
 * it replaces the property with the first item and marks it as nullable.
 *
 * @param properties - The schema properties to preprocess.
 * @returns The preprocessed schema properties.
 */
export function preprocessSchema(
  properties: SchemaProperties,
): SchemaProperties {
  const newProps = { ...properties };

  for (const key in newProps) {
    if (!("anyOf" in newProps[key])) continue;

    if (newProps[key].anyOf.length !== 2) continue;

    if (newProps[key].anyOf[1].type === "null") {
      let replaceProp = newProps[key].anyOf[0];
      replaceProp.title = newProps[key].title;
      replaceProp.nullable = true;
      newProps[key] = replaceProp;
    }
  }
  return newProps;
}

/**
 * Builds a Yup validation schema from the given properties.
 * It supports various types like integer, number, string, and boolean,
 * and applies constraints based on the property definitions.
 *
 * @param properties - The schema properties to build the Yup schema from.
 * @returns A Yup object schema.
 */
export function buildYupSchema(
  properties: SchemaProperties,
): Yup.ObjectSchema<any> {
  const shape: Record<string, any> = {};
  for (const key in properties) {
    const prop = properties[key];
    let validator;
    switch (prop.type) {
      case "integer":
      case "number":
        validator = Yup.number();
        if (prop.minimum !== undefined) validator = validator.min(prop.minimum);
        if (prop.maximum !== undefined) validator = validator.max(prop.maximum);
        if (prop.type === "integer") validator = validator.integer();
        break;
      case "string":
        validator = Yup.string();
        if (prop.minLength !== undefined)
          validator = validator.min(prop.minLength);
        if (prop.maxLength !== undefined)
          validator = validator.max(prop.maxLength);
        break;
      case "boolean":
        validator = Yup.boolean();
        break;
      default:
        validator = Yup.mixed();
    }
    if (prop.nullable === true) {
      // Yup rejects null unless told otherwise, which is exactly the value a
      // nullable field holds when the user leaves it empty.
      validator = validator.nullable();
    } else if (prop.default === undefined) {
      validator = validator.required("Required");
    }
    shape[key] = validator;
  }
  return Yup.object().shape(shape);
}

export const RAG_QUERIES_DATA_TYPE = "Queries";
export const RAG_REFERENCE_DATA_TYPE = "Dict";
export const RAG_TRACE_DATA_TYPE = "Trace";
export const RAG_TIMINGS_DATA_TYPE = "Timings";
export const RAG_MESSAGE_DATA_TYPE = "str";

export const RAG_PROGRESS_STAGE_TRANSFORMING = "transforming";
export const RAG_PROGRESS_STAGE_RETRIEVING = "retrieving";
export const RAG_PROGRESS_STAGE_GENERATING = "generating";

/**
 * Partitions a RAG process's output rows by their data_type.
 *
 * New processes store five rows: a "Queries" JSON list, a "Dict" sources map,
 * a "Trace" JSON retrieval trace, a "Timings" JSON stage-duration map and a
 * "str" answer. Older processes omit the "Timings" and/or "Trace" rows, and
 * legacy ones store only "Dict" and "str" (no "Queries" either). Rows are
 * matched by data_type, never by position, so every format is handled.
 * Null/undefined rows are ignored.
 *
 * @param output - The process output rows, possibly null or empty.
 * @returns The first query row, the first reference row, the first trace row
 *   (or null when absent), and the message rows (every row that is neither a
 *   query, reference, trace nor timings row).
 */
export function splitRAGOutputRows<T extends { data_type?: string }>(
  output: Array<T | undefined | null> | undefined | null,
): {
  queryRow: T | null;
  referenceRow: T | null;
  traceRow: T | null;
  messageRows: T[];
} {
  let queryRow: T | null = null;
  let referenceRow: T | null = null;
  let traceRow: T | null = null;
  const messageRows: T[] = [];

  for (const row of output ?? []) {
    if (!row) continue;
    if (row.data_type === RAG_QUERIES_DATA_TYPE) {
      queryRow = queryRow ?? row;
    } else if (row.data_type === RAG_REFERENCE_DATA_TYPE) {
      referenceRow = referenceRow ?? row;
    } else if (row.data_type === RAG_TRACE_DATA_TYPE) {
      traceRow = traceRow ?? row;
    } else if (row.data_type === RAG_TIMINGS_DATA_TYPE) {
      // Stage durations are not rendered yet; dropping the row here keeps it
      // from ever being mistaken for a message.
    } else {
      messageRows.push(row);
    }
  }

  return { queryRow, referenceRow, traceRow, messageRows };
}

/**
 * Parses a RAG "Trace" output row's JSON payload.
 *
 * Malformed or missing trace data resolves to null rather than throwing, so a
 * corrupt row can never crash the chat render.
 *
 * @param traceRow - The trace row, possibly null.
 * @returns The parsed trace payload, or null when absent/unparseable.
 */
export function parseRAGTraceRow(
  traceRow: { data?: string } | null | undefined,
): unknown {
  if (!traceRow || typeof traceRow.data !== "string") return null;
  try {
    return JSON.parse(traceRow.data);
  } catch {
    return null;
  }
}

export type RAGProgressText = {
  key?: string;
  values?: Record<string, string>;
  text?: string;
  detail?: string;
};

/**
 * Resolves a known RAG stage to its localized fallback status.
 *
 * @param progress - The process progress payload.
 * @returns The i18n key and interpolation values, or null for an unknown or
 *   incomplete stage payload.
 */
function resolveRAGStageText(
  progress: RAGProgressPayload,
): RAGProgressText | null {
  switch (progress.stage) {
    case RAG_PROGRESS_STAGE_TRANSFORMING:
      return { key: "generative:rag.chatProgress.transformingQuery" };
    case RAG_PROGRESS_STAGE_RETRIEVING: {
      const queries = progress.queries;
      if (!Array.isArray(queries)) return null;
      const normalized = queries
        .filter((query) => typeof query === "string")
        .map((query) => query.trim())
        .filter((query) => query.length > 0);
      if (normalized.length === 0) return null;
      return {
        key: "generative:rag.chatProgress.searchingSources",
        values: { queries: normalized.join("; ") },
      };
    }
    case RAG_PROGRESS_STAGE_GENERATING:
      return { key: "generative:rag.chatProgress.generatingAnswer" };
    default:
      return null;
  }
}

/**
 * Maps a live RAG process `progress` payload to a status line.
 *
 * The backend reports `process.progress` as null (or omits it on older
 * payloads) until a RAG run starts, then advances it through the stages
 * `{"stage":"transforming"}`, `{"stage":"retrieving","queries":[...]}` (a
 * non-empty list of strings), and `{"stage":"generating"}`, finally resetting
 * it to null when the answer or an error arrives.
 *
 * LLM-backed stages may add `message` (a short user-facing sentence) and
 * `justification` (a short rationale). A non-empty `message` replaces the
 * localized fallback and the justification becomes the secondary `detail` line.
 * Without a message, a non-empty justification is appended as `detail` to the
 * stage fallback. Empty/whitespace-only narrative is ignored.
 *
 * Anything unrecognized (null/undefined, a non-object, a missing or unknown
 * stage with no message/detail, or a retrieving payload without a non-empty
 * string array and no narrative) resolves to null so the caller can fall back
 * to the generic waiting bubble instead of rendering an empty or broken status.
 * A retriever narrative update may omit `queries`; a justification-only update
 * still renders the justification as the primary line.
 * Note the payload is deliberately defensive: it may be absent on older
 * responses, so undefined is treated exactly like null.
 *
 * @param progress - The process progress payload, possibly null or undefined.
 * @returns The message/fallback text, the i18n key and interpolation values,
 *   and an optional detail line; or null when no status should be shown.
 */
export function resolveRAGProgressText(
  progress: RAGProgressPayload | null | undefined,
): RAGProgressText | null {
  if (!progress || typeof progress !== "object") return null;

  const message =
    typeof progress.message === "string" ? progress.message.trim() : "";
  const justification =
    typeof progress.justification === "string"
      ? progress.justification.trim()
      : "";
  const detail = justification || undefined;

  if (message) {
    return detail ? { text: message, detail } : { text: message };
  }

  const stageText = resolveRAGStageText(progress);
  if (!stageText) {
    return detail ? { text: detail } : null;
  }
  return detail ? { ...stageText, detail } : stageText;
}
