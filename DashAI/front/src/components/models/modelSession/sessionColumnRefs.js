/**
 * Synthetic-key representation of a session's ColumnRef (see the backend's
 * DashAI.back.preprocessing.column_ref module). A raw dataset column is
 * just its own name; a converter's not-yet-materialized output group is
 * represented as a synthetic string key, so every UI piece that already
 * knows how to work with a flat `{name: string}` column list (Autocomplete
 * options, MaterialReactTable rows, columnTypes maps) can represent a group
 * without knowing groups exist at all.
 *
 * A step's output isn't always one homogeneous type — e.g. SimpleImputer
 * with "most_frequent"/"constant" just preserves each scope column's own
 * type, so a scope mixing a categorical and a numeric column produces both
 * kinds of columns. `slot` (a DashAI type's display_name(), e.g.
 * "Categorical") picks out just the columns of one declared type from a
 * step's output, mirroring the backend's GroupColumnRef.slot /
 * SessionPreprocessor.resolved_slots. A step with only one declared type —
 * the common case, and everything before slots existed — has no slot
 * (`slot: null`), which means "the whole group," unchanged from before.
 */

const GROUP_KEY_PREFIX = "__group__";
const SLOT_SEPARATOR = "__slot__";

export const groupKey = (step, slot = null) =>
  slot == null
    ? `${GROUP_KEY_PREFIX}${step}`
    : `${GROUP_KEY_PREFIX}${step}${SLOT_SEPARATOR}${slot}`;

export const isGroupKey = (key) =>
  typeof key === "string" && key.startsWith(GROUP_KEY_PREFIX);

export const stepFromGroupKey = (key) => {
  const withoutPrefix = key.slice(GROUP_KEY_PREFIX.length);
  const separatorIndex = withoutPrefix.indexOf(SLOT_SEPARATOR);
  const stepPart =
    separatorIndex === -1
      ? withoutPrefix
      : withoutPrefix.slice(0, separatorIndex);
  return Number(stepPart);
};

export const slotFromGroupKey = (key) => {
  const withoutPrefix = key.slice(GROUP_KEY_PREFIX.length);
  const separatorIndex = withoutPrefix.indexOf(SLOT_SEPARATOR);
  return separatorIndex === -1
    ? null
    : withoutPrefix.slice(separatorIndex + SLOT_SEPARATOR.length);
};

/** ColumnRef -> synthetic key */
export const refToKey = (ref) =>
  ref.kind === "raw" ? ref.name : groupKey(ref.step, ref.slot ?? null);

/** synthetic key -> ColumnRef */
export const keyToRef = (key) => {
  if (!isGroupKey(key)) return { kind: "raw", name: key };
  const step = stepFromGroupKey(key);
  const slot = slotFromGroupKey(key);
  return slot == null ? { kind: "group", step } : { kind: "group", step, slot };
};

// A step's declared output, normalized to a list of slots — even a
// homogeneous step (the common case) is one "slot" with slot: null, so
// every caller iterates the same shape regardless of how many there are.
// Falls back defensively for a step that predates outputSlots.
function stepOutputSlots(step) {
  if (Array.isArray(step?.outputSlots) && step.outputSlots.length > 0) {
    return step.outputSlots;
  }
  return [
    {
      slot: null,
      type: step?.outputType ?? null,
      dtype: step?.outputDtype ?? null,
    },
  ];
}

/**
 * Every column key a session's preprocessing sequence can be scoped over,
 * up to (and not including) `uptoStep`: every raw dataset column, plus one
 * group key per declared slot of every converter step before it (usually
 * one key per step; more than one only when that step's scope mixed
 * column types). Passing no `uptoStep` includes every configured step
 * (used once a sequence is final and being displayed, e.g. in
 * SelectColumnsStep, where every step is already "before" the
 * column-selection step that comes after all of them).
 */
export function buildColumnKeysAndTypes({
  datasetTypes,
  preprocessing,
  uptoStep,
}) {
  const steps = preprocessing || [];
  const limit = uptoStep === undefined ? steps.length : uptoStep;

  const columnTypes = { ...datasetTypes };
  const optionLabels = {};
  const allKeys = Object.keys(datasetTypes || {});

  for (let index = 0; index < limit; index += 1) {
    const step = steps[index];
    stepOutputSlots(step).forEach(({ slot, type, dtype }) => {
      const key = groupKey(index, slot);
      columnTypes[key] = { type: type || null, dtype: dtype || null };
      optionLabels[key] = slot
        ? `${step.converter}: output (${slot})`
        : `${step.converter}: output`;
      allKeys.push(key);
    });
  }

  return { allKeys, columnTypes, optionLabels };
}

// SimpleImputer only preserves its input column's type for the
// "most_frequent"/"constant" strategies (no arithmetic performed); "mean"/
// "median" always produce something numeric, but which exact numeric type
// depends on a statistic computed from real data, so there's nothing to
// resolve ahead of a fit — tool.metadata.output_type ("Float") already
// covers that case correctly, since every allowed_types list in this
// codebase that includes Integer also includes Float (they're always
// interchangeable for compatibility checks).
function simpleImputerPreservesType(toolName, params) {
  if (toolName !== "SimpleImputer") return false;
  const strategy = params?.strategy;
  return strategy === "most_frequent" || strategy === "constant";
}

/**
 * The output slot(s) to record for a converter step once its scope is
 * known — always an array of {slot, type, dtype}, even when there's just
 * one (slot: null, meaning "the whole group", exactly like before slots
 * existed).
 *
 * Most converters' declared output_type/output_dtype (metadata computed
 * backend-side from a bare, never-fitted instance) is the best available
 * answer regardless of scope, and stays a single slot. But a converter
 * that only keeps or drops whole columns unchanged (backend
 * PRESERVES_INPUT_TYPE, e.g. feature selection, VarianceThreshold, or
 * SimpleImputer with "most_frequent"/"constant") has an output type
 * that's actually already knowable — it's just whatever the chosen
 * scope's own column type already is. When that scope mixes distinct
 * types, this splits into one slot per distinct type instead of falling
 * back to a single guess, matching exactly what SessionPreprocessor.
 * _classify_by_type computes for real once the session is created.
 */
export function resolveDeclaredOutputSlots({
  tool,
  params,
  scope,
  datasetTypes,
  preprocessing,
}) {
  const fallback = [
    {
      slot: null,
      type: tool?.metadata?.output_type || null,
      dtype: tool?.metadata?.output_dtype || null,
    },
  ];

  const preservesInputType =
    Boolean(tool?.metadata?.preserves_input_type) ||
    simpleImputerPreservesType(tool?.name, params);

  if (!preservesInputType || !scope?.length) return fallback;

  const { columnTypes } = buildColumnKeysAndTypes({
    datasetTypes,
    preprocessing,
  });
  const scopeEntries = scope.map((ref) => columnTypes[refToKey(ref)]);
  if (scopeEntries.some((entry) => !entry?.type)) return fallback;

  const distinctTypes = [...new Set(scopeEntries.map((entry) => entry.type))];

  const dtypeFor = (type) => {
    const dtypes = [
      ...new Set(
        scopeEntries
          .filter((entry) => entry.type === type)
          .map((entry) => entry.dtype)
          .filter(Boolean),
      ),
    ];
    return dtypes.length === 1 ? dtypes[0] : null;
  };

  if (distinctTypes.length === 1) {
    return [
      { slot: null, type: distinctTypes[0], dtype: dtypeFor(distinctTypes[0]) },
    ];
  }

  return distinctTypes.map((type) => ({
    slot: type,
    type,
    dtype: dtypeFor(type),
  }));
}

/**
 * Every RAW dataset column name needed to compute a list of ColumnRef,
 * walking group refs back to their step's own scope recursively (a group
 * ref's step may itself reference an earlier group, chained arbitrarily
 * deep). This is what a caller must actually supply values for — e.g.
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
