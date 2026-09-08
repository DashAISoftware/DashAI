import React from "react";
import { useStrategyKind } from "../../../hooks/useStrategyKind";
import { STRATEGY_KINDS } from "../../../utils/splitsPayload";
import PropTypes from "prop-types";
import { Box, Typography, Tab, Tooltip, Chip } from "@mui/material";
import { useTranslation } from "react-i18next";
import PillTabs from "../../shared/PillTabs";
import { useModels } from "../ModelsContext";

const groupLabelSx = {
  textTransform: "uppercase",
  letterSpacing: 0.5,
  fontWeight: 600,
  pl: 2,
  pt: 1,
};

/** The vertical rule that separates two tab groups. */
function GroupDivider() {
  // Empty spacer just for the horizontal gap between groups. Kept out of the
  // flex height/alignment calculation so the actual rule (positioned
  // absolutely inside it) can be sized freely without pushing the tabs around.
  return (
    <Box sx={{ position: "relative", alignSelf: "stretch", width: 0, mx: 4 }}>
      <Box
        sx={{
          position: "absolute",
          top: 32,
          bottom: -16,
          left: 0,
          width: "1px",
          bgcolor: "divider",
        }}
      />
    </Box>
  );
}

// Matches the MUI small Chip's height, so tabs with a count chip don't grow
// taller than plain-text tabs and push their label off-center.
const TAB_LABEL_HEIGHT = 24;
// Shared width for every tab (both Metrics rows and the Operations row), so
// pills line up horizontally instead of each one hugging its own label
// length. Sized to fit the longest label + chip ("Nested CV Results").
const TAB_LABEL_WIDTH = 140;
const tabLabelRowSx = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 2,
  height: TAB_LABEL_HEIGHT,
  width: TAB_LABEL_WIDTH,
};

/**
 * The three grouped pill tab bars (Metrics: Live/Hyperparameters, Operations:
 * Explainability/Predictions, Model: Visualization) shown above a run's
 * results, with a vertical rule between the groups. Purely presentational.
 */
export default function ResultsTabsHeader({
  activeTab,
  onTabChange,
  isFinished,
  optimizables,
  explainerCount,
  predictionCount,
  supportsModelArtifacts = false,
  run,
}) {
  const { t } = useTranslation(["models"]);

  // Explains *why* a tab is disabled, so it reads as a real (if currently
  // unavailable) tab rather than being confused with the static group labels.
  const notFinishedTooltip = !isFinished
    ? t("models:message.tabAvailableAfterFinish")
    : "";
  const hyperparametersTooltip = !isFinished
    ? notFinishedTooltip
    : optimizables === 0
      ? t("models:message.noOptimizableParamsForHpo")
      : "";
  const visualizationTooltip = !isFinished
    ? notFinishedTooltip
    : !supportsModelArtifacts
      ? t("models:message.modelHasNoVisualization")
      : "";
  const nestedCvResultsTooltip = !isFinished
    ? notFinishedTooltip
    : !run?.nested
      ? t("models:message.nestedCvResultsOnlyForNestedCv")
      : "";

  // Get session from context to check if the evaluation strategy is Cross Validation
  const { selectedSession } = useModels();
  const isCrossValidation =
    useStrategyKind(selectedSession?.evaluation_strategy) === STRATEGY_KINDS.CV;
  const isNestedCrossValidation = !!run?.nested;

  // Cross-validation runs can only be explained when the session reserved rows
  // for it: the final model is refit on everything else, so without a test set
  // there is no data the model has not already seen.
  let sessionSplits = null;
  try {
    sessionSplits = selectedSession?.splits
      ? JSON.parse(selectedSession.splits)
      : null;
  } catch {
    sessionSplits = null;
  }
  // Sessions written while the reserved proportion was still called "holdout"
  // carry that key instead, the same fallback the backend normalizer applies.
  const hasDataToExplain =
    !isCrossValidation ||
    Number(sessionSplits?.test_size ?? sessionSplits?.holdout) > 0;
  const explainabilityTooltip = !isFinished
    ? notFinishedTooltip
    : !hasDataToExplain
      ? t("models:message.explainabilityNeedsHoldout")
      : "";

  return (
    <Box sx={{ display: "flex", alignItems: "flex-start" }}>
      <Box sx={{ display: "flex", flexDirection: "column" }}>
        <Typography variant="caption" color="text.secondary" sx={groupLabelSx}>
          {t("models:label.metrics")}
        </Typography>
        {/* Stacked rows instead of a single pill bar: each PillTabs sizes its
            tabs to their own content, and the second row only takes up space
            when Cross Validation adds fold/nested-CV results. */}
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
          <PillTabs
            value={[0, 3].includes(activeTab) ? activeTab : false}
            onChange={(e, newValue) => onTabChange(newValue)}
            aria-label="Result characteristics tabs"
          >
            <Tab
              value={0}
              label={
                <Box sx={tabLabelRowSx}>{t("models:label.liveMetrics")}</Box>
              }
            />
            <Tab
              value={3}
              label={
                <Tooltip title={hyperparametersTooltip}>
                  <Box sx={{ ...tabLabelRowSx, pointerEvents: "auto" }}>
                    {t("models:label.hyperparameters")}
                  </Box>
                </Tooltip>
              }
              disabled={!isFinished || optimizables === 0}
            />
          </PillTabs>
          {isCrossValidation && (
            <PillTabs
              value={[4, 5].includes(activeTab) ? activeTab : false}
              onChange={(e, newValue) => onTabChange(newValue)}
              aria-label="Result cross-validation tabs"
            >
              <Tab
                value={4}
                label={
                  <Box sx={tabLabelRowSx}>{t("models:label.foldGraphs")}</Box>
                }
                disabled={!isFinished}
              />
              <Tab
                value={5}
                label={
                  <Tooltip title={nestedCvResultsTooltip}>
                    <Box sx={{ ...tabLabelRowSx, pointerEvents: "auto" }}>
                      {t("models:label.nestedCvResults")}
                    </Box>
                  </Tooltip>
                }
                disabled={!isFinished || !isNestedCrossValidation}
              />
            </PillTabs>
          )}
        </Box>
      </Box>

      <GroupDivider />

      <Box sx={{ display: "flex", flexDirection: "column" }}>
        <Typography variant="caption" color="text.secondary" sx={groupLabelSx}>
          {t("models:label.operations")}
        </Typography>
        <PillTabs
          value={[1, 2].includes(activeTab) ? activeTab : false}
          onChange={(e, newValue) => onTabChange(newValue)}
          aria-label="Result operations tabs"
        >
          <Tab
            value={1}
            label={
              <Tooltip title={explainabilityTooltip}>
                <Box sx={{ ...tabLabelRowSx, pointerEvents: "auto" }}>
                  <span>{t("models:label.explainability")}</span>
                  {isFinished && (
                    <Chip label={explainerCount} size="small" color="primary" />
                  )}
                </Box>
              </Tooltip>
            }
            disabled={!isFinished || !hasDataToExplain}
          />
          <Tab
            value={2}
            label={
              <Tooltip title={notFinishedTooltip}>
                <Box sx={{ ...tabLabelRowSx, pointerEvents: "auto" }}>
                  <span>{t("models:label.predictions")}</span>
                  {isFinished && (
                    <Chip
                      label={predictionCount}
                      size="small"
                      color="primary"
                    />
                  )}
                </Box>
              </Tooltip>
            }
            disabled={!isFinished}
          />
        </PillTabs>
      </Box>

      <GroupDivider />

      <Box sx={{ display: "flex", flexDirection: "column" }}>
        <Typography variant="caption" color="text.secondary" sx={groupLabelSx}>
          {t("models:label.model")}
        </Typography>
        <PillTabs
          value={activeTab === 6 ? 6 : false}
          onChange={(e, newValue) => onTabChange(newValue)}
          aria-label="Model tabs"
        >
          <Tab
            value={6}
            label={
              <Tooltip title={visualizationTooltip}>
                <Box sx={{ ...tabLabelRowSx, pointerEvents: "auto" }}>
                  {t("models:label.visualization")}
                </Box>
              </Tooltip>
            }
            disabled={!isFinished || !supportsModelArtifacts}
          />
        </PillTabs>
      </Box>
    </Box>
  );
}

ResultsTabsHeader.propTypes = {
  activeTab: PropTypes.number.isRequired,
  onTabChange: PropTypes.func.isRequired,
  isFinished: PropTypes.bool,
  optimizables: PropTypes.number,
  explainerCount: PropTypes.number,
  predictionCount: PropTypes.number,
  supportsModelArtifacts: PropTypes.bool,
  run: PropTypes.object,
};
