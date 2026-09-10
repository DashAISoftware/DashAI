import React, { useState, useEffect } from "react";
import { Box, CircularProgress, Typography } from "@mui/material";
import PropTypes from "prop-types";
import { useSnackbar } from "notistack";

import { getComponents as getComponentsRequest } from "../../api/component";
import ComponentSelector from "../custom/ComponentSelector";
import { useTranslation } from "react-i18next";

function SetNameAndExplainerStep({
  newExpl,
  setNewExpl,
  setNextEnabled,
  scope,
  taskName,
  modelName,
}) {
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(false);

  const [explainers, setExplainers] = useState([]);
  const [selectedExplainer, setSelectedExplainer] = useState({});
  const [selectedExplainerOk, setSelectedExplainerOk] = useState(false);
  const { t } = useTranslation(["explainers"]);

  const getExplainers = async () => {
    setLoading(true);
    try {
      // Explainers related to the task are model agnostic (usable by any
      // model of the task); explainers related to the run's model are
      // model specific ones the model declares in COMPATIBLE_COMPONENTS.
      const [taskRelated, modelRelated] = await Promise.all([
        getComponentsRequest({
          selectTypes: [`${scope}Explainer`],
          relatedComponent: taskName,
        }),
        modelName
          ? getComponentsRequest({
              selectTypes: [`${scope}Explainer`],
              relatedComponent: modelName,
            })
          : Promise.resolve([]),
      ]);
      const seen = new Set();
      const result = [...taskRelated, ...modelRelated].filter((obj) => {
        if (seen.has(obj.name)) return false;
        seen.add(obj.name);
        return true;
      });
      setExplainers(result.filter((obj) => !obj.name.startsWith("Fit")));
    } catch (error) {
      enqueueSnackbar(t("explainers:error.fetchExplainers"), {
        variant: "error",
      });
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedExplainer && "name" in selectedExplainer) {
      setNewExpl({
        ...newExpl,
        explainer_name: selectedExplainer.name,
      });
      setSelectedExplainerOk(true);
    }
  }, [selectedExplainer]);

  useEffect(() => {
    getExplainers();
  }, []);

  useEffect(() => {
    setNextEnabled(selectedExplainerOk);
  }, [selectedExplainerOk]);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Typography variant="subtitle2">
        {t("explainers:label.selectExplainer")}
      </Typography>

      {loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <ComponentSelector
          components={explainers}
          selected={selectedExplainer?.name ? selectedExplainer : null}
          onSelect={setSelectedExplainer}
          flat
          searchPlaceholder={t("explainers:label.searchExplainers", {
            defaultValue: "Search explainers...",
          })}
        />
      )}
    </Box>
  );
}

SetNameAndExplainerStep.propTypes = {
  newExpl: PropTypes.shape({
    explainer_name: PropTypes.string,
    dataset_id: PropTypes.number,
    parameters: PropTypes.object,
    fit_parameters: PropTypes.object,
  }),
  setNewExpl: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
  scope: PropTypes.string.isRequired,
  taskName: PropTypes.string,
  modelName: PropTypes.string,
};

export default SetNameAndExplainerStep;
