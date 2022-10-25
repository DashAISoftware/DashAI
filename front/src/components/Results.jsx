import React, { useEffect, useState } from 'react';
import {
  Card,
} from 'react-bootstrap';
import ListGroup from 'react-bootstrap/ListGroup';
import PropTypes from 'prop-types';
import {
  StyledButton,
  StyledCard,
} from '../styles/globalComponents';
import * as S from '../styles/components/ResultsStyles';

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
    <S.SpanParameterValue>{String(value)}</S.SpanParameterValue>
  );
}
function Results({ scrollToNextStep }) {
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
              <S.ListGroupItem>
                <S.SpanSection>Train Results</S.SpanSection>
                <S.SpanNumber>{`${results[model].train_results.toFixed(4) * 100}%`}</S.SpanNumber>
              </S.ListGroupItem>

              <S.ListGroupItem>
                <S.SpanSection>Test Results</S.SpanSection>
                <S.SpanNumber>{`${results[model].test_results.toFixed(4) * 100}%`}</S.SpanNumber>
              </S.ListGroupItem>
              <S.ListGroupItem>
                <S.SpanSection>Parameters</S.SpanSection>
                { jsonToList(results[model].parameters) }
              </S.ListGroupItem>
            </ListGroup>
          </div>
        </StyledCard>
        <br />
        <StyledButton type="button" onClick={scrollToNextStep}>Next</StyledButton>
      </div>
    );
  }
  return (
    <div />
  );
}

Results.propTypes = {
  scrollToNextStep: PropTypes.func.isRequired,
};
export default Results;
