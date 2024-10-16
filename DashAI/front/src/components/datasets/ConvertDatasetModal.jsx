import React, { useState } from "react";
import PropTypes from "prop-types";
import { GridActionsCellItem } from "@mui/x-data-grid";
import { Settings } from "@mui/icons-material";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  Grid,
  Button,
  DialogActions,
  Typography,
} from "@mui/material";
import DatasetSummaryTable from "./DatasetSummaryTable";
import ConverterSelector from "./ConverterSelector";
import ConverterTable from "./ConverterTable";
import { useSnackbar } from "notistack";
import { enqueueConverterJob as enqueueConverterJobRequest } from "../../api/job";
import { startJobQueue as startJobQueueRequest } from "../../api/job";
import { saveDatasetConverterList } from "../../api/converter";

function ConvertDatasetModal({ datasetId }) {
  const { enqueueSnackbar } = useSnackbar();
  const [open, setOpen] = useState(false);
  const [convertersToApply, setConvertersToApply] = useState([]);

  const handleCloseContent = () => {
    setOpen(false);
  };

  const enqueueConverterJob = async (converterListId) => {
    try {
      await enqueueConverterJobRequest(converterListId);
      enqueueSnackbar("Converter job successfully created.", {
        variant: "success",
      });
    } catch (error) {
      enqueueSnackbar("Error while trying to enqueue converter job.");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  const startJobQueue = async () => {
    try {
      await startJobQueueRequest();
    } catch (error) {
      enqueueSnackbar("Error while trying to start job queue");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  const handleSaveConfig = async () => {
    try {
      const response = await saveDatasetConverterList(
        datasetId,
        convertersToApply.reduce((acc, { name, params, scope, pipelineId }) => {
          acc[name] = {
            params: params,
            scope: scope,
            pipelineId: pipelineId,
          };
          return acc;
        }, {}),
      );
      const converterListId = response.id;
      await enqueueConverterJob(converterListId);
      enqueueSnackbar("Converter job successfully created.", {
        variant: "success",
      });
      await startJobQueue();
      enqueueSnackbar("Running converter jobs.", {
        variant: "success",
      });

      setConvertersToApply([]);
      setOpen(false);
    } catch (error) {
      enqueueSnackbar("Error while trying to modify the dataset");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  return (
    <React.Fragment>
      <GridActionsCellItem
        key="converter-component"
        icon={<Settings />}
        label="Apply converters"
        onClick={() => setOpen(true)}
        sx={{ color: "warning.main" }}
      />
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        fullWidth
        maxWidth={"md"}
      >
        <DialogTitle>Apply converters</DialogTitle>
        <DialogContent dividers>
          <Grid
            container
            direction="row"
            justifyContent="space-around"
            alignItems="stretch"
            rowGap={2}
            onClick={(event) => event.stopPropagation()}
          >
            {/* Dataset summary table */}
            <Grid item xs={12}>
              <Typography variant="subtitle1" component="h3" mb={1}>
                Dataset preview
              </Typography>
            </Grid>
            <DatasetSummaryTable datasetId={datasetId} />

            {/* Converter selector */}
            <Grid item xs={12}>
              <Typography variant="subtitle1" component="h3" mb={1}>
                Add converter
              </Typography>
            </Grid>
            <ConverterSelector setConvertersToApply={setConvertersToApply} />
            {/* Selected converters table */}
            <ConverterTable
              datasetId={datasetId}
              convertersToApply={convertersToApply}
              setConvertersToApply={setConvertersToApply}
            />
          </Grid>
        </DialogContent>
        {/* Actions - Close and Modify */}
        <DialogActions>
          <Button onClick={handleCloseContent}>Close</Button>
          <Button
            onClick={handleSaveConfig}
            autoFocus
            variant="contained"
            color="primary"
            disabled={convertersToApply.length === 0}
          >
            Modify
          </Button>
        </DialogActions>
      </Dialog>
    </React.Fragment>
  );
}

ConvertDatasetModal.propTypes = {
  datasetId: PropTypes.number.isRequired,
};

export default ConvertDatasetModal;
