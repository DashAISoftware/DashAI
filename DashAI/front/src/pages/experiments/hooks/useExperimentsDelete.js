import { useState } from "react";
import { deleteExperiment as deleteExperimentRequest } from "../../../api/experiment";

export default function useExperimentsDelete({ onSuccess, onError }) {
  const [loading, setLoading] = useState(false);

  const deleteExperiment = async (id) => {
    setLoading(true);
    try {
      await deleteExperimentRequest(id);

      onSuccess && onSuccess();
    } catch (error) {
      console.error(error);
      onError && onError();
    } finally {
      setLoading(false);
    }
  };

  return { deleteExperiment, loading };
}
