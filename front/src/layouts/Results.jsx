import React, { useEffect, useState } from 'react';
import {
  Container,
  Row,
  Col,
  Card,
  Button,
} from 'react-bootstrap';
import styled from 'styled-components';
import Form from 'react-bootstrap/Form';
import Spinner from 'react-bootstrap/Spinner';
import ListGroup from 'react-bootstrap/ListGroup';
import { Link } from 'react-router-dom';
import {
  StyledButton,
  StyledFloatingLabel,
  StyledTextInput,
  StyledCard,
  P,
} from '../styles/globalComponents';

const StyledSection = styled.span`
  font-weight: 700;
  font-size: 20px;
`;

const StyledNumber = styled.span`
  float: right;
  font-size: 20px;
`;

const StyledListGroupItem = styled(ListGroup.Item)`
  background-color: ${(props) => props.theme.rootBackground};
  color: ${(props) => props.theme.title};
  border-color: ${(props) => props.theme.simpleText};
`;

const ParameterValue = styled.span`
  color: ${(props) => props.theme.list.parameterValues};
`;

function jsonToList(value) {
  if (typeof value === 'object' && value !== null) {
    return (
      <ul>
        {
        Object.keys(value).map(
          (parameter) => (
            <li key={parameter}>
              <span style={{ fontWeight: 600, fontSize: '15px' }}>{`${parameter}: `}</span>
              { jsonToList(value[parameter]) }
            </li>
          ),
        )
        }
      </ul>
    );
  }
  return (
    <ParameterValue>{String(value)}</ParameterValue>
  );
}
function Results() {
  const [results, setResults] = useState({});
  const [modelPrediction, setModelPrediction] = useState('');
  const sessionId = 0;
  const getResults = async () => {
    const fetchedResults = await fetch(`${process.env.REACT_APP_EXPERIMENT_RESULTS_ENDPOINT + sessionId}`);
    const res = await fetchedResults.json();
    setResults(res);
  };
  useEffect(() => { getResults(); }, []);
  const handleSubmit = async (e) => {
    e.preventDefault();
    setModelPrediction('null');
    const data = Object.fromEntries(Array.from(new FormData(e.target)));
    const fetchedPrediction = await fetch(`${process.env.REACT_APP_PLAY_ENDPOINT + sessionId}/0/{input}?input_data=${data.modelInput}`);
    const prediction = await fetchedPrediction.json();
    setModelPrediction(prediction);
  };
  if (Object.keys(results).length > 0) {
    const model = Object.keys(results)[0];
    return (
      <Container style={{ margin: '20px' }}>
        <Row>
          <Col md="6">
            <StyledCard>
              <Card.Header>
                <Card.Title>
                  <span style={{ fontWeight: 700, verticalAlign: 'middle' }}>Model: </span>
                  <span style={{ verticalAlign: 'middle' }}>{model}</span>
                </Card.Title>
              </Card.Header>
              <div style={{ margin: '10px' }}>
                <ListGroup variant="flush">
                  <StyledListGroupItem>
                    <StyledSection>Train Results</StyledSection>
                    <StyledNumber>{`${results[model].train_results.toFixed(4) * 100}%`}</StyledNumber>
                  </StyledListGroupItem>

                  <StyledListGroupItem>
                    <StyledSection>Test Results</StyledSection>
                    <StyledNumber>{`${results[model].test_results.toFixed(4) * 100}%`}</StyledNumber>
                  </StyledListGroupItem>
                  <StyledListGroupItem>
                    <StyledSection>Parameters</StyledSection>
                    { jsonToList(results[model].parameters) }
                  </StyledListGroupItem>
                </ListGroup>
              </div>
            </StyledCard>
            <br />
            <Button as={Link} to="/" variant="dark">Return to setup</Button>
          </Col>

          <Col md="6">
            <StyledCard>
              <Card.Header>Play with the model</Card.Header>
              <Form style={{ margin: '10px' }} onSubmit={handleSubmit}>
                <P>Enter input for the model</P>
                <StyledFloatingLabel label="Input" className="mb-3">
                  <StyledTextInput className="form-control" as="textarea" name="modelInput" style={{ height: '6rem' }} />
                </StyledFloatingLabel>
                <StyledButton type="submit" variant="dark">Send</StyledButton>
              </Form>
              <StyledCard className="text-center" style={{ margin: '1rem' }}>
                <Card.Title style={{ margin: '20px' }}>
                  {
                  modelPrediction === 'null'
                    ? <Spinner animation="border" role="status" />
                    : <Card.Title style={{ margin: '20px' }}>{modelPrediction}</Card.Title>
                  }
                </Card.Title>
              </StyledCard>
            </StyledCard>
            <br />
          </Col>
        </Row>
      </Container>
    );
  }
  return (
    <h1 style={{ margin: '20px' }}>No results :(</h1>
  );
}

export default Results;
