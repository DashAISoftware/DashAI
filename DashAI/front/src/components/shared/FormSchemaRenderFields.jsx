import React, { useCallback } from "react";
import FormSchemaField from "./FormSchemaField";
import FormSchemaFieldWithOptions from "./FormSchemaFieldWithOptions";
import FormSchemaFieldWithCollapse from "./FormSchemaFieldWithCollapse";
import FormSchemaFieldWithOptimizers from "./FormSchemaFieldWithOptimizers";
import FormSchemaFieldWithParent from "./FormSchemaFieldWithParent";
import { getModelFromSubform } from "../../utils/schema";

function FormSchemaRenderFields({
  modelSchema,
  formik,
  autoSave,
  handleUpdateSchema,
  onFormSubmit,
  setError,
  errorsMessage,
}) {
  if (!modelSchema) return null;

  const renderFields = useCallback(() => {
    const fields = [];

    const onChange = (name, subName) => (value) => {
      if (subName) {
        handleUpdateSchema(
          { [name]: { ...formik?.values[name], [subName]: value } },
          autoSave ? onFormSubmit : null,
        );
        formik?.setFieldValue(name, {
          ...formik?.values[name],
          [subName]: value,
        });
        return;
      }

      handleUpdateSchema({ [name]: value }, autoSave ? onFormSubmit : null);
      formik?.setFieldValue(name, value);
    };

    for (const key in modelSchema) {
      const fieldSchema = modelSchema[key];
      const objName = key;
      if ("anyOf" in fieldSchema) {
        fields.push(
          <FormSchemaFieldWithOptions
            key={objName}
            title={fieldSchema.title}
            description={fieldSchema.description}
            options={fieldSchema.anyOf}
            required={fieldSchema.required}
            objName={objName}
            setError={setError}
            field={{
              value: formik?.values[objName],
              onChange: onChange(objName),
              error: formik?.errors[objName],
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
                value: formik?.values[objName],
                onChange: onChange(objName),
                error: formik?.errors[objName],
              }}
            />,
          );
        } else if (Boolean(fieldSchema?.parent)) {
          fields.push(
            <FormSchemaFieldWithParent
              key={objName}
              name={objName}
              selectedModel={getModelFromSubform(formik.values[objName])}
              label={fieldSchema.title}
              description={fieldSchema.description}
            />,
          );
        } else {
          fields.push(
            <FormSchemaFieldWithCollapse
              key={objName}
              name={objName}
              label={fieldSchema.title}
              description={fieldSchema.description}
              errorMessage={errorsMessage?.[objName]?.message}
            >
              {fieldSchema?.properties &&
                Object.keys(fieldSchema.properties).map((subField) => {
                  const fieldSubschema = fieldSchema.properties[subField];
                  const subfieldName = objName + "." + subField;

                  const value = formik?.values[objName]
                    ? formik?.values[objName][subField]
                    : null;
                  const error = formik?.errors[objName]
                    ? formik?.errors[objName][subField]
                    : undefined;

                  return (
                    <FormSchemaField
                      key={subfieldName}
                      objName={subfieldName}
                      setError={setError}
                      paramJsonSchema={fieldSubschema}
                      field={{
                        value,
                        onChange: onChange(objName, subField),
                        error,
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
              value: formik?.values[objName],
              onChange: onChange(objName),
              error: formik?.errors[objName],
            }}
          />,
        );
      }
    }

    return fields;
  }, [JSON.stringify(formik.values), modelSchema, autoSave]);

  return <>{renderFields()}</>;
}

export default FormSchemaRenderFields;
