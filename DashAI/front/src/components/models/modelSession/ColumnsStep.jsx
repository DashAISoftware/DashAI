import React, { useEffect, useMemo, useRef, useState } from "react";
import PropTypes from "prop-types";

import {
  Grid,
  CircularProgress,
  Box,
  Alert,
  AlertTitle,
  Chip,
} from "@mui/material";
import DivideDatasetColumns from "./DivideDatasetColumns";
import {
  buildAtomList,
  atomKey,
  realAtomKey,
  toRealAtom,
  reseedColumnSelection,
  isAtomSelectionValidLocally,
} from "./buildAtomList";
import {
  getModelSessionById as getModelSessionByIdRequest,
  validateColumns as validateColumnsRequest,
  updateModelSession as updateModelSessionRequest,
  getConvertersOutputSlots as getConvertersOutputSlotsRequest,
} from "../../../api/modelSession";
import { getDatasetTypes as getDatasetTypesRequest } from "../../../api/datasets";
import { getComponents as getComponentsRequest } from "../../../api/component";
import { useSnackbar } from "notistack";
import { getColorByColumnType } from "../../../utils";
import { useTranslation } from "react-i18next";
import { Trans } from "react-i18next";

// Human-readable display label for an atom in the picker: a "column" atom
// shows its own name, a "group" atom shows its owning converter's name and
// the declared label of that output slot (rather than the internal
// `__group__${converterId}__${slot}` synthetic key used as its identity).
const atomDisplayLabel = (atom) =>
  atom.kind === "column" ? atom.name : `${atom.converterName}: ${atom.label}`;

/**
 * Step of the session wizard: pick input/output columns from the session's
 * *current* column set — i.e. after any converters configured in the
 * preprocessing step have been applied — rather than from the raw dataset.
 *
 * This step does not own its own submit button: the wizard's shared footer
 * (CreateSessionSteps.jsx) owns "Atrás"/"Siguiente"/"Crear sesión". Instead,
 * this component hands the wizard a ready-to-call PATCH closure via
 * `onReadyToFinalize`, re-supplied on every render so the wizard always has
 * the latest valid input/output selection, without this component needing
 * to know anything about wizard-level navigation.
 *
 * @param {string|number} modelSessionId id of the model session being created
 * @param {string} taskName name of the task selected for this session
 * @param {object} dataset the raw dataset backing this session (its `id` is
 *   still required by the /validation endpoint's schema)
 * @param {number} refreshTrigger bumped by the wizard every time the user
 *   advances into this step, so the column set is re-read after any converter
 *   applied in the preprocessing step (this component never unmounts)
 * @param {function} setNextEnabled function to enable or disable the wizard's "Next" action
 * @param {function} onReadyToFinalize called with a `() => Promise` closure that PATCHes
 *   the session's final input/output columns, re-supplied whenever the selection changes
 */
function ColumnsStep({
  modelSessionId,
  taskName,
  dataset,
  refreshTrigger,
  setNextEnabled,
  onReadyToFinalize,
}) {
  // The full, ever-growing list of selectable atoms built by
  // `buildAtomList`: every raw dataset column, plus one atom per declared
  // output slot of every converter configured on the session (see the
  // design spec, section C). Never removes anything, regardless of what a
  // later converter might do to earlier columns.
  const [atoms, setAtoms] = useState([]);
  const { enqueueSnackbar } = useSnackbar();
  const [infoLoading, setInfoLoading] = useState(true);
  const { t } = useTranslation(["experiments", "common"]);

  // null means "not fetched yet" — distinct from the empty-but-loaded shape
  // getTaskRequirements falls back to when the task genuinely isn't found.
  // The banner below only renders once this is non-null, otherwise it briefly
  // interpolates its message with blank task name/types/cardinality.
  const [taskRequirements, setTaskRequirements] = useState(null);

  const [inputColumnNames, setInputColumnNames] = useState([]);
  const [outputColumnNames, setOutputColumnNames] = useState([]);

  const [columnsReady, setColumnsReady] = useState(false);
  const [columnsAreValid, setColumnsAreValid] = useState(false);
  // True until the current column selection has actually been checked against
  // the backend at least once — distinct from columnsAreValid=false, so the
  // banner doesn't flash red while columns are still being auto-selected or a
  // check is in flight, only once a real valid/invalid result is known.
  const [validationPending, setValidationPending] = useState(true);

  // Mirror of the current selection, readable from the async fetch below
  // without capturing a stale render closure (the fetch only re-runs on
  // refreshTrigger, so its closure can be several renders old by the time it
  // resolves). Assigned during render, which is safe: it's a pure copy of
  // state this component already rendered.
  const selectionRef = useRef({ input: [], output: [] });
  selectionRef.current = {
    input: inputColumnNames,
    output: outputColumnNames,
  };

  const fetchCurrentColumns = async () => {
    setInfoLoading(true);
    try {
      const [rawColumnTypes, session] = await Promise.all([
        getDatasetTypesRequest(dataset.id),
        getModelSessionByIdRequest(String(modelSessionId)),
      ]);

      // `session.converters` entries carry only what the backend persists
      // (id/converter/params/input_scope/target_column), never a tool's
      // `output_slots`, so those have to be fetched separately — from this
      // specific converter *instance*'s real params (e.g. a `SimpleImputer`
      // configured with `add_indicator: true` really declares a second
      // slot), not the generic per-converter-class metadata `/component/`
      // returns, which always reflects default params and would never see
      // that. Same pattern as SessionConvertersRightBar.jsx.
      const outputSlotsByConverterId = session.converters?.length
        ? await getConvertersOutputSlotsRequest(session.converters)
        : {};
      const sessionConvertersWithMetadata = (session.converters || []).map(
        (entry) => ({
          ...entry,
          metadata: { output_slots: outputSlotsByConverterId[entry.id] || [] },
        }),
      );

      const nextAtoms = buildAtomList({
        datasetColumnTypes: rawColumnTypes,
        converters: sessionConvertersWithMetadata,
      });
      setAtoms(nextAtoms);

      // Converters configured in the previous step can add output-slot
      // groups (and the raw dataset columns can, in principle, change too),
      // so anything still selected from a previous visit to this step has
      // to be checked against the freshly-built atom set — keeping a
      // reference to an atom that no longer exists would silently finalize
      // the session with a column/group that isn't there anymore.
      // `reseedColumnSelection` also prefers a real column (never a group
      // atom) as the default output whenever it has to pick one from
      // scratch, since a converter's generated feature is essentially
      // never what someone wants as a default prediction target.
      const {
        inputKeys,
        outputKeys,
        atomsByKey: nextAtomsByKey,
      } = reseedColumnSelection({
        atoms: nextAtoms,
        previousInputKeys: selectionRef.current.input.map(realAtomKey),
        previousOutputKeys: selectionRef.current.output.map(realAtomKey),
      });

      setInputColumnNames(
        inputKeys.map((key) => toRealAtom(nextAtomsByKey[key])),
      );
      setOutputColumnNames(
        outputKeys.map((key) => toRealAtom(nextAtomsByKey[key])),
      );
    } catch (error) {
      enqueueSnackbar(t("experiments:error.errorFetchingDatasetInfo"));
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    } finally {
      setInfoLoading(false);
    }
  };

  const getTaskRequirements = async () => {
    try {
      const taskComponents = await getComponentsRequest({
        selectTypes: ["Task"],
      });

      const currentTask = taskComponents.find((task) => task.name === taskName);
      if (currentTask) {
        setTaskRequirements(currentTask);
      } else {
        enqueueSnackbar(
          t("experiments:error.taskRequirementsNotFound", {
            taskName: taskName,
          }),
        );
        setTaskRequirements({
          name: taskName,
          metadata: {
            inputs_types: [],
            inputs_cardinality: "",
            outputs_types: [],
            outputs_cardinality: "",
          },
        });
      }
    } catch (error) {
      enqueueSnackbar(t("experiments:error.errorFetchingTaskRequirements"));
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  // `DivideDatasetColumns` (like the shared `ColumnSelector`) still expects
  // a flat `{name: {type, dtype}}` map rather than a list of atom objects,
  // so atoms are translated into that shape via the synthetic key
  // convention above, and selections are translated back into real atoms
  // before landing in `inputColumnNames`/`outputColumnNames` state.
  const atomsByKey = useMemo(() => {
    const map = {};
    atoms.forEach((atom) => {
      map[atomKey(atom)] = atom;
    });
    return map;
  }, [atoms]);

  const allAtomKeys = useMemo(() => Object.keys(atomsByKey), [atomsByKey]);

  const columnTypesForSelector = useMemo(() => {
    const map = {};
    for (const [key, atom] of Object.entries(atomsByKey)) {
      map[key] =
        atom.kind === "column"
          ? { type: atom.type, dtype: atom.dtype }
          : { type: atom.type || t("common:unknown"), dtype: "" };
    }
    return map;
  }, [atomsByKey, t]);

  // Human-readable label for every atom, keyed by its synthetic key — a
  // "column" atom shows its own name, a "group" atom shows
  // "ConverterName: slot label" instead of its raw `__group__...` key.
  const optionLabels = useMemo(() => {
    const map = {};
    for (const [key, atom] of Object.entries(atomsByKey)) {
      map[key] = atomDisplayLabel(atom);
    }
    return map;
  }, [atomsByKey]);

  const validateColumns = async () => {
    try {
      if (!atoms || atoms.length === 0) {
        setColumnsAreValid(false);
        return;
      }

      if (inputColumnNames.length === 0 || outputColumnNames.length === 0) {
        setColumnsAreValid(false);
        return;
      }

      const hasGroupAtom = (columns) =>
        columns.some((atom) => atom.kind === "group");

      if (hasGroupAtom(inputColumnNames) || hasGroupAtom(outputColumnNames)) {
        // The `/model-session/validation` endpoint predates converter
        // output groups: it materializes a small sample of the RAW dataset
        // (or a previous training run's preprocessed partition) and checks
        // literal column names against it, with no notion of a group
        // atom's synthetic key. Sending it one there is no column by that
        // name, so it can only 400 (its own input-length sanity check) or
        // 500 (an uncaught KeyError) — never a clean "invalid" response —
        // which would permanently block "Crear sesión" for any session
        // with a converter. So a selection containing any group atom is
        // validated locally instead, via `isAtomSelectionValidLocally`
        // (see buildAtomList.js for the exact rules mirrored from the
        // backend's `BaseTask.validate_dataset_for_task`).
        const resolve = (columns) =>
          columns.map((column) => atomsByKey[realAtomKey(column)]);

        setColumnsAreValid(
          isAtomSelectionValidLocally({
            inputAtoms: resolve(inputColumnNames),
            outputAtoms: resolve(outputColumnNames),
            taskRequirements,
          }),
        );
        return;
      }

      const validation = await validateColumnsRequest(
        taskName,
        dataset.id, // still required by the endpoint's schema
        inputColumnNames.map(realAtomKey),
        outputColumnNames.map(realAtomKey),
        Number(modelSessionId),
      );
      setColumnsAreValid(validation.dataset_status === "valid");
    } catch (error) {
      enqueueSnackbar(t("experiments:error.errorFetchingColumnsValidation"));
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
      setColumnsAreValid(false);
    } finally {
      setValidationPending(false);
    }
  };

  useEffect(() => {
    if (inputColumnNames.length >= 1 && outputColumnNames.length >= 1) {
      setColumnsReady(true);
    } else {
      setColumnsReady(false);
    }
  }, [inputColumnNames, outputColumnNames]);

  useEffect(() => {
    if (columnsReady && atoms && atoms.length > 0) {
      setValidationPending(true);
      validateColumns();
    } else {
      setColumnsAreValid(false);
      setValidationPending(true);
    }
    // `taskRequirements` is a dependency because, when the selection
    // contains a group atom, validity is now computed locally against its
    // `metadata.inputs_types`/`outputs_types`/cardinality (see
    // `validateColumns`) instead of an authoritative backend call — so a
    // selection made before task requirements finish loading has to be
    // re-checked once they arrive, or it would be stuck at whatever the
    // "requirements not loaded yet" fallback produced.
  }, [
    columnsReady,
    inputColumnNames,
    outputColumnNames,
    atoms,
    taskRequirements,
  ]);

  useEffect(() => {
    setNextEnabled(!validationPending && columnsAreValid && columnsReady);
    // `inputColumnNames`/`outputColumnNames` are also dependencies, even
    // though the computed value only reads the three booleans above: the
    // wizard's parent force-disables "Crear sesión" on every return visit
    // to this step (see CreateSessionSteps.jsx's handleStep1Next), expecting
    // this effect to re-enable it once the freshly refetched selection is
    // confirmed valid again. But when a revisit's refetched selection ends
    // up identical to what was already valid before the visit (the common
    // case — nothing the user picked actually changed), `columnsReady`/
    // `columnsAreValid`/`validationPending` never change value either, so
    // an effect keyed on only those three never re-fires, and the parent's
    // forced `false` was never overwritten — "Crear sesión" stayed
    // disabled even though everything shown was genuinely valid. Selection
    // identity always changes on a fresh fetch (new array references), so
    // including it here forces this effect to re-assert its (possibly
    // unchanged) verdict on every refetch, not just when the verdict itself
    // flips.
  }, [
    columnsReady,
    columnsAreValid,
    validationPending,
    inputColumnNames,
    outputColumnNames,
  ]);

  useEffect(() => {
    fetchCurrentColumns();
    // refreshTrigger isn't read inside fetchCurrentColumns — it's a pure
    // re-run signal, bumped by CreateSessionSteps every time the wizard
    // advances into this step, so converters applied (or removed) in the
    // preprocessing step since the last visit are reflected here even though
    // this component never unmounts.
  }, [modelSessionId, refreshTrigger]);

  useEffect(() => {
    getTaskRequirements();
  }, []);

  // Re-supplied every time the selection changes so the wizard's "Crear
  // sesión" action always closes over the latest input/output columns,
  // without this component owning any wizard-level navigation itself.
  useEffect(() => {
    onReadyToFinalize(() =>
      updateModelSessionRequest({
        id: modelSessionId,
        formData: {
          input_columns: inputColumnNames,
          output_columns: outputColumnNames,
        },
      }),
    );
  }, [modelSessionId, inputColumnNames, outputColumnNames]);

  const selectedInputKeys = useMemo(
    () => inputColumnNames.map(realAtomKey),
    [inputColumnNames],
  );
  const selectedOutputKeys = useMemo(
    () => outputColumnNames.map(realAtomKey),
    [outputColumnNames],
  );

  const handleInputKeysChange = (keys) => {
    setInputColumnNames(keys.map((key) => toRealAtom(atomsByKey[key])));
  };
  const handleOutputKeysChange = (keys) => {
    setOutputColumnNames(keys.map((key) => toRealAtom(atomsByKey[key])));
  };

  const renderTypesAsChips = (typesList) => {
    if (!typesList || typesList.length === 0) {
      return <span>{t("common:any")}</span>;
    }

    return (
      <Box
        component="span"
        sx={{
          display: "inline-flex",
          gap: 1,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        {typesList.map((type, index) => (
          <React.Fragment key={type}>
            <Chip
              label={type}
              size="small"
              sx={{
                backgroundColor: getColorByColumnType(type),
                color: "#fff",
                fontWeight: 600,
                fontSize: "0.75rem",
                height: "22px",
              }}
            />
            {index < typesList.length - 1 && (
              <span style={{ margin: "0 4px" }}>{t("common:or")}</span>
            )}
          </React.Fragment>
        ))}
      </Box>
    );
  };

  return (
    <React.Fragment>
      {taskRequirements && !validationPending && (
        <Alert
          severity={columnsAreValid ? "success" : "error"}
          sx={{
            mb: 2,
            "& .MuiAlert-icon": { fontSize: 24 },
            bgcolor: (theme) =>
              `${theme.palette[columnsAreValid ? "success" : "error"].main}40`,
            border: (theme) =>
              `1px solid ${
                theme.palette[columnsAreValid ? "success" : "error"].main
              }`,
          }}
          data-tour="models-validation-alert"
        >
          <AlertTitle>
            {t(
              columnsAreValid
                ? "experiments:label.columnsValidRequirements"
                : "experiments:label.columnsInvalidRequirements",
              { taskName: taskRequirements.display_name },
            )}
          </AlertTitle>
          <Grid container spacing={4}>
            <Grid size={{ xs: 12 }}>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 2,
                  flexWrap: "wrap",
                }}
              >
                <Trans i18nKey="experiments:label.datasetInputColumnRequirements">
                  <span>The input columns must be of the types</span>
                  {renderTypesAsChips(taskRequirements.metadata.inputs_types)}
                  <span>
                    , and they should have a cardinality of
                    <span>
                      {{
                        cardinality:
                          taskRequirements.metadata.inputs_cardinality,
                      }}
                      .
                    </span>
                  </span>
                </Trans>
              </Box>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 2,
                  flexWrap: "wrap",
                }}
              >
                <Trans i18nKey="experiments:label.datasetOutputColumnRequirements">
                  <span>The output columns must be of the types</span>
                  {renderTypesAsChips(taskRequirements.metadata.outputs_types)}
                  <span>
                    , and they should have a cardinality of
                    {{
                      cardinality:
                        taskRequirements.metadata.outputs_cardinality,
                    }}
                    .
                  </span>
                </Trans>
              </Box>
            </Grid>
          </Grid>
        </Alert>
      )}

      {!infoLoading ? (
        <Grid container spacing={2}>
          <DivideDatasetColumns
            allColumnNames={allAtomKeys}
            columnTypes={columnTypesForSelector}
            optionLabels={optionLabels}
            selectedInputColumnNames={selectedInputKeys}
            onInputColumnNamesChange={handleInputKeysChange}
            selectedOutputColumnNames={selectedOutputKeys}
            onOutputColumnNamesChange={handleOutputKeysChange}
            disabled={infoLoading || allAtomKeys.length === 0}
          />
        </Grid>
      ) : (
        <Box sx={{ display: "flex", justifyContent: "center" }}>
          <CircularProgress />
        </Box>
      )}
    </React.Fragment>
  );
}

ColumnsStep.propTypes = {
  modelSessionId: PropTypes.oneOfType([PropTypes.string, PropTypes.number])
    .isRequired,
  taskName: PropTypes.string.isRequired,
  dataset: PropTypes.object.isRequired,
  refreshTrigger: PropTypes.number,
  setNextEnabled: PropTypes.func.isRequired,
  onReadyToFinalize: PropTypes.func.isRequired,
};
export default ColumnsStep;
