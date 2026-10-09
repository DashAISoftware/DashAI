import React from "react";
import PropTypes from "prop-types";
import { Grid, ToggleButton, ToggleButtonGroup } from "@mui/material";
import { useTranslation } from "react-i18next";

/**
 * Toggle that picks which split's metrics are displayed.
 *
 * Which buttons appear is driven by the metrics the run actually produced, not
 * by its evaluation strategy: a cross-validation run always scores a validation
 * partition, and only scores a test one when the session reserved rows the
 * folds never see.
 */
function ResultsTabMetricsToggle({
  displaySet,
  setDisplaySet,
  hasTrainData = true,
  hasValidationData = true,
  hasTestData = true,
}) {
  const { t } = useTranslation(["common"]);

  return (
    <Grid>
      <ToggleButtonGroup
        value={displaySet}
        exclusive
        onChange={(event, newSet) => {
          // condition to enforce value set
          if (newSet !== null) {
            setDisplaySet(newSet);
          }
        }}
        sx={{ float: "right" }}
      >
        {hasTestData && (
          <ToggleButton value="test_metrics">{t("common:test")}</ToggleButton>
        )}
        {hasTrainData && (
          <ToggleButton value="train_metrics">{t("common:train")}</ToggleButton>
        )}
        {hasValidationData && (
          <ToggleButton value="validation_metrics">
            {t("common:validation")}
          </ToggleButton>
        )}
      </ToggleButtonGroup>
    </Grid>
  );
}

ResultsTabMetricsToggle.propTypes = {
  displaySet: PropTypes.string.isRequired,
  setDisplaySet: PropTypes.func.isRequired,
  hasTrainData: PropTypes.bool,
  hasValidationData: PropTypes.bool,
  hasTestData: PropTypes.bool,
};

export default ResultsTabMetricsToggle;
