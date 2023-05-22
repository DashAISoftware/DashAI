import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { GridActionsCellItem } from "@mui/x-data-grid";
import EditIcon from "@mui/icons-material/Edit";
import {
  Button,
  // ButtonGroup,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  TextField,
  Typography,
} from "@mui/material";
import ItemSelector from "./datasets/ItemSelector";
import { updateDataset as updateDatasetRequest } from "../api/datasets";
import { getTasks as getTasksRequest } from "../api/task";
import { useSnackbar } from "notistack";

function EditDatasetModal({ datasetId, name, taskName, updateDatasets }) {
  const { enqueueSnackbar } = useSnackbar();
  const [open, setOpen] = useState(false);
  const [datasetName, setDatasetName] = useState(name);
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState({});
  const [loading, setLoading] = useState(true);

  const editDataset = async () => {
    try {
      await updateDatasetRequest(datasetId, datasetName, selectedTask.class);
    } catch (error) {
      enqueueSnackbar("Error while trying to update the dataset", {
        variant: "error",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unkown Error", error.message);
      }
    } finally {
      enqueueSnackbar("Dataset updated successfully", {
        variant: "success",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
    }
  };

  const getTasks = async () => {
    setLoading(true);
    try {
      const tasks = await getTasksRequest();
      setTasks(tasks);
      const previouslySelectedTask = tasks.find(
        (task) => task.class === taskName,
      );
      setSelectedTask(previouslySelectedTask);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain available tasks", {
        variant: "error",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unkown Error", error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = () => {
    editDataset();
    setTimeout(() => updateDatasets());
    setOpen(false);
  };

  // fetch available tasks
  useEffect(() => {
    getTasks();
  }, []);
  return (
    <React.Fragment>
      <GridActionsCellItem
        key="edit-button"
        icon={<EditIcon />}
        label="Edit"
        onClick={() => setOpen(true)}
        sx={{ color: "#f1ae61" }}
      />
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        fullWidth
        maxWidth={"md"}
      >
        <DialogTitle>Edit dataset</DialogTitle>
        <DialogContent>
          <Grid
            container
            direction="row"
            justifyContent="space-around"
            alignItems="stretch"
            spacing={2}
          >
            {/* New name field */}
            <Grid item xs={12}>
              <Typography variant="subtitle1" component="h3" sx={{ mb: 3 }}>
                Enter a new name and select a new task for your dataset
              </Typography>

              <TextField
                id="dataset-name-input"
                label="Dataset Name"
                value={datasetName}
                fullWidth
                onChange={(event) => setDatasetName(event.target.value)}
                sx={{ mb: 2 }}
              />
            </Grid>

            {/* Select a new task */}
            <Grid item xs={12}>
              {!loading && (
                <ItemSelector
                  itemsList={tasks}
                  selectedItem={selectedTask}
                  setSelectedItem={setSelectedTask}
                />
              )}
            </Grid>
          </Grid>
        </DialogContent>

        {/* Actions - Save */}
        <DialogActions>
          <Button
            onClick={handleSaveConfig}
            autoFocus
            variant="contained"
            color="primary"
            disabled={false}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </React.Fragment>
  );
}

EditDatasetModal.propTypes = {
  datasetId: PropTypes.number.isRequired,
  name: PropTypes.string.isRequired,
  taskName: PropTypes.string.isRequired,
  updateDatasets: PropTypes.func.isRequired,
};

export default EditDatasetModal;
