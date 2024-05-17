import { Button, ButtonGroup } from "@mui/material";
import React, { useCallback, useState } from "react";
import useFormSchema from "../../hooks/useFormSchema";
import FormSchemaFields from "./FormSchemaFields";
import ModalSchemaFieldsWithOptions from "./FormSchemaFieldsWithOptions";
import FormSchemaParameterContainer from "./FormSchemaParameterContainer";
import FormSchemaSubform from "./FormSchemaSubform";
import PropTypes from "prop-types";
/**
 * This code implements a component that is responsible for rendering the main form,
 * managing the values of all the subforms, and submitting the values of the parameters.
 * It acts as a central control point for the entire form.
 * @param {string} model string that describes a configurable object
 * @param {object} initialValues default values of the parameters, obtained from parameterSchema
 * @param {function} onFormSubmit  function that submits the form, receives the parameter values as a key-value object.
 * @param {bool} autoSave if true, the form will be submitted automatically when a parameter changes
 * @param {function} onCancel function to call when the cancel button is clicked
 * @param {object} extraOptions a component of code that includes additional behavior to the form
 * @param {object} formSubmitRef a reference to the formik object
 * @param {function} setError function to set an error in the form
 * @param {object} errors object that contains the errors of the form
 */
function FormSchema({
  model,
  initialValues,
  onFormSubmit,
  autoSave,
  onCancel,
  extraOptions,
  formSubmitRef,
  setError,
  errors,
}) {
  const [localError, setLocalError] = useState(false);
  const { formik, modelSchema, loading, handleUpdateSchema } = useFormSchema({
    model,
    initialValues,
    formSubmitRef,
    setError,
  });

  const renderFields = useCallback(() => {
    const fields = [];

    const onChange = (name, subName) => (value) => {
      if (subName) {
        handleUpdateSchema(
          { [name]: { ...formik.values[name], [subName]: value } },
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
            key={objName}
            title={fieldSchema.title}
            description={fieldSchema.description}
            options={fieldSchema.anyOf}
            required={fieldSchema.required}
            objName={objName}
            setError={setError || setLocalError}
            field={{
              value: formik.values[objName],
              onChange: onChange(objName),
              error: formik.errors[objName],
            }}
          />,
        );
        
      } else if (fieldSchema.type === "object" && !(fieldSchema.placeholder?.optimize!== undefined)) {
        fields.push(
          fieldSchema.parent ? (
            <FormSchemaSubform
              key={objName}
              name={objName}
              label={fieldSchema.title}
              description={fieldSchema.description}
            />
          ) : (
            <FormSchemaSubform
              key={objName}
              name={objName}
              label={fieldSchema.title}
              description={fieldSchema.description}
              errorMessage={errors?.[objName]?.message}
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
            </FormSchemaSubform>
          ),
        );
      } else {
        fields.push(
          <FormSchemaFields
            key={objName}
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
          <Button
            variant="contained"
            onClick={onFormSubmit}
            disabled={Object.keys(formik?.errors).length > 0 || localError}
          >
            Save
          </Button>
        )}
      </ButtonGroup>
    </>
  );
}

FormSchema.propTypes = {
  model: PropTypes.string,
  initialValues: PropTypes.object,
  onFormSubmit: PropTypes.func,
  autoSave: PropTypes.bool,
  onCancel: PropTypes.func,
  extraOptions: PropTypes.shape({}),
  formSubmitRef: PropTypes.shape({ current: PropTypes.any }),
  setError: PropTypes.func,
  errors: PropTypes.object,
};

export default FormSchema;
