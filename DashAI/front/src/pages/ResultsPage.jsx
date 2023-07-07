import React from "react";
import { useParams } from "react-router-dom";
import ExperimentsDrawer from "../components/results/ExperimentsDrawer";
import RunsTable from "../components/results/RunsTable";
/**
 * This component renders a table that shows the runs of the experiments and a drawer to select the experiment to visualize
 */
function ResultsPage() {
  // gets the id of the selected experiment in the url
  const { id } = useParams();

  return (
    <React.Fragment>
      <RunsTable experimentId={id} />
      <ExperimentsDrawer />
    </React.Fragment>
  );
}

export default ResultsPage;