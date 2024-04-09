/* eslint-disable no-unused-vars */
import React, { useState } from "react";
import PropTypes from "prop-types";
import { DialogContentText, Grid, Paper } from "@mui/material";
import ParameterForm from "../configurableObject/ParameterForm";
import SplitsParams from "../configurableObject/SplitsParams";
import { getDefaultValues } from "../../utils/values";
import FormSchemaLayout from "../shared/FormSchemaLayout";
import FormSchema from "../shared/FormSchema";
/**
 * To show the dataloader's parameters to be able to upload the data,
 * is displayed a modal with ParameterForm, but inside this modal
 * it is the splits div there, passed like a extra section.
 * @param {string} dataloader name of the dataloader to configure
 * @param {object} paramsSchema JSON with the parameters of the dataloder
 * @param {object} newDataset An object that stores all the important states for the dataset modal.
 * @param {function} onSubmit  Function to handle values when submitting the dataloader configuration form
 * @param {object} formSubmitRef useRef to trigger form submit from outside "ParameterForm" component
 */
function DataloaderConfiguration({
  dataloader,
  paramsSchema,
  newDataset,
  onSubmit,
  formSubmitRef,
}) {
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
    console.log(values);
    const auxForm = { ...newDataset };
    // let sum = 0;
    const appendItemsToJSON = (object, items) => {
      for (let i = 0; i < Object.keys(items).length; i += 1) {
        const key = Object.keys(items)[i];
        const value = items[key];
        auxForm[object][key] = value;
      }
    };

    // if (auxForm.splits === undefined) {
    //   // If user leaves the default values in split settings
    //   auxForm.splits = getDefaultValues(paramsSchema.splits);
    //   const moreOptions = getDefaultValues(paramsSchema.splits.more_options);
    //   appendItemsToJSON("splits", moreOptions);
    // }
    // switch (modelName) {
    //   case "splits": // Add the splits parameters
    //     sum = values.train_size + values.test_size + values.val_size;
    //     if (sum >= 0.999 && sum <= 1) {
    //       setSplitsError(false);
    //       appendItemsToJSON("splits", values);
    //       onSubmit(auxForm);
    //     } else {
    //       setSplitsError(true);
    //     }
    //     break;
    //   case "Advanced": // Add the more options parameters
    //     appendItemsToJSON("splits", values);
    //     onSubmit(auxForm);
    //     break;
    //   default: // Add the rest of parameters of principal modal
    //     auxForm.dataloader_params = values;
    //     if (values.class_column !== undefined) {
    //       auxForm.class_column = values.class_column;
    //       delete auxForm.dataloader_params.class_column;
    //     }
    //     if (values.splits_in_folders !== undefined) {
    //       auxForm.splits_in_folders = values.splits_in_folders;
    //       delete auxForm.dataloader_params.splits_in_folders;
    //     }
    //     onSubmit(auxForm);
    // }
  };

  return (
    <Paper variant="outlined" sx={{ p: 4 }}>
      <Grid container direction={"column"} alignItems={"center"}>
        {/* Form title */}
        <Grid item>
          <DialogContentText>{dataloader} configuration</DialogContentText>
        </Grid>
        <Grid item sx={{ p: 3 }}>
          {/* Main dataloader form */}
          <FormSchemaLayout>
            <FormSchema
              autoSave
              model={dataloader}
              onFormSubmit={(values) => {
                handleSubmitButtonClick(dataloader, values);
              }}
              formSubmitRef={formSubmitRef}
              // extraOptions={
              //   // form to configure the splits
              //   <div style={{ marginBottom: "15px" }}>
              //     {paramsSchema.splits !== undefined ? (
              //       <SplitsParams
              //         paramsSchema={paramsSchema.splits}
              //         onSubmit={handleSubmitButtonClick} // TODO: build json to submit
              //         showSplitConfig={showSplitConfig}
              //         setSplitConfig={setShowSplitConfig}
              //         showMoreOptions={showMoreOptions}
              //         setShowMoreOptions={setShowMoreOptions}
              //         showSplitsError={showSplitsError}
              //       />
              //     ) : null}
              //   </div>
              // }
              // getValues={
              //   paramsSchema.properties.splits_in_folders !== undefined
              //     ? ["splits_in_folders", setShowSplitConfig]
              //     : null
              // }
            />
          </FormSchemaLayout>
        </Grid>
      </Grid>
    </Paper>
  );
}
DataloaderConfiguration.propTypes = {
  dataloader: PropTypes.string.isRequired,
  paramsSchema: PropTypes.objectOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object]),
  ).isRequired,
  onSubmit: PropTypes.func.isRequired,
  newDataset: PropTypes.shape({
    task_name: PropTypes.string,
    dataloader_name: PropTypes.string,
  }).isRequired,
  formSubmitRef: PropTypes.shape({ current: PropTypes.any }).isRequired,
};

export default DataloaderConfiguration;
