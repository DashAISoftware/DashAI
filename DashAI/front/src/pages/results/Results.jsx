import React, { useState } from "react";
import PropTypes from "prop-types";
import { IconButton } from "@mui/material";
import VisibilityIcon from "@mui/icons-material/Visibility";
import ResultsDialogLayout from "./components/ResultsDialogLayout";
import TimestampWrapper from "../../components/shared/TimestampWrapper";
import { TIMESTAMP_KEYS } from "../../constants/timestamp";

function Results({ experiment }) {
  const [open, setOpen] = useState(false);
  const [showTable, setShowTable] = useState(true);

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleShowTable = () => {
    setShowTable(true);
  };

  const handleShowGraphs = () => {
    setShowTable(false);
  };

  return (
    <>
      <TimestampWrapper eventName={TIMESTAMP_KEYS.experiments.showResults}>
        <IconButton onClick={handleOpen}>
          <VisibilityIcon />
        </IconButton>
      </TimestampWrapper>

      <ResultsDialogLayout
        experiment={experiment}
        open={open}
        onClose={handleClose}
        showTable={showTable}
        handleShowTable={handleShowTable}
        handleShowGraphs={handleShowGraphs}
      />
    </>
  );
}

Results.propTypes = {
  experiment: PropTypes.shape({
    name: PropTypes.string,
    id: PropTypes.number,
  }).isRequired,
};

export default Results;
