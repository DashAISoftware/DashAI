import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { GridActionsCellItem } from "@mui/x-data-grid";
import EditIcon from "@mui/icons-material/Edit";
import ParameterForm from "../ConfigurableObject/ParameterForm";
import {
  // Button,
  CircularProgress,
  Dialog,
  // DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  Paper,
} from "@mui/material";
import { getModelSchema as getModelSchemaRequest } from "../../api/oldEndpoints";
import { useSnackbar } from "notistack";

function EditModelDialog({ modelToConfigure }) {
  const { enqueueSnackbar } = useSnackbar();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [modelSchema, setModelSchema] = useState({});

  const getObjectSchema = async () => {
    setLoading(true);
    try {
      const schema = await getModelSchemaRequest(modelToConfigure);
      setModelSchema(schema);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain model schema", {
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

  // fetches the JSON object on mount
  useEffect(() => {
    getObjectSchema();
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
      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>{`${modelToConfigure} parameters`}</DialogTitle>
        <DialogContent>
          <Paper
            variant="outlined"
            sx={{ p: 4, maxHeight: "80vh", overflow: "auto" }}
          >
            <Grid container direction={"column"} alignItems={"center"}>
              {loading ? (
                <CircularProgress />
              ) : (
                <ParameterForm parameterSchema={modelSchema} submitButton />
              )}
            </Grid>
          </Paper>
        </DialogContent>
        {/* <DialogActions>
          <Button onClick={() => setOpen(false)} autoFocus>
            Cancel
          </Button>
          <Button onClick={handleEdit}>Save</Button>
        </DialogActions> */}
      </Dialog>
    </React.Fragment>
  );
}

EditModelDialog.propTypes = {
  modelToConfigure: PropTypes.string.isRequired,
};

export default EditModelDialog;
