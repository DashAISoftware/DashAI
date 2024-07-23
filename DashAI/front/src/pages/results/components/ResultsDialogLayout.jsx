import React from "react";
import PropTypes from "prop-types";
import { Dialog, DialogTitle, Divider, Grid } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import useMediaQuery from "@mui/material/useMediaQuery";
import CustomLayout from "../../../components/custom/CustomLayout";
import ResultsDialogViews from "./ResultsDialogViews";
import ResultsTable from "./ResultsTable";
import ResultsGraphs from "./ResultsGraphs";
import { TIMESTAMP_KEYS } from "../../../constants/timestamp";
import { useTimestamp } from "../../../hooks/useTimestamp";

function ResultsDialogLayout({
  experiment,
  open,
  onClose,
  showTable,
  handleShowTable,
  handleShowGraphs,
}) {
  const theme = useTheme();
  const screenSm = useMediaQuery(theme.breakpoints.down("sm"));
  const { handleClick } = useTimestamp({
    eventName: TIMESTAMP_KEYS.experiments.leavingResults,
  });

  const handleOnClose = () => {
    handleClick();
    onClose();
  };

  return (
    <Dialog
      open={open}
      fullScreen={screenSm}
      fullWidth
      maxWidth={"lg"}
      onClose={handleOnClose}
      PaperProps={{
        sx: {
          minHeight: "90vh",
          overflow: "auto",
          maxHeight: "90vh",
        },
      }}
    >
      <DialogTitle>{`Experiment ${experiment.name} results`}</DialogTitle>
      <Divider />
      <ResultsDialogViews
        showTable={showTable}
        handleShowTable={handleShowTable}
        handleShowGraphs={handleShowGraphs}
      />
      <Divider />
      <Grid item xs={10}>
        <CustomLayout>
          {showTable ? (
            <ResultsTable experimentId={experiment.id.toString()} />
          ) : null}
          {!showTable ? (
            <ResultsGraphs experimentId={experiment.id.toString()} />
          ) : null}
        </CustomLayout>
      </Grid>
    </Dialog>
  );
}

ResultsDialogLayout.propTypes = {
  experiment: PropTypes.shape({
    name: PropTypes.string,
    id: PropTypes.number,
  }).isRequired,
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  showTable: PropTypes.bool.isRequired,
  handleShowTable: PropTypes.func.isRequired,
  handleShowGraphs: PropTypes.func.isRequired,
};

export default ResultsDialogLayout;
