import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import ResultsCard from '../components/ResultsCard';
import {
  CustomContainer,
  P,
  Loading,
} from '../styles/globalComponents';

function Results() {
  const { state } = useLocation();
  const run = state === null ? false : state.run;
  const [READY, WAITING] = [0, 1];
  const [resultsState, setResultsState] = useState(run ? WAITING : READY);
  //
  useEffect(() => {
    const runExperiment = async () => {
      let sessionId = -1;
      if (run) {
        const executionConfig = JSON.parse(localStorage.getItem('executionConfig'));
        await Promise.all(executionConfig.map(async (config) => {
          const fetchedResults = await fetch(
            `${process.env.REACT_APP_SELECTED_PARAMETERS_ENDPOINT + config.model_name}`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify(config.payload),
            },
          );
          sessionId = await fetchedResults.json();
        }));
        await fetch(
          `${process.env.REACT_APP_EXPERIMENT_RUN_ENDPOINT + sessionId}`,
          { method: 'POST' },
        );
        setResultsState(READY);
      }
    };
    runExperiment();
  }, []);
  //
  return (
    <CustomContainer>
      <div>
        {
        resultsState === READY
        && <ResultsCard />
        }
        {
        resultsState === WAITING
        && (
        <div>
          <P>Loading results...</P>
          <Loading alt="" src="/images/loading.png" width="58" height="58" />
        </div>
        )
        }
      </div>
    </CustomContainer>
  );
}

export default Results;
