import React, { useState, useRef, useMemo } from "react";
import PropTypes from "prop-types";
import {
  Box,
  Typography,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  ToggleButton,
} from "@mui/material";
import { LoadingButton } from "@mui/lab";
import {
  Close as CloseIcon,
  AddCircleOutline,
  PlayArrow as PlayArrowIcon,
} from "@mui/icons-material";
import { alpha } from "@mui/material/styles";
import { useTranslation } from "react-i18next";

import PillToggleButtonGroup from "../../shared/PillToggleButtonGroup";
import PredictionCard from "../PredictionCard";
import ManualPredictionsTable from "../ManualPredictionsTable";
import DatasetPredictionPanel from "../DatasetPredictionPanel";

/**
 * The Predictions tab: a dataset / manual toggle over the run's predictions.
 * Dataset predictions render as cards created through a dialog; manual ones
 * render in an editable table. Panel visibility is controlled by the parent so
 * an external "open prediction dialog" event can trigger it.
 */
export default function PredictionResultsTab({
  run,
  session,
  predictions,
  predictionDisplayNumbers,
  outputColumn,
  trainingDatasetSample,
  showDatasetPanel,
  setShowDatasetPanel,
  onSaved,
  onDelete,
  onUpdate,
}) {
  const { t } = useTranslation(["models", "common", "prediction"]);
  const [predictionFilter, setPredictionFilter] = useState("dataset");
  const datasetRunRef = useRef(null);
  const [datasetRunState, setDatasetRunState] = useState({
    canRun: false,
    isSubmitting: false,
  });
  // Add Row / Run Prediction for the manual table live here (next to the
  // Dataset/Manual toggle) so both prediction types share one header layout.
  // ManualPredictionsTable exposes its actions through this ref and reports
  // button-enabled state through onStateChange.
  const manualActionsRef = useRef(null);
  const [manualRunState, setManualRunState] = useState({
    canAddRow: false,
    canRun: false,
    isRunning: false,
  });

  const visiblePredictions = useMemo(
    () =>
      predictions.filter((p) =>
        predictionFilter === "dataset" ? p.dataset_id : !p.dataset_id,
      ),
    [predictions, predictionFilter],
  );

  return (
    <Box
      sx={{
        pb: 4,
        width: "100%",
        display: "grid",
        gridTemplateColumns: "1fr auto",
        columnGap: 2,
        rowGap: 4,
      }}
    >
      {predictionFilter === "dataset" ? (
        <Box
          sx={{
            gridColumn: "1",
            gridRow: "1",
            display: "flex",
            alignItems: "flex-end",
            gap: 2,
          }}
        >
          <Button
            variant="outlined"
            size="small"
            startIcon={<AddCircleOutline />}
            onClick={() => {
              setDatasetRunState({ canRun: false, isSubmitting: false });
              setShowDatasetPanel(true);
            }}
            sx={{ textTransform: "none", fontWeight: 500 }}
          >
            {t("models:button.addNewPrediction")}
          </Button>
        </Box>
      ) : (
        <Box
          sx={{
            gridColumn: "1",
            gridRow: "1",
            display: "flex",
            alignItems: "flex-end",
            gap: 2,
          }}
        >
          <Button
            variant="outlined"
            size="small"
            startIcon={<AddCircleOutline />}
            onClick={() => manualActionsRef.current?.addRow()}
            disabled={!manualRunState.canAddRow}
            sx={{ textTransform: "none", fontWeight: 500 }}
          >
            {t("common:addRow")}
          </Button>
          <LoadingButton
            variant="contained"
            size="small"
            color="primary"
            startIcon={<PlayArrowIcon />}
            onClick={() => manualActionsRef.current?.runPrediction()}
            disabled={!manualRunState.canRun}
            loading={manualRunState.isRunning}
            sx={{ textTransform: "none", fontWeight: 500 }}
          >
            {t("prediction:button.runPrediction")}
          </LoadingButton>
        </Box>
      )}

      {/* Spans every row below it so its containing block covers the whole
          scrollable list, not just this header row - otherwise it would stop
          sticking as soon as the header row itself scrolls out of view.
          zIndex above the Manual table's own sticky header (max z-index 2, see
          leanDatasetTable.css) so it always paints on top instead of being
          covered once both reach top:0. */}
      <Box
        sx={{
          gridColumn: "2",
          gridRow: "1 / -1",
          justifySelf: "end",
          alignSelf: "start",
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}
      >
        <PillToggleButtonGroup
          value={predictionFilter}
          onChange={(e, newValue) => {
            if (newValue !== null) setPredictionFilter(newValue);
          }}
          sx={{
            bgcolor: (theme) => alpha(theme.palette.ui.box, 0.8),
            backdropFilter: "blur(8px)",
          }}
        >
          <ToggleButton value="dataset" sx={{ px: 1.5 }}>
            {t("models:label.datasetPredictions")}
          </ToggleButton>
          <ToggleButton value="manual" sx={{ px: 1.5 }}>
            {t("models:label.manualPredictions")}
          </ToggleButton>
        </PillToggleButtonGroup>
      </Box>

      <Box sx={{ gridColumn: "1 / -1", gridRow: "2", minWidth: 0 }}>
        <Dialog
          open={showDatasetPanel}
          onClose={() => setShowDatasetPanel(false)}
          maxWidth="md"
          fullWidth
          PaperProps={{ sx: { minHeight: "500px" } }}
        >
          <DialogTitle sx={{ bgcolor: "background.paper" }}>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <Typography variant="h6" component="span">
                {t("models:button.newDatasetPrediction")}
              </Typography>
              <IconButton
                size="small"
                onClick={() => setShowDatasetPanel(false)}
                sx={{ color: "text.secondary" }}
              >
                <CloseIcon />
              </IconButton>
            </Box>
          </DialogTitle>
          <DialogContent dividers sx={{ bgcolor: "background.paper" }}>
            <DatasetPredictionPanel
              run={run}
              session={session}
              onSaved={(prediction) => {
                onSaved(prediction);
                setShowDatasetPanel(false);
              }}
              onClose={() => setShowDatasetPanel(false)}
              runRef={datasetRunRef}
              onStateChange={setDatasetRunState}
            />
          </DialogContent>
          <DialogActions sx={{ p: 2, bgcolor: "background.paper" }}>
            <Button
              variant="outlined"
              onClick={() => setShowDatasetPanel(false)}
              disabled={datasetRunState.isSubmitting}
            >
              {t("common:cancel")}
            </Button>
            <LoadingButton
              variant="contained"
              color="primary"
              disabled={!datasetRunState.canRun}
              loading={datasetRunState.isSubmitting}
              onClick={() => datasetRunRef.current?.()}
            >
              {t("prediction:button.runPrediction")}
            </LoadingButton>
          </DialogActions>
        </Dialog>

        {predictionFilter === "manual" ? (
          <ManualPredictionsTable
            run={run}
            session={session}
            predictions={visiblePredictions}
            targetColumn={outputColumn}
            datasetSample={trainingDatasetSample}
            onSaved={onSaved}
            onDelete={onDelete}
            actionsRef={manualActionsRef}
            onStateChange={setManualRunState}
          />
        ) : visiblePredictions.length === 0 ? (
          <Typography
            variant="body2"
            color="text.secondary"
            align="center"
            sx={{ py: 3 }}
          >
            {t("models:label.noDatasetPredictionsYet")}
          </Typography>
        ) : (
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              gap: 2,
            }}
          >
            {visiblePredictions.map((prediction) => (
              <PredictionCard
                key={prediction.id}
                prediction={prediction}
                onDelete={onDelete}
                onUpdate={onUpdate}
                targetColumn={outputColumn}
                datasetSample={trainingDatasetSample}
                displayNumber={predictionDisplayNumbers.get(prediction.id)}
              />
            ))}
          </Box>
        )}
      </Box>
    </Box>
  );
}

PredictionResultsTab.propTypes = {
  run: PropTypes.object.isRequired,
  session: PropTypes.object,
  predictions: PropTypes.array.isRequired,
  predictionDisplayNumbers: PropTypes.instanceOf(Map).isRequired,
  outputColumn: PropTypes.string,
  trainingDatasetSample: PropTypes.object,
  showDatasetPanel: PropTypes.bool.isRequired,
  setShowDatasetPanel: PropTypes.func.isRequired,
  onSaved: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onUpdate: PropTypes.func.isRequired,
};
