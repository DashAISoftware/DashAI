import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import ResultsCard from "../components/ResultsCard";
import { P, Loading } from "../styles/globalComponents";
import {
  submitParameters as submitParametersRequest,
  runExperiment as runExperimentRequest,
} from "../api/oldEnpoints";

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
        const executionConfig = JSON.parse(
          localStorage.getItem("executionConfig")
        );
        await Promise.all(
          executionConfig.map(async (config) => {
            submitParametersRequest(
              config.model_name,
              JSON.stringify(config.payload)
            );
            sessionId = 0;
          })
        );
        await runExperimentRequest(sessionId);
        setResultsState(READY);
      }
    };
    runExperiment();
  }, []);
  //
  return (
    <React.Fragment>
      {resultsState === READY && <ResultsCard />}
      {resultsState === WAITING && (
        <div>
          <P>Loading results...</P>
          <Loading alt="" src="/images/loading.png" width="58" height="58" />
        </div>
      )}
    </React.Fragment>
  );
}

export default Results;
