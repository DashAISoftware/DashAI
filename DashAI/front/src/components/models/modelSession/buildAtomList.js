/**
 * Builds the full, ever-growing list of selectable atoms for the session
 * wizard: every raw dataset column, plus one atom per declared output
 * slot of every converter already configured. Never removes anything,
 * regardless of what a later converter might do to earlier columns (see
 * the design spec, section C).
 */
export function buildAtomList({ datasetColumnTypes, converters }) {
  const columnAtoms = Object.entries(datasetColumnTypes || {}).map(
    ([name, typeInfo]) => ({
      kind: "column",
      name,
      type: typeInfo.type,
      dtype: typeInfo.dtype,
    }),
  );

  const groupAtoms = (converters || []).flatMap((converter) =>
    (converter.metadata?.output_slots || []).map((slot) => ({
      kind: "group",
      converterId: converter.id,
      slot: slot.slot,
      label: slot.label,
      converterName: converter.converter,
      type: slot.type,
    })),
  );

  return [...columnAtoms, ...groupAtoms];
}

/**
 * Synthetic key for a `buildAtomList` atom: a "column" atom's key is just
 * its own name; a "group" atom's key is `__group__${converterId}__${slot}`.
 * This lets the flat `{name: {type, dtype}}` shape ColumnSelector/
 * DivideDatasetColumns expect represent group atoms too, without either of
 * those shared components needing to know about atoms at all. Shared by
 * every session-wizard step that needs this translation (ColumnsStep.jsx,
 * ScopeStepSessionConverter.jsx).
 */
export const atomKey = (atom) =>
  atom.kind === "column"
    ? atom.name
    : `__group__${atom.converterId}__${atom.slot}`;

/**
 * Same key, but for a *real*, backend-shaped atom — the `{kind, name}` /
 * `{kind, converter_id, slot}` shape persisted as input/output columns or
 * an `input_scope` entry — which uses `converter_id` (snake_case, matching
 * the backend schema) rather than a `buildAtomList` atom's `converterId`.
 * Produces the same string as `atomKey` for the same underlying group, so
 * a real atom's key can be looked up directly in a map keyed by `atomKey`.
 */
export const realAtomKey = (atom) =>
  atom.kind === "column"
    ? atom.name
    : `__group__${atom.converter_id}__${atom.slot}`;

/**
 * Translates a `buildAtomList` atom back into the real, backend-shaped
 * atom callers persist (as input/output columns or an `input_scope` entry).
 */
export const toRealAtom = (atom) =>
  atom.kind === "column"
    ? { kind: "column", name: atom.name }
    : { kind: "group", converter_id: atom.converterId, slot: atom.slot };

/**
 * Prunes a previous input/output column selection (given as arrays of
 * synthetic keys) against a freshly-built atom list, dropping any key that
 * no longer resolves to a real atom, then re-seeds whichever side (or
 * both) that pruning left empty.
 *
 * The default-output heuristic prefers the last *column* atom (a real
 * dataset column) over a group atom: a converter's generated output slot
 * is essentially never what someone wants as a default prediction target,
 * even though group atoms sort after column atoms in `buildAtomList`'s
 * output and would otherwise become "the last atom". Falls back to the
 * literal last atom only if there are no column atoms at all.
 *
 * @param {object} params
 * @param {Array} params.atoms the current, full atom list (from `buildAtomList`)
 * @param {string[]} params.previousInputKeys previously-selected input atoms, as synthetic keys
 * @param {string[]} params.previousOutputKeys previously-selected output atoms, as synthetic keys
 * @returns {{inputKeys: string[], outputKeys: string[], atomsByKey: object}}
 */
export function reseedColumnSelection({
  atoms,
  previousInputKeys,
  previousOutputKeys,
}) {
  const atomsByKey = {};
  (atoms || []).forEach((atom) => {
    atomsByKey[atomKey(atom)] = atom;
  });
  const allKeys = Object.keys(atomsByKey);

  const pickDefaultOutputKey = (candidateKeys) => {
    const columnCandidate = [...candidateKeys]
      .reverse()
      .find((key) => atomsByKey[key].kind === "column");
    if (columnCandidate) return columnCandidate;
    return candidateKeys.length > 0
      ? candidateKeys[candidateKeys.length - 1]
      : undefined;
  };

  let nextInputKeys = (previousInputKeys || []).filter(
    (key) => key in atomsByKey,
  );
  let nextOutputKeys = (previousOutputKeys || []).filter(
    (key) => key in atomsByKey,
  );

  if (nextOutputKeys.length === 0) {
    const candidateKeys = allKeys.filter((key) => !nextInputKeys.includes(key));
    const outputKey = pickDefaultOutputKey(candidateKeys);
    nextOutputKeys = outputKey ? [outputKey] : [];
  }

  // Any atom that's neither the resolved output nor already part of the
  // input selection defaults into Input Columns — whether this is the
  // session's very first visit to this step or a converter was just
  // configured on a return trip from Preprocessing. Without this, a
  // converter added after the first visit left its group atom out of
  // Input Columns entirely (present as an option, never pre-selected),
  // while the exact same converter configured before the first visit was
  // pre-selected — a same-feature, different-order inconsistency with no
  // signal to the user about why.
  const selectedSoFar = new Set([...nextInputKeys, ...nextOutputKeys]);
  const newKeys = allKeys.filter((key) => !selectedSoFar.has(key));
  nextInputKeys = [...nextInputKeys, ...newKeys];

  return { inputKeys: nextInputKeys, outputKeys: nextOutputKeys, atomsByKey };
}

/**
 * Locally validates a resolved input/output atom selection against a
 * task's declared type/cardinality requirements, mirroring the exact
 * rules `BaseTask.validate_dataset_for_task` enforces on the backend (see
 * `back/tasks/base_task.py`). Used only when a selection contains a group
 * atom, which the backend's `/model-session/validation` endpoint has no
 * way to resolve (it validates literal column names against a
 * materialized dataset sample) — see ColumnsStep.jsx's `validateColumns`.
 *
 * `taskRequirements` may be `null` (not loaded yet, or a fetch that never
 * recovered) — in that case the selection is treated as NOT valid rather
 * than permissively valid, since there's no real requirement data yet to
 * check against; this closes the window where a group-atom selection
 * could read as "valid" before its own type/cardinality data has arrived.
 *
 * A `null`/missing atom `type` — many converters don't declare a static
 * output type for a slot (e.g. `OneHotEncoder`/`OrdinalEncoder`, whose
 * output width depends on the fitted data) — is never, on its own, a type
 * mismatch: it's simply "unknown", not "incompatible". The real,
 * authoritative type check still happens later at preprocessing/training
 * time via the backend's `prepare_for_task`; this check only exists to
 * give fast feedback in the wizard for the common case, so letting an
 * unknown-type atom through here creates no actual risk.
 *
 * @param {object} params
 * @param {Array} params.inputAtoms resolved input atoms (with `.type`)
 * @param {Array} params.outputAtoms resolved output atoms (with `.type`)
 * @param {object|null} params.taskRequirements the fetched task component
 *   (`taskRequirements.metadata.inputs_types`/`outputs_types`/
 *   `inputs_cardinality`/`outputs_cardinality`), or `null` if not loaded
 * @returns {boolean}
 */
export function isAtomSelectionValidLocally({
  inputAtoms,
  outputAtoms,
  taskRequirements,
}) {
  if (!taskRequirements) return false;
  if (
    (inputAtoms || []).some((atom) => !atom) ||
    (outputAtoms || []).some((atom) => !atom)
  ) {
    return false;
  }

  const metadata = taskRequirements.metadata || {};
  const inputTypes = metadata.inputs_types || [];
  const outputTypes = metadata.outputs_types || [];
  const inputCardinality = metadata.inputs_cardinality;
  const outputCardinality = metadata.outputs_cardinality;

  const typesOk = (atoms, allowedTypes) =>
    !allowedTypes ||
    allowedTypes.length === 0 ||
    atoms.every(
      (atom) => atom.type == null || allowedTypes.includes(atom.type),
    );

  const cardinalityOk = (atoms, cardinality) =>
    cardinality === undefined ||
    cardinality === "n" ||
    atoms.length === Number(cardinality);

  return (
    typesOk(inputAtoms, inputTypes) &&
    typesOk(outputAtoms, outputTypes) &&
    cardinalityOk(inputAtoms, inputCardinality) &&
    cardinalityOk(outputAtoms, outputCardinality)
  );
}
