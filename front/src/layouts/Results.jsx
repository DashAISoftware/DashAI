import React, { useEffect, useState } from 'react';
import {
  Container,
  Row,
  Col,
  Card,
  Button,
} from 'react-bootstrap';
import Form from 'react-bootstrap/Form';

function Results() {
  const [results, setResults] = useState({});
  const sessionId = 0;
  const getResults = async () => {
    const fetchedResults = await fetch(`http://localhost:8000/experiment/results/${sessionId}`);
    const res = await fetchedResults.json();
    setResults(res);
  };
  useEffect(() => { getResults(); }, []);
  if (Object.keys(results).length > 0) {
    const model = Object.keys(results)[0];
    console.log(model);
    console.log(results);
    return (
      <Container style={{ margin: '20px' }}>
        <Row>
          <Col md="6">
            <Card>
              <Card.Header>
                <Card.Title>{`Model: ${model}`}</Card.Title>
              </Card.Header>
              <div style={{ margin: '10px' }}>
                <p>{`Train Results: ${results[model].train_results}`}</p>
                <p>{`Test Results: ${results[model].test_results}`}</p>
                <pre>{`Parameters: ${JSON.stringify(results[model].parameters, null, 2)}`}</pre>
              </div>
            </Card>
          </Col>

          <Col md="6">
            <Card>
              <Card.Header>Play with the model</Card.Header>
              <Form style={{ margin: '10px' }}>
                <Form.Group>
                  <Form.Label>Enter input to try the model</Form.Label>
                  <Form.Control as="textarea" rows={3} />
                </Form.Group>
                <br />
                <Button type="button" variant="dark">Send</Button>
              </Form>
            </Card>
            <br />
            <Card className="text-center">
              <Card.Title style={{ margin: '20px' }}>Positive</Card.Title>
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
