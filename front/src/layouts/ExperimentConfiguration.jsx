import React, { useState } from 'react';
import {
  Container,
  Row,
  Col,
  Form,
  Button,
} from 'react-bootstrap';
import Spinner from 'react-bootstrap/Spinner';
import styled from 'styled-components';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import ModelsTable from '../components/ModelsTable';
import Upload from '../components/Upload';
import ParameterForm from '../components/ParameterForm';
import {
  StyledButton,
  Title,
  P,
  SubTitle,
  StyledTextInput,
  StyledSelect,
  StyledFloatingLabel,
} from '../styles/globalComponents';

const StyledContainer = styled(Container)`
  margin: 20px;
`;

async function getFullDefaultValues(parameterJsonSchema, choice = 'none') {
  const { properties } = parameterJsonSchema;
  if (typeof properties !== 'undefined') {
    const parameters = Object.keys(properties);
    const defaultValues = choice === 'none' ? {} : { choice };
    parameters.forEach(async (param) => {
      const val = properties[param].oneOf[0].default;
      if (val !== undefined) {
        defaultValues[param] = val;
      } else {
        const { parent } = properties[param].oneOf[0];
        const fetchedOptions = await fetch(`${process.env.REACT_APP_GET_CHILDREN_ENDPOINT + parent}`);
        const receivedOptions = await fetchedOptions.json();
        const [first] = receivedOptions;
        const fetchedParams = await fetch(`${process.env.REACT_APP_SELECT_MODEL_ENDPOINT + first}`);
        const parameterSchema = await fetchedParams.json();
        defaultValues[param] = await getFullDefaultValues(parameterSchema, first);
      }
    });
    return (defaultValues);
  }
  return ({});
}

function AddModels({
  availableModels,
  renderFormFactory,
  taskName,
  setConfigByTableIndex,
}) {
  AddModels.propTypes = {
    availableModels: PropTypes.arrayOf(PropTypes.string).isRequired,
    renderFormFactory: PropTypes.func.isRequired,
    taskName: PropTypes.string.isRequired,
    setConfigByTableIndex: PropTypes.func.isRequired,
  };
  const [modelsInTable, setModelsInTable] = useState([]);
  const [addModelValues, setAddModelValues] = useState({ name: '', type: '' });
  const handleSubmit = async (e) => {
    e.preventDefault(e);
    if (addModelValues.type !== '' && addModelValues.type !== 'none') {
      const index = modelsInTable.length;
      setModelsInTable([...modelsInTable, addModelValues]);
      const fetchedJsonSchema = await fetch(`${process.env.REACT_APP_SELECT_MODEL_ENDPOINT + addModelValues.type}`);
      const parameterSchema = await fetchedJsonSchema.json();
      const defaultValues = await getFullDefaultValues(parameterSchema);
      setConfigByTableIndex(index, addModelValues.type, defaultValues);
    }
  };
  const handleChange = (e) => {
    setAddModelValues((state) => ({
      ...state,
      [e.target.name]: e.target.value,
    }));
  };
  if (availableModels.length !== 0) {
    return (
      <div>
        <br />
        <SubTitle>{`Task Type: ${taskName}`}</SubTitle>
        <br />
        <Title>Add Models</Title>
        <P>Add new models by selecting a type</P>
        <Form className="d-flex" style={{ display: 'grid', gridGap: '10px' }}>
          {/* <input */}
          {/*   name="name" */}
          {/*   value={addModelValues.name} */}
          {/*   onChange={handleChange} */}
          {/*   label="nickname (optional)" */}
          {/* /> */}
          <StyledFloatingLabel className="mb-3" label="nickname (optional)">
            <StyledTextInput
              type="text"
              name="name"
              value={addModelValues.name}
              placeholder="model 1"
              onChange={handleChange}
            />
          </StyledFloatingLabel>
          <StyledFloatingLabel className="mb-3" label="model type">
            {/* <select value={addModelValues.type} name="type" onChange={handleChange}> */}
            <StyledSelect
              value={addModelValues.type}
              name="type"
              onChange={handleChange}
              aria-label="Select a model type"
            >
              <option value="none">Select model</option>
              { availableModels.map((model) => <option value={model} key={model}>{model}</option>) }
              {/* </select> */}
            </StyledSelect>
          </StyledFloatingLabel>
          <StyledButton style={{ height: '60px', verticalAlign: 'middle' }} onClick={handleSubmit} variant="dark">Add</StyledButton>
        </Form>
        <br />
        <ModelsTable
          rows={modelsInTable}
          renderFormFactory={renderFormFactory}
        />
      </div>
    );
  }
  return (<div />);
}

function ExperimentConfiguration() {
  const [availableModels, setAvailableModels] = useState([]);
  const [formData, setFormData] = useState({ type: '', index: -1, parameterSchema: {} });
  const [executionConfig, setExecutionConfig] = useState({});
  const [taskName, setTaskName] = useState('');
  const [resultsState, setResultsState] = useState('none');
  const [showUpload, setShowUpload] = useState(true);
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
    }
  );
  const sendModelConfig = async () => {
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
  return (
    <StyledContainer>
      <Row>
        <Col>
          <Title>Load Dataset</Title>
          { showUpload
            ? (
              <Upload
                setModels={setAvailableModels}
                setTaskName={setTaskName}
                setShowUpload={setShowUpload}
              />
            )
            : (
              <div>
                <br />
                <StyledButton
                  type="button"
                  onClick={() => setShowUpload(true)}
                >
                  Upload a new dataset
                </StyledButton>
              </div>
            )}
          <AddModels
            availableModels={availableModels}
            renderFormFactory={renderFormFactory}
            taskName={taskName}
            setConfigByTableIndex={setConfigByTableIndex}
          />
          <div>
            {
            Object.keys(executionConfig).length > 0
              && <StyledButton variant="dark" onClick={sendModelConfig}>Run Experiment</StyledButton>
            }
            {
            resultsState === 'ready'
            && <Button as={Link} to="/results/0" variant="dark" style={{ float: 'right' }}>Show Results</Button>
            }
            {
            resultsState === 'waiting'
            && <Spinner style={{ verticalAlign: 'middle', float: 'right' }} animation="border" role="status" />
            }
          </div>
        </Col>

        <Col style={{ margin: '20px 0px' }}>
          <ParameterForm
            type={formData.type}
            index={formData.index}
            parameterSchema={formData.parameterSchema}
            setConfigByTableIndex={setConfigByTableIndex}
            defaultValues={executionConfig[formData.index]}
            key={formData.index}
          />
        </Col>
      </Row>
    </StyledContainer>
  );
}
export default ExperimentConfiguration;
