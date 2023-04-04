import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { CustomContainer, StyledButton } from "../styles/globalComponents";
import AddModels from "../components/AddModels";
import ParameterForm from "../components/ParameterForm";

function Experiment() {
  const [compatibleModels] = useState(
    JSON.parse(localStorage.getItem("compatibleModels")) || []
  );
  useEffect(
    () =>
      localStorage.setItem(
        "compatibleModels",
        JSON.stringify(compatibleModels)
      ),
    [compatibleModels]
  );
  //
  const [modelsInTable, setModelsInTable] = useState(
    JSON.parse(localStorage.getItem("modelsInTable")) || []
  );
  useEffect(
    () => localStorage.setItem("modelsInTable", JSON.stringify(modelsInTable)),
    [modelsInTable]
  );
  //
  const [executionConfig, setExecutionConfig] = useState(
    JSON.parse(localStorage.getItem("executionConfig")) || []
  );
  useEffect(
    () =>
      localStorage.setItem("executionConfig", JSON.stringify(executionConfig)),
    [executionConfig]
  );
  //
  const [formData, setFormData] = useState(
    JSON.parse(localStorage.getItem("formData")) || {
      type: "",
      index: -1,
      parameterSchema: {},
    }
  );
  useEffect(
    () => localStorage.setItem("formData", JSON.stringify(formData)),
    [formData]
  );
  //
  const [showModal, setShowModal] = useState(false);
  // functions
  const handleModalClose = () => setShowModal(false);
  const setConfigByTableIndex = (index, modelName, newValues) => {
    const modelConfig = { model_name: modelName, payload: newValues };
    const executionConfigAux = [...executionConfig];
    if (index >= executionConfig.length) {
      executionConfigAux.push(modelConfig);
      setExecutionConfig(executionConfigAux);
    }
    executionConfigAux[index] = modelConfig;
    setExecutionConfig(executionConfigAux);
  };
  const setConfigFactory = (index) => (modelName, newValues) =>
    setConfigByTableIndex(index, modelName, newValues);
  const renderFormFactory = (type, index) => async () => {
    const fetchedJsonSchema = await fetch(
      `${process.env.REACT_APP_SELECT_MODEL_ENDPOINT + type}`
    );
    const parameterSchema = await fetchedJsonSchema.json();
    const newFormData = { type, index, parameterSchema };
    setFormData(newFormData);
    setShowModal(true);
  };
  const removeModelFromTableFactory = (index) => () => {
    const modelsArray = [...modelsInTable];
    const configArray = [...executionConfig];
    modelsArray.splice(index, 1);
    configArray.splice(index, 1);
    setModelsInTable(modelsArray);
    setExecutionConfig(configArray);
  };
  const navigate = useNavigate();
  const goToResults = () => {
    navigate("/results", { state: { run: true } });
  };
  return (
    <CustomContainer>
      <AddModels
        compatibleModels={compatibleModels}
        modelsInTable={modelsInTable}
        setModelsInTable={setModelsInTable}
        renderFormFactory={renderFormFactory}
        removeModelFromTableFactory={removeModelFromTableFactory}
        setConfigByTableIndex={setConfigByTableIndex}
      />
      <ParameterForm
        type={formData.type}
        parameterSchema={formData.parameterSchema}
        handleFormSubmit={setConfigFactory(formData.index)}
        defaultValues={executionConfig[formData.index]}
        showModal={showModal}
        handleModalClose={handleModalClose}
        key={formData.index}
      />
      {Object.keys(executionConfig).length > 0 && (
        <StyledButton variant="dark" onClick={goToResults}>
          Run Experiment
        </StyledButton>
      )}
    </CustomContainer>
  );
}

export default Experiment;
