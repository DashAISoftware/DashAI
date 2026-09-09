/**
 * Synthetic-key representation of a session's ColumnRef (see the backend's
 * DashAI.back.preprocessing.column_ref module). A raw dataset column is
 * just its own name; a converter's not-yet-materialized output group is
 * represented as a synthetic string key, so every UI piece that already
 * knows how to work with a flat `{name: string}` column list (Autocomplete
 * options, MaterialReactTable rows, columnTypes maps) can represent a group
 * without knowing groups exist at all.
 */

const GROUP_KEY_PREFIX = "__group__";

export const groupKey = (step) => `${GROUP_KEY_PREFIX}${step}`;

export const isGroupKey = (key) =>
  typeof key === "string" && key.startsWith(GROUP_KEY_PREFIX);

export const stepFromGroupKey = (key) =>
  Number(key.slice(GROUP_KEY_PREFIX.length));

/** ColumnRef -> synthetic key */
export const refToKey = (ref) =>
  ref.kind === "raw" ? ref.name : groupKey(ref.step);

/** synthetic key -> ColumnRef */
export const keyToRef = (key) =>
  isGroupKey(key)
    ? { kind: "group", step: stepFromGroupKey(key) }
    : { kind: "raw", name: key };

/**
 * Every column key a session's preprocessing sequence can be scoped over,
 * up to (and not including) `uptoStep`: every raw dataset column, plus one
 * group key per converter step before it. Passing no `uptoStep` includes
 * every configured step (used once a sequence is final and being displayed,
 * e.g. in SelectColumnsStep, where every step is already "before" the
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
    const key = groupKey(index);
    columnTypes[key] = {
      type: step.outputType || null,
      dtype: step.outputDtype || null,
    };
    optionLabels[key] = `${step.converter}: output`;
    allKeys.push(key);
  }

  return { allKeys, columnTypes, optionLabels };
}
