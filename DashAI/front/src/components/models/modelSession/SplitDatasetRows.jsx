import React, { useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import { parseRangeToIndex } from "../../../utils/parseRange";
import {
  Box,
  FormHelperText,
  Grid,
  Paper,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
  Select,
  MenuItem,
  FormControl,
} from "@mui/material";
import { DescriptionBlock } from "../../shared/FormSchemaFieldCard";
import FormSchema from "../../shared/FormSchema";
import FormSchemaLayout from "../../shared/FormSchemaLayout";
import {
  defaultHoldoutSplitter,
  filterByPartitioning,
  findStrategy,
  FOLD_PARTITIONING,
  HOLDOUT_PARTITIONING,
  resolveSplitterName,
  STRATEGY_KINDS,
  strategyKindOf,
} from "../../../utils/splitsPayload";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { getComponents } from "../../../api/component";

/**
 * Splits card shell — same Paper/header visual as FormSchemaFieldCard but WITHOUT
 * the label-hiding CSS so Train / Validation / Test TextField labels stay visible.
 */
function SplitsCard({ label, description, errorMessage, children, warning }) {
  return (
    <Paper variant="outlined" sx={{ borderRadius: 2, overflow: "hidden" }}>
      <Box
        sx={{
          px: 4,
          py: 3,
          borderBottom: "1px solid",
          borderColor: "divider",
        }}
      >
        <Typography
          variant="body2"
          fontWeight={600}
          color={
            errorMessage
              ? "error.main"
              : warning
                ? "warning.main"
                : "text.primary"
          }
        >
          {label}
        </Typography>
      </Box>
      <Box sx={{ px: 8, pt: 2, pb: description || errorMessage ? 2 : 4 }}>
        {children}
      </Box>
      {(description || errorMessage || warning) && (
        <Box sx={{ px: 8, pb: 2 }}>
          <DescriptionBlock
            text={errorMessage ?? description}
            isError={Boolean(errorMessage)}
          />
        </Box>
      )}
    </Paper>
  );
}

function SplitDatasetRows({
  datasetInfo,
  rowsPartitionsIndex,
  setRowsPartitionsIndex,
  setSplitsReady,
  splitType,
  setSplitType,
  SPLIT_TYPES,
  splitterParams,
  setSplitterParams,
  paramsError,
  setParamsError,
  evaluationStrategy,
  setEvaluationStrategy,
  cvType,
  setCvType,
  holdoutType,
  setHoldoutType,
  strategyKind,
  setStrategyKind,
  groupColumn,
  setGroupColumn,
  inputColumnNames,
  taskName,
}) {
  const { t } = useTranslation(["experiments", "common"]);
  const { enqueueSnackbar } = useSnackbar();
  const totalRows = datasetInfo.total_rows;
  const trainDatasetPercentage = (datasetInfo.train_size / totalRows).toFixed(
    2,
  );
  const validationDatasetPercentage = (
    datasetInfo.val_size / totalRows
  ).toFixed(2);
  const testDatasetPercentage = (datasetInfo.test_size / totalRows).toFixed(2);

  const hasPredefinedSplits =
    trainDatasetPercentage > 0 ||
    validationDatasetPercentage > 0 ||
    testDatasetPercentage > 0;

  const checkSplit = (train, validation, test) =>
    Math.abs(train + validation + test - 1) < 0.0001;

  // The splitter's own parameters come from the schema generated form; only the
  // rules the schema cannot express are checked here.
  const splitterName = resolveSplitterName(strategyKind, cvType, holdoutType);
  const isIndexMode =
    splitType === SPLIT_TYPES.MANUAL || splitType === SPLIT_TYPES.PREDEFINED;
  const params = splitterParams ?? {};
  const proportionsAreNumbers = ["train", "validation", "test"].every(
    (key) => typeof params[key] === "number",
  );
  const proportionsSumToOne =
    proportionsAreNumbers &&
    checkSplit(params.train, params.validation, params.test);
  const trainIsEmpty = params.train === 0;
  const folds = params.n_splits;
  const tooManyFolds =
    typeof folds === "number" && folds > (datasetInfo.total_rows ?? 0);
  // group_column is rendered by hand because its options are the dataset's own
  // columns, so the generated form never validates it.
  // Memoized because the generated form memoizes its field list on this array.
  const excludedFields = useMemo(
    () =>
      isIndexMode
        ? ["group_column", "train", "test", "validation"]
        : ["group_column"],
    [isIndexMode],
  );

  // The generated form reports its values only once the user edits a field, so
  // the schema placeholders are pushed up here: without them a session created
  // without touching the form would carry no splitter parameters at all.
  //
  // The schema is fetched by name rather than read from the shared schema hook
  // on purpose. That hook keeps the previous splitter's schema for one render
  // after the name changes, and seeding from it left the parameters of the
  // splitter that was selected a moment ago in place.
  useEffect(() => {
    if (!splitterName) return undefined;
    let cancelled = false;

    const seedSplitterParams = async () => {
      try {
        const component = await getComponents({ model: splitterName });
        if (cancelled) return;
        const properties = component?.schema?.properties ?? {};
        const defaults = Object.fromEntries(
          Object.entries(properties)
            .filter(([, property]) => "placeholder" in property)
            .map(([key, property]) => [key, property.placeholder]),
        );
        if (Object.keys(defaults).length > 0) {
          setSplitterParams(defaults);
        }
      } catch (error) {
        console.error(`Error fetching the ${splitterName} schema`, error);
      }
    };

    seedSplitterParams();

    return () => {
      cancelled = true;
    };
  }, [splitterName]);

  // Rules that span several fields, which a per field schema cannot express.
  let splitsMessage = "";
  if (
    strategyKind === STRATEGY_KINDS.HOLDOUT &&
    splitType === SPLIT_TYPES.RANDOM
  ) {
    if (trainIsEmpty) {
      splitsMessage = t("experiments:error.trainSplitMustBeGreaterThanZero");
    } else if (proportionsAreNumbers && !proportionsSumToOne) {
      splitsMessage = t("experiments:error.splitsMustSumToOne");
    }
  } else if (strategyKind === STRATEGY_KINDS.CV && tooManyFolds) {
    splitsMessage = t("experiments:error.foldsMustBeLessThanDatasetSize", {
      datasetSize: datasetInfo.total_rows,
    });
  }

  const [manualSplitError, setManualSplitError] = useState(false);
  const [manualSplitErrorText, setManualSplitErrorText] = useState("");

  const [groupColumnError, setGroupColumnError] = useState(true);
  const [allowedCvTypes, setAllowedCvTypes] = useState([]);
  const [allowedHoldoutTypes, setAllowedHoldoutTypes] = useState([]);
  const [allowedStrategies, setAllowedStrategies] = useState([]);

  // Update allowed CV types when task changes
  useEffect(() => {
    const getSplittersForTask = async () => {
      try {
        const response = await getComponents({
          selectTypes: ["Splitter"],
          relatedComponent: taskName,
        });
        // A holdout splitter is not a cross-validation method, so the two
        // kinds are kept apart rather than both landing in the CV dropdown.
        setAllowedCvTypes(filterByPartitioning(response, FOLD_PARTITIONING));
        setAllowedHoldoutTypes(
          filterByPartitioning(response, HOLDOUT_PARTITIONING),
        );

        // Which strategies exist is a property of the task too, so a
        // forecasting session cannot be pointed at one that scores its
        // training partition.
        const strategies = await getComponents({
          selectTypes: ["EvaluationStrategy"],
          relatedComponent: taskName,
        });
        setAllowedStrategies(strategies);
      } catch (error) {
        console.error("Error fetching splitters:", error);
        enqueueSnackbar(t("models:error.fetchingStatisticalTests"), {
          variant: "error",
        });
      }
    };

    getSplittersForTask();
  }, [taskName]);

  // Set default CV type when allowedCvTypes changes
  useEffect(() => {
    setCvType(allowedCvTypes.length > 0 ? allowedCvTypes[0] : null);
  }, [allowedCvTypes]);

  // Same for the holdout splitter, which used to be a hardcoded name.
  useEffect(() => {
    setHoldoutType(defaultHoldoutSplitter(allowedHoldoutTypes));
  }, [allowedHoldoutTypes]);

  // Publish the split shape so the rest of the session reads it instead of
  // comparing strategy names.
  useEffect(() => {
    setStrategyKind(
      strategyKindOf(findStrategy(allowedStrategies, evaluationStrategy)),
    );
  }, [allowedStrategies, evaluationStrategy, setStrategyKind]);

  // And for the strategy itself, which the session used to start on by name.
  useEffect(() => {
    if (!allowedStrategies.length) return;
    if (findStrategy(allowedStrategies, evaluationStrategy)) return;
    const holdout = allowedStrategies.find(
      (strategy) => strategyKindOf(strategy) === STRATEGY_KINDS.HOLDOUT,
    );
    setEvaluationStrategy((holdout ?? allowedStrategies[0]).name);
  }, [allowedStrategies, evaluationStrategy, setEvaluationStrategy]);

  const handleSplitTypeChange = (_e, newType) => {
    if (!newType) return;
    setSplitType(newType);

    if (newType === SPLIT_TYPES.PREDEFINED) {
      setSplitsReady(true);
    }
    if (newType === SPLIT_TYPES.MANUAL) {
      const newIndex = { train: [], test: [], validation: [] };
      setRowsPartitionsIndex(newIndex);
      setManualSplitErrorText(
        t("experiments:error.trainSplitMustHaveAtLeastOneRow"),
      );
      setManualSplitError(true);
    }
  };

  const handleRowsChange = (event) => {
    const value = event.target.value;
    const id = event.target.id;

    try {
      const rowsIndex = parseRangeToIndex(value, totalRows);
      const updatedIndex = { ...rowsPartitionsIndex, [id]: rowsIndex };
      setRowsPartitionsIndex(updatedIndex);
      if (updatedIndex.train.length === 0) {
        setManualSplitErrorText(
          t("experiments:error.trainSplitMustHaveAtLeastOneRow"),
        );
        setManualSplitError(true);
      } else {
        setManualSplitError(false);
      }
    } catch (error) {
      setManualSplitErrorText(error.message);
      setManualSplitError(true);
    }
  };

  const handleGroupColumnChange = (event) => {
    const value = event.target.value;
    setGroupColumn(value);
    if (value) {
      setGroupColumnError(false);
    } else {
      setGroupColumnError(true);
    }
  };

  useEffect(() => {
    if (hasPredefinedSplits) {
      setSplitType(SPLIT_TYPES.PREDEFINED);
    } else {
      setSplitType(SPLIT_TYPES.RANDOM);
    }
  }, [hasPredefinedSplits]);

  useEffect(() => {
    if (paramsError) {
      setSplitsReady(false);
      return;
    }
    if (strategyKind === STRATEGY_KINDS.HOLDOUT) {
      if (splitType === SPLIT_TYPES.PREDEFINED) {
        setSplitsReady(true);
      } else if (
        splitType === SPLIT_TYPES.MANUAL &&
        !manualSplitError &&
        rowsPartitionsIndex.train.length >= 1
      ) {
        setSplitsReady(true);
      } else if (
        splitType === SPLIT_TYPES.RANDOM &&
        proportionsSumToOne &&
        !trainIsEmpty
      ) {
        setSplitsReady(true);
      } else {
        setSplitsReady(false);
      }
    } else if (strategyKind === STRATEGY_KINDS.CV) {
      setSplitsReady(
        Boolean(splitterName) && !tooManyFolds && !groupColumnError,
      );
    } else {
      setSplitsReady(false);
    }
  }, [
    rowsPartitionsIndex,
    manualSplitError,
    splitType,
    evaluationStrategy,
    paramsError,
    proportionsSumToOne,
    trainIsEmpty,
    tooManyFolds,
    groupColumnError,
    splitterName,
  ]);

  const splitOptions = [
    {
      value: SPLIT_TYPES.PREDEFINED,
      label: t("experiments:label.predefined"),
      disabled: !hasPredefinedSplits,
    },
    { value: SPLIT_TYPES.RANDOM, label: t("experiments:label.random") },
    { value: SPLIT_TYPES.MANUAL, label: t("experiments:label.manual") },
  ];

  const splitFields = [
    { id: "train", label: t("common:train") },
    { id: "validation", label: t("common:validation") },
    { id: "test", label: t("common:test") },
  ];

  // Validate group column when grouping CV type is selected
  useEffect(() => {
    const isGrouping = Boolean(cvType?.schema?.properties?.group_column);
    if (isGrouping && !groupColumn) {
      setGroupColumnError(true);
    } else {
      setGroupColumnError(false);
    }
  }, [cvType, groupColumn, t]);

  return (
    <Stack spacing={4} data-tour="exp-dataset-splits">
      {/* Evaluation Strategy Selector */}
      <Paper variant="outlined" sx={{ borderRadius: 2, overflow: "hidden" }}>
        <Box
          sx={{
            px: 8,
            py: 3,
            borderBottom: "1px solid",
            borderColor: "divider",
          }}
        >
          <Typography variant="body2" fontWeight={600}>
            {t("experiments:label.selectEvaluationStrategy")}
          </Typography>
        </Box>
        <Box sx={{ px: 8, pt: 2, pb: 4 }}>
          <ToggleButtonGroup
            value={evaluationStrategy}
            exclusive={true}
            onChange={(_, value) => {
              value && setEvaluationStrategy(value);
            }}
            fullWidth
            size="small"
          >
            {allowedStrategies.map((strategy) => (
              <ToggleButton
                key={strategy.name}
                value={strategy.name}
                sx={{ textTransform: "none", fontSize: "0.8rem" }}
              >
                {strategyKindOf(strategy) === STRATEGY_KINDS.CV
                  ? t("experiments:label.crossValidation")
                  : t("experiments:label.holdout")}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Box>
      </Paper>

      {/* HOLDOUT SECTION */}
      {strategyKind === STRATEGY_KINDS.HOLDOUT && (
        <>
          {/* Split type selector */}
          <Paper
            variant="outlined"
            sx={{ borderRadius: 2, overflow: "hidden" }}
          >
            <Box
              sx={{
                px: 8,
                py: 3,
                borderBottom: "1px solid",
                borderColor: "divider",
              }}
            >
              <Typography variant="body2" fontWeight={600}>
                {t("experiments:label.splitType")}
              </Typography>
            </Box>
            <Box sx={{ px: 8, pt: 2, pb: 4 }}>
              <ToggleButtonGroup
                value={splitType}
                exclusive
                onChange={handleSplitTypeChange}
                fullWidth
                size="small"
              >
                {splitOptions.map((opt) => (
                  <ToggleButton
                    key={opt.value}
                    value={opt.value}
                    disabled={opt.disabled}
                    sx={{ textTransform: "none", fontSize: "0.8rem" }}
                  >
                    {opt.label}
                  </ToggleButton>
                ))}
              </ToggleButtonGroup>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ display: "block", mb: 3 }}
              >
                {t("experiments:label.selectHowToDivideDataset")}
              </Typography>
            </Box>
          </Paper>

          {/* Predefined */}
          {splitType === SPLIT_TYPES.PREDEFINED && (
            <SplitsCard
              label={t("experiments:label.splits")}
              description={t("experiments:label.splitsDescription")}
            >
              <Grid container spacing={2}>
                {[
                  { id: "train", value: trainDatasetPercentage },
                  { id: "validation", value: validationDatasetPercentage },
                  { id: "test", value: testDatasetPercentage },
                ].map(({ id, value }) => (
                  <Grid key={id} size={{ xs: 4 }}>
                    <TextField
                      label={t(`common:${id}`)}
                      value={value}
                      type="number"
                      size="small"
                      fullWidth
                      disabled
                      slotProps={{ inputLabel: { shrink: true } }}
                      sx={{
                        "& .MuiInputBase-input.Mui-disabled": {
                          WebkitTextFillColor: "#999",
                        },
                        "& .MuiInputLabel-root.Mui-disabled": { color: "#bbb" },
                      }}
                    />
                  </Grid>
                ))}
              </Grid>
            </SplitsCard>
          )}

          {/* Manual */}
          {splitType === SPLIT_TYPES.MANUAL && (
            <SplitsCard
              label={t("experiments:label.rowIndexes")}
              description={t("experiments:label.rowIndexesDescription")}
              errorMessage={manualSplitError ? manualSplitErrorText : undefined}
            >
              <Grid container spacing={2}>
                {splitFields.map(({ id, label }) => (
                  <Grid key={id} size={{ xs: 4 }}>
                    <TextField
                      id={id}
                      label={label}
                      size="small"
                      fullWidth
                      error={manualSplitError}
                      onChange={handleRowsChange}
                      slotProps={{ inputLabel: { shrink: true } }}
                    />
                  </Grid>
                ))}
              </Grid>
            </SplitsCard>
          )}
        </>
      )}

      {/* CROSS-VALIDATION SECTION */}
      {strategyKind === STRATEGY_KINDS.CV && (
        <>
          {/* CV Type Selector */}
          <SplitsCard label={t("experiments:label.cvType")}>
            <FormControl fullWidth size="small">
              <Select
                value={cvType}
                onChange={(e) => setCvType(e.target.value)}
              >
                {allowedCvTypes.map((type) => (
                  <MenuItem key={type.name} value={type}>
                    {type.display_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </SplitsCard>

          {/* Group Column */}
          {Boolean(cvType?.schema?.properties?.group_column) && (
            <SplitsCard
              label={t("experiments:label.groupColumn")}
              description={t("experiments:label.groupColumnDescription")}
              warning={groupColumnError && !groupColumn ? true : false}
            >
              <FormControl fullWidth size="small">
                <Select
                  value={groupColumn || ""}
                  onChange={handleGroupColumnChange}
                  error={groupColumnError && !groupColumn}
                  displayEmpty
                >
                  <MenuItem value="" disabled>
                    <em>{t("experiments:label.selectAColumn")}</em>
                  </MenuItem>
                  {inputColumnNames?.map((col) => (
                    <MenuItem key={col} value={col}>
                      {col}
                    </MenuItem>
                  )) || []}
                </Select>
              </FormControl>
            </SplitsCard>
          )}
        </>
      )}

      {/* Splitter parameters, generated from the component schema */}
      {splitterName && (
        <>
          <FormSchemaLayout>
            <FormSchema
              autoSave
              hideButtons
              key={splitterName}
              model={splitterName}
              onFormSubmit={setSplitterParams}
              setError={setParamsError}
              excludeFields={excludedFields}
            />
          </FormSchemaLayout>
          {splitsMessage && (
            <FormHelperText error sx={{ px: 4 }}>
              {splitsMessage}
            </FormHelperText>
          )}
        </>
      )}
    </Stack>
  );
}

SplitDatasetRows.propTypes = {
  datasetInfo: PropTypes.object.isRequired,
  rowsPartitionsIndex: PropTypes.object.isRequired,
  setRowsPartitionsIndex: PropTypes.func.isRequired,
  setSplitsReady: PropTypes.func.isRequired,
  splitType: PropTypes.string.isRequired,
  setSplitType: PropTypes.func.isRequired,
  SPLIT_TYPES: PropTypes.object.isRequired,
  splitterParams: PropTypes.object,
  setSplitterParams: PropTypes.func.isRequired,
  paramsError: PropTypes.bool,
  setParamsError: PropTypes.func.isRequired,
  evaluationStrategy: PropTypes.string.isRequired,
  setEvaluationStrategy: PropTypes.func.isRequired,
  cvType: PropTypes.object,
  holdoutType: PropTypes.object,
  setHoldoutType: PropTypes.func,
  strategyKind: PropTypes.string,
  setStrategyKind: PropTypes.func,
  setCvType: PropTypes.func.isRequired,
  groupColumn: PropTypes.string,
  setGroupColumn: PropTypes.func.isRequired,
  inputColumnNames: PropTypes.arrayOf(PropTypes.string),
  taskName: PropTypes.string,
};

export default SplitDatasetRows;
