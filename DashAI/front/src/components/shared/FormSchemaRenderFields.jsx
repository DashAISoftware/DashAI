import { useCallback, useMemo } from "react";
import FormSchemaField from "./FormSchemaField";
import FormSchemaFieldCard from "./FormSchemaFieldCard";
import FormSchemaFieldWithOptions from "./FormSchemaFieldWithOptions";
import FormSchemaFieldWithCollapse from "./FormSchemaFieldWithCollapse";
import FormSchemaFieldWithOptimizers from "./FormSchemaFieldWithOptimizers";
import FormSchemaFieldWithParent from "./FormSchemaFieldWithParent";
import { getModelFromSubform } from "../../utils/schema";
import { Stack } from "@mui/material";
import PropTypes from "prop-types";

// Extracted to its own component so useMemo is called at the top level (Rules of Hooks)
function SubFieldItem({
  objName,
  subField,
  value,
  error,
  handleChange,
  setError,
  fieldSubschema,
}) {
  const subFieldObj = useMemo(
    () => ({
      value: value?.[subField],
      error: error?.[subField],
      onChange: handleChange(objName, subField),
    }),
    [value, error, objName, subField, handleChange],
  );

  return (
    <FormSchemaField
      objName={`${objName}.${subField}`}
      setError={setError}
      paramJsonSchema={fieldSubschema}
      field={subFieldObj}
    />
  );
}

SubFieldItem.propTypes = {
  objName: PropTypes.string.isRequired,
  subField: PropTypes.string.isRequired,
  value: PropTypes.any,
  error: PropTypes.any,
  handleChange: PropTypes.func.isRequired,
  setError: PropTypes.func,
  fieldSubschema: PropTypes.object.isRequired,
};

function FormSchemaRenderFields({
  modelSchema,
  formik,
  autoSave,
  handleUpdateSchema,
  onFormSubmit,
  setError,
  errorsMessage,
  spacing = 1,
  excludeFields = [],
}) {
  if (!modelSchema) return null;

  const handleChange = useCallback(
    (name, subName) => (value) => {
      const fieldPath = subName ? `${name}.${subName}` : name;
      formik.setFieldValue(fieldPath, value, true);
      // Always pass complete formik.values so handleUpdateSchema receives
      // ALL fields regardless of whether the context store has been
      // initialised yet (prevents race-condition with useEffect init).
      handleUpdateSchema(
        { ...formik.values, [fieldPath]: value },
        autoSave ? onFormSubmit : null,
      );
    },
    [formik, handleUpdateSchema, autoSave, onFormSubmit],
  );

  const renderFields = useCallback(() => {
    const fields = [];

    for (const key in modelSchema) {
      // Fields the caller renders by hand: a schema field whose input needs
      // context the schema cannot carry, such as a dataset's column names.
      if (excludeFields.includes(key)) continue;

      const fieldSchema = modelSchema[key];
      const objName = key;
      const value = formik?.values?.[objName];
      const error = formik?.errors?.[objName];
      const isOptimizable = fieldSchema.placeholder?.optimize !== undefined;

      const baseField = {
        value,
        error,
        onChange: handleChange(objName),
      };

      if ("anyOf" in fieldSchema) {
        // FormSchemaFieldWithOptions renders its own card
        fields.push(
          <FormSchemaFieldWithOptions
            key={objName}
            title={fieldSchema.title}
            description={fieldSchema.description}
            options={fieldSchema.anyOf}
            required={fieldSchema.required}
            objName={objName}
            setError={setError}
            field={baseField}
          />,
        );
      } else if (isOptimizable) {
        // FormSchemaFieldWithOptimizers renders its own card
        fields.push(
          <FormSchemaFieldWithOptimizers
            key={objName}
            objName={objName}
            paramJsonSchema={fieldSchema}
            field={baseField}
          />,
        );
      } else if (fieldSchema.type === "object") {
        if (Boolean(fieldSchema?.parent)) {
          // FormSchemaFieldWithParent renders its own card
          fields.push(
            <FormSchemaFieldWithParent
              key={objName}
              name={objName}
              field={baseField}
              selectedModel={getModelFromSubform(value)}
              label={fieldSchema.title}
              description={fieldSchema.description}
            />,
          );
        } else {
          // FormSchemaFieldWithCollapse renders its own card
          fields.push(
            <FormSchemaFieldWithCollapse
              key={objName}
              name={objName}
              label={fieldSchema.title}
              description={fieldSchema.description}
              errorMessage={errorsMessage?.[objName]?.message}
            >
              {fieldSchema?.properties &&
                Object.keys(fieldSchema.properties).map((subField) => (
                  <SubFieldItem
                    key={`${objName}.${subField}`}
                    objName={objName}
                    subField={subField}
                    value={value}
                    error={error}
                    handleChange={handleChange}
                    setError={setError}
                    fieldSubschema={fieldSchema.properties[subField]}
                  />
                ))}
            </FormSchemaFieldWithCollapse>,
          );
        }
      } else {
        // Simple scalar fields — wrap in a card here
        fields.push(
          <FormSchemaFieldCard
            key={objName}
            label={fieldSchema.title}
            paramKey={objName}
            description={fieldSchema.description}
          >
            <FormSchemaField
              objName={objName}
              paramJsonSchema={fieldSchema}
              field={baseField}
            />
          </FormSchemaFieldCard>,
        );
      }
    }

    return fields;
  }, [
    modelSchema,
    formik.values,
    formik.errors,
    handleChange,
    setError,
    errorsMessage,
    excludeFields,
  ]);

  return <Stack spacing={spacing}>{renderFields()}</Stack>;
}

FormSchemaRenderFields.propTypes = {
  modelSchema: PropTypes.object,
  formik: PropTypes.object.isRequired,
  autoSave: PropTypes.bool,
  handleUpdateSchema: PropTypes.func.isRequired,
  onFormSubmit: PropTypes.func,
  setError: PropTypes.func,
  errorsMessage: PropTypes.object,
  spacing: PropTypes.number,
  excludeFields: PropTypes.arrayOf(PropTypes.string),
};

export default FormSchemaRenderFields;
