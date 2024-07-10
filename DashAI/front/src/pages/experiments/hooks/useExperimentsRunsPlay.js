import { useSnackbar } from "notistack";
import {
  enqueueRunnerJob as enqueueRunnerJobRequest,
  startJobQueue as startJobQueueRequest,
} from "../../../api/job";

/*
 * Custom hook to enqueue runs to the job queue
 * @param {function} setExpRunning - callback function to set the experiment running state
 * @param {object} expRunning - object containing the experiments running state
 * @param {object} experiment - experiment object
 * @param {array} rowSelectionModel - array containing the selected runs
 */

export default function useExperimentsRunsPlay({
  setExpRunning,
  expRunning,
  experiment,
  rowSelectionModel,
}) {
  const { enqueueSnackbar } = useSnackbar();

  const enqueueRunnerJob = async (runId) => {
    try {
      await enqueueRunnerJobRequest(runId);
      return false; // return false for sucess
    } catch (error) {
      enqueueSnackbar(`Error while trying to enqueue run with id ${runId}`);
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
      return true; // return true for error
    }
  };

  const startJobQueue = async () => {
    try {
      await startJobQueueRequest();
    } catch (error) {
      setExpRunning({ ...expRunning, [experiment.id]: false });
      enqueueSnackbar("Error while trying to start job queue");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  const handleExecuteRuns = async () => {
    setExpRunning({ ...expRunning, [experiment.id]: true });
    let enqueueErrors = 0;
    // send runs to the job queue
    for (const runId of rowSelectionModel) {
      const error = await enqueueRunnerJob(runId);
      enqueueErrors = error ? enqueueErrors + 1 : enqueueErrors;
    }

    // verify that at least one job was succesfully enqueued to start the job queue
    if (enqueueErrors < rowSelectionModel.length) {
      startJobQueue(true); // true to stop when queue empties
    } else {
      setExpRunning({ ...expRunning, [experiment.id]: false });
    }
  };
  return { handleExecuteRuns };
}
