import SettingsIcon from "@mui/icons-material/Settings";
import { GridActionsCellItem } from "@mui/x-data-grid";
import PropTypes from "prop-types";
import React, { useState } from "react";
import FormSchema from "../shared/FormSchema";
import FormSchemaDialog from "../shared/FormSchemaDialog";
/**
 * This component handles the configuration of a single model
 * @param {string} modelToConfigure name of the model to configure
 * @param {function} updateParameters updates the parameters of the model to configure in the modal state (newExp.runs)
 * @param {object} paramsInitialValues Initial values for the model to be configured, used so that the user can edit the parameters,
 * picking up from the last time they configured.
 */
function EditModelDialog({
  modelToConfigure,
  updateParameters,
  paramsInitialValues,
}) {
  // const { enqueueSnackbar } = useSnackbar();
  const [open, setOpen] = useState(false);
  // const [loading, setLoading] = useState(true);
  // const [modelSchema, setFormSchema] = useState({});

  // const getObjectSchema = async () => {
  //   setLoading(true);
  //   try {
  //     const schema = await getFormSchemaRequest(modelToConfigure);
  //     setFormSchema(schema);
  //   } catch (error) {
  //     enqueueSnackbar("Error while trying to obtain model schema");
  //     if (error.response) {
  //       console.error("Response error:", error.message);
  //     } else if (error.request) {
  //       console.error("Request error", error.request);
  //     } else {
  //       console.error("Unknown Error", error.message);
  //     }
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  // // fetches the JSON object on mount
  // useEffect(() => {
  //   getObjectSchema();
  // }, []

  return (
    <React.Fragment>
      <GridActionsCellItem
        key="edit-button"
        icon={<SettingsIcon />}
        label="Edit"
        onClick={() => setOpen(true)}
      />
      <FormSchemaDialog
        modelToConfigure={modelToConfigure}
        open={open}
        setOpen={setOpen}
        onFormSubmit={(values) => {
          updateParameters(values);
          setOpen(false);
        }}
      >
        <FormSchema
          onFormSubmit={(values) => {
            updateParameters(values);
            setOpen(false);
          }}
          modelToConfigure={modelToConfigure}
          initialValues={paramsInitialValues}
          onCancel={() => setOpen(false)}
        />
      </FormSchemaDialog>
    </React.Fragment>
  );
}

EditModelDialog.propTypes = {
  modelToConfigure: PropTypes.string.isRequired,
  updateParameters: PropTypes.func.isRequired,
  paramsInitialValues: PropTypes.objectOf(
    PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.bool,
      PropTypes.number,
      PropTypes.object,
    ]),
  ),
};

export default EditModelDialog;
