export const SPLIT_TYPES = {
  RANDOM: "random",
  MANUAL: "manual",
  PREDEFINED: "predefined",
  CV: "cv",
};

/**
 * How an evaluation strategy divides the dataset.
 *
 * Read from the component's metadata rather than from its name. Comparing
 * names meant a new strategy rendered no split controls at all, since none of
 * the checks scattered through these screens matched it.
 */
export const STRATEGY_KINDS = {
  HOLDOUT: "holdout",
  CV: "cv",
};

/**
 * Read the split shape a strategy component declares.
 *
 * @param {object} strategy an EvaluationStrategy component
 * @returns {string|null} "holdout", "cv", or null when it declares neither
 */
export const strategyKindOf = (strategy) => strategy?.metadata?.kind ?? null;

/**
 * Find the strategy component a session's stored strategy name refers to.
 *
 * @param {Array} strategies strategy components allowed for the task
 * @param {string} name the stored evaluation_strategy
 * @returns {object|null} the matching component
 */
export const findStrategy = (strategies, name) =>
  (strategies ?? []).find((strategy) => strategy?.name === name) ?? null;

// Proportions describe a random split only. Manual and predefined splits carry
// the row indexes instead, and the backend splitter picks its index branch when
// no proportion is present, so sending both would be ambiguous.
const PROPORTION_KEYS = ["train", "test", "validation"];

const INDEX_MODES = [SPLIT_TYPES.MANUAL, SPLIT_TYPES.PREDEFINED];

const PARTITION_INDEX_KEYS = {
  train: "train_indexes",
  validation: "val_indexes",
  test: "test_indexes",
};

/**
 * Build the splits payload stored on a model session.
 *
 * The selected splitter's schema parameters stay at the top level, next to the
 * three meta keys the schemas do not own: splitter_name, splitType and
 * splitted_indexes. Keeping the schema keys verbatim is what stops the payload
 * and the splitter from drifting apart.
 *
 * @param {string} splitterName registry name of the selected splitter
 * @param {string} splitType one of SPLIT_TYPES
 * @param {object} params values submitted by the schema generated form
 * @param {object} indexes row indexes per partition, for the index modes
 * @returns {object} the payload to serialize into the model session splits
 */
export const buildSplitsPayload = ({
  splitterName,
  splitType,
  params = {},
  indexes = null,
}) => {
  const isIndexMode = INDEX_MODES.includes(splitType);

  const payload = { splitter_name: splitterName, splitType };

  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value === undefined) return;
    if (isIndexMode && PROPORTION_KEYS.includes(key)) return;
    payload[key] = value;
  });

  if (isIndexMode) {
    payload.splitted_indexes = {
      train_indexes: indexes?.train ?? [],
      test_indexes: indexes?.test ?? [],
      val_indexes: indexes?.validation ?? [],
    };
  }

  return payload;
};

/** Splitters that produce one set of partitions rather than several folds. */
export const HOLDOUT_PARTITIONING = "holdout";
/** Splitters that produce several train and validation pairs. */
export const FOLD_PARTITIONING = "folds";

/**
 * Keep only the splitters that pair with a given evaluation strategy.
 *
 * The backend reports how each splitter carves the dataset, so which strategy
 * it belongs to is read from the component rather than inferred from its name.
 *
 * @param {Array} splitters splitter components compatible with the task
 * @param {string} partitioning HOLDOUT_PARTITIONING or FOLD_PARTITIONING
 * @returns {Array} the splitters that carve the dataset that way
 */
export const filterByPartitioning = (splitters, partitioning) =>
  (splitters ?? []).filter(
    (splitter) => splitter?.metadata?.partitioning === partitioning,
  );

/**
 * Resolve the registry name of the splitter a session configuration uses.
 *
 * Both strategies now pick from the splitters the task allows. Holdout used to
 * return the literal "HoldoutSplitter" whatever the task was, which offered a
 * shuffling splitter for time series: shuffling a series trains a model on its
 * own future and reports a score it could never reproduce, with nothing raising
 * an error.
 *
 * @param {string} strategyKind the split shape of the selected strategy
 * @param {object} cvType the splitter component selected for cross-validation
 * @param {object} holdoutType the splitter component selected for holdout
 * @returns {string|null} the splitter name, or null when none is resolved yet
 */
export const resolveSplitterName = (
  strategyKind,
  cvType,
  holdoutType = null,
) => {
  if (strategyKind === STRATEGY_KINDS.HOLDOUT) return holdoutType?.name ?? null;
  if (strategyKind === STRATEGY_KINDS.CV) return cvType?.name ?? null;
  return null;
};

/**
 * Choose which holdout splitter a task should start on.
 *
 * Every task that had one before keeps it, so enabling this selection changes
 * nothing for them. A task without it, which today means forecasting, takes the
 * only holdout splitter it allows.
 *
 * @param {Array} holdoutSplitters the task's holdout splitter components
 * @returns {object|null} the splitter to select by default
 */
export const defaultHoldoutSplitter = (holdoutSplitters) => {
  const options = holdoutSplitters ?? [];
  return (
    options.find((splitter) => splitter?.name === "HoldoutSplitter") ??
    options[0] ??
    null
  );
};

/**
 * Report whether a splits payload gives a partition any rows.
 *
 * Cross-validation splits every fold into train and validation, so those two
 * always receive rows; it only fills a test partition when the session reserved
 * rows the folds never see. Index modes carry row indexes, random splits carry
 * proportions, and payloads written before the splits followed the splitter
 * schema carry the indexes under the partition names.
 *
 * @param {object} splits a splits payload
 * @param {string} partition one of "train", "validation", "test"
 * @returns {boolean} true when the partition receives rows
 */
export const hasPartition = (splits, partition) => {
  if (!splits) return false;
  if (splits.splitType === SPLIT_TYPES.CV) {
    // Sessions written while the reserved proportion was still called
    // "holdout" carry that key instead, the same fallback the backend
    // normalizer applies.
    if (partition === "test")
      return Number(splits.test_size ?? splits.holdout ?? 0) > 0;
    return true;
  }

  const indexes = splits.splitted_indexes;
  if (indexes) {
    return (indexes[PARTITION_INDEX_KEYS[partition]] ?? []).length > 0;
  }

  const value = splits[partition];
  if (Array.isArray(value)) return value.length > 0;
  return typeof value === "number" && value !== 0;
};
