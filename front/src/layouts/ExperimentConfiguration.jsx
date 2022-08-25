import React, { useEffect, useState } from 'react';
import {
  Container,
  Row,
  Col,
  Form,
  Dropdown,
  DropdownButton,
} from 'react-bootstrap';
import styled from 'styled-components';
// import ModelsTable from '../components/ModelsTable';
import PropTypes from 'prop-types';
import Upload from '../components/Upload';
import ParameterForm from '../components/ParameterForm';

const StyledContainer = styled(Container)`
  margin: 20px;
`;

function SelectModels({ availableModels, checkedOptions, setCheckedOptions }) {
  SelectModels.propTypes = {
    availableModels: PropTypes.arrayOf(PropTypes.string).isRequired,
    checkedOptions: PropTypes.arrayOf(PropTypes.string).isRequired,
    setCheckedOptions: PropTypes.func.isRequired,
  };
  const handleChange = ({ target }) => {
    if (target.checked) {
      setCheckedOptions([...checkedOptions, target.name]);
    } else {
      setCheckedOptions(checkedOptions.filter((x) => x !== target.name));
    }
  };
  if (availableModels.length !== 0) {
    return (
      <div>
        <h4>Task Type: Text Classification</h4>
        <p>Select the models to train.</p>
        <Form>
          {availableModels.map((model) => <Form.Check inline onChange={handleChange} label={model} name={model} type="checkbox" key={`checkbox-${model}`} />)}
        </Form>
      </div>
    );
  }
  return (<div />);
}

function ExperimentConfiguration() {
  const [response, setResponse] = useState({ knn: { } });
  const [availableModels, setAvailableModels] = useState([]);
  const [selectedModels, setSelectedModels] = useState([]);
  const [configOption, setConfigOption] = useState('Select model');
  const [parameterSchema, setParameterSchema] = useState({});
  const handleSelect = async (eventkey, event) => {
    const selectedOption = event.target.firstChild.data;
    setConfigOption(selectedOption);
    const fetchedOption = await fetch(`http://localhost:8000/selectModel/${selectedOption}`);
    const formJson = await fetchedOption.json();
    setParameterSchema(formJson);
  };
  useEffect(() => {
    async function fetchData() {
      const fetched = await fetch('http://localhost:8000/experiment/results/0');
      const res = await fetched.json();
      setResponse(res);
    }
    fetchData();
  }, []);
  return (
    <StyledContainer>
      <Row>
        <Col md="6">
          <h2>Load Dataset</h2>
          <Upload setModels={setAvailableModels} />
          <SelectModels
            availableModels={availableModels}
            checkedOptions={selectedModels}
            setCheckedOptions={setSelectedModels}
          />
        </Col>

        <Col md="6">
          <DropdownButton title={configOption} variant="secondary" onSelect={handleSelect}>
            {selectedModels.map((model) => <Dropdown.Item key={model}>{model}</Dropdown.Item>)}
          </DropdownButton>
          <ParameterForm model={configOption} parameterSchema={parameterSchema} />
          <p>
            Model Accuracy:
            {response.knn.accuracy}
          </p>
        </Col>
      </Row>
    </StyledContainer>
  );
}
export default ExperimentConfiguration;
