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
import { FormSchemaProvider } from "../../contexts/schema";
import {
  formattedModel,
  formattedSubform,
  generateYupSchema,
  getModelFromSubform,
  getParamsFromSubform,
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
 * Renders a parent-model selector field as a card. The "configure sub-model"
 * icon button lives in the card header and the body contains the model select
 * dropdown.
 *
 * The declared parent is authoritative: it drives both the options request and
 * every value this component writes back. The current selection is read from
 * the field value itself, in either accepted shape, so the component works
 * without a form context.
 *
 * @param {object} props component props
 * @param {string} props.name field name in the parent form, used as the card key
 * @param {string} props.parent schema-declared parent class whose child
 *   components populate the dropdown
 * @param {string} props.label card label
 * @param {object} props.field current field state: `value` plus `onChange`
 * @param {string} [props.description] card description
 * @param {string} [props.errorMessage] validation message shown on the card
 * @returns {JSX.Element} the selector card and its sub-model configuration dialog
 */
function FormSchemaFieldWithParent({
  name,
  parent,
  label,
  field,
  description,
  errorMessage,
}) {
  const parentComponent = parent;
  const { models, markDownloaded } = useModelParents({
    parent: parentComponent,
  });
  const { t } = useTranslation(["common"]);

  // State for handling the sub-modal
  const [openSubModal, setOpenSubModal] = useState(false);
  const formikRef = useRef(null);

  const selectedModelName = getModelFromSubform(field?.value);

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

  /**
   * Params to open the sub-model dialog with.
   *
   * `getParamsFromSubform` reads both accepted value shapes: the generated
   * nested form shape (`properties.params.comp.params`) and a canonical flat
   * ref (`{ component, params }`). When the field has no stored params, the
   * selected model's schema defaults are used instead.
   *
   * @returns {object} initial params for the nested configuration form
   */
  const getSubModelInitialValues = () =>
    getParamsFromSubform(field?.value) ?? subModelDefaultValues ?? {};

  /**
   * Persist the sub-model configuration.
   *
   * Builds a canonical subform from the declared parent rather than whatever
   * parent the stored value carries, so a legacy value that names a concrete
   * component as its parent cannot be re-persisted. Both accepted value shapes
   * are replaced by that canonical nested shape, and `onChange` is the only
   * state write: both call sites propagate the complete value to their own
   * state.
   *
   * @param {object} values params collected by the nested configuration form
   * @returns {void}
   */
  const handleSubModelSave = (values) => {
    if (!parentComponent || !selectedModelName) {
      return;
    }
    const updated = formattedSubform({
      parent: parentComponent,
      model: selectedModelName,
      params: values,
    });
    field.onChange(updated);
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
          value={selectedModelName}
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
  parent: PropTypes.string.isRequired,
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
