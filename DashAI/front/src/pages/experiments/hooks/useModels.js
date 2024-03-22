import { useSnackbar } from "notistack";
import uuid from "react-uuid";
import { getModelSchema as getModelSchemaRequest } from "../../../api/oldEndpoints";
import { getFullDefaultValues } from "../../../api/values";
import { useCallback, useEffect, useState } from "react";

/*
 * Custom hook to fetch the schema of a model
 * @param {string} selectedModel - id of the selected model
 */

export default function useModels({ selectedModel }) {
  const { enqueueSnackbar } = useSnackbar();
  const [schema, setSchema] = useState({});
  const [loading, setLoading] = useState(false);

  const getModel = useCallback(async () => {
    const schemaDefaultValues = await getFullDefaultValues(schema);
    return {
      id: uuid(),
      name,
      model: selectedModel,
      params: schemaDefaultValues,
    };
  }, [schema, selectedModel]);

  useEffect(() => {
    const getModelSchema = async () => {
      setLoading(true);
      try {
        const schema = await getModelSchemaRequest(selectedModel);
        setSchema(schema);
      } catch (error) {
        enqueueSnackbar("Error while trying to obtain model schema");
        if (error.response) {
          console.error("Response error:", error.message);
        } else if (error.request) {
          console.error("Request error", error.request);
        } else {
          console.error("Unknown Error", error.message);
        }
      } finally {
        setLoading(false);
      }
    };
    if (selectedModel && selectedModel !== "") {
      getModelSchema();
    }
  }, [selectedModel]);

  return { schema, loading, getModel };
}
