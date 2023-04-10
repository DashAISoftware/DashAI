import React, { useState, useRef, useEffect } from "react";
import { Container } from "react-bootstrap";
import styled from "styled-components";
import Upload from "../components/Upload";
import ParameterForm from "../components/ParameterForm";
import { StyledButton, P, Loading } from "../styles/globalComponents";
import AddModels from "../components/AddModels";
import Results from "../components/Results";
import Play from "../components/Play";

const Step = styled.div`
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  justify-content: center;
  display: ${(props) => props.showStep};
`;

function Experiment() {
  // code for dataset state
  const EMPTY = 0;
  // App state
  // const [sessionId, setSessionId] = useState(0);
  const [taskName, setTaskName] = useState("");
  const [compatibleModels, setCompatibleModels] = useState([]);
  const [modelsInTable, setModelsInTable] = useState([]);
  const [executionConfig, setExecutionConfig] = useState([]);
  const [datasetState, setDatasetState] = useState(EMPTY);
  //
  const [formData, setFormData] = useState({
    type: "",
    index: -1,
    parameterSchema: {},
  });
  const [resultsState, setResultsState] = useState("none");
  const [showStep, setShowStep] = useState(["", "", "none", "none"]);
  const [showModal, setShowModal] = useState(false);
  const [loadDatasetError, setLoadDatasetError] = useState(false);
  // ref for auto scroll to steps
  const loadDatasetRef = useRef(null);
  const addModelsRef = useRef(null);
  const resultsRef = useRef(null);
  const playRef = useRef(null);
  //
  const scrollToAddModel = () => {
    addModelsRef.current?.scrollIntoView({ behavior: "smooth" });
    setShowStep(["", "", "", "none"]);
  };
  const scrollToResults = () => {
    resultsRef.current?.scrollIntoView({ behavior: "smooth" });
    setShowStep(["", "", "", ""]);
  };
  const scrollToPlay = () => {
    playRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  //
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
  const renderFormFactory = (type, index) => async () => {
    const fetchedJsonSchema = await fetch(
      `${process.env.REACT_APP_SELECT_MODEL_ENDPOINT + type}`
    );
    const parameterSchema = await fetchedJsonSchema.json();
    setFormData({ type, index, parameterSchema });
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

  const sendModelConfig = async () => {
    scrollToResults();
    setResultsState("waiting");
    // const sendModelParameters = async () => {
    //   let sessionId = 0;
    //   executionConfig.forEach(async (config) => {
    //     const fetchedResults = await fetch(
    //       `${process.env.REACT_APP_SELECTED_PARAMETERS_ENDPOINT + config.model_name}`,
    //       {
    //         method: 'POST',
    //         headers: {
    //           'Content-Type': 'application/json',
    //         },
    //         body: JSON.stringify(config.payload),
    //       },
    //     );
    //     sessionId = await fetchedResults.json();
    //   });
    //   return (sessionId);
    // };
    // const fetchedResults = await fetch(
    //   `${process.env.REACT_APP_SELECTED_PARAMETERS_ENDPOINT + executionConfig[0].model_name}`,
    //   {
    //     method: 'POST',
    //     headers: {
    //       'Content-Type': 'application/json',
    //     },
    //     body: JSON.stringify(executionConfig[0].payload),
    //   },
    // );
    // const sessionId = 0;// await fetchedResults.json();
    let sessionId = -1;
    await Promise.all(
      executionConfig.map(async (config) => {
        const fetchedResults = await fetch(
          `${
            process.env.REACT_APP_SELECTED_PARAMETERS_ENDPOINT +
            config.model_name
          }`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(config.payload),
          }
        );
        sessionId = await fetchedResults.json();
      })
    );
    await fetch(
      `${process.env.REACT_APP_EXPERIMENT_RUN_ENDPOINT + sessionId}`,
      { method: "POST" }
    );
    setResultsState("ready");
  };
  useEffect(() => window.scrollTo(0, 0), []);

  const resetAppState = () => {
    setTaskName("");
    setDatasetState(EMPTY);
    setCompatibleModels([]);
    setModelsInTable([]);
    setExecutionConfig([]);
    setShowStep(["", "", "none", "none"]);
    setLoadDatasetError(false);
  };
  return (
    <Container>
      <Step
        style={{ height: "89.5vh" }}
        ref={loadDatasetRef}
        showStep={showStep[0]}
      >
        <Upload
          setCompatibleModels={setCompatibleModels}
          datasetState={datasetState}
          setDatasetState={setDatasetState}
          taskName={taskName}
          setTaskName={setTaskName}
          resetAppState={resetAppState}
          scrollToNextStep={scrollToAddModel}
          error={loadDatasetError}
          setError={setLoadDatasetError}
        />
      </Step>
      <Step ref={addModelsRef} showStep={showStep[1]}>
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
          index={formData.index}
          parameterSchema={formData.parameterSchema}
          setConfigByTableIndex={setConfigByTableIndex}
          defaultValues={executionConfig[formData.index]}
          showModal={showModal}
          handleModalClose={handleModalClose}
          key={formData.index}
        />
        {Object.keys(executionConfig).length > 0 && (
          <StyledButton variant="dark" onClick={sendModelConfig}>
            Run Experiment
          </StyledButton>
        )}
      </Step>
      <Step ref={resultsRef} showStep={showStep[2]}>
        <div>
          {resultsState === "ready" && (
            <Results scrollToNextStep={scrollToPlay} />
          )}
          {resultsState === "waiting" && (
            <div>
              <P>Loading results...</P>
              <Loading
                alt=""
                src="/images/loading.png"
                width="58"
                height="58"
              />
            </div>
          )}
        </div>
      </Step>
      <Step ref={playRef} showStep={showStep[3]}>
        <Play />
        <br />
        <StyledButton onClick={() => window.scrollTo(0, 0)}>
          Back to Top
        </StyledButton>
      </Step>
    </Container>
  );
}
export default Experiment;
