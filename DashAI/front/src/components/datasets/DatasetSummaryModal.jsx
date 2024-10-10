import React, { useState } from "react";
import PropTypes from "prop-types";
import { GridActionsCellItem } from "@mui/x-data-grid";
import { Search } from "@mui/icons-material";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  Grid,
  Button,
  DialogActions,
} from "@mui/material";
import DatasetSummaryTable from "./DatasetSummaryTable";
import { ExplorationModuleLauncher } from "../explorations";

function DatasetSummaryModal({ datasetId }) {
  const [open, setOpen] = useState(false);

  const handleCloseContent = () => {
    setOpen(false);
  };
  return (
    <React.Fragment>
      <GridActionsCellItem
        key="dataset-summary-button"
        icon={<Search />}
        label="Dataset Summary"
        onClick={() => setOpen(true)}
        sx={{ color: "warning.main" }}
      />
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        fullWidth
        maxWidth={"md"}
      >
        <DialogTitle>Dataset Summary</DialogTitle>
        <DialogContent>
          <Grid
            container
            direction="row"
            justifyContent="space-around"
            alignItems="stretch"
            spacing={2}
            onClick={(event) => event.stopPropagation()}
          >
            {/* Dataset Summary Table */}
            <DatasetSummaryTable datasetId={datasetId} />
          </Grid>
        </DialogContent>
        {/* Actions - Close */}
        <DialogActions>
          <ExplorationModuleLauncher datasetId={datasetId} />
          <Button
            onClick={handleCloseContent}
            autoFocus
            variant="contained"
            color="primary"
            disabled={false}
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </React.Fragment>
  );
}

DatasetSummaryModal.propTypes = {
  datasetId: PropTypes.number.isRequired,
};

export default DatasetSummaryModal;
