import { useEffect, useState } from "react";
import { getExperiments as getExperimentsRequest } from "../../../api/experiment";

/*
 * Custom hook to fetch experiments from the backend
 * @param {function} onSuccess - callback function to be called on successful fetch
 * @param {function} onError - callback function to be called on error
 * @param {function} onSettled - callback function to be called on completion of fetch
 * @param {boolean} refresh - boolean to indicate whether to refresh the experiments
 */
export default function useExperiments({
  onSuccess,
  onError,
  onSettled,
  refresh = false,
}) {
  const [loading, setLoading] = useState(true);
  const [experiments, setExperiments] = useState([]);

  useEffect(() => {
    if (refresh) {
      const getExperiments = async () => {
        setLoading(true);
        try {
          const experiments = await getExperimentsRequest();
          setExperiments(experiments);
          // initially set all experiments running state to false
          const initialRunningState = experiments.reduce(
            (accumulator, current) => {
              return { ...accumulator, [current.id]: false };
            },
            {},
          );
          onSuccess && onSuccess(initialRunningState);
        } catch (error) {
          onError && onError(error);
          if (error.response) {
            console.error("Response error:", error.message);
          } else if (error.request) {
            console.error("Request error", error.request);
          } else {
            console.error("Unknown Error", error.message);
          }
        } finally {
          onSettled && onSettled();
          setLoading(false);
        }
      };

      getExperiments();
    }
  }, [refresh]);

  return { experiments, loading };
}
