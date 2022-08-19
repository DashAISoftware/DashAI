import React, { useEffect, useState } from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import styled from 'styled-components';
import ModelsTable from '../components/ModelsTable';
import Upload from '../components/Upload';

const StyledContainer = styled(Container)`
  margin: 20px;
`;

function ExperimentConfiguration() {
  const [response, setResponse] = useState([]);

  useEffect(() => {
    async function fetchData() {
      const fetched = await fetch('http://localhost:8000/');
      const res = await fetched.json();
      setResponse(res);
    }
    fetchData();
  }, []);
  return (
    <StyledContainer>
      <Col md="6">
        <Row>
          <h2>Load Dataset</h2>
          <Upload />
        </Row>

        <Row>
          <h4>Task Type: Text Classification</h4>
        </Row>

        <Row>
          <p>Select the models to train.</p>
          <ModelsTable />
          <p>{response.message}</p>
        </Row>
      </Col>
    </StyledContainer>
  );
}
export default ExperimentConfiguration;
