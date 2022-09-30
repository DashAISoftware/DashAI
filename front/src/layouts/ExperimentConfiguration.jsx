import React, { useState } from 'react';
// import React, { useState, useEffect } from 'react';
import {
  Container,
  Row,
  Col,
  Form,
  Button,
} from 'react-bootstrap';
import styled from 'styled-components';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import ModelsTable from '../components/ModelsTable';
import Upload from '../components/Upload';
import ParameterForm from '../components/ParameterForm';

const StyledContainer = styled(Container)`
  margin: 20px;
`;

function AddModels({
  availableModels,
  renderFormFactory,
  taskName,
}) {
  AddModels.propTypes = {
    availableModels: PropTypes.arrayOf(PropTypes.string).isRequired,
    renderFormFactory: PropTypes.func.isRequired,
    taskName: PropTypes.string.isRequired,
  };
  const [modelsInTable, setModelsInTable] = useState([]);
  const [addModelValues, setAddModelValues] = useState({ name: '', type: '' });
  const handleSubmit = (e) => {
    e.preventDefault(e);
    setModelsInTable([...modelsInTable, addModelValues]);
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
  const [showResultsButton, setShowResultsButton] = useState(false);
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
    console.log(executionConfig[0]);
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
    setShowResultsButton(true);
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
          />
          <div>
            {
            Object.keys(executionConfig).length > 0
              && <Button variant="dark" onClick={sendModelConfig}>Run Experiment</Button>
            }
            {
            showResultsButton
            && <Button as={Link} to="/results/0" variant="dark" style={{ float: 'right' }}>Show Results</Button>
            }
          </div>
        </Col>

        <Col md="6">
          <ParameterForm
            type={formData.type}
            index={formData.index}
            parameterSchema={formData.parameterSchema}
            setConfigByTableIndex={setConfigByTableIndex}
            key={formData.index}
          />
        </Col>
      </Row>
    </StyledContainer>
  );
}
export default ExperimentConfiguration;
