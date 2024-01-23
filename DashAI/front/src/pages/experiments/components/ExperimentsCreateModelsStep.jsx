import PropTypes from "prop-types";
import React, { useState } from "react";
import ModelsTable from "../../../components/experiments/ModelsTable";
import useCompatibleModels from "../hooks/useCompatibleModels";
import useModels from "../hooks/useModels";
import ExperimentsCreateModelsStepLayout from "./ExperimentsCreateModelsStepLayout";
import ExperimentsCreateModelsToolbar from "./ExperimentsCreateModelsToolbar";

function ExperimentsCreateModelsStep({ newExp, setNewExp, setNextEnabled }) {
  const [selectedModel, setSelectedModel] = useState("");

  const { compatibleModels } = useCompatibleModels({
    relatedComponent: newExp?.task_name,
  });

  const { getModel } = useModels({ selectedModel });

  const handleAddButton = async ({ onSuccess }) => {
    const newModel = await getModel();
    setNewExp({ ...newExp, runs: [newModel, ...newExp.runs] });
    setNextEnabled(true);
    setSelectedModel("");
    onSuccess();
  };

  return (
    <ExperimentsCreateModelsStepLayout
      toolbar={
        <ExperimentsCreateModelsToolbar
          selectedModel={selectedModel}
          setSelectedModel={setSelectedModel}
          compatibleModels={compatibleModels}
          handleAddButton={handleAddButton}
        />
      }
    >
      <ModelsTable newExp={newExp} setNewExp={setNewExp} />
    </ExperimentsCreateModelsStepLayout>
  );
}
ExperimentsCreateModelsStep.propTypes = {
  newExp: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string,
    dataset: PropTypes.object,
    task_name: PropTypes.string,
    step: PropTypes.string,
    created: PropTypes.instanceOf(Date),
    last_modified: PropTypes.instanceOf(Date),
    runs: PropTypes.array,
  }),
  setNewExp: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};

export default ExperimentsCreateModelsStep;
