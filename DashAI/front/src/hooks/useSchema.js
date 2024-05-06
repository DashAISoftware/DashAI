import { useEffect, useState } from "react";
import { getComponents } from "../api/component";
import { formattedModel, generateYupSchema } from "../utils/schema";

/**
 * This hook is used to get the schema of a model, it will return the schema and the initial values of the model
 * @param {string} modelName - The name of the model to get the schema
 */

export default function useSchema({ modelName = null } = {}) {
  const [model, setModel] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const getModel = async () => {
      try {
        setLoading(true);
        const result = await getComponents({
          model: modelName,
        });

        const formattedSchema = await formattedModel(result?.schema);

        setModel(formattedSchema);
      } catch (error) {
        console.log(error);
      } finally {
        setLoading(false);
      }
    };

    if (modelName) {
      getModel();
    }
  }, [modelName]);

  const { schema, initialValues } = model
    ? generateYupSchema(model)
    : { schema: {}, initialValues: {} };

  return {
    modelSchema: model,
    defaultValues: initialValues,
    yupSchema: schema,
    loading,
  };
}
