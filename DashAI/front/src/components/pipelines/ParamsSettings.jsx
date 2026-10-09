import React from "react";
import PropTypes from "prop-types";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogActions,
  Button,
  Stack,
  IconButton,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import FormSchemaField from "../../components/shared/FormSchemaField";
import FormSchemaFieldWithOptions from "../../components/shared/FormSchemaFieldWithOptions";
import FormSchemaFieldWithCollapse from "../../components/shared/FormSchemaFieldWithCollapse";
import FormSchemaFieldWithOptimizers from "../../components/shared/FormSchemaFieldWithOptimizers";
import FormSchemaFieldWithParent from "../../components/shared/FormSchemaFieldWithParent";
import { getModelFromSubform, normalizeEmptyValue } from "../../utils/schema";

function ParamsSettings({
  open,
  modelSchema = null,
  values = {},
  onChange,
  onClose,
}) {
  if (!modelSchema) return null;

  const [localValues, setLocalValues] = React.useState(values || {});

  React.useEffect(() => {
    setLocalValues(values || {});
  }, [values]);

  const handleFieldChange = (fieldName, fieldValue) => {
    setLocalValues((prev) => {
      const newValues = { ...prev };
      const parts = fieldName.split(".");
      let current = newValues;

      for (let i = 0; i < parts.length - 1; i++) {
        const part = parts[i];
        if (!current[part]) current[part] = {};
        current = current[part];
      }

      current[parts[parts.length - 1]] = fieldValue;
      return newValues;
    });
  };

  const createSelectInputHandler = (fieldName) => {
    return (value) => {
      handleFieldChange(fieldName, value);
    };
  };

  const renderFields = () => {
    const fields = [];

    for (const key in modelSchema) {
      const fieldSchema = modelSchema[key];
      const objName = key;
      const value = localValues?.[objName];

      const fieldOnChange = (fieldValue) => {
        // Same shared helper as the main renderer: this fork exists only
        // because the shared one needs a provider context, so the empty-value
        // semantics must not differ between the two. When the two dispatchers
        // are collapsed, this call site goes with them.
        handleFieldChange(
          objName,
          normalizeEmptyValue(fieldValue, fieldSchema),
        );
      };

      if ("anyOf" in fieldSchema) {
        fields.push(
          <FormSchemaFieldWithOptions
            key={objName}
            title={fieldSchema.title}
            description={fieldSchema.description}
            options={fieldSchema.anyOf}
            required={fieldSchema.required}
            objName={objName}
            placeholder={fieldSchema.placeholder}
            field={{
              value: value,
              onChange: fieldOnChange,
            }}
          />,
        );
      } else if (fieldSchema.type === "object") {
        if (fieldSchema.placeholder?.optimize !== undefined) {
          fields.push(
            <FormSchemaFieldWithOptimizers
              key={objName}
              objName={objName}
              paramJsonSchema={fieldSchema}
              field={{
                value: value,
                onChange: fieldOnChange,
              }}
            />,
          );
        } else if (Boolean(fieldSchema?.parent)) {
          fields.push(
            <FormSchemaFieldWithParent
              key={objName}
              name={objName}
              label={fieldSchema.title}
              description={fieldSchema.description}
              selectedModel={getModelFromSubform(value)}
              field={{
                value: value,
                onChange: fieldOnChange,
              }}
            />,
          );
        } else {
          fields.push(
            <FormSchemaFieldWithCollapse
              key={objName}
              name={objName}
              label={fieldSchema.title}
              description={fieldSchema.description}
            >
              {fieldSchema?.properties &&
                Object.keys(fieldSchema.properties).map((subField) => {
                  const fieldSubschema = fieldSchema.properties[subField];
                  const subfieldName = objName + "." + subField;
                  const subValue = localValues?.[objName]?.[subField];

                  return (
                    <FormSchemaField
                      key={subfieldName}
                      objName={subfieldName}
                      paramJsonSchema={fieldSubschema}
                      field={{
                        value: subValue,
                        onChange: createSelectInputHandler(subfieldName),
                      }}
                    />
                  );
                })}
            </FormSchemaFieldWithCollapse>,
          );
        }
      } else {
        fields.push(
          <FormSchemaField
            key={objName}
            objName={objName}
            paramJsonSchema={fieldSchema}
            field={{
              value: value,
              onChange: fieldOnChange,
            }}
          />,
        );
      }
    }

    return fields;
  };

  const handleSave = () => {
    onChange(localValues);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle
        sx={{
          m: 0,
          p: 4,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        Model Settings
        <IconButton
          aria-label="close"
          onClick={onClose}
          sx={{
            color: (theme) => theme.palette.grey[500],
          }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent>
        <Stack spacing={4}>{renderFields()}</Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleSave} color="primary">
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
}

ParamsSettings.propTypes = {
  open: PropTypes.bool.isRequired,
  modelSchema: PropTypes.object,
  values: PropTypes.object,
  onChange: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
};

export default ParamsSettings;
