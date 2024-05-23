import { useFormik } from "formik";
import { useEffect } from "react";
import { useFormSchemaStore } from "../contexts/schema";
import useSchema from "./useSchema";

/**
 * This hook is used to handle the formik schema of a model, it will initialize the formik schema with the default values of the model
 * @param {string} model - The model to get the schema from
 * @param {object} initialValues - The initial values of the form
 * @param {object} formSubmitRef - The reference to the formik object
 * @param {function} setError - The function to set the error state of the form
 */

function useFormSchema({ model, initialValues, formSubmitRef, setError }) {
  const { modelSchema, defaultValues, yupSchema, loading } = useSchema({
    modelName: model,
  });

  const { formValues, handleUpdateSchema } = useFormSchemaStore();

  const formik = useFormik({
    initialValues:
      initialValues && Object.keys(initialValues).length > 0
        ? initialValues
        : defaultValues,
    enableReinitialize: true,
    validationSchema: yupSchema,
  });



  // Updates the formSubmitRef with the current formik object if formSubmitRef is not null
  useEffect(() => {
    if (formSubmitRef) {
      formSubmitRef.current = formik;
    }
  }, [formSubmitRef, formik]);

  // Updates the formik schema with the initial values if the formValues is empty
  useEffect(() => {
    if (formValues && Object.keys(formValues).length === 0) {
      if (initialValues && Object.keys(initialValues).length > 0) {
        handleUpdateSchema(initialValues);
      } else if (defaultValues && Object.keys(defaultValues).length > 0) {
        handleUpdateSchema(defaultValues);
      }
    }
  }, [formValues, initialValues, defaultValues]);

  // Sets the error state of the form if setError is not null
  useEffect(() => {
    if (setError && formik.errors) {
      const isError = Object.keys(formik.errors).length > 0;
      setError(isError);
    }
  }, [formik.errors, setError]);

  const formProps = {
    formik,
    modelSchema,
    defaultValues,
    loading,
    handleUpdateSchema,
  };

  return formProps;
}

export default useFormSchema;
