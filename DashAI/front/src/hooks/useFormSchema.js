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
 * @param {function} onValuesChange - The function to call when the form values change
 */

function useFormSchema({
  model,
  initialValues,
  formSubmitRef,
  setError,
  onValuesChange,
}) {
  const { modelSchema, defaultValues, yupSchema, loading } = useSchema({
    modelName: model,
  });

  const { formValues, handleUpdateSchema } = useFormSchemaStore();

  const formik = useFormik({
    initialValues:
      initialValues && Object.keys(initialValues).length > 0
        ? { ...defaultValues, ...initialValues }
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

  // The shared formValues context starts empty on every fresh mount (e.g.
  // switching wizard steps remounts this hook) and gets seeded from
  // initialValues/defaultValues here, one render after mount. hasPendingSeed
  // is exposed so the onValuesChange effect below can avoid notifying the
  // parent with this still-empty value before the seed lands.
  const formValuesEmpty = Object.keys(formValues ?? {}).length === 0;
  const hasInitialValues = Boolean(
    initialValues && Object.keys(initialValues).length > 0,
  );
  const hasDefaultValues = Boolean(
    defaultValues && Object.keys(defaultValues).length > 0,
  );
  const hasPendingSeed =
    formValuesEmpty && (hasInitialValues || hasDefaultValues);

  // Updates the formik schema with the merged initial values if the formValues is empty
  useEffect(() => {
    if (!formValuesEmpty) return;
    if (hasInitialValues) {
      handleUpdateSchema({ ...defaultValues, ...initialValues });
    } else if (hasDefaultValues) {
      handleUpdateSchema(defaultValues);
    }
  }, [
    formValuesEmpty,
    hasInitialValues,
    hasDefaultValues,
    initialValues,
    defaultValues,
  ]);

  // Sets the error state of the form if setError is not null
  useEffect(() => {
    if (setError && formik.errors) {
      const isError = Object.keys(formik.errors).length > 0;
      setError(isError);
    }
  }, [formik.errors, setError]);

  // Skip while a seed is pending — the shared context still holds the empty
  // value from this fresh mount, and notifying now would overwrite the
  // parent's already-correct saved values with that empty object for a beat
  // (visible as a flash of schema-default values) before the seed effect
  // above corrects it.
  useEffect(() => {
    if (onValuesChange && !hasPendingSeed) {
      onValuesChange();
    }
  }, [formik.values, hasPendingSeed]);

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
