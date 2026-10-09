import React, { useEffect } from "react";
import PropTypes from "prop-types";
import { Alert } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useModels } from "../ModelsContext";
import SessionConvertersRightBar from "./SessionConvertersRightBar";
import AppliedConvertersView from "./AppliedConvertersView";
import usePreprocessingStructure from "./usePreprocessingStructure";

/**
 * Optional preprocessing step of the session wizard: build a chain of
 * converters, fit on training data only (see the backend's
 * PreprocessingJob), over the candidate columns picked in BaseColumnsStep.
 *
 * The dataset structure along the chain is estimated by the backend
 * (usePreprocessingStructure) on every change: a new converter can only be
 * scoped on columns that exist at the end of the chain, each card shows
 * what its step produces, and a step that cannot work is flagged and blocks
 * moving on.
 *
 * Styled like the notebook module's own converter picker: the catalog
 * (search + category list/grid) lives in the right bar
 * (SessionConvertersRightBar), the already-added converters are shown as
 * cards in the main content area (AppliedConvertersView).
 */
function PreprocessingStep({ newExp, setNewExp, setNextEnabled, dataset }) {
  const { t } = useTranslation(["models"]);
  const { setSessionRightContent } = useModels();
  const { structure, loading, error } = usePreprocessingStructure({
    datasetId: dataset?.id,
    candidates: newExp.candidate_columns,
    outputColumns: newExp.output_columns,
    steps: newExp.preprocessing,
  });

  useEffect(() => {
    setNextEnabled(Boolean(structure?.valid) && !loading && !error);
  }, [structure, loading, error, setNextEnabled]);

  useEffect(() => {
    setSessionRightContent(
      <SessionConvertersRightBar
        newExp={newExp}
        setNewExp={setNewExp}
        dataset={dataset}
        structure={structure}
      />,
    );
    return () => setSessionRightContent(null);
  }, [newExp, setNewExp, dataset, structure]);

  return (
    <>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {t("models:structure.loadError")}
        </Alert>
      )}
      <AppliedConvertersView
        newExp={newExp}
        setNewExp={setNewExp}
        structure={structure}
      />
    </>
  );
}

PreprocessingStep.propTypes = {
  newExp: PropTypes.object.isRequired,
  setNewExp: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
  dataset: PropTypes.object,
};

export default PreprocessingStep;
