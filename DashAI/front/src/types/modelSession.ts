import type { IDataset } from "./dataset";
import type { IRun } from "./run";

/**
 * A selectable unit in the session wizard and everything downstream of it:
 * either a literal column of the raw dataset, or the whole output group
 * (one declared slot) of a converter configured earlier in the same
 * session. Mirrors the backend's `ColumnAtom`
 * (`api_v1/schemas/model_sessions_params.py`).
 */
export interface IColumnAtom {
  kind: "column" | "group";
  /** Set when `kind === "column"`: the raw dataset column's name. */
  name?: string;
  /** Set when `kind === "group"`: the id of the source converter. */
  converter_id?: string;
  /** Set when `kind === "group"`: which of that converter's output slots. */
  slot?: number;
}

/**
 * What a session's `input_columns`/`output_columns` and a session
 * converter's `input_scope` actually hold. The plain-string form is the
 * legacy shape (the DB column is untyped JSON, so sessions persisted before
 * output groups existed still read back as flat column names) and is
 * tolerated everywhere a column atom is accepted — see
 * `utils/columnAtoms.js`.
 */
export type SessionColumn = string | IColumnAtom;

/** One declared output slot of a converter instance, as returned by
 * `POST /model-session/converters/output-slots` (real params, not a
 * converter's generic default-params metadata). */
export interface IOutputSlot {
  slot: number;
  label: string;
  type: string | null;
}

export interface ISessionConverter {
  /** Stable per-session id, referenced by later converters' group atoms. */
  id: string;
  converter: string;
  params: Record<string, unknown>;
  /**
   * Replaces the old literal `columns: string[]`: the converter's scope is
   * now expressed as atoms, so it can reference an earlier converter's
   * output group instead of only real column names. An empty list means
   * "every column".
   */
  input_scope: SessionColumn[];
  target_column?: string | null;
}

export interface IModelSession {
  id: string;
  dataset: IDataset;
  task_name: string;
  input_columns: SessionColumn[];
  output_columns: SessionColumn[];
  splits: string;
  converters?: ISessionConverter[];
  converters_invalidated?: boolean;
  // 0=NOT_STARTED, 1=DELIVERED, 2=STARTED, 3=FINISHED, 4=ERROR
  preprocessing_status?: number;
  preprocessing_huey_id?: string | null;
  preprocessed_path?: string | null;
  evaluation_strategy?: string;
  step: string;
  created: Date;
  last_modified: Date;
  runs: IRun[];
}
