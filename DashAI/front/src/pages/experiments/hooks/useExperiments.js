import { useEffect, useState } from "react";
import { getExperiments as getExperimentsRequest } from "../../../api/experiment";

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
