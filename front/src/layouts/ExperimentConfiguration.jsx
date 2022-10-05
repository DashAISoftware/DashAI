import React, { useState } from 'react';
// import React, { useState, useEffect } from 'react';
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
        const fetchedOptions = await fetch(
          `http://localhost:8000/getChildren/${parent}`,
        );
        const receivedOptions = await fetchedOptions.json();
        const [first] = receivedOptions;
        const fetchedParams = await fetch(`http://localhost:8000/selectModel/${first}`);
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
    const index = modelsInTable.length;
    setModelsInTable([...modelsInTable, addModelValues]);
    const fetchedJsonSchema = await fetch(`http://localhost:8000/selectModel/${addModelValues.type}`);
    const parameterSchema = await fetchedJsonSchema.json();
    const defaultValues = await getFullDefaultValues(parameterSchema);
    setConfigByTableIndex(index, addModelValues.type, defaultValues);
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
        <h4>{`Task Type: ${taskName}`}</h4>
        <p>Add models to train.</p>
        <Form className="d-flex" style={{ display: 'grid', gridGap: '10px' }}>
          <input type="text" placeholder="nickname (optional)" name="name" value={addModelValues.name} onChange={handleChange} />
          <select value={addModelValues.type} name="type" onChange={handleChange}>
            <option>Select model</option>
            { availableModels.map((model) => <option value={model} key={model}>{model}</option>) }
          </select>
          <Button onClick={handleSubmit} variant="dark">Add</Button>
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
  const setConfigByTableIndex = (index, modelName, newValues) => setExecutionConfig(
    {
      ...executionConfig,
      [index]: { model_name: modelName, payload: newValues },
    },
  );
  const renderFormFactory = (type, index) => (
    async () => {
      const fetchedJsonSchema = await fetch(`http://localhost:8000/selectModel/${type}`);
      const parameterSchema = await fetchedJsonSchema.json();
      setFormData({ type, index, parameterSchema });
    }
  );
  const sendModelConfig = async () => {
    setResultsState('waiting');
    const fetchedResults = await fetch(
      `http://localhost:8000/selectedParameters/${executionConfig[0].model_name}`,
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
      `http://localhost:8000/experiment/run/${sessionId}`,
      { method: 'POST' },
    );
    setResultsState('ready');
  };
  return (
    <StyledContainer>
      <Row>
        <Col md="6">
          <h2>Load Dataset</h2>
          <Upload setModels={setAvailableModels} setTaskName={setTaskName} />
          <AddModels
            availableModels={availableModels}
            renderFormFactory={renderFormFactory}
            taskName={taskName}
            setConfigByTableIndex={setConfigByTableIndex}
          />
          <div>
            {
            Object.keys(executionConfig).length > 0
              && <Button variant="dark" onClick={sendModelConfig}>Run Experiment</Button>
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

        <Col md="6" key={formData.index}>
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
