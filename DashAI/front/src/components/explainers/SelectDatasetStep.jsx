import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";

import {
  Alert,
  AlertTitle,
  Box,
  Divider,
  FormControl,
  FormControlLabel,
  Link,
  Radio,
  RadioGroup,
  Slider,
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import { useSnackbar } from "notistack";
import { Link as RouterLink } from "react-router-dom";
import { Trans, useTranslation } from "react-i18next";

import {
  getDatasets as getDatasetsRequest,
  getDatasetInfo,
  getDatasetFile,
  getDatasetTypes,
  getDatasetTypesByFilePath,
  getDatasetSample,
} from "../../api/datasets";
import { getValidDatasets as getValidDatasetsRequest } from "../../api/explainer";
import { getRunById } from "../../api/run";
import { getModelSessionById } from "../../api/modelSession";
import { atomColumnNames } from "../../utils/columnAtoms";
import LeanDatasetTable from "../shared/leanDatasetTable/LeanDatasetTable";
import ManualInput from "../predictions/ManualInput";
import NoteBox from "../notebooks/NoteBox";
import DatasetAutocomplete from "../notebooks/notebookCreation/DatasetAutocomplete";
import ExplainerSourceToggle from "./ExplainerSourceToggle";
import RowSelectionModeToggle from "./RowSelectionModeToggle";
import ExplanationInfo from "./ExplanationInfo";

const SPLIT_VALUES = ["train", "test", "val", "all"];

export default function SelectDatasetStep({
  newExpl,
  setNewExpl,
  setNextEnabled,
}) {
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["explainers", "common", "datasets"]);

  // Where the instances to explain come from.
  const [source, setSource] = useState("dataset");

  // Dataset source state.
  const [datasets, setDatasets] = useState([]);
  const [loadingDatasets, setLoadingDatasets] = useState(true);
  const [requestError, setRequestError] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [isValidDataset, setIsValidDataset] = useState(false);
  const [totalRows, setTotalRows] = useState(0);
  const [columnTypes, setColumnTypes] = useState({});

  // Model session metadata (drives the explanation info and the manual form).
  const [inputColumns, setInputColumns] = useState([]);
  // Column *atoms* (`{kind: "column", name}` / `{kind: "group",
  // converter_id, slot}`) exactly as the session persists them, not plain
  // names — ExplanationInfo formats them for display.
  const [outputColumns, setOutputColumns] = useState([]);
  const [sessionConverters, setSessionConverters] = useState([]);
  const [trainingDatasetId, setTrainingDatasetId] = useState(null);
  const [splitFractions, setSplitFractions] = useState({
    train: 0,
    test: 0,
    validation: 0,
    all: 1,
  });

  // Row selection controls (dataset source).
  const [rowMode, setRowMode] = useState("percentage");
  const [split, setSplit] = useState("test");
  const [percentage, setPercentage] = useState(20);
  const [shuffle, setShuffle] = useState(false);
  const [selectedRowIndices, setSelectedRowIndices] = useState(() => new Set());

  // Manual input source state.
  const [manualTypes, setManualTypes] = useState({});
  const [manualSample, setManualSample] = useState(null);
  const [loadingManual, setLoadingManual] = useState(false);
  const [manualRows, setManualRows] = useState([]);

  // ----- data fetching -------------------------------------------------

  // Only datasets compatible with the run's model (same input/output columns)
  // can be explained. A single endpoint validates them all server-side and
  // returns the valid ids, which we use to filter the dataset list.
  useEffect(() => {
    const fetchDatasets = async () => {
      if (!newExpl.run_id) return;
      setLoadingDatasets(true);
      try {
        const [all, validIds] = await Promise.all([
          getDatasetsRequest(),
          getValidDatasetsRequest(newExpl.run_id),
        ]);
        const validIdSet = new Set(validIds.map(String));
        setDatasets(all.filter((ds) => validIdSet.has(String(ds.id))));
      } catch (error) {
        enqueueSnackbar(t("explainers:error.fetchDatasets"), {
          variant: "error",
        });
        setRequestError(true);
        console.error("Error fetching datasets", error);
      } finally {
        setLoadingDatasets(false);
      }
    };
    fetchDatasets();
  }, [newExpl.run_id]);

  // Run -> model session metadata (input/target columns, splits, training id).
  useEffect(() => {
    const fetchRunInfo = async () => {
      if (!newExpl.run_id) return;
      try {
        const run = await getRunById(newExpl.run_id);
        const session = await getModelSessionById(run.model_session_id);
        const sessionOutputColumns = session.output_columns ?? [];
        setOutputColumns(sessionOutputColumns);
        setSessionConverters(session.converters ?? []);
        setTrainingDatasetId(session.dataset_id);
        // Not `session.input_columns`: a converter that adds/renames input
        // columns (BagOfWords' `bow_<word>`, PCA's `pca0`/`pca1`) means
        // those names only exist in the session's preprocessed data, never
        // in a raw dataset — this info panel showed a required column no
        // real dataset (including a fully compatible one) would ever have.
        // The training dataset's own raw schema is what a compatible
        // dataset actually needs to provide.
        try {
          const rawTypes = await getDatasetTypes(session.dataset_id);
          // `sessionOutputColumns` holds atoms, so `.includes(col)` against
          // a raw column name never matched and the target column leaked
          // into this list. Only `column` atoms name a real raw column; a
          // `group` atom's real columns don't exist in the raw dataset at
          // all, so it correctly excludes nothing here.
          const targetColumnNames = atomColumnNames(sessionOutputColumns);
          setInputColumns(
            Object.keys(rawTypes).filter(
              (col) => !targetColumnNames.includes(col),
            ),
          );
        } catch (error) {
          console.error("Error loading training dataset schema", error);
          setInputColumns([]);
        }
        const sessionSplits = JSON.parse(session.splits);
        setSplitFractions((prev) => ({
          ...prev,
          train: sessionSplits.train,
          test: sessionSplits.test,
          validation: sessionSplits.validation,
        }));
      } catch (error) {
        console.error(`Error fetching run info for ${newExpl.run_id}`, error);
      }
    };
    fetchRunInfo();
  }, [newExpl.run_id]);

  // The list only contains valid datasets, so on selection just load the row
  // count and column types needed by the rows table.
  useEffect(() => {
    const onDatasetSelected = async () => {
      setSelectedRowIndices(new Set());
      if (!selectedDataset) {
        setIsValidDataset(false);
        return;
      }
      setIsValidDataset(true);
      try {
        const [info, types] = await Promise.all([
          getDatasetInfo(selectedDataset.id),
          getDatasetTypesByFilePath(selectedDataset.file_path),
        ]);
        setTotalRows(info.total_rows ?? 0);
        setColumnTypes(types ?? {});
      } catch (error) {
        enqueueSnackbar(t("explainers:error.validateDataset"), {
          variant: "error",
        });
        console.error("Error loading dataset info", error);
      }
    };
    onDatasetSelected();
  }, [selectedDataset]);

  // Load types + sample for the manual-input form (from the training dataset).
  useEffect(() => {
    const loadManualSchema = async () => {
      if (source !== "manual" || !trainingDatasetId || manualSample) return;
      setLoadingManual(true);
      try {
        const [types, sample] = await Promise.all([
          getDatasetTypes(trainingDatasetId),
          getDatasetSample(trainingDatasetId),
        ]);
        setManualTypes(types);
        setManualSample(sample);
      } catch (error) {
        enqueueSnackbar(t("explainers:error.validateDataset"), {
          variant: "error",
        });
        console.error("Error loading manual input schema", error);
      } finally {
        setLoadingManual(false);
      }
    };
    loadManualSchema();
  }, [source, trainingDatasetId]);

  // ----- write the scope / dataset_id / manual_input into newExpl ------

  useEffect(() => {
    if (source === "manual") {
      setNewExpl((prev) => ({
        ...prev,
        dataset_id: trainingDatasetId,
        scope: { mode: "manual" },
        manual_input: manualRows,
      }));
      return;
    }

    const scope =
      rowMode === "manual"
        ? {
            mode: "rows",
            row_indexes: [...selectedRowIndices].sort((a, b) => a - b),
          }
        : { mode: "split", split, percentage, shuffle };

    setNewExpl((prev) => ({
      ...prev,
      dataset_id: selectedDataset?.id ?? null,
      scope,
      manual_input: null,
    }));
  }, [
    source,
    rowMode,
    split,
    percentage,
    shuffle,
    selectedRowIndices,
    selectedDataset,
    manualRows,
    trainingDatasetId,
    setNewExpl,
  ]);

  // ----- gate the Next button ------------------------------------------

  const datasetReady = Boolean(selectedDataset) && isValidDataset;
  const dataValid =
    source === "manual"
      ? Boolean(manualSample) && manualRows.length > 0
      : rowMode === "manual"
        ? datasetReady && selectedRowIndices.size > 0
        : datasetReady;

  useEffect(() => {
    setNextEnabled(dataValid);
  }, [dataValid]);

  // ----- handlers ------------------------------------------------------

  const fractionFor = (splitValue) =>
    splitValue === "val"
      ? splitFractions.validation
      : (splitFractions[splitValue] ?? 0);

  const rowsInSplit = Math.round(totalRows * fractionFor(split));
  const rowsSelectedByPercentage =
    percentage > 0
      ? Math.max(1, Math.round((percentage / 100) * rowsInSplit))
      : 1;

  const datasetFetchPage = (page, pageSize) =>
    getDatasetFile(selectedDataset.file_path, page, pageSize);

  // ----- render --------------------------------------------------------

  return (
    <Box sx={{ width: "100%" }}>
      <ExplainerSourceToggle source={source} onChange={setSource} />

      {source === "manual" ? (
        <ManualInput
          experiment={{ input_columns: inputColumns }}
          loading={loadingManual}
          types={manualTypes}
          sample={manualSample}
          manualInputData={manualRows}
          setManualInputData={setManualRows}
          showTarget={false}
          title={t("explainers:label.enterInstancesManually")}
          subtitle={t("explainers:label.manualInputDescription")}
        />
      ) : (
        <Box sx={{ width: "100%" }}>
          <Typography variant="subtitle1" component="h3" sx={{ mb: 3 }}>
            {t("explainers:label.selectDatasetToExplain")}
          </Typography>

          {datasets.length === 0 && !loadingDatasets && !requestError && (
            <Alert severity="warning" sx={{ mb: 4 }}>
              <Trans i18nKey="explainers:label.noDatasetsAvailable">
                <AlertTitle>There are no datasets available.</AlertTitle>
                Go to
                <Link component={RouterLink} to="/app/data?action=upload">
                  data tab
                </Link>
                to upload one first.
              </Trans>
            </Alert>
          )}

          <DatasetAutocomplete
            datasets={datasets}
            selectedDataset={selectedDataset}
            setSelectedDataset={setSelectedDataset}
            showDetails={false}
          />

          {datasetReady && (
            <Stack spacing={4} sx={{ mt: 4 }}>
              <ExplanationInfo
                inputColumns={inputColumns}
                outputColumns={outputColumns}
                converters={sessionConverters}
              />
              <Box>
                {rowMode === "manual" && (
                  <Typography variant="subtitle2" sx={{ mb: 2 }}>
                    {t("explainers:label.markRowsToExplain")}
                  </Typography>
                )}
                <LeanDatasetTable
                  key={selectedDataset.id}
                  fetchPage={datasetFetchPage}
                  initialPageSize={5}
                  columnTypes={columnTypes}
                  datasetPath={selectedDataset.file_path}
                  datasetName={selectedDataset.name}
                  showExportButton={false}
                  enableRowSelection={rowMode === "manual"}
                  selectedRowIndices={selectedRowIndices}
                  onRowSelectionChange={setSelectedRowIndices}
                />
              </Box>
            </Stack>
          )}

          {datasetReady && (
            <Box sx={{ mt: 6 }}>
              <Typography variant="subtitle2" sx={{ mb: 2 }}>
                {t("explainers:label.rowSelectionMode")}
              </Typography>
              <RowSelectionModeToggle mode={rowMode} onChange={setRowMode} />

              {rowMode === "percentage" ? (
                <Box sx={{ mt: 4 }}>
                  <FormControl
                    component="fieldset"
                    sx={{ width: "100%", mb: 4 }}
                  >
                    <Typography gutterBottom>
                      {t("explainers:label.datasetSplit")}
                    </Typography>
                    <RadioGroup
                      row
                      value={split}
                      onChange={(e) => setSplit(e.target.value)}
                      sx={{ mt: 2 }}
                    >
                      {SPLIT_VALUES.map((value) => (
                        <FormControlLabel
                          key={value}
                          value={value}
                          control={<Radio />}
                          label={t(
                            `common:${value === "val" ? "validation" : value}`,
                          )}
                        />
                      ))}
                    </RadioGroup>
                  </FormControl>
                  <Typography gutterBottom>
                    {t("explainers:label.percentageOfSplitToUse")}
                  </Typography>
                  <Stack direction="row" spacing={4} alignItems="center">
                    <Slider
                      value={typeof percentage === "number" ? percentage : 0}
                      onChange={(_e, v) => setPercentage(v)}
                      valueLabelDisplay="auto"
                      step={1}
                      marks={[
                        { value: 0, label: "0%" },
                        { value: 25, label: "25%" },
                        { value: 50, label: "50%" },
                        { value: 75, label: "75%" },
                        { value: 100, label: "100%" },
                      ]}
                      min={0}
                      max={100}
                      sx={{ flex: 1 }}
                    />
                    <TextField
                      label="%"
                      type="number"
                      size="small"
                      value={percentage}
                      onChange={(e) => {
                        const val =
                          e.target.value === "" ? "" : Number(e.target.value);
                        if (val === "" || (val >= 0 && val <= 100)) {
                          setPercentage(val);
                        }
                      }}
                      inputProps={{ min: 0, max: 100 }}
                      sx={{ width: "80px" }}
                    />
                  </Stack>
                  <FormControlLabel
                    sx={{ mt: 4 }}
                    control={
                      <Switch
                        checked={shuffle}
                        onChange={(e) => setShuffle(e.target.checked)}
                      />
                    }
                    label={t("explainers:label.shuffleRows")}
                  />
                  <Divider sx={{ my: 3 }} />
                  <Typography variant="caption" color="text.secondary">
                    <Trans i18nKey="explainers:label.splitSelectionSummary">
                      Percentage: {{ percentage }}% | Rows selected:
                      {{ rowsSelected: rowsSelectedByPercentage }}/{" "}
                      {{ totalRows: rowsInSplit }}
                    </Trans>
                  </Typography>
                </Box>
              ) : (
                <Box sx={{ mt: 4 }}>
                  <Typography variant="caption" color="text.secondary">
                    {t("explainers:label.rowsSelectedManually", {
                      selected: selectedRowIndices.size,
                      total: totalRows,
                    })}
                  </Typography>
                </Box>
              )}

              <Box sx={{ mt: 4 }}>
                <NoteBox message={t("explainers:label.datasetSelection")} />
              </Box>
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
}

SelectDatasetStep.propTypes = {
  newExpl: PropTypes.shape({
    run_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    explainer_name: PropTypes.string,
    dataset_id: PropTypes.number,
    parameters: PropTypes.object,
    fit_parameters: PropTypes.object,
  }),
  setNewExpl: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};
