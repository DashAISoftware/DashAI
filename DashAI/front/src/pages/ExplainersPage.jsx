import React from "react";
import CustomLayout from "../components/custom/CustomLayout";
import TrainedModelsTable from "../components/explainers/TrainedModelsTable";
/**
 * This component renders a table that shows the runs of the experiments and a list to select the experiment to visualize
 */
function ExplainersPage() {
  // gets the id of the selected experiment in the url

  return (
    <CustomLayout>
      <TrainedModelsTable />
    </CustomLayout>
  );
}

export default ExplainersPage;
