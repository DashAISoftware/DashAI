import SettingsIcon from "@mui/icons-material/Settings";
import PropTypes from "prop-types";
import React, { useState } from "react";
import { IconButton, Tooltip } from "@mui/material";
import FormSchemaDialog from "../shared/FormSchemaDialog";
import FormSchemaWithSelectedModel from "../shared/FormSchemaWithSelectedModel";
import { useTranslation } from "react-i18next";

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
  const [open, setOpen] = useState(false);
  const { t } = useTranslation("common");

  return (
    <React.Fragment>
      <Tooltip title={t("edit")}>
        <span>
          <IconButton
            key="edit-button"
            size="small"
            aria-label={t("edit")}
            onClick={() => setOpen(true)}
          >
            <SettingsIcon />
          </IconButton>
        </span>
      </Tooltip>
      <FormSchemaDialog
        modelToConfigure={modelToConfigure}
        open={open}
        setOpen={setOpen}
        onFormSubmit={(values) => {
          updateParameters(values);
          setOpen(false);
        }}
      >
        <FormSchemaWithSelectedModel
          modelToConfigure={modelToConfigure}
          initialValues={paramsInitialValues}
          onFormSubmit={(values) => {
            updateParameters(values);
            setOpen(false);
          }}
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
