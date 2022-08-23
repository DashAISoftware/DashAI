import React, { useEffect, useState } from 'react';
import {
  Container,
  Row,
  Col,
  Form,
} from 'react-bootstrap';
import styled from 'styled-components';
// import ModelsTable from '../components/ModelsTable';
import PropTypes from 'prop-types';
import Upload from '../components/Upload';

const StyledContainer = styled(Container)`
  margin: 20px;
`;

function SelectModels({ models }) {
  SelectModels.propTypes = {
    models: PropTypes.arrayOf(PropTypes.string).isRequired,
  };
  const [selectedModels, setSelectedModels] = useState({});
  const handleChange = (e) => {
    e.preventDefault();
    console.log(e);
    setSelectedModels({ [e.name]: true });
  };
  if (models.length !== 0) {
    return (
      <div>
        <h4>Task Type: Text Classification</h4>
        <p>Select the models to train.</p>
        <Form onChange={handleChange}>
          {models.map((model) => <Form.Check inline label={model} name={model} type="checkbox" key={`checkbox-${model}`} checked={selectedModels[model]} />)}
        </Form>
      </div>
    );
  }
  return (<div />);
}

function ExperimentConfiguration() {
  const [response, setResponse] = useState({ knn: { } });
  const [models, setModels] = useState([]);

  useEffect(() => {
    async function fetchData() {
      const fetched = await fetch('http://localhost:8000/experiment/results/0');
      const res = await fetched.json();
      setResponse(res);
      console.log(response);
    }
    fetchData();
  }, []);
  return (
    <StyledContainer>
      <Col md="6">
        <Row>
          <h2>Load Dataset</h2>
          <Upload setModels={setModels} />
        </Row>

        <SelectModels models={models} />
      </Col>
    </StyledContainer>
  );
}
export default ExperimentConfiguration;
