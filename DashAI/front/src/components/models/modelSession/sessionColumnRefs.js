/**
 * Synthetic-key representation of a session's ColumnRef (see the backend's
 * DashAI.back.preprocessing.column_ref module), so every UI piece that
 * already works with a flat list of string column names (Autocomplete
 * options, MaterialReactTable rows, columnTypes maps) can also represent
 * what a converter produces, without knowing converters exist:
 *
 * - an original dataset column is just its own name;
 * - a generated column whose name is known before fit (e.g. DateFeatures'
 *   "date_month") is "__group__{step}__name__{name}";
 * - a block of columns only known after fit (e.g. one-hot columns) is
 *   "__group__{step}", or "__group__{step}__slot__{type}" when the step
 *   outputs blocks of several types, mirroring the backend's
 *   GroupColumnRef.slot and SessionPreprocessor.resolved_slots.
 *
 * Which of these exist at each point of a chain comes from the backend's
 * estimated structure (see usePreprocessingStructure and stateToOptions).
 */

const GROUP_KEY_PREFIX = "__group__";
const SLOT_SEPARATOR = "__slot__";
const NAME_SEPARATOR = "__name__";
// The step, then at most one of a slot or a column name. Only the first
// separator after the step counts, so a slot or column name that itself
// contains a separator stays intact.
const GROUP_KEY_PATTERN = new RegExp(
  `^${GROUP_KEY_PREFIX}(\\d+)(?:${SLOT_SEPARATOR}(.*)|${NAME_SEPARATOR}(.*))?$`,
  "s",
);

export const groupKey = (step, slot = null) =>
  slot == null
    ? `${GROUP_KEY_PREFIX}${step}`
    : `${GROUP_KEY_PREFIX}${step}${SLOT_SEPARATOR}${slot}`;

// A generated column whose name is known before fit (e.g. DateFeatures'
// "date_month"), mirroring the backend's GroupColumnRef.name.
export const namedGroupKey = (step, name) =>
  `${GROUP_KEY_PREFIX}${step}${NAME_SEPARATOR}${name}`;

export const isGroupKey = (key) =>
  typeof key === "string" && key.startsWith(GROUP_KEY_PREFIX);

const parseGroupKey = (key) => {
  const match = GROUP_KEY_PATTERN.exec(key);
  return {
    step: Number(match[1]),
    slot: match[2] ?? null,
    name: match[3] ?? null,
  };
};

export const stepFromGroupKey = (key) => parseGroupKey(key).step;

export const slotFromGroupKey = (key) => parseGroupKey(key).slot;

/** ColumnRef -> synthetic key */
export const refToKey = (ref) => {
  if (ref.kind === "raw") return ref.name;
  if (ref.name != null) return namedGroupKey(ref.step, ref.name);
  return groupKey(ref.step, ref.slot ?? null);
};

/** synthetic key -> ColumnRef */
export const keyToRef = (key) => {
  if (!isGroupKey(key)) return { kind: "raw", name: key };
  const { step, slot, name } = parseGroupKey(key);
  if (name != null) return { kind: "group", step, name };
  return slot == null ? { kind: "group", step } : { kind: "group", step, slot };
};

/**
 * The ColumnRef that points at an item of the estimated dataset structure
 * (see the backend's infer_structure): an original column by name, a
 * generated column by its step and name, a block by its step and slot (a
 * lone block has no slot: it is its step's whole group).
 */
export const itemToRef = (item) => {
  if (item.kind === "column") {
    return item.origin == null
      ? { kind: "raw", name: item.name }
      : { kind: "group", step: item.origin, name: item.name };
  }
  return item.slot == null
    ? { kind: "group", step: item.step }
    : { kind: "group", step: item.step, slot: item.slot };
};

// English text for callers that pass no translation function (e.g. tests).
const englishLabels = (key, params = {}) =>
  ({
    "models:structure.output": "output",
    "models:structure.unknownColumns": "N columns",
    "models:structure.columns":
      params.count === 1 ? "1 column" : `${params.count} columns`,
  })[key] ?? key;

const blockLabel = (block, stepName, t) => {
  const base =
    block.label && block.label !== "output"
      ? `${stepName}: ${block.label}`
      : `${stepName}: ${t("models:structure.output")}`;
  // "N columns" when the column count is only known after fit.
  const size =
    block.count == null
      ? t("models:structure.unknownColumns")
      : t("models:structure.columns", { count: block.count });
  return `${base} (${size})`;
};

/**
 * Selector options for the items of an estimated dataset state: one key per
 * item (the synthetic key of the ColumnRef pointing at it), its type, and a
 * label for every item that is not an original column. Plugs into the same
 * `{allKeys, columnTypes, optionLabels}` shape ColumnSelector and
 * DivideDatasetColumns already take.
 *
 * @param {Array<object>} state items from a StructureResult state
 * @param {string[]} stepDisplayNames one name per step (see
 *   buildStepDisplayNames)
 * @param {Function} [t] i18next translation function for the block labels
 *   ("output", column counts); English when omitted
 */
export function stateToOptions(
  state,
  stepDisplayNames = [],
  t = englishLabels,
) {
  const allKeys = [];
  const columnTypes = {};
  const optionLabels = {};
  (state || []).forEach((item) => {
    const key = refToKey(itemToRef(item));
    allKeys.push(key);
    columnTypes[key] = { type: item.type ?? null, dtype: item.dtype ?? null };
    if (item.kind === "block") {
      optionLabels[key] = blockLabel(
        item,
        stepDisplayNames[item.step] ?? "",
        t,
      );
    } else if (item.origin != null) {
      optionLabels[key] = item.name;
    }
  });
  return { allKeys, columnTypes, optionLabels };
}

/**
 * A label for a ColumnRef without the estimated structure, for sessions
 * that are already created (e.g. the session info panel).
 */
export function labelForRef(ref, stepDisplayNames = [], t = englishLabels) {
  if (ref.kind === "raw") return ref.name;
  if (ref.name != null) return ref.name;
  const stepName = stepDisplayNames[ref.step] ?? `${ref.step}`;
  const output = t("models:structure.output");
  return ref.slot == null
    ? `${stepName}: ${output}`
    : `${stepName}: ${output} (${ref.slot})`;
}

/**
 * One display name per step, disambiguated when the sequence has more than
 * one step of the same converter type (same registry name, or same
 * fallback string when `convertersMeta` hasn't loaded yet): the first
 * occurrence keeps the bare name, later ones get " (2)", " (3)", etc., by
 * order of appearance. Computed over the full `steps` array, so a step's
 * numbering never shifts depending on which view is asking.
 */
export function buildStepDisplayNames(steps, convertersMeta = {}) {
  const baseNames = (steps || []).map(
    (step) => convertersMeta[step?.converter]?.display_name || step?.converter,
  );

  const totalByName = {};
  baseNames.forEach((name) => {
    totalByName[name] = (totalByName[name] || 0) + 1;
  });

  const seenSoFar = {};
  return baseNames.map((name) => {
    if (totalByName[name] <= 1) return name;
    seenSoFar[name] = (seenSoFar[name] || 0) + 1;
    return seenSoFar[name] === 1 ? name : `${name} (${seenSoFar[name]})`;
  });
}

/**
 * Every RAW dataset column name needed to compute a list of ColumnRef,
 * walking group refs back to their step's own scope recursively (a group
 * ref's step may itself reference an earlier group, chained arbitrarily
 * deep). This is what a caller must actually supply values for, e.g.
 * manual prediction, where the backend only ever accepts real dataset
 * columns as input (see BaseTask.process_manual_input), never a
 * converter's resolved output name like "pca_1": it runs the raw values
 * through the session's persisted preprocessor itself before predicting.
 */
export function rawColumnsNeededFor(refs, steps) {
  const needed = [];
  const seen = new Set();
  const visit = (ref) => {
    if (ref.kind === "raw") {
      if (!seen.has(ref.name)) {
        seen.add(ref.name);
        needed.push(ref.name);
      }
      return;
    }
    const step = (steps || [])[ref.step];
    if (!step) return;
    (step.scope || []).forEach(visit);
  };
  (refs || []).forEach(visit);
  return needed;
}
