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

const StyledSection = styled.span`
  font-weight: 700;
  font-size: 20px;
`;

const StyledNumber = styled.span`
  float: right;
  font-size: 20px;
`;

const StyledCard = styled(Card)`
  color: ${(props) => props.theme.title};
  background-color: ${(props) => props.theme.rootBackground};
`;

const StyledListGroupItem = styled(ListGroup.Item)`
  background-color: ${(props) => props.theme.rootBackground};
  color: ${(props) => props.theme.title};
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
    <span style={{ color: '#808080' }}>{String(value)}</span>
  );
}
function Results() {
  const [results, setResults] = useState({});
  const [modelPrediction, setModelPrediction] = useState('');
  const sessionId = 0;
  const getResults = async () => {
    const fetchedResults = await fetch(`http://localhost:8000/experiment/results/${sessionId}`);
    const res = await fetchedResults.json();
    setResults(res);
  };
  useEffect(() => { getResults(); }, []);
  const handleSubmit = async (e) => {
    e.preventDefault();
    setModelPrediction('null');
    const data = Object.fromEntries(Array.from(new FormData(e.target)));
    const fetchedPrediction = await fetch(`http://localhost:8000/play/${sessionId}/0/{input}?input_data=${data.modelInput}`);
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
            <Card>
              <Card.Header>Play with the model</Card.Header>
              <Form style={{ margin: '10px' }} onSubmit={handleSubmit}>
                <Form.Group>
                  <Form.Label>Enter input for the model</Form.Label>
                  <Form.Control as="textarea" name="modelInput" rows={3} />
                </Form.Group>
                <br />
                <Button type="submit" variant="dark">Send</Button>
              </Form>
            </Card>
            <br />
            <Card className="text-center">
              <Card.Title style={{ margin: '20px' }}>
                {
                modelPrediction === 'null'
                  ? <Spinner animation="border" role="status" />
                  : <Card.Title style={{ margin: '20px' }}>{modelPrediction}</Card.Title>
                }
              </Card.Title>
            </Card>
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
