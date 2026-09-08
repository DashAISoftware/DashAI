/**
 * Shared helpers for the "column atom" shape a model session persists in
 * `input_columns`/`output_columns` (and a session converter persists in its
 * own `input_scope`) since converter output groups were introduced.
 *
 * An atom is either
 *   - `{kind: "column", name: "SepalLengthCm"}` — a literal raw dataset
 *     column, or
 *   - `{kind: "group", converter_id: "conv_0", slot: 0}` — the whole output
 *     group (one declared slot) of a converter configured earlier in the
 *     same session.
 *
 * A bare string is also accepted everywhere here: the DB column is untyped
 * JSON, so sessions persisted before this feature (and a few callers that
 * still pass flat `string[]`) can still be read back as plain column names.
 * A bare string is unambiguously a raw-column reference — the same
 * backward-compatibility rule the backend applies in
 * `dataset_split_utils._atom_names_if_all_columns` and
 * `session_preprocessing_job.resolve_final_columns`.
 *
 * These live in `utils/` rather than next to the session wizard's own
 * `buildAtomList.js` because the consumers are spread across the *post*-
 * creation screens too (predictions, explanations, run results), and the
 * exact same shape landing wrong in many places is what caused several
 * crashes ("Objects are not valid as a React child") and silent
 * mis-comparisons (`col !== targetColumn` against an object) before.
 */

/**
 * The real raw dataset column name an atom refers to, or `null` when there
 * isn't one.
 *
 * A `group` atom deliberately returns `null`: its real column names/count
 * only exist after the session's converters have actually been fitted, so
 * they cannot be resolved against a raw dataset here. Every caller that
 * needs a raw column name (indexing a dataset sample, matching a table
 * column key, excluding the target from an input form) must treat `null`
 * as "no raw column", never as a name.
 */
export const atomColumnName = (atom) => {
  if (atom == null) return null;
  if (typeof atom === "string") return atom;
  if (atom.kind === "column") return atom.name ?? null;
  return null;
};

/**
 * Every real raw column name in an atom list, with group atoms dropped
 * (see `atomColumnName`). Useful for membership checks against raw
 * dataset column keys, e.g. "every raw column except the target".
 */
export const atomColumnNames = (atoms) =>
  (atoms || []).map(atomColumnName).filter((name) => name != null);

/**
 * Stable identity key for an atom, comparable across the legacy string
 * form and the object form: a column atom's identity is its own name, a
 * group atom's is its `converter_id` + `slot`. Produces the same string as
 * the session wizard's `realAtomKey` (see
 * `components/models/modelSession/buildAtomList.js`) for the same atom, so
 * keys are interchangeable between the wizard and these screens.
 */
export const atomIdentityKey = (atom) => {
  if (atom == null) return null;
  if (typeof atom === "string") return atom;
  if (atom.kind === "column") return atom.name ?? null;
  if (atom.kind === "group") {
    return `__group__${atom.converter_id}__${atom.slot}`;
  }
  return null;
};

/**
 * Whether two values refer to the same atom, regardless of whether either
 * side is a legacy plain string or an atom object. Never true for a pair
 * whose identity can't be determined (a malformed atom, `null`).
 */
export const isSameAtom = (a, b) => {
  const keyA = atomIdentityKey(a);
  const keyB = atomIdentityKey(b);
  return keyA != null && keyA === keyB;
};

/**
 * Membership check for an atom list that works when either side is a plain
 * string or an atom object — the atom-aware replacement for
 * `columns.includes(col)`, which silently never matches once the list
 * holds objects and `col` is a raw column name (or vice versa).
 */
export const atomListIncludes = (atoms, value) =>
  (atoms || []).some((atom) => isSameAtom(atom, value));

/**
 * Turns one atom into a human-readable display string.
 *
 * A `group` atom is resolved back to its owning converter (via the
 * session's own `converters` list) and that converter's declared
 * output-slot label (via the fetched `Converter` component list's
 * `metadata.output_slots`), producing the same "ConverterName: slot label"
 * convention the session wizard's column picker uses.
 *
 * Both context lists are optional: without `converterTools` the converter's
 * raw component name and the bare slot number are used, which is still
 * readable, so screens that would otherwise have no reason to fetch the
 * component list don't have to. Falls back to `unknownLabel` only when the
 * atom itself can't be interpreted at all.
 *
 * @param {object|string|null} atom the atom to format
 * @param {object} [context]
 * @param {Array} [context.converters] the session's `converters` list
 * @param {Array} [context.converterTools] the fetched `Converter` components
 * @param {string} [context.unknownLabel] shown when the atom can't be resolved
 * @returns {string}
 */
export function formatColumnAtom(atom, context = {}) {
  const {
    converters = [],
    converterTools = [],
    unknownLabel = "—",
    converterDisplayNames = null,
  } = context;

  if (atom == null) return unknownLabel;
  if (typeof atom === "string") return atom;
  if (atom.kind === "column") return atom.name ?? unknownLabel;
  if (atom.kind === "group") {
    const sourceConverter = (converters || []).find(
      (converter) => converter.id === atom.converter_id,
    );
    if (!sourceConverter) return unknownLabel;
    const toolDefinition = (converterTools || []).find(
      (tool) => tool.name === sourceConverter.converter,
    );
    const converterLabel =
      converterDisplayNames?.[sourceConverter.converter] ||
      toolDefinition?.display_name ||
      sourceConverter.converter;
    const slotDefinition = (toolDefinition?.metadata?.output_slots || []).find(
      (slot) => slot.slot === atom.slot,
    );
    return `${converterLabel}: ${slotDefinition?.label ?? atom.slot}`;
  }
  return unknownLabel;
}

/**
 * `formatColumnAtom` over a whole list, joined for inline display.
 */
export const formatColumnList = (atoms, context = {}) =>
  (atoms || []).map((atom) => formatColumnAtom(atom, context)).join(", ");
