/**
 * Which dataset columns a component will accept, decided in one place.
 *
 * A component's metadata declares three restrictions and the backend applies
 * them in `validate_columns` (DashAI/back/exploration/base_explorer.py):
 *
 *   - `allowed_types`: semantic types. An empty list means no restriction.
 *   - `allowed_dtypes`: storage dtypes. An empty list means no restriction, and
 *     the backend normalizes `["*"]` to `[]` before serving, so `"*"` never
 *     reaches the browser.
 *   - `non_allowed_dtypes`: a blacklist, always present in the payload.
 *
 * That contract was reimplemented four times in the frontend and one copy went
 * stale: it read `restricted_dtypes`, a key renamed to `non_allowed_dtypes` and
 * explicitly popped by the backend, and it tested `allowed_dtypes.includes("*")`
 * to mean "no restriction". Since the backend had normalized `["*"]` away, that
 * test was always false, so an explorer with no dtype restriction filtered its
 * columns against an empty allow-list, ended up with none, and was disabled.
 * The undefined blacklist threw before any of that could be seen, so the
 * exploration picker showed an error and no options at all.
 *
 * One implementation, mirroring the backend's, so the copies cannot drift again.
 */

/**
 * @typedef {object} ColumnEligibility
 * @property {Array<object>} validColumns columns the component accepts
 * @property {null|{kind: "exact"|"min", required: number, available: number}} shortfall
 *   set when there are fewer acceptable columns than the component needs
 * @property {string[]} restrictions the type and dtype names it does accept,
 *   for a message naming them
 * @property {boolean} restricted whether any restriction was applied at all,
 *   which is what separates "this dataset has no suitable column" from "this
 *   dataset has no columns"
 */

/**
 * Apply a component's declared column restrictions to a dataset's columns.
 *
 * @param {object} metadata the component's `metadata` from the components API
 * @param {Array<object>} columns dataset columns, each with `dataType` and
 *   `valueType`
 * @param {object} [options]
 * @param {string} [options.unknownLabel] the localized label the column table
 *   shows for a column whose dtype the backend could not name. The backend
 *   spells that case as the empty string in its blacklist, so the two have to
 *   be matched up before comparing.
 * @returns {ColumnEligibility}
 */
export function evaluateColumnEligibility(metadata, columns, options = {}) {
  const { unknownLabel } = options;
  const allowedTypes = metadata?.allowed_types || [];
  const allowedDtypes = metadata?.allowed_dtypes || [];
  const nonAllowedDtypes = metadata?.non_allowed_dtypes || [];
  const cardinality = metadata?.input_cardinality || {};

  let validColumns = Array.isArray(columns) ? columns : [];

  // An empty list is "no restriction", not "nothing allowed". This is the
  // polarity the stale copy had backwards.
  if (allowedTypes.length > 0) {
    validColumns = validColumns.filter((column) =>
      allowedTypes.includes(column.valueType),
    );
  }
  if (allowedDtypes.length > 0) {
    validColumns = validColumns.filter((column) =>
      allowedDtypes.includes(column.dataType),
    );
  }
  if (nonAllowedDtypes.length > 0) {
    validColumns = validColumns.filter((column) => {
      const dtype =
        unknownLabel && column.dataType === unknownLabel ? "" : column.dataType;
      return !nonAllowedDtypes.includes(dtype);
    });
  }

  let shortfall = null;
  if (cardinality.exact !== undefined && cardinality.exact !== null) {
    if (validColumns.length < cardinality.exact) {
      shortfall = {
        kind: "exact",
        required: cardinality.exact,
        available: validColumns.length,
      };
    }
  } else if (cardinality.min !== undefined && cardinality.min !== null) {
    if (validColumns.length < cardinality.min) {
      shortfall = {
        kind: "min",
        required: cardinality.min,
        available: validColumns.length,
      };
    }
  }

  return {
    validColumns,
    shortfall,
    restrictions: [...allowedTypes, ...allowedDtypes],
    restricted:
      allowedTypes.length > 0 ||
      allowedDtypes.length > 0 ||
      nonAllowedDtypes.length > 0,
  };
}

/**
 * The dtypes a component refuses, for a message that names them.
 *
 * A separate accessor because it is the key that went stale: reading it in one
 * place means a future rename breaks one line rather than silently rendering
 * nothing, which is what happened to the "does not accept" chips in the column
 * dialog for as long as the key had the old name.
 *
 * @param {object} metadata the component's metadata
 * @returns {string[]} the blacklisted dtypes, empty when there are none
 */
export function refusedDtypes(metadata) {
  return metadata?.non_allowed_dtypes || [];
}
