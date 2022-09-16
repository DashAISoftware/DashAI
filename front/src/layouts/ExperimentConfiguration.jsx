import React, { useState, useEffect } from 'react';
import {
  Container,
  Row,
  Col,
  // Dropdown,
  // DropdownButton,
  Form,
  Button,
} from 'react-bootstrap';
import styled from 'styled-components';
import PropTypes from 'prop-types';
import ModelsTable from '../components/ModelsTable';
import Upload from '../components/Upload';
import ParameterForm from '../components/ParameterForm';

const StyledContainer = styled(Container)`
  margin: 20px;
`;

function AddModels({
  availableModels,
  modelsInTable,
  setModelsInTable,
  setParameterSchema,
  setShowForm,
}) {
  AddModels.propTypes = {
    availableModels: PropTypes.arrayOf(PropTypes.string).isRequired,
    modelsInTable: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string)).isRequired,
    setModelsInTable: PropTypes.func.isRequired,
    setParameterSchema: PropTypes.func.isRequired,
    setShowForm: PropTypes.func.isRequired,
  };
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
          <input type="text" name="name" value={addModelValues.name} onChange={handleChange} />
          <select value={addModelValues.type} name="type" onChange={handleChange}>
            <option>Select model</option>
            { availableModels.map((model) => <option value={model} key={model}>{model}</option>) }
          </select>
          <Button onClick={handleSubmit}>Add</Button>
        </Form>
        <br />
        <ModelsTable
          rows={modelsInTable}
          setParameterSchema={setParameterSchema}
          setShowForm={setShowForm}
        />
      </div>
    );
  }
  return (<div />);
}

function ExperimentConfiguration() {
  const [availableModels, setAvailableModels] = useState([]);
  const [modelsInTable, setModelsInTable] = useState([]);
  const [parameterSchema, setParameterSchema] = useState(null);
  const [showForm, setShowForm] = useState(true);

  useEffect(() => setShowForm(true), [showForm]);
  return (
    <StyledContainer>
      <Row>
        <Col md="6">
          <h2>Load Dataset</h2>
          <Upload setModels={setAvailableModels} />
          <AddModels
            availableModels={availableModels}
            modelsInTable={modelsInTable}
            setModelsInTable={setModelsInTable}
            setParameterSchema={setParameterSchema}
            setShowForm={setShowForm}
          />
        </Col>

        <Col md="6">
          { parameterSchema !== null && showForm
          && <ParameterForm model="" parameterSchema={parameterSchema} />}
        </Col>
      </Row>
    </StyledContainer>
  );
}
export default ExperimentConfiguration;
