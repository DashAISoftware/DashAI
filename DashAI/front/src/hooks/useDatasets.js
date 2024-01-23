import { useSnackbar } from "notistack";
import { useEffect, useState } from "react";
import { getDatasets as getDatasetsRequest } from "../api/datasets";

export default function useDatasets({ taskName } = {}) {
  const { enqueueSnackbar } = useSnackbar();

  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // fetch datasets when the component is mounting
  useEffect(() => {
    const getDatasets = async () => {
      setLoading(true);
      try {
        const datasets = await getDatasetsRequest();

        const filteredDatasets = taskName
          ? datasets.filter((dataset) => dataset.task_name === taskName)
          : datasets;
        setDatasets(filteredDatasets);
      } catch (error) {
        enqueueSnackbar("Error while trying to obtain the datasets list.");
        setError(true);

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
    getDatasets();
  }, []);
  return { datasets, loading, error };
}
