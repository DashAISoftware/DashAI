import React from "react";

import CustomLayout from "../../components/custom/CustomLayout";
import { rows } from "../../example_data/experiments";
import ExperimentsCreateStepperDialog from "./components/ExperimentsCreateStepperDialog";
import ExperimentsTable from "./components/ExperimentsTable";

function Experiments() {
  const [showNewExperimentModal, setShowNewExperimentModal] =
    React.useState(false);
  const [updateTableFlag, setUpdateTableFlag] = React.useState(true);
  return (
    <CustomLayout>
      {/* New experiment Modal */}
      <ExperimentsCreateStepperDialog
        open={showNewExperimentModal}
        handleCloseDialog={() => setShowNewExperimentModal(false)}
        updateExperiments={() => setUpdateTableFlag(true)}
      />

      {/* Experiment table */}
      <ExperimentsTable
        initialRows={rows}
        handleOpenNewExperimentModal={() => setShowNewExperimentModal(true)}
        updateTableFlag={updateTableFlag}
        setUpdateTableFlag={setUpdateTableFlag}
      />
    </CustomLayout>
  );
}

Experiments.propTypes = {};

export default Experiments;
