import React, { useEffect } from "react";
import PropTypes from "prop-types";
import { useModels } from "../ModelsContext";
import SessionConvertersRightBar from "./SessionConvertersRightBar";
import AppliedConvertersView from "./AppliedConvertersView";

/**
 * Optional preprocessing step of the session wizard: pick converters to fit
 * on training data only (see the backend's PreprocessingJob), and configure
 * each one's scope. A converter's scope may include the not-yet-materialized
 * output group of an earlier converter in the same list, which is how
 * chaining works before any real fit exists.
 *
 * Styled like the notebook module's own converter picker: the catalog
 * (search + category list/grid) lives in the right bar
 * (SessionConvertersRightBar), the already-added converters are shown as
 * cards in the main content area (AppliedConvertersView).
 */
function PreprocessingStep({
  newExp,
  setNewExp,
  setNextEnabled,
  dataset,
  datasetTypes,
}) {
  const { setSessionRightContent } = useModels();

  useEffect(() => {
    setNextEnabled(true);
  }, [setNextEnabled]);

  useEffect(() => {
    setSessionRightContent(
      <SessionConvertersRightBar
        newExp={newExp}
        setNewExp={setNewExp}
        dataset={dataset}
        datasetTypes={datasetTypes}
      />,
    );
    return () => setSessionRightContent(null);
  }, [newExp, setNewExp, dataset, datasetTypes]);

  return (
    <AppliedConvertersView
      newExp={newExp}
      setNewExp={setNewExp}
      datasetTypes={datasetTypes}
    />
  );
}

PreprocessingStep.propTypes = {
  newExp: PropTypes.object.isRequired,
  setNewExp: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
  dataset: PropTypes.object,
  datasetTypes: PropTypes.object,
};

export default PreprocessingStep;
