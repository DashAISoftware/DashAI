import React from "react";
// import PropTypes from "prop-types";

import NewExperimentModal from "../components/experiments/NewExperimentModal";
import ExperimentsTable from "../components/experiments/ExperimentsTable";

function ExperimentsPage() {
  const [showNewExperimentModal, setShowNewExperimentModal] =
    React.useState(false);

  return (
    <React.Fragment>
      {/* New experiment Modal */}
      <NewExperimentModal
        open={showNewExperimentModal}
        setOpen={setShowNewExperimentModal}
      />

      {/* Experiment table */}
      <ExperimentsTable
        initialRows={[]}
        handleOpenNewExperimentModal={() => setShowNewExperimentModal(true)}
      />
    </React.Fragment>
  );
}

ExperimentsPage.propTypes = {};

export default ExperimentsPage;
