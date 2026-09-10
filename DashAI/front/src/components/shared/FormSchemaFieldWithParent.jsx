import {
  Box,
  MenuItem,
  Tooltip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from "@mui/material";
import PropTypes from "prop-types";
import { Input } from "../configurableObject/Inputs/InputStyles";
import React, { useState, useRef } from "react";
import { useFormSchemaStore, FormSchemaProvider } from "../../contexts/schema";
import {
  formattedModel,
  formattedSubform,
  generateYupSchema,
} from "../../utils/schema";
import useModelParents from "../../hooks/useModelParents";
import { Settings } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import FormSchemaFieldCard from "./FormSchemaFieldCard";
import FormSchema from "./FormSchema";
import FormSchemaLayout from "./FormSchemaLayout";
import useSchema from "../../hooks/useSchema";
import ComponentDownloadControl from "../models/model/ComponentDownloadControl";

/**
 * Renders a parent-model selector field as a card.
 * The "configure sub-model" icon button lives in the card header.
 * The body contains the model select dropdown.
 */
function FormSchemaFieldWithParent({
  name,
  label,
  field,
  description,
  errorMessage,
}) {
  const { formValues, setFormValues, getModelFromCurrentProperty } =
    useFormSchemaStore();
  const parentComponent =
    field?.value?.properties?.component ?? field?.value?.component ?? null;
  const { models, markDownloaded } = useModelParents({
    parent: parentComponent,
  });
  const { t } = useTranslation(["common"]);

  // State for handling the sub-modal
  const [openSubModal, setOpenSubModal] = useState(false);
  const formikRef = useRef(null);

  // Get the currently selected model name
  const selectedModelName = getModelFromCurrentProperty(name);

  // Get default values for the sub-model
  const { defaultValues: subModelDefaultValues } = useSchema({
    modelName: selectedModelName,
  });

  const selectedComponent = models?.find(
    (model) => model.name === selectedModelName,
  );

  const handleOnChange = async (event) => {
    if (!parentComponent) {
      return;
    }

    const model = models?.find((model) => model.name === event.target.value);
    if (!model?.schema) {
      return;
    }

    const { initialValues } = generateYupSchema(
      await formattedModel(model?.schema),
    );

    field.onChange(
      formattedSubform({
        parent: parentComponent,
        model: model?.name,
        params: initialValues,
      }),
    );
  };

  const handleClick = () => {
    if (selectedModelName) {
      setOpenSubModal(true);
    }
  };

  // Function to get current values for the sub-model
  const getSubModelInitialValues = () => {
    if (!formValues || !formValues[name]) {
      return subModelDefaultValues || {};
    }

    const fieldValue = formValues[name];
    if (fieldValue?.properties?.params?.comp?.params) {
      return fieldValue.properties.params.comp.params;
    }

    return subModelDefaultValues || {};
  };

  // Handle saving the sub-model configuration
  const handleSubModelSave = (values) => {
    if (formValues && formValues[name]) {
      const model = getModelFromCurrentProperty(name);
      const parent = formValues[name]?.properties?.component ?? parentComponent;
      // Build the updated component-ref value and fire onChange so the
      // parent form's auto-save propagates the change to savedParamsRef.
      const updated = formattedSubform(
        parent && model
          ? { parent, model, params: values }
          : { parent: parentComponent, model: model, params: values },
      );
      setFormValues((prevFormValues) => {
        const updatedFormValues = { ...prevFormValues };
        if (!updatedFormValues[name]) {
          updatedFormValues[name] = {};
        }
        if (!updatedFormValues[name].properties) {
          updatedFormValues[name].properties = {};
        }
        if (!updatedFormValues[name].properties.params) {
          updatedFormValues[name].properties.params = {};
        }
        if (!updatedFormValues[name].properties.params.comp) {
          updatedFormValues[name].properties.params.comp = { params: {} };
        }
        updatedFormValues[name].properties.params.comp.params = {
          ...updatedFormValues[name].properties.params.comp.params,
          ...values,
        };
        return updatedFormValues;
      });
      // Trigger the parent form's onChange to propagate auto-save
      field.onChange(updated);
    }
    setOpenSubModal(false);
  };

  const configureButton = (
    <Tooltip title={t("common:configureSubmodel")}>
      <IconButton size="small" onClick={handleClick}>
        <Settings fontSize="small" />
      </IconButton>
    </Tooltip>
  );

  return (
    <>
      <FormSchemaFieldCard
        label={label}
        paramKey={name}
        description={description}
        errorMessage={errorMessage}
        headerRight={configureButton}
      >
        <Input
          select
          value={getModelFromCurrentProperty(name)}
          onChange={handleOnChange}
          size="small"
          sx={{ width: "100%" }}
        >
          {models?.map((model) => (
            <MenuItem key={model.name} value={model.name}>
              {model.name}
            </MenuItem>
          ))}
        </Input>
        {selectedComponent?.metadata?.requires_download && (
          <Box sx={{ mt: 1 }}>
            <ComponentDownloadControl
              component={selectedComponent}
              onStatusChange={(isDownloaded) =>
                markDownloaded(selectedComponent.name, isDownloaded)
              }
            />
          </Box>
        )}
      </FormSchemaFieldCard>

      <Dialog
        open={openSubModal}
        onClose={() => setOpenSubModal(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            maxHeight: "80vh",
            zIndex: 1400,
          },
        }}
        BackdropProps={{
          sx: {
            zIndex: 1399,
          },
        }}
      >
        <DialogTitle>{`${selectedModelName} Configuration`}</DialogTitle>
        <FormSchemaProvider key={`subform-provider-${selectedModelName}`}>
          <DialogContent dividers sx={{ minHeight: 200 }}>
            {selectedModelName && (
              <FormSchemaLayout>
                <FormSchema
                  model={selectedModelName}
                  initialValues={getSubModelInitialValues()}
                  onFormSubmit={handleSubModelSave}
                  autoSave={false}
                  onCancel={() => setOpenSubModal(false)}
                  formSubmitRef={formikRef}
                  hideButtons={true}
                />
              </FormSchemaLayout>
            )}
          </DialogContent>
        </FormSchemaProvider>
        <DialogActions>
          <Button onClick={() => setOpenSubModal(false)} color="inherit">
            {t("common:cancel")}
          </Button>
          <Button
            onClick={() => {
              if (formikRef.current && formikRef.current.values) {
                handleSubModelSave(formikRef.current.values);
              } else {
                handleSubModelSave(getSubModelInitialValues());
              }
            }}
            variant="contained"
            color="primary"
          >
            {t("common:save")}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

FormSchemaFieldWithParent.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  field: PropTypes.shape({
    value: PropTypes.any,
    onChange: PropTypes.func.isRequired,
    error: PropTypes.any,
  }).isRequired,
  description: PropTypes.string,
  errorMessage: PropTypes.string,
};

export default FormSchemaFieldWithParent;
