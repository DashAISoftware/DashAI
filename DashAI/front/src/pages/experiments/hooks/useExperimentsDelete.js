import { useState } from "react";
import { deleteExperiment as deleteExperimentRequest } from "../../../api/experiment";

/*
 * Custom hook to delete an experiment
 * @param {function} onSuccess - callback function to be called on successful fetch
 * @param {function} onError - callback function to be called on error
 */

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
