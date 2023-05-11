import React, { useState } from "react";
import PropTypes from "prop-types";
import { DialogContentText, Grid, Paper } from "@mui/material";
import ParameterForm from "./ParameterForm";
import SplitsParams from "./SplitsParams";
import { getDefaultValues } from "../../utils/values";
/**
 * To show the dataloader's parameters to be able to upload the data,
 * is displayed a modal with ParameterForm, but inside this modal
 * it is the splits div there, passed like a extra section.
 * @param {*} param0
 * @returns
 */
function ParamsModal({ dataloader, paramsSchema, newDataset, onSubmit }) {
  const [showSplitConfig, setShowSplitConfig] = useState(false);
  const [showMoreOptions, setShowMoreOptions] = useState(false);
  const [showSplitsError, setSplitsError] = useState(false);
  /*
How the parameters are in different sections,
we need to join all the parameters in a single JSON
to send to the endpoint. For that depending on the
parameters model defined in backend (pydantic model)
here is building that JSON of parameters.
*/
  const handleSubmitButtonClick = (modelName, values) => {
    const auxForm = { ...newDataset };
    let sum = 0;
    const appendItemsToJSON = (object, items) => {
      for (let i = 0; i < Object.keys(items).length; i += 1) {
        const key = Object.keys(items)[i];
        const value = items[key];
        auxForm[object][key] = value;
      }
    };
    if (auxForm.splits === undefined) {
      // If user leaves the default values in split settings
      auxForm.splits = getDefaultValues(paramsSchema.splits);
      const moreOptions = getDefaultValues(paramsSchema.splits.more_options);
      appendItemsToJSON("splits", moreOptions);
    }
    switch (modelName) {
      case "splits": // Add the splits parameters
        sum = values.train_size + values.test_size + values.val_size;
        if (sum >= 0.999 && sum <= 1) {
          setSplitsError(false);
          appendItemsToJSON("splits", values);
          onSubmit(auxForm);
        } else {
          setSplitsError(true);
        }
        break;
      case "Advanced": // Add the more options parameters
        appendItemsToJSON("splits", values);
        onSubmit(auxForm);
        break;
      default: // Add the rest of parameters of principal modal
        auxForm.dataloader_params = values;
        if (values.class_column !== undefined) {
          auxForm.class_column = values.class_column;
          delete auxForm.dataloader_params.class_column;
        }
        if (values.splits_in_folders !== undefined) {
          auxForm.splits_in_folders = values.splits_in_folders;
          delete auxForm.dataloader_params.splits_in_folders;
        }
        onSubmit(auxForm);
    }
  };

  return (
    <Paper
      variant="outlined"
      sx={{ p: 4, maxHeight: "55vh", overflow: "auto" }}
    >
      <Grid container direction={"column"} alignItems={"center"}>
        <Grid item>
          <DialogContentText>{dataloader} configuration</DialogContentText>
        </Grid>
        <Grid item sx={{ p: 3 }}>
          <ParameterForm
            parameterSchema={paramsSchema}
            onFormSubmit={(values) => {
              handleSubmitButtonClick(dataloader, values);
            }}
            submitButton
            extraOptions={
              <div style={{ marginBottom: "15px" }}>
                {paramsSchema.splits !== undefined ? (
                  <SplitsParams
                    paramsSchema={paramsSchema.splits}
                    onSubmit={handleSubmitButtonClick} // TODO: build json to submit
                    showSplitConfig={showSplitConfig}
                    setSplitConfig={setShowSplitConfig}
                    showMoreOptions={showMoreOptions}
                    setShowMoreOptions={setShowMoreOptions}
                    showSplitsError={showSplitsError}
                  />
                ) : null}
              </div>
            }
            getValues={
              paramsSchema.properties.splits_in_folders !== undefined
                ? ["splits_in_folders", setShowSplitConfig]
                : null
            }
          />
        </Grid>
      </Grid>
    </Paper>
  );
}
ParamsModal.propTypes = {
  dataloader: PropTypes.string.isRequired,
  paramsSchema: PropTypes.objectOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object]),
  ).isRequired,
  onSubmit: PropTypes.func.isRequired,
  newDataset: PropTypes.shape({
    task_name: PropTypes.string,
    dataloader_name: PropTypes.string,
  }).isRequired,
};

export default ParamsModal;
