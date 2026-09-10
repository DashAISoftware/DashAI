import React from "react";
import PropTypes from "prop-types";
import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import ParamInfoList from "./ParamInfoBox";

/**
 * Shared body for a run's "Configuración" view — the parameters it was
 * trained with, plus its optimizer setup if it was tuned via HPO. Used both
 * as a tab inside RunResults and as a standalone dialog opened from the
 * compact model card.
 */
function ModelConfigurationContent({ run, model }) {
  const { t } = useTranslation(["models", "common"]);
  const paramProperties = model?.schema?.properties ?? {};
  const getParamLabel = (key) => paramProperties[key]?.title ?? key;

  const hasParams = run.parameters && Object.keys(run.parameters).length > 0;
  const hasOptimizer = run.optimizer_name && run.goal_metric;

  if (!hasParams && !hasOptimizer) {
    return (
      <Typography variant="body2" color="text.secondary">
        {t("models:label.noConfigurationAvailable")}
      </Typography>
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 4 }}>
      {hasParams && (
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            {t("models:label.modelConfiguration")}
          </Typography>
          <ParamInfoList
            rows={Object.entries(run.parameters).map(([key, value]) => [
              getParamLabel(key),
              value,
            ])}
          />
        </Box>
      )}

      {hasOptimizer && (
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            {t("common:optimizer")}: {run.optimizer_name}
          </Typography>
          {run.optimizer_parameters &&
            Object.keys(run.optimizer_parameters).length > 0 && (
              <ParamInfoList
                rows={Object.entries(run.optimizer_parameters).map(
                  ([key, value]) => [key, value],
                )}
              />
            )}
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            {t("models:label.goalMetric")}: <strong>{run.goal_metric}</strong>
          </Typography>
        </Box>
      )}
    </Box>
  );
}

ModelConfigurationContent.propTypes = {
  run: PropTypes.shape({
    parameters: PropTypes.object,
    optimizer_name: PropTypes.string,
    optimizer_parameters: PropTypes.object,
    goal_metric: PropTypes.string,
  }).isRequired,
  model: PropTypes.shape({
    schema: PropTypes.object,
  }),
};

export default ModelConfigurationContent;
