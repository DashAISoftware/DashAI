import { useFormik } from "formik";
import { useEffect } from "react";
import { useFormSchemaStore } from "../contexts/schema";
import useSchema from "./useSchema";

function useFormSchema({ model, initialValues, formSubmitRef }) {
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

  useEffect(() => {
    if (formSubmitRef) {
      formSubmitRef.current = formik;
    }
  }, [formSubmitRef, formik]);

  useEffect(() => {
    if (formValues && Object.keys(formValues).length === 0) {
      if (initialValues && Object.keys(initialValues).length > 0) {
        handleUpdateSchema(initialValues);
      } else if (defaultValues && Object.keys(defaultValues).length > 0) {
        handleUpdateSchema(defaultValues);
      }
    }
  }, [formValues, initialValues, defaultValues]);

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
