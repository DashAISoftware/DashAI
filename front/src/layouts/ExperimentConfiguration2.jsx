import React, { useState } from 'react';
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
}) {
  AddModels.propTypes = {
    availableModels: PropTypes.arrayOf(PropTypes.string).isRequired,
    modelsInTable: PropTypes.arrayOf(PropTypes.objectOf(PropTypes.string)).isRequired,
    setModelsInTable: PropTypes.func.isRequired,
    setParameterSchema: PropTypes.func.isRequired,
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
  // const handleChange = ({ target }) => {
  //   if (target.checked) {
  //     setCheckedOptions([...checkedOptions, target.name]);
  //   } else {
  //     setCheckedOptions(checkedOptions.filter((x) => x !== target.name));
  //   }
  // };
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
        <ModelsTable rows={modelsInTable} setParameterSchema={setParameterSchema} />
      </div>
    );
  }
  return (<div />);
}

function ExperimentConfiguration() {
  const [availableModels, setAvailableModels] = useState([]);
  const [modelsInTable, setModelsInTable] = useState([]);
  // const [selectedModels, setSelectedModels] = useState([]);
  // const [configOption, setConfigOption] = useState('Select model');
  const [parameterSchema, setParameterSchema] = useState(null);
  // const handleSelect = async (eventkey, event) => {
  //   const selectedOption = event.target.firstChild.data;
  //   setConfigOption(selectedOption);
  //   const fetchedOption = await fetch(`http://localhost:8000/selectModel/${selectedOption}`);
  //   const formJson = await fetchedOption.json();
  //   setParameterSchema(formJson);
  // };
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
          />
        </Col>

        <Col md="6">
          { parameterSchema !== null
          && <ParameterForm model="" parameterSchema={parameterSchema} />}
        </Col>
      </Row>
    </StyledContainer>
  );
}
export default ExperimentConfiguration;
