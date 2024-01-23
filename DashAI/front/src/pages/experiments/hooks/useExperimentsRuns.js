import { useSnackbar } from "notistack";
import { useEffect, useRef, useState } from "react";
import { getRuns as getRunsRequest } from "../../../api/run";
import { getRunStatus } from "../../../utils/runStatus";

export default function useExperimentsRuns({
  experiment,
  expRunning,
  onSuccess,
}) {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(false);
  const intervalRef = useRef(null);

  const { enqueueSnackbar } = useSnackbar();

  const getRuns = async ({ showLoading }) => {
    showLoading && setLoading(true);

    try {
      const runs = await getRunsRequest(experiment.id.toString());

      // transform status code to a string
      const runsWithStringStatus = runs.map((run) => {
        return { ...run, status: getRunStatus(run.status) };
      });

      setRuns(runsWithStringStatus);

      onSuccess && onSuccess(runsWithStringStatus);
    } catch (error) {
      enqueueSnackbar(
        `Error while trying to obtain the runs associated to ${experiment.name}`,
      );
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    } finally {
      showLoading && setLoading(false);
    }
  };

  useEffect(() => {
    getRuns({ showLoading: true });
  }, []);

  // polling to update the state of the runs
  useEffect(() => {
    if (expRunning[experiment.id]) {
      // Fetch data initially
      const initialGetRuns = async () => {
        await getRuns({ showLoading: false });
      };
      initialGetRuns().then(() => {
        // clear previous interval
        clearInterval(intervalRef.current);
        // start polling
        intervalRef.current = setInterval(
          () => getRuns({ showLoading: false }),
          1000, // Poll every 1 second
        );
      });
    } else {
      clearInterval(intervalRef.current);
    }

    return () => clearInterval(intervalRef.current);
  }, [expRunning]);

  return { runs, loading };
}
