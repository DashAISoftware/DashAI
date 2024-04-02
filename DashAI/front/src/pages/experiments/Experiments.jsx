import React from "react";

import NewExperimentModal from "../../components/experiments/NewExperimentModal";
import ExperimentsTable from "../../components/experiments/ExperimentsTable";
import { rows } from "../../example_data/experiments";
import CustomLayout from "../../components/custom/CustomLayout";

function ExperimentsPage() {
  const [showNewExperimentModal, setShowNewExperimentModal] =
    React.useState(false);
  const [updateTableFlag, setUpdateTableFlag] = React.useState(false);
  return (
    <CustomLayout>
      {/* New experiment Modal */}
      <NewExperimentModal
        open={showNewExperimentModal}
        setOpen={setShowNewExperimentModal}
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

ExperimentsPage.propTypes = {};

export default ExperimentsPage;
