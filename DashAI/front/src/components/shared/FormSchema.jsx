/* eslint-disable react/prop-types */
import { Button, ButtonGroup } from "@mui/material";
import React, { useCallback } from "react";
import useFormSchema from "../../hooks/useFormSchema";
import FormSchemaFields from "./FormSchemaFields";
import ModalSchemaFieldsWithOptions from "./FormSchemaFieldsWithOptions";
import FormSchemaParameterContainer from "./FormSchemaParameterContainer";
import FormSchemaSubform from "./FormSchemaSubform";
/**
 * This code implements a component that is responsible for rendering the main form,
 * managing the values of all the subforms, and submitting the values of the parameters.
 * It acts as a central control point for the entire form.
 * @param {object} parameterSchema JSON object that describes a configurable object
 * @param {object} defaultValues default values of the parameters, obtained from parameterSchema
 * @param {object} extraOptions a component of code that includes additional behavior to the form
 * @param {bool} submitButton true to render a submit button, false to not.
 * @param {function} onFormSubmit  function that submits the form, receives the parameter values as a key-value object.
 * The function should be defined as follows: (values) => {...}
 * @param {Array} getValues array [name_of_parameter, function] the function is called when the parameter changes
 * to include additional behavior to the form e.g showing more parameters depending on a boolean value.
 */
function FormSchema({
  model,
  initialValues,
  onFormSubmit,
  autoSave,
  onCancel,
  extraOptions,
  formSubmitRef,
}) {
  // manages and submits the values of the parameters in the form

  const { formik, modelSchema, loading, handleUpdateSchema } = useFormSchema({
    model,
    initialValues,
    formSubmitRef,
  });

  const renderFields = useCallback(() => {
    const fields = [];

    const onChange = (name, subName) => (value) => {
      if (subName) {
        handleUpdateSchema(
          { [name]: { [subName]: value } },
          autoSave ? onFormSubmit : null,
        );
        formik.setFieldValue(name, {
          ...formik.values[name],
          [subName]: value,
        });
        return;
      }

      handleUpdateSchema({ [name]: value }, autoSave ? onFormSubmit : null);
      formik.setFieldValue(name, value);
    };

    for (const key in modelSchema) {
      const fieldSchema = modelSchema[key];
      const objName = key;

      if ("anyOf" in fieldSchema) {
        fields.push(
          <ModalSchemaFieldsWithOptions
            title={fieldSchema.title}
            description={fieldSchema.description}
            options={fieldSchema.anyOf}
            name={objName}
            field={{
              value: formik.values[objName],
              onChange: onChange(objName),
              error: formik.errors[objName],
            }}
          />,
        );
      } else if (fieldSchema.type === "object") {
        fields.push(
          fieldSchema.parent ? (
            <FormSchemaSubform
              name={objName}
              label={fieldSchema.title}
              description={fieldSchema.description}
            />
          ) : (
            <FormSchemaSubform
              name={objName}
              label={fieldSchema.title}
              description={fieldSchema.description}
            >
              {Object.keys(fieldSchema.properties).map((subField) => {
                const fieldSubschema = fieldSchema.properties[subField];
                const subfieldName = objName + "." + subField;

                const value = formik.values[objName]
                  ? formik.values[objName][subField]
                  : null;
                const error = formik.errors[objName]
                  ? formik.errors[objName][subField]
                  : undefined;

                return (
                  <FormSchemaFields
                    key={subfieldName}
                    objName={subfieldName}
                    paramJsonSchema={fieldSubschema}
                    field={{
                      value,
                      onChange: onChange(objName, subField),
                      error,
                    }}
                  />
                );
              })}
            </FormSchemaSubform>
          ),
        );
      } else {
        fields.push(
          <FormSchemaFields
            objName={objName}
            paramJsonSchema={fieldSchema}
            field={{
              value: formik.values[objName],
              onChange: onChange(objName),
              error: formik.errors[objName],
            }}
          />,
        );
      }
    }

    return fields;
  }, [modelSchema, formik, autoSave]);

  return (
    <>
      <FormSchemaParameterContainer>
        {loading ? <>loading..</> : renderFields()}{" "}
      </FormSchemaParameterContainer>
      {/* Renders additional behavior if extraOptions is not null */}
      {extraOptions}
      {/* renders a submit button if submitButton is true */}

      <ButtonGroup size="large" sx={{ justifyContent: "flex-end" }}>
        {onCancel && (
          <Button variant="outlined" onClick={onCancel}>
            Back
          </Button>
        )}
        {!autoSave && (
          <Button variant="contained" onClick={onFormSubmit}>
            Save
          </Button>
        )}
      </ButtonGroup>
    </>
  );
}

export default FormSchema;
