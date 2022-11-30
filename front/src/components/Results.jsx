import React, { useEffect, useState } from 'react';
import {
  Table,
  Tab,
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
      <ul style={{ maxHeight: '20rem', overflowY: 'auto', paddingRight: '2rem' }}>
        {
        Object.keys(value).map(
          (parameter) => (
            <li key={parameter}>
              <span style={{ fontWeight: 600, fontSize: '15px' }}>
                {`${parameter}: `}
              </span>
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
  const [key, setKey] = useState(
    Object.keys(results).length > 1 ? 'main' : results[Object.keys(results)[0]],
  );
  const sessionId = 0;
  const getResults = async () => {
    const fetchedResults = await fetch(`${process.env.REACT_APP_EXPERIMENT_RESULTS_ENDPOINT + sessionId}`);
    const res = await fetchedResults.json();
    setResults(res);
  };
  useEffect(() => { getResults(); }, []);
  if (Object.keys(results).length > 0) {
    return (
      <div>
        <StyledCard style={{ width: '32rem', textAlign: 'left' }}>
          <S.Tabs
            activeKey={key}
            onSelect={(k) => setKey(k)}
            className="mb-3"
          >
            { Object.keys(results).length > 1
            && (
            <Tab eventKey="main" key="main" title="Summary" style={{ minHeight: '30rem' }}>
              <div style={{ margin: '10px', textAlign: 'left' }}>
                <Table bordered style={{ color: '#fff' }}>
                  <thead>
                    <tr>
                      <th>Model</th>
                      <th>Train</th>
                      <th>Test</th>
                    </tr>
                  </thead>

                  <tbody>
                    {Object.keys(results).map(
                      (modelName) => (
                        <tr key={modelName}>
                          <td>{modelName}</td>
                          <td>{`${(results[modelName].train_results * 100).toFixed(2)}%`}</td>
                          <td>{`${(results[modelName].test_results * 100).toFixed(2)}%`}</td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </Table>
              </div>
            </Tab>
            )}
            {
            Object.keys(results).map((modelName) => (
              <Tab eventKey={modelName} key={modelName} title={modelName} style={{ minHeight: '30rem' }}>
                <div style={{ margin: '10px', textAlign: 'left' }}>
                  <ListGroup variant="flush">
                    <S.ListGroupItem>
                      <S.SpanSection>Train Results</S.SpanSection>
                      <S.SpanNumber>{`${(results[modelName].train_results * 100).toFixed(2)}%`}</S.SpanNumber>
                    </S.ListGroupItem>

                    <S.ListGroupItem>
                      <S.SpanSection>Test Results</S.SpanSection>
                      <S.SpanNumber>{`${(results[modelName].test_results * 100).toFixed(2)}%`}</S.SpanNumber>
                    </S.ListGroupItem>
                    <S.ListGroupItem>
                      <S.SpanSection>Parameters</S.SpanSection>
                      { jsonToList(results[modelName].parameters) }
                    </S.ListGroupItem>
                  </ListGroup>
                </div>
              </Tab>
            ))
          }
          </S.Tabs>
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
