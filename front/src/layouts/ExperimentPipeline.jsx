import React, { useState, useRef } from 'react';
import { Container } from 'react-bootstrap';
import styled from 'styled-components';
import Upload from '../components/Upload';
import ParameterForm from '../components/ParameterForm';
import {
  StyledButton,
  P,
  Loading,
} from '../styles/globalComponents';
import AddModels from '../components/AddModels';
import Results from '../components/Results';
import Play from '../components/Play';

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
  const [availableModels, setAvailableModels] = useState([]);
  const [formData, setFormData] = useState({ type: '', index: -1, parameterSchema: {} });
  const [executionConfig, setExecutionConfig] = useState({});
  const [resultsState, setResultsState] = useState('none');
  const [showStep, setShowStep] = useState(['', '', 'none', 'none']);
  const [show, setShow] = useState(false);
  const handleClose = () => setShow(false);
  const setConfigByTableIndex = (index, modelName, newValues) => setExecutionConfig(
    {
      ...executionConfig,
      [index]: { model_name: modelName, payload: newValues },
    },
  );
  const renderFormFactory = (type, index) => (
    async () => {
      const fetchedJsonSchema = await fetch(`${process.env.REACT_APP_SELECT_MODEL_ENDPOINT + type}`);
      const parameterSchema = await fetchedJsonSchema.json();
      setFormData({ type, index, parameterSchema });
      setShow(true);
    }
  );
  const resultsRef = useRef(null);
  const scrollToResults = () => {
    resultsRef.current?.scrollIntoView({ behavior: 'smooth' });
    setShowStep(['', '', '', '']);
  };
  const sendModelConfig = async () => {
    scrollToResults();
    setResultsState('waiting');
    const fetchedResults = await fetch(
      `${process.env.REACT_APP_SELECTED_PARAMETERS_ENDPOINT + executionConfig[0].model_name}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(executionConfig[0].payload),
      },
    );
    const sessionId = await fetchedResults.json();
    await fetch(
      `${process.env.REACT_APP_EXPERIMENT_RUN_ENDPOINT + sessionId}`,
      { method: 'POST' },
    );
    setResultsState('ready');
  };
  const loadDatasetRef = useRef(null);
  const addModelsRef = useRef(null);
  const scrollToAddModel = () => {
    addModelsRef.current?.scrollIntoView({ behavior: 'smooth' });
    setShowStep(['', '', '', 'none']);
  };
  const playRef = useRef(null);
  const scrollToPlay = () => {
    playRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  return (
    <Container>
      <Step style={{ height: '89.5vh' }} ref={loadDatasetRef} showStep={showStep[0]}>
        <Upload
          setModels={setAvailableModels}
          scrollToNextStep={scrollToAddModel}
        />
      </Step>
      <Step ref={addModelsRef} showStep={showStep[1]}>
        <AddModels
          availableModels={availableModels}
          renderFormFactory={renderFormFactory}
          setConfigByTableIndex={setConfigByTableIndex}
        />
        <ParameterForm
          type={formData.type}
          index={formData.index}
          parameterSchema={formData.parameterSchema}
          setConfigByTableIndex={setConfigByTableIndex}
          defaultValues={executionConfig[formData.index]}
          modalShow={show}
          handleClose={handleClose}
          key={formData.index}
        />
        {
          Object.keys(executionConfig).length > 0
            && <StyledButton variant="dark" onClick={sendModelConfig}>Run Experiment</StyledButton>
        }
      </Step>
      <Step ref={resultsRef} showStep={showStep[2]}>
        <div>
          {
          resultsState === 'ready'
          && <Results scrollToNextStep={scrollToPlay} />
          }
          {
          resultsState === 'waiting'
          && (
          <div>
            <P>Loading results...</P>
            <Loading alt="" src="images/loading.png" width="58" height="58" />
          </div>
          )
          }
        </div>
      </Step>
      <Step ref={playRef} showStep={showStep[3]}>
        <Play />
        <br />
        <StyledButton
          onClick={() => loadDatasetRef.current?.scrollIntoView({ behavior: 'smooth' })}
        >
          Back to Top
        </StyledButton>
      </Step>
    </Container>
  );
}
export default Experiment;
