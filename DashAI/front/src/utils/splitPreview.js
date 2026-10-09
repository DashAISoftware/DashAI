import { SPLIT_TYPES } from "./splitsPayload";

export const SPLIT_GEOMETRIES = {
  PARTITIONS: "partitions",
  SEQUENTIAL_PARTITIONS: "sequential_partitions",
  BLOCKED_FOLDS: "blocked_folds",
  EXPANDING_WINDOW: "expanding_window",
};

export const SPLIT_ROLES = {
  TRAIN: "train",
  VALIDATION: "validation",
  TEST: "test",
  UNUSED: "unused",
};

export const geometryOf = (splitter) => splitter?.metadata?.geometry ?? null;

const MAX_DRAWN_FOLDS = 8;
const LEADING_DRAWN_FOLDS = 3;
const NOMINAL_ROWS = 100;
const NEGLIGIBLE = 1e-9;

const numberOr = (value, fallback) =>
  typeof value === "number" && Number.isFinite(value) ? value : fallback;

const clamp01 = (value) => Math.min(1, Math.max(0, numberOr(value, 0)));

const segment = (role, fraction) => ({ role, fraction });

const drawable = (segments) =>
  segments.filter((piece) => piece.fraction > NEGLIGIBLE);

const rowsOf = (datasetInfo) =>
  Math.max(
    1,
    Math.round(numberOr(Number(datasetInfo?.total_rows), NOMINAL_ROWS)),
  );

const proportionsFromDataset = (datasetInfo) => {
  const totalRows = Number(datasetInfo?.total_rows);
  if (!totalRows) return null;
  return {
    train: numberOr(datasetInfo?.train_size, 0) / totalRows,
    validation: numberOr(datasetInfo?.val_size, 0) / totalRows,
    test: numberOr(datasetInfo?.test_size, 0) / totalRows,
  };
};

const proportionsFromIndexes = (indexes, datasetInfo) => {
  const totalRows = Number(datasetInfo?.total_rows);
  if (!totalRows) return null;
  return {
    train: (indexes?.train?.length ?? 0) / totalRows,
    validation: (indexes?.validation?.length ?? 0) / totalRows,
    test: (indexes?.test?.length ?? 0) / totalRows,
  };
};

const proportionsFromParams = (params) => ({
  train: clamp01(params.train),
  validation: clamp01(params.validation),
  test: clamp01(params.test),
});

const partitionProportions = ({ splitType, params, indexes, datasetInfo }) => {
  if (splitType === SPLIT_TYPES.PREDEFINED) {
    return proportionsFromDataset(datasetInfo);
  }
  if (splitType === SPLIT_TYPES.MANUAL) {
    return proportionsFromIndexes(indexes, datasetInfo);
  }
  return proportionsFromParams(params);
};

const partitionRow = ({ train, validation, test }) => {
  const requested = train + validation + test;
  const scale = requested > 1 ? 1 / requested : 1;
  const unused = requested < 1 ? 1 - requested : 0;

  return {
    key: "dataset",
    labelKey: "experiments:splitPreview.wholeDataset",
    segments: drawable([
      segment(SPLIT_ROLES.TRAIN, train * scale),
      segment(SPLIT_ROLES.VALIDATION, validation * scale),
      segment(SPLIT_ROLES.TEST, test * scale),
      segment(SPLIT_ROLES.UNUSED, unused),
    ]),
  };
};

const reservedRow = (pool, reserved) => ({
  key: "reserved",
  labelKey: "experiments:splitPreview.reservedTest",
  segments: drawable([
    segment(SPLIT_ROLES.UNUSED, pool),
    segment(SPLIT_ROLES.TEST, reserved),
  ]),
});

const finalFitRow = (pool, reserved) => ({
  key: "final",
  labelKey: "experiments:splitPreview.finalFit",
  segments: drawable([
    segment(SPLIT_ROLES.TRAIN, pool),
    segment(SPLIT_ROLES.TEST, reserved),
  ]),
});

const drawnFoldIndexes = (foldCount) => {
  if (foldCount <= MAX_DRAWN_FOLDS) {
    return Array.from({ length: foldCount }, (_, index) => index);
  }
  return [
    ...Array.from({ length: LEADING_DRAWN_FOLDS }, (_, index) => index),
    null,
    foldCount - 1,
  ];
};

const ellipsisRow = (hiddenCount) => ({
  key: "ellipsis",
  ellipsis: true,
  hiddenCount,
});

const foldRows = (foldCount, buildRow) =>
  drawnFoldIndexes(foldCount).map((index) =>
    index === null
      ? ellipsisRow(foldCount - LEADING_DRAWN_FOLDS - 1)
      : buildRow(index),
  );

const blockedFoldRow = ({ index, foldCount, pool, reserved }) => {
  const block = pool / foldCount;
  return {
    key: "fold-" + index,
    labelKey: "experiments:splitPreview.fold",
    labelValues: { index: index + 1 },
    segments: drawable([
      segment(SPLIT_ROLES.TRAIN, block * index),
      segment(SPLIT_ROLES.VALIDATION, block),
      segment(SPLIT_ROLES.TRAIN, block * (foldCount - index - 1)),
      segment(SPLIT_ROLES.UNUSED, reserved),
    ]),
  };
};

const expandingFoldRow = ({
  index,
  pool,
  reserved,
  poolRows,
  initialTrainRows,
  horizon,
  step,
}) => {
  const origin = initialTrainRows + index * step;
  const train = (origin / poolRows) * pool;
  const validation = (horizon / poolRows) * pool;
  return {
    key: "fold-" + index,
    labelKey: "experiments:splitPreview.fold",
    labelValues: { index: index + 1 },
    segments: drawable([
      segment(SPLIT_ROLES.TRAIN, train),
      segment(SPLIT_ROLES.VALIDATION, validation),
      segment(SPLIT_ROLES.UNUSED, pool - train - validation + reserved),
    ]),
  };
};

const hiddenFoldsNote = (foldCount) =>
  foldCount > MAX_DRAWN_FOLDS
    ? [{ key: "foldsHidden", values: { total: foldCount } }]
    : [];

const partitionsPreview = ({ splitType, params, indexes, datasetInfo }) => {
  const proportions = partitionProportions({
    splitType,
    params,
    indexes,
    datasetInfo,
  });
  if (!proportions) return null;

  return { rows: [partitionRow(proportions)], notes: [], error: null };
};

const blockedFoldsPreview = ({ params, datasetInfo }) => {
  const reserved = clamp01(params.test_size);
  const pool = 1 - reserved;
  const poolRows = Math.max(1, Math.round(rowsOf(datasetInfo) * pool));
  const declaredFolds = numberOr(params.n_splits, null);
  const foldCount = Math.max(
    1,
    Math.round(declaredFolds === null ? poolRows : declaredFolds),
  );

  const rows = [
    ...(reserved > NEGLIGIBLE ? [reservedRow(pool, reserved)] : []),
    ...foldRows(foldCount, (index) =>
      blockedFoldRow({ index, foldCount, pool, reserved }),
    ),
    ...(reserved > NEGLIGIBLE ? [finalFitRow(pool, reserved)] : []),
  ];

  return { rows, notes: hiddenFoldsNote(foldCount), error: null };
};

const expandingWindowPreview = ({ params, datasetInfo }) => {
  const reserved = clamp01(params.test_size);
  const pool = 1 - reserved;
  const poolRows = Math.max(1, Math.round(rowsOf(datasetInfo) * pool));
  const foldCount = Math.max(1, Math.round(numberOr(params.n_splits, 5)));
  const horizon = Math.max(1, Math.round(numberOr(params.horizon, 1)));
  const step = Math.max(1, Math.round(numberOr(params.step, 1)));
  const initialTrainRows = poolRows - horizon - (foldCount - 1) * step;

  if (initialTrainRows <= 0) {
    return {
      rows: [],
      notes: [],
      error: {
        key: "notEnoughRows",
        values: { folds: foldCount, horizon, step, rows: poolRows },
      },
    };
  }

  const rows = [
    ...(reserved > NEGLIGIBLE ? [reservedRow(pool, reserved)] : []),
    ...foldRows(foldCount, (index) =>
      expandingFoldRow({
        index,
        pool,
        reserved,
        poolRows,
        initialTrainRows,
        horizon,
        step,
      }),
    ),
    ...(reserved > NEGLIGIBLE ? [finalFitRow(pool, reserved)] : []),
  ];

  return { rows, notes: hiddenFoldsNote(foldCount), error: null };
};

const sharesOf = (rows) => {
  const representative =
    rows.find((row) => !row.ellipsis && row.key.startsWith("fold-")) ??
    rows.find((row) => !row.ellipsis);
  if (!representative) return {};

  const shares = {};
  representative.segments.forEach(({ role, fraction }) => {
    shares[role] = (shares[role] ?? 0) + fraction;
  });

  const reserved = rows.find((row) => row.key === "reserved");
  const heldOut = reserved?.segments.find(
    (piece) => piece.role === SPLIT_ROLES.TEST,
  );
  if (heldOut) {
    shares[SPLIT_ROLES.TEST] = heldOut.fraction;
    shares[SPLIT_ROLES.UNUSED] = Math.max(
      0,
      (shares[SPLIT_ROLES.UNUSED] ?? 0) - heldOut.fraction,
    );
  }
  return shares;
};

export const buildSplitPreview = ({
  geometry,
  splitType,
  params,
  indexes,
  datasetInfo,
}) => {
  const values = params ?? {};
  let preview = null;

  switch (geometry) {
    case SPLIT_GEOMETRIES.PARTITIONS:
    case SPLIT_GEOMETRIES.SEQUENTIAL_PARTITIONS:
      preview = partitionsPreview({
        splitType,
        params: values,
        indexes,
        datasetInfo,
      });
      break;
    case SPLIT_GEOMETRIES.BLOCKED_FOLDS:
      preview = blockedFoldsPreview({ params: values, datasetInfo });
      break;
    case SPLIT_GEOMETRIES.EXPANDING_WINDOW:
      preview = expandingWindowPreview({ params: values, datasetInfo });
      break;
    default:
      return null;
  }

  if (!preview) return null;
  return { ...preview, shares: sharesOf(preview.rows) };
};
