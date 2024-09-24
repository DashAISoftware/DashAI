import React, { useCallback, useState } from "react";
import PropTypes from "prop-types";

import { Button } from "@mui/material";

import { ExplorerProvider } from "./context";
import { ExplorerModal } from "./";

/**
 * ExplorerLauncher functional component.
 *
 * This component is used to launch the ExplorerModal component through a button.
 * It also provides the ExplorerProvider to use ExplorerContext within.
 *
 * @param {Object} props - The props of the component.
 * @param {Function} props.onClose - Function to launch when the modal is closed.
 * @param {number} props.datasetId - The ID of the dataset to explore.
 */
function ExplorerLauncher({ onClose = () => {}, datasetId }) {
  const [open, setOpen] = useState(false);

  const handleCloseContent = useCallback(() => {
    setOpen(false);
    onClose();
  }, [onClose]);

  return (
    <React.Fragment>
      <Button variant="contained" color="primary" onClick={() => setOpen(true)}>
        Explore
      </Button>

      {/* only create context and modal on open */}
      {open && (
        <ExplorerProvider datasetId={datasetId}>
          <ExplorerModal open={open} onClose={handleCloseContent} />
        </ExplorerProvider>
      )}
    </React.Fragment>
  );
}

ExplorerLauncher.propTypes = {
  onClose: PropTypes.func,
  datasetId: PropTypes.number.isRequired,
};

export default ExplorerLauncher;
