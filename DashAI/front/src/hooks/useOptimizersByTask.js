import { useState, useEffect } from "react";
import { getComponents as getComponentsRequest } from "../api/component";
import { useSnackbar } from "notistack";

export default function useOptimizersByTask({ taskName }) {
  const [compatibleModels, setCompatibleOptimizers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { enqueueSnackbar } = useSnackbar();

  const getCompatibleOptimizers = async () => {
    setLoading(true);
    try {
      const optimizers = await getComponentsRequest({
        selectTypes: ["Optimizer"],
        relatedComponent: taskName,
      });
      setCompatibleOptimizers(optimizers);
      setError(null);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain compatible optimizers");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
      setError(error);
    } finally {
      setLoading(false);
    }
  };

  // in mount, fetches the compatible models with the previously selected task
  useEffect(() => {
    getCompatibleOptimizers();
  }, []);

  return { compatibleModels, loading, error };
}
