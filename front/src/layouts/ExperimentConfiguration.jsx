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
import uuid from 'react-uuid';
import ModelsTable from '../components/ModelsTable';
import Upload from '../components/Upload';
import ParameterForm from '../components/ParameterForm';

const StyledContainer = styled(Container)`
  margin: 20px;
`;

function AddModels({
  availableModels,
  renderFormFactory,
}) {
  AddModels.propTypes = {
    availableModels: PropTypes.arrayOf(PropTypes.string).isRequired,
    renderFormFactory: PropTypes.func.isRequired,
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
        <h4>Task Type: Text Classification</h4>
        <p>Add models to train.</p>
        <Form className="d-flex" style={{ display: 'grid', gridGap: '10px' }}>
          <input type="text" placeholder="nickname (optional)" name="name" value={addModelValues.name} onChange={handleChange} />
          <select value={addModelValues.type} name="type" onChange={handleChange}>
            <option>Select model</option>
            { availableModels.map((model) => <option value={model} key={model}>{model}</option>) }
          </select>
          <Button onClick={handleSubmit}>Add</Button>
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
  const setConfigByTableIndex = (index, newValues) => setExecutionConfig(
    {
      ...executionConfig,
      [index]: newValues,
    },
  );
  const renderFormFactory = (type, index) => (
    async () => {
      const fetchedJsonSchema = await fetch(`http://localhost:8000/selectModel/${type}`);
      const parameterSchema = await fetchedJsonSchema.json();
      setFormData({ type, index, parameterSchema });
    }
  );
  return (
    <StyledContainer>
      <Row>
        <Col md="6">
          <h2>Load Dataset</h2>
          <Upload setModels={setAvailableModels} />
          <AddModels
            availableModels={availableModels}
            renderFormFactory={renderFormFactory}
          />
          { Object.keys(executionConfig).length > 0
          && <Button onClick={() => console.log(executionConfig)}>Run Experiment</Button> }
        </Col>

        <Col md="6">
          <ParameterForm
            type={formData.type}
            index={formData.index}
            parameterSchema={formData.parameterSchema}
            setConfigByTableIndex={setConfigByTableIndex}
            key={uuid()}
          />
        </Col>
      </Row>
    </StyledContainer>
  );
}
export default ExperimentConfiguration;
