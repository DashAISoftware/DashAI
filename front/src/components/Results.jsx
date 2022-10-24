import React, { useEffect, useState } from 'react';
import {
  // Container,
  // Row,
  // Col,
  Card,
  // Button,
} from 'react-bootstrap';
// import Form from 'react-bootstrap/Form';
// import Spinner from 'react-bootstrap/Spinner';
import ListGroup from 'react-bootstrap/ListGroup';
import PropTypes from 'prop-types';
// import { Link } from 'react-router-dom';
import {
  StyledButton,
  // StyledFloatingLabel,
  // StyledTextInput,
  StyledCard,
  // P,
} from '../styles/globalComponents';
import {
  StyledSection,
  StyledNumber,
  StyledListGroupItem,
  ParameterValue,
} from '../styles/layouts/ResultsStyles';

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
function Results({ scrollToNextStep }) {
  Results.propTypes = {
    scrollToNextStep: PropTypes.func.isRequired,
  };
  const [results, setResults] = useState({});
  const sessionId = 0;
  const getResults = async () => {
    const fetchedResults = await fetch(`${process.env.REACT_APP_EXPERIMENT_RESULTS_ENDPOINT + sessionId}`);
    const res = await fetchedResults.json();
    setResults(res);
  };
  useEffect(() => { getResults(); }, []);
  if (Object.keys(results).length > 0) {
    const model = Object.keys(results)[0];
    return (
      <div>
        <StyledCard style={{ width: '32rem', textAlign: 'left' }}>
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
        <StyledButton type="button" onClick={scrollToNextStep}>Next</StyledButton>
      </div>
    );
  }
  return (
    <h1 style={{ margin: '20px' }}>No results :(</h1>
  );
}

export default Results;
