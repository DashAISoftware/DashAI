/* eslint-disable no-unused-vars */
import React, { useState } from "react";
import PropTypes from "prop-types";
import { DialogContentText, Grid, Paper, Stack } from "@mui/material";
import ParameterForm from "../configurableObject/ParameterForm";
import SplitsParams from "../configurableObject/SplitsParams";
import { getDefaultValues } from "../../utils/values";
import FormSchemaLayout from "../shared/FormSchemaLayout";
import FormSchema from "../shared/FormSchema";
import { useSnackbar } from "notistack";
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
  onSubmit,
  formSubmitRef,
  error,
  setError,
}) {
  const handleSubmitButtonClick = (values) => {
    const sum =
      values.splits.train_size +
      values.splits.test_size +
      values.splits.val_size;

    if (sum >= 0.999 && sum <= 1) {
      onSubmit(values);
      setError(false);
    } else {
      setError(true);
    }
  };

  return (
    <Paper variant="outlined" sx={{ p: 4 }}>
      <Stack spacing={3}>
        {/* Form title */}

        <DialogContentText sx={{ alignSelf: "center" }}>
          {dataloader} configuration
        </DialogContentText>

        <FormSchemaLayout>
          <FormSchema
            autoSave
            model={dataloader}
            onFormSubmit={(values) => {
              handleSubmitButtonClick(values);
            }}
            formSubmitRef={formSubmitRef}
            errors={
              error
                ? {
                    splits: {
                      message:
                        "The sum of the splits must be between 0.999 and 1",
                    },
                  }
                : null
            }
          />
        </FormSchemaLayout>
      </Stack>
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
  setError: PropTypes.func.isRequired,
  error: PropTypes.bool.isRequired,
};

export default DataloaderConfiguration;
